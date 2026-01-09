from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import typer


def _bh_fdr(pvals: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Benjamini–Hochberg FDR 控制：返回每个 pval 是否拒绝原假设。
    """

    m = len(pvals)
    if m == 0:
        return []
    idx = sorted(range(m), key=lambda i: pvals[i])
    thresh = [alpha * (k + 1) / m for k in range(m)]

    keep = [False] * m
    max_k = -1
    for rank, i in enumerate(idx):
        if pvals[i] <= thresh[rank]:
            max_k = rank
    if max_k >= 0:
        for rank in range(max_k + 1):
            keep[idx[rank]] = True
    return keep


def _safe_filename(s: str) -> str:
    return (
        str(s)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )


def _as_tuple(v: Any) -> Tuple[Any, ...]:
    return v if isinstance(v, tuple) else (v,)


def _bucket_tag(cols: List[str], vals: Any) -> str:
    vals_t = _as_tuple(vals)
    parts: List[str] = []
    for c, v in zip(cols, vals_t):
        if c == "temperature":
            try:
                parts.append(f"t{float(v):g}")
            except Exception:
                parts.append(f"t{_safe_filename(str(v))}")
        elif c == "n_questions":
            try:
                parts.append(f"n{int(v)}")
            except Exception:
                parts.append(f"n{_safe_filename(str(v))}")
        elif c in {"scenario", "model"}:
            parts.append(_safe_filename(str(v)))
        else:
            parts.append(f"{c}-{_safe_filename(str(v))}")
    return "__".join([p for p in parts if p])


def _bucket_title(cols: List[str], vals: Any) -> str:
    vals_t = _as_tuple(vals)
    parts: List[str] = []
    for c, v in zip(cols, vals_t):
        if c == "scenario":
            parts.append(str(v))
        elif c == "temperature":
            try:
                parts.append(f"t={float(v):g}")
            except Exception:
                parts.append(f"t={v}")
        elif c == "n_questions":
            try:
                parts.append(f"n={int(v)}")
            except Exception:
                parts.append(f"n={v}")
        else:
            parts.append(f"{c}={v}")
    return ", ".join(parts)


app = typer.Typer(add_completion=False, help="汇总 results.csv，输出统计表与图（可选统计检验）。")

def _read_jsonl_minimal(path: Path) -> Iterable[Dict[str, Any]]:
    """
    逐行读取 JSONL，返回 dict。
    - 自动跳过空行与解析失败行。
    """
    import json

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _load_questions_meta(questions_jsonl: Path):
    """
    从 questions_v1_clean.jsonl 提取 paper 分析需要的 meta 字段。
    返回 pandas.DataFrame：
      - question_id, scenario, gold, margin, must_n
      - must_has_cost, must_has_lead, must_has_compliance, must_has_weight, must_has_perf
    """
    import pandas as pd

    rows: List[Dict[str, Any]] = []
    for q in _read_jsonl_minimal(questions_jsonl):
        qid = str(q.get("id") or "")
        if not qid:
            continue
        scenario = str(q.get("scenario") or "")
        gold = q.get("answer")
        meta = q.get("meta") or {}
        margin = meta.get("margin", None)
        must_sample = meta.get("must_sample") or []
        # must_sample 里是中文 reason 文本，做粗粒度关键词分类即可
        must_text = "；".join([str(x) for x in must_sample if x is not None])

        def _has_any(keys: List[str]) -> bool:
            return any(k in must_text for k in keys)

        rows.append(
            {
                "question_id": qid,
                "scenario": scenario,
                "gold": gold,
                "margin": float(margin) if margin is not None else float("nan"),
                "must_n": int(len(must_sample)),
                "must_has_cost": _has_any(["成本"]),
                "must_has_lead": _has_any(["交期"]),
                "must_has_compliance": _has_any(["PFAS", "合规", "可持续"]),
                "must_has_weight": _has_any(["克重", "gsm", "臃肿", "bulk"]),
                "must_has_perf": _has_any(["拒水", "防泼", "透气", "耐磨", "保暖", "排汗", "快干", "抗风", "loft", "clo"]),
            }
        )
    return pd.DataFrame(rows)


def _extract_seed_from_run_id(run_id: str) -> int:
    import re

    seed_re = re.compile(r"_seed(\d+)\b")
    m = seed_re.search(str(run_id or ""))
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _load_log_minimal(log_jsonl: Path):
    """
    读取 per_question_log.jsonl，并做去重（同一 run_key+question_id 保留 timestamp 最新的一条）。
    返回 pandas.DataFrame：
      - strategy, scenario, temperature, repeat_idx, seed, question_id
      - pred, is_correct, llm_error
      - tokens, latency_s, calls
      - timestamp
    """
    import pandas as pd

    latest: Dict[Tuple[str, str, float, int, int, str], Dict[str, Any]] = {}
    for row in _read_jsonl_minimal(log_jsonl):
        strategy = str(row.get("strategy") or "")
        scenario = str(row.get("scenario") or "")
        try:
            temperature = float(row.get("temperature") or 0.0)
        except Exception:
            continue
        try:
            repeat_idx = int(row.get("repeat_idx") or 0)
        except Exception:
            continue
        qid = str(row.get("question_id") or "")
        if not qid:
            continue
        run_id = str(row.get("run_id") or "")
        seed = _extract_seed_from_run_id(run_id)
        ts = str(row.get("timestamp") or "")

        usage_sum = row.get("usage_sum") or {}
        try:
            tokens = int(usage_sum.get("total_tokens") or 0)
        except Exception:
            tokens = 0
        try:
            latency_s = float(row.get("latency_sum_s") or 0.0)
        except Exception:
            latency_s = 0.0
        calls_list = row.get("calls") or []
        calls_n = int(len(calls_list)) if isinstance(calls_list, list) else 0

        key = (strategy, scenario, temperature, repeat_idx, seed, qid)
        prev = latest.get(key)
        if prev is None or (ts and str(prev.get("timestamp") or "") < ts):
            latest[key] = {
                "strategy": strategy,
                "scenario": scenario,
                "temperature": temperature,
                "repeat_idx": repeat_idx,
                "seed": seed,
                "question_id": qid,
                "pred": row.get("pred"),
                "is_correct": bool(row.get("is_correct")),
                "llm_error": bool(row.get("llm_error")),
                "tokens": tokens,
                "latency_s": latency_s,
                "calls": calls_n,
                "timestamp": ts,
            }

    return pd.DataFrame(list(latest.values()))


def _ensure_strategy_order(strategies: List[str]) -> List[str]:
    """
    给图/表一个稳定的策略顺序：把 garmentagents_* 放在最后（或按需要突出）。
    """
    known = [
        "zero_shot",
        "few_shot",
        "cot_few_shot",
        "self_reflection",
        "fashionprompt",
        "voting",
        "weighted_voting",
        "borda",
        "garmentagents_fixed",
        "garmentagents_adaptive",
    ]
    s_set = set(strategies)
    ordered = [s for s in known if s in s_set]
    ordered.extend([s for s in strategies if s not in set(ordered)])
    return ordered


@app.command()
def main(
    results: Path = typer.Option(Path("outputs/results.csv"), help="eval_run 输出的 results.csv"),
    out_dir: Path = typer.Option(Path("outputs/figs"), help="图表输出目录"),
    log_jsonl: Optional[Path] = typer.Option(
        None,
        "--log-jsonl",
        help="可选：per_question_log.jsonl 路径。传入后会计算 valid_output_rate / llm_error_rate 并写入汇总表。",
    ),
    questions_jsonl: Optional[Path] = typer.Option(
        None,
        "--questions-jsonl",
        help="可选：questions.jsonl/questions_v1_clean.jsonl。传入后可生成数据集可信度统计与按难度/约束分组表现。",
    ),
    scenario: List[str] = typer.Option([], "--scenario", help="只保留指定场景（可重复指定）。不传则不过滤。"),
    temperature: List[float] = typer.Option([], "--temperature", help="只保留指定温度（可重复指定；浮点用近似匹配）。不传则不过滤。"),
    n_questions: List[int] = typer.Option([], "--n-questions", help="只保留指定题数（可重复指定）。不传则不过滤。"),
    model: List[str] = typer.Option([], "--model", help="只保留指定模型（可重复指定）。不传则不过滤。"),
    by_config: bool = typer.Option(
        True,
        "--by-config/--no-by-config",
        help="默认按 (scenario, temperature, n_questions, model) 分桶汇总/出图，避免混合不同实验设置。",
    ),
    paper: bool = typer.Option(
        False,
        "--paper/--no-paper",
        help="生成论文常见信息结构的额外图表/表格：overall 总表、成本气泡图、场景分组条形、难度分桶热力图、数据集分布。",
    ),
) -> None:
    import pandas as pd
    import numpy as np
    import json

    df = pd.read_csv(results)
    out_dir.mkdir(parents=True, exist_ok=True)

    required_cols = {
        "scenario",
        "strategy",
        "accuracy",
        "avg_tokens",
        "avg_calls",
        "avg_latency_s",
        "temperature",
        "n_questions",
        "model",
    }
    missing = sorted([c for c in required_cols if c not in df.columns])
    if missing:
        raise typer.BadParameter(f"results.csv missing columns: {missing}")

    # 过滤（不传参数则不过滤）
    if scenario:
        df = df[df["scenario"].isin(scenario)]
    if model:
        df = df[df["model"].isin(model)]
    if n_questions:
        df = df[df["n_questions"].isin(n_questions)]
    if temperature:
        series = pd.to_numeric(df["temperature"], errors="coerce")
        mask = np.zeros(len(df), dtype=bool)
        for t in temperature:
            mask |= np.isclose(series, float(t), atol=1e-6, rtol=0.0)
        df = df[mask]

    if df.empty:
        typer.echo("No rows after filtering; nothing to summarize.")
        return

    # 可选：从 per_question_log.jsonl 读取并计算 valid_output_rate / llm_error_rate（并供 paper 分析复用）
    log_df = None
    if log_jsonl is not None and Path(log_jsonl).exists():
        log_df = _load_log_minimal(Path(log_jsonl))
        if not log_df.empty:
            df_rates = (
                log_df.assign(valid=lambda x: x["pred"].notna().astype(int))
                .groupby(["strategy", "scenario", "temperature", "repeat_idx", "seed"], dropna=False)
                .agg(
                    n=("question_id", "count"),
                    valid=("valid", "sum"),
                    llm_error=("llm_error", "sum"),
                )
                .reset_index()
            )
            df_rates["valid_output_rate"] = df_rates["valid"] / df_rates["n"].replace({0: np.nan})
            df_rates["llm_error_rate"] = df_rates["llm_error"] / df_rates["n"].replace({0: np.nan})
            df = df.merge(
                df_rates[
                    [
                        "strategy",
                        "scenario",
                        "temperature",
                        "repeat_idx",
                        "seed",
                        "valid_output_rate",
                        "llm_error_rate",
                    ]
                ],
                on=["strategy", "scenario", "temperature", "repeat_idx", "seed"],
                how="left",
            )

    bucket_cols = ["scenario", "temperature", "n_questions", "model"] if by_config else ["scenario"]
    group_cols = [*bucket_cols, "strategy"]

    # 汇总表
    grp = (
        df.groupby(group_cols, dropna=False)
        .agg(
            n=("accuracy", "count"),
            acc_mean=("accuracy", "mean"),
            acc_std=("accuracy", "std"),
            tokens_mean=("avg_tokens", "mean"),
            calls_mean=("avg_calls", "mean"),
            latency_mean=("avg_latency_s", "mean"),
            valid_mean=("valid_output_rate", "mean") if "valid_output_rate" in df.columns else ("accuracy", "count"),
            llm_error_mean=("llm_error_rate", "mean") if "llm_error_rate" in df.columns else ("accuracy", "count"),
        )
        .reset_index()
        .sort_values([*bucket_cols, "acc_mean"], ascending=[*([True] * len(bucket_cols)), False])
    )
    # 若没有 log_jsonl，则上面 valid_mean/llm_error_mean 是占位（accuracy count）；这里清空，避免误导
    if "valid_output_rate" not in df.columns:
        grp = grp.drop(columns=["valid_mean"], errors="ignore")
    else:
        grp = grp.rename(columns={"valid_mean": "valid_output_rate_mean"})
    if "llm_error_rate" not in df.columns:
        grp = grp.drop(columns=["llm_error_mean"], errors="ignore")
    else:
        grp = grp.rename(columns={"llm_error_mean": "llm_error_rate_mean"})

    grp.to_csv(out_dir / "summary_by_strategy.csv", index=False)
    typer.echo(f"Wrote summary -> {out_dir/'summary_by_strategy.csv'}")

    # 绘图
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        typer.echo(f"matplotlib not available: {e}")
        return

    for bucket_vals, sub in grp.groupby(bucket_cols, dropna=False):
        sub = sub.sort_values("acc_mean", ascending=False)
        tag = _bucket_tag(bucket_cols, bucket_vals)
        title = _bucket_title(bucket_cols, bucket_vals)
        plt.figure(figsize=(10, 4))
        plt.bar(sub["strategy"], sub["acc_mean"], yerr=sub["acc_std"].fillna(0.0))
        plt.xticks(rotation=30, ha="right")
        plt.ylim(0, 1)
        plt.title(f"Accuracy by Strategy\n({title})")
        plt.tight_layout()
        out_path = out_dir / f"acc_bar_{tag}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()

    # Paper-mode extras: overall tables + richer plots + dataset credibility + grouped performance
    if paper:
        # 1) Paper Table 1: overall summary across scenarios (within the same config bucket)
        paper_bucket_cols = ["questions_path", "temperature", "n_questions", "model"] if "questions_path" in df.columns else ["temperature", "n_questions", "model"]
        for bucket_vals, sdf in df.groupby(paper_bucket_cols, dropna=False):
            bucket_vals_t = _as_tuple(bucket_vals)
            bucket_rec = {c: v for c, v in zip(paper_bucket_cols, bucket_vals_t)}
            tag = _bucket_tag(paper_bucket_cols, bucket_vals)
            title_bits = ", ".join([f"{k}={v}" for k, v in bucket_rec.items() if k != "questions_path"])

            # overall (all scenarios pooled)
            overall = (
                sdf.groupby(["strategy"], dropna=False)
                .agg(
                    n=("accuracy", "count"),
                    acc_mean=("accuracy", "mean"),
                    acc_std=("accuracy", "std"),
                    tokens_mean=("avg_tokens", "mean"),
                    calls_mean=("avg_calls", "mean"),
                    latency_mean=("avg_latency_s", "mean"),
                    valid_mean=("valid_output_rate", "mean") if "valid_output_rate" in sdf.columns else ("accuracy", "count"),
                    llm_error_mean=("llm_error_rate", "mean") if "llm_error_rate" in sdf.columns else ("accuracy", "count"),
                )
                .reset_index()
            )
            if "valid_output_rate" not in sdf.columns:
                overall = overall.drop(columns=["valid_mean"], errors="ignore")
            else:
                overall = overall.rename(columns={"valid_mean": "valid_output_rate_mean"})
            if "llm_error_rate" not in sdf.columns:
                overall = overall.drop(columns=["llm_error_mean"], errors="ignore")
            else:
                overall = overall.rename(columns={"llm_error_mean": "llm_error_rate_mean"})

            # per-scenario accuracy mean±std (wide)
            per_sc = (
                sdf.groupby(["scenario", "strategy"], dropna=False)
                .agg(acc_mean=("accuracy", "mean"), acc_std=("accuracy", "std"))
                .reset_index()
            )
            per_sc["scenario"] = per_sc["scenario"].astype(str)
            # pivot to columns acc_mean__scenario, acc_std__scenario
            per_sc_mean = per_sc.pivot(index="strategy", columns="scenario", values="acc_mean")
            per_sc_std = per_sc.pivot(index="strategy", columns="scenario", values="acc_std")
            per_sc_mean.columns = [f"acc_mean__{c}" for c in per_sc_mean.columns]
            per_sc_std.columns = [f"acc_std__{c}" for c in per_sc_std.columns]
            per_sc_wide = pd.concat([per_sc_mean, per_sc_std], axis=1).reset_index()

            paper_table = overall.merge(per_sc_wide, on="strategy", how="left")
            # stable ordering
            paper_table["strategy"] = paper_table["strategy"].astype(str)
            order = _ensure_strategy_order(list(paper_table["strategy"].unique()))
            paper_table["strategy"] = pd.Categorical(paper_table["strategy"], categories=order, ordered=True)
            paper_table = paper_table.sort_values("strategy")

            out_csv = out_dir / f"paper_table1_overall_{tag}.csv"
            paper_table.to_csv(out_csv, index=False)

            # 2) Paper Figure: bubble trade-off (tokens vs acc, bubble size ~ latency)
            try:
                bub = paper_table.copy()
                if "latency_mean" in bub.columns:
                    sizes = bub["latency_mean"].astype(float).fillna(0.0)
                    # size scaling: keep within reasonable pixels
                    s = 40 + 260 * (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-9)
                else:
                    s = 80
                plt.figure(figsize=(8, 4.5))
                plt.scatter(bub["tokens_mean"], bub["acc_mean"], s=s, alpha=0.75)
                for _, row in bub.iterrows():
                    plt.annotate(str(row["strategy"]), (row["tokens_mean"], row["acc_mean"]), textcoords="offset points", xytext=(6, 6), fontsize=8)
                # highlight adaptive
                ga = bub[bub["strategy"] == "garmentagents_adaptive"]
                if not ga.empty:
                    plt.scatter(ga["tokens_mean"], ga["acc_mean"], marker="*", s=240, color="red", alpha=0.95, label="garmentagents_adaptive")
                    plt.legend(loc="lower right", fontsize=8, frameon=False)
                plt.xlabel("Avg tokens / question")
                plt.ylabel("Accuracy")
                plt.ylim(0, 1)
                plt.title(f"Trade-off: Accuracy vs Tokens (bubble≈latency)\n({title_bits})")
                plt.tight_layout()
                plt.savefig(out_dir / f"paper_tradeoff_bubble_{tag}.png", dpi=200, bbox_inches="tight")
                plt.close()
            except Exception:
                pass

            # 3) Paper Figure: grouped bar by scenario (accuracy)
            try:
                scenarios = sorted([str(x) for x in sdf["scenario"].unique()])
                # keep only two scenarios for grouped layout; if more, fallback to per-scenario bars already generated
                if len(scenarios) == 2:
                    sc_a, sc_b = scenarios[0], scenarios[1]
                    # build from per_sc (mean/std)
                    tmp = per_sc.copy()
                    tmp["strategy"] = tmp["strategy"].astype(str)
                    tmp["scenario"] = tmp["scenario"].astype(str)
                    a = tmp[tmp["scenario"] == sc_a].set_index("strategy")
                    b = tmp[tmp["scenario"] == sc_b].set_index("strategy")
                    strategies = _ensure_strategy_order(sorted(set(a.index) | set(b.index)))
                    a = a.reindex(strategies)
                    b = b.reindex(strategies)

                    x = np.arange(len(strategies))
                    w = 0.38
                    plt.figure(figsize=(11, 4.2))
                    plt.bar(x - w / 2, a["acc_mean"].values, width=w, yerr=a["acc_std"].fillna(0.0).values, label=sc_a, alpha=0.9)
                    plt.bar(x + w / 2, b["acc_mean"].values, width=w, yerr=b["acc_std"].fillna(0.0).values, label=sc_b, alpha=0.9)
                    plt.xticks(x, strategies, rotation=30, ha="right")
                    plt.ylim(0, 1)
                    plt.ylabel("Accuracy")
                    plt.title(f"Scenario Breakdown (mean±sd over repeats)\n({title_bits})")
                    plt.legend(loc="lower right", fontsize=9, frameon=False)
                    plt.tight_layout()
                    plt.savefig(out_dir / f"paper_acc_grouped_by_scenario_{tag}.png", dpi=200, bbox_inches="tight")
                    plt.close()
            except Exception:
                pass

            # 4) Paper Figure: reliability (valid output rate / llm error rate), if available
            try:
                if "valid_output_rate_mean" in paper_table.columns:
                    tmp = paper_table.copy()
                    tmp["valid_output_rate_mean"] = tmp["valid_output_rate_mean"].astype(float)
                    plt.figure(figsize=(10, 3.6))
                    plt.bar(tmp["strategy"].astype(str), tmp["valid_output_rate_mean"].values)
                    plt.xticks(rotation=30, ha="right")
                    plt.ylim(0, 1)
                    plt.ylabel("Valid output rate")
                    plt.title(f"Reliability: valid output rate\n({title_bits})")
                    plt.tight_layout()
                    plt.savefig(out_dir / f"paper_valid_output_rate_{tag}.png", dpi=200, bbox_inches="tight")
                    plt.close()
                if "llm_error_rate_mean" in paper_table.columns:
                    tmp = paper_table.copy()
                    tmp["llm_error_rate_mean"] = tmp["llm_error_rate_mean"].astype(float)
                    plt.figure(figsize=(10, 3.6))
                    plt.bar(tmp["strategy"].astype(str), tmp["llm_error_rate_mean"].values)
                    plt.xticks(rotation=30, ha="right")
                    plt.ylim(0, max(0.01, float(tmp["llm_error_rate_mean"].max()) * 1.2))
                    plt.ylabel("LLM error rate")
                    plt.title(f"Reliability: LLM error rate\n({title_bits})")
                    plt.tight_layout()
                    plt.savefig(out_dir / f"paper_llm_error_rate_{tag}.png", dpi=200, bbox_inches="tight")
                    plt.close()
            except Exception:
                pass

        # 4) Dataset credibility + grouped performance by difficulty/constraints (requires questions_jsonl + log_jsonl)
        if questions_jsonl is not None and Path(questions_jsonl).exists():
            qdf = _load_questions_meta(Path(questions_jsonl))
            if not qdf.empty:
                # dataset summary
                ds = (
                    qdf.groupby(["scenario"], dropna=False)
                    .agg(
                        n=("question_id", "count"),
                        margin_mean=("margin", "mean"),
                        margin_p10=("margin", lambda s: float(np.nanquantile(s, 0.10))),
                        margin_p50=("margin", lambda s: float(np.nanquantile(s, 0.50))),
                        margin_p90=("margin", lambda s: float(np.nanquantile(s, 0.90))),
                        must_n_mean=("must_n", "mean"),
                    )
                    .reset_index()
                )
                # answer distribution (gold)
                ans = (
                    qdf.groupby(["scenario", "gold"], dropna=False)
                    .agg(n=("question_id", "count"))
                    .reset_index()
                )
                ds.to_csv(out_dir / "paper_dataset_summary_by_scenario.csv", index=False)
                ans.to_csv(out_dir / "paper_dataset_answer_dist.csv", index=False)

                # dataset plots: margin histogram + must_n distribution
                try:
                    import matplotlib.pyplot as plt

                    scenarios = sorted([str(x) for x in qdf["scenario"].unique()])
                    plt.figure(figsize=(10, 4))
                    for sc in scenarios:
                        vals = qdf[qdf["scenario"] == sc]["margin"].astype(float).values
                        plt.hist(vals, bins=20, alpha=0.5, label=sc)
                    plt.xlabel("Oracle margin (top1 - top2)")
                    plt.ylabel("Count")
                    plt.title("Dataset difficulty distribution (margin)")
                    plt.legend(loc="upper right", fontsize=8, frameon=False)
                    plt.tight_layout()
                    plt.savefig(out_dir / "paper_dataset_margin_hist.png", dpi=200, bbox_inches="tight")
                    plt.close()

                    plt.figure(figsize=(8, 3.6))
                    must_counts = sorted([int(x) for x in qdf["must_n"].dropna().unique()])
                    for sc in scenarios:
                        sub = qdf[qdf["scenario"] == sc]
                        cnts = [int((sub["must_n"] == m).sum()) for m in must_counts]
                        plt.plot(must_counts, cnts, marker="o", label=sc)
                    plt.xticks(must_counts)
                    plt.xlabel("# must constraints per question")
                    plt.ylabel("Count")
                    plt.title("Dataset constraint density")
                    plt.legend(loc="upper right", fontsize=8, frameon=False)
                    plt.tight_layout()
                    plt.savefig(out_dir / "paper_dataset_must_count.png", dpi=200, bbox_inches="tight")
                    plt.close()
                except Exception:
                    pass

        if log_df is not None and (questions_jsonl is not None) and Path(questions_jsonl).exists():
            try:
                qdf = _load_questions_meta(Path(questions_jsonl))
                if not qdf.empty and not log_df.empty:
                    # join to get margin/must_n/flags
                    mdf = log_df.merge(qdf, on=["question_id"], how="left", suffixes=("", "_q"))
                    # missing flags -> False
                    for c in ["must_has_cost", "must_has_lead", "must_has_compliance", "must_has_weight", "must_has_perf"]:
                        if c in mdf.columns:
                            mdf[c] = mdf[c].fillna(False).astype(bool)

                    # difficulty buckets per scenario (tertiles)
                    def _bucket_margin(sub):
                        m = sub["margin"].astype(float)
                        q33 = float(np.nanquantile(m, 1 / 3))
                        q67 = float(np.nanquantile(m, 2 / 3))
                        return q33, q67

                    buckets = {}
                    for sc in sorted([str(x) for x in qdf["scenario"].unique()]):
                        subq = qdf[qdf["scenario"] == sc]
                        if len(subq) >= 3:
                            buckets[sc] = _bucket_margin(subq)

                    def _assign_bucket(row):
                        sc = str(row.get("scenario") or "")
                        if sc not in buckets:
                            return "unknown"
                        q33, q67 = buckets[sc]
                        m = row.get("margin")
                        try:
                            mv = float(m)
                        except Exception:
                            return "unknown"
                        if mv <= q33:
                            return "hard"
                        if mv <= q67:
                            return "medium"
                        return "easy"

                    mdf["difficulty"] = mdf.apply(_assign_bucket, axis=1)

                    # per-run accuracy in each difficulty bucket
                    run_cols = ["strategy", "scenario", "temperature", "repeat_idx", "seed"]
                    per_run = (
                        mdf.groupby([*run_cols, "difficulty"], dropna=False)
                        .agg(n=("question_id", "count"), acc=("is_correct", "mean"))
                        .reset_index()
                    )
                    per_run.to_csv(out_dir / "paper_acc_by_difficulty_per_run.csv", index=False)

                    # aggregate across repeats
                    agg = (
                        per_run.groupby(["strategy", "scenario", "difficulty"], dropna=False)
                        .agg(acc_mean=("acc", "mean"), acc_std=("acc", "std"))
                        .reset_index()
                    )
                    agg.to_csv(out_dir / "paper_acc_by_difficulty.csv", index=False)

                    # heatmap per scenario
                    try:
                        import matplotlib.pyplot as plt

                        diffs = ["hard", "medium", "easy"]
                        for sc in sorted([str(x) for x in mdf["scenario"].dropna().unique()]):
                            sub = agg[agg["scenario"] == sc]
                            if sub.empty:
                                continue
                            strategies = _ensure_strategy_order(sorted(sub["strategy"].astype(str).unique()))
                            mat = np.full((len(strategies), len(diffs)), np.nan)
                            for i, st in enumerate(strategies):
                                for j, d in enumerate(diffs):
                                    v = sub[(sub["strategy"] == st) & (sub["difficulty"] == d)]["acc_mean"]
                                    if len(v) > 0:
                                        mat[i, j] = float(v.iloc[0])
                            plt.figure(figsize=(8.5, 4.6))
                            im = plt.imshow(mat, aspect="auto", vmin=0, vmax=1, cmap="viridis")
                            plt.colorbar(im, fraction=0.046, pad=0.04, label="Accuracy")
                            plt.xticks(range(len(diffs)), diffs)
                            plt.yticks(range(len(strategies)), strategies)
                            for i in range(len(strategies)):
                                for j in range(len(diffs)):
                                    if mat[i, j] == mat[i, j]:
                                        plt.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center", fontsize=7, color="white")
                            plt.title(f"Accuracy by difficulty (margin tertiles)\n(scenario={sc})")
                            plt.tight_layout()
                            plt.savefig(out_dir / f"paper_heatmap_difficulty_{_safe_filename(sc)}.png", dpi=200, bbox_inches="tight")
                            plt.close()
                    except Exception:
                        pass

                    # constraint-type grouping (by must keyword flags)
                    flag_cols = ["must_has_cost", "must_has_lead", "must_has_compliance", "must_has_weight", "must_has_perf"]
                    flag_rows = []
                    for flag in flag_cols:
                        if flag not in mdf.columns:
                            continue
                        sub = mdf[mdf[flag] == True]  # noqa: E712
                        if sub.empty:
                            continue
                        pr = (
                            sub.groupby(run_cols, dropna=False)
                            .agg(n=("question_id", "count"), acc=("is_correct", "mean"))
                            .reset_index()
                        )
                        pr["constraint"] = flag.replace("must_has_", "")
                        flag_rows.append(pr)
                    if flag_rows:
                        per_run_flag = pd.concat(flag_rows, ignore_index=True)
                        per_run_flag.to_csv(out_dir / "paper_acc_by_constraint_per_run.csv", index=False)
                        agg_flag = (
                            per_run_flag.groupby(["strategy", "scenario", "constraint"], dropna=False)
                            .agg(acc_mean=("acc", "mean"), acc_std=("acc", "std"), n_runs=("acc", "count"))
                            .reset_index()
                        )
                        agg_flag.to_csv(out_dir / "paper_acc_by_constraint.csv", index=False)

                        # also save dataset counts for each constraint flag
                        ds_flag = []
                        for sc in sorted([str(x) for x in qdf["scenario"].unique()]):
                            subq = qdf[qdf["scenario"] == sc]
                            for flag in flag_cols:
                                if flag not in subq.columns:
                                    continue
                                ds_flag.append(
                                    {
                                        "scenario": sc,
                                        "constraint": flag.replace("must_has_", ""),
                                        "n_questions": int((subq[flag] == True).sum()),  # noqa: E712
                                    }
                                )
                        if ds_flag:
                            pd.DataFrame(ds_flag).to_csv(out_dir / "paper_dataset_constraint_counts.csv", index=False)

                        # heatmap per scenario
                        try:
                            import matplotlib.pyplot as plt

                            constraints = ["compliance", "perf", "weight", "cost", "lead"]
                            for sc in sorted([str(x) for x in agg_flag["scenario"].unique()]):
                                sub = agg_flag[agg_flag["scenario"] == sc]
                                if sub.empty:
                                    continue
                                strategies = _ensure_strategy_order(sorted(sub["strategy"].astype(str).unique()))
                                mat = np.full((len(strategies), len(constraints)), np.nan)
                                for i, st in enumerate(strategies):
                                    for j, cst in enumerate(constraints):
                                        v = sub[(sub["strategy"] == st) & (sub["constraint"] == cst)]["acc_mean"]
                                        if len(v) > 0:
                                            mat[i, j] = float(v.iloc[0])
                                plt.figure(figsize=(8.8, 4.6))
                                im = plt.imshow(mat, aspect="auto", vmin=0, vmax=1, cmap="magma")
                                plt.colorbar(im, fraction=0.046, pad=0.04, label="Accuracy")
                                plt.xticks(range(len(constraints)), constraints, rotation=0)
                                plt.yticks(range(len(strategies)), strategies)
                                for i in range(len(strategies)):
                                    for j in range(len(constraints)):
                                        if mat[i, j] == mat[i, j]:
                                            plt.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center", fontsize=7, color="white")
                                plt.title(f"Accuracy by constraint type (subset where constraint appears)\n(scenario={sc})")
                                plt.tight_layout()
                                plt.savefig(out_dir / f"paper_heatmap_constraint_{_safe_filename(sc)}.png", dpi=200, bbox_inches="tight")
                                plt.close()
                        except Exception:
                            pass
            except Exception:
                pass

    # Scatter: tokens vs acc（按 scenario 分图）
    for bucket_vals, sub in grp.groupby(bucket_cols, dropna=False):
        tag = _bucket_tag(bucket_cols, bucket_vals)
        title = _bucket_title(bucket_cols, bucket_vals)
        plt.figure(figsize=(8, 4))
        # 普通点
        plt.scatter(sub["tokens_mean"], sub["acc_mean"], alpha=0.85)
        offsets = [(6, 6), (6, -6), (-6, 6), (-6, -6), (0, 8), (0, -8)]
        for i, (_, row) in enumerate(sub.iterrows()):
            dx, dy = offsets[i % len(offsets)]
            plt.annotate(
                str(row["strategy"]),
                (row["tokens_mean"], row["acc_mean"]),
                textcoords="offset points",
                xytext=(dx, dy),
                fontsize=8,
            )
        # 突出 garmentagents_adaptive（early-stop 主要体现在 calls/tokens 低）
        try:
            ga = sub[sub["strategy"] == "garmentagents_adaptive"]
            if not ga.empty:
                plt.scatter(ga["tokens_mean"], ga["acc_mean"], marker="*", s=180, color="red", alpha=0.95, label="garmentagents_adaptive")
                plt.legend(loc="lower right", fontsize=8, frameon=False)
        except Exception:
            pass
        plt.xlabel("Avg tokens / question")
        plt.ylabel("Accuracy")
        plt.ylim(0, 1)
        plt.title(f"Accuracy vs Cost\n({title})")
        plt.tight_layout()
        out_path = out_dir / f"acc_vs_tokens_{tag}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()

    # Scatter: latency vs acc
    for bucket_vals, sub in grp.groupby(bucket_cols, dropna=False):
        tag = _bucket_tag(bucket_cols, bucket_vals)
        title = _bucket_title(bucket_cols, bucket_vals)
        plt.figure(figsize=(8, 4))
        plt.scatter(sub["latency_mean"], sub["acc_mean"], alpha=0.85)
        offsets = [(6, 6), (6, -6), (-6, 6), (-6, -6), (0, 8), (0, -8)]
        for i, (_, row) in enumerate(sub.iterrows()):
            dx, dy = offsets[i % len(offsets)]
            plt.annotate(
                str(row["strategy"]),
                (row["latency_mean"], row["acc_mean"]),
                textcoords="offset points",
                xytext=(dx, dy),
                fontsize=8,
            )
        try:
            ga = sub[sub["strategy"] == "garmentagents_adaptive"]
            if not ga.empty:
                plt.scatter(ga["latency_mean"], ga["acc_mean"], marker="*", s=180, color="red", alpha=0.95, label="garmentagents_adaptive")
                plt.legend(loc="lower right", fontsize=8, frameon=False)
        except Exception:
            pass
        plt.xlabel("Avg latency / question (s)")
        plt.ylabel("Accuracy")
        plt.ylim(0, 1)
        plt.title(f"Accuracy vs Latency\n({title})")
        plt.tight_layout()
        out_path = out_dir / f"acc_vs_latency_{tag}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()

    typer.echo(f"Wrote figs -> {out_dir}")

    # 统计检验（可选）：Kruskal-Wallis + pairwise Mann-Whitney + BH
    try:
        from scipy.stats import kruskal, mannwhitneyu, shapiro  # type: ignore
    except Exception as e:
        typer.echo(f"scipy not available, skip stats tests: {e}")
        return

    stats_rows: List[Dict[str, object]] = []

    for bucket_vals, sdf in df.groupby(bucket_cols, dropna=False):
        bucket_vals_t = _as_tuple(bucket_vals)
        bucket_rec = {c: v for c, v in zip(bucket_cols, bucket_vals_t)}
        strategies = sorted(sdf["strategy"].unique())
        groups = [sdf[sdf["strategy"] == s]["accuracy"].dropna().values for s in strategies]
        if any(len(g) == 0 for g in groups) or len(groups) < 2:
            continue

        # Shapiro（小样本很不稳定，这里只做记录）
        for s, g in zip(strategies, groups):
            if len(g) >= 3:
                try:
                    p = float(shapiro(g).pvalue)
                except Exception:
                    p = float("nan")
                stats_rows.append({**bucket_rec, "test": "shapiro", "strategy": s, "p": p})

        # Kruskal-Wallis
        try:
            p_kw = float(kruskal(*groups).pvalue)
        except Exception:
            p_kw = float("nan")
        stats_rows.append({**bucket_rec, "test": "kruskal_wallis", "strategy": "ALL", "p": p_kw})

        # Pairwise Mann-Whitney（双侧）
        pairs: List[Tuple[str, str]] = []
        pvals: List[float] = []
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                a = sdf[sdf["strategy"] == strategies[i]]["accuracy"].dropna().values
                b = sdf[sdf["strategy"] == strategies[j]]["accuracy"].dropna().values
                if len(a) == 0 or len(b) == 0:
                    continue
                try:
                    p = float(mannwhitneyu(a, b, alternative="two-sided").pvalue)
                except Exception:
                    p = float("nan")
                pairs.append((strategies[i], strategies[j]))
                pvals.append(p)

        rejects = _bh_fdr([p for p in pvals if p == p], alpha=0.05)  # 过滤 nan 后做 BH
        # 将 rejects 对齐回原列表（nan 视为不拒绝）
        rej_full: List[bool] = []
        k = 0
        for p in pvals:
            if p == p:  # not nan
                rej_full.append(rejects[k])
                k += 1
            else:
                rej_full.append(False)

        for (a, b), p, rej in zip(pairs, pvals, rej_full):
            stats_rows.append(
                {
                    **bucket_rec,
                    "test": "mannwhitneyu",
                    "strategy": f"{a} vs {b}",
                    "p": p,
                    "bh_reject@0.05": rej,
                }
            )

    import pandas as pd

    if stats_rows:
        pd.DataFrame(stats_rows).to_csv(out_dir / "stats_tests.csv", index=False)
        typer.echo(f"Wrote stats -> {out_dir/'stats_tests.csv'}")


if __name__ == "__main__":
    app()



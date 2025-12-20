from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

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


@app.command()
def main(
    results: Path = typer.Option(Path("outputs/results.csv"), help="eval_run 输出的 results.csv"),
    out_dir: Path = typer.Option(Path("outputs/figs"), help="图表输出目录"),
    scenario: List[str] = typer.Option([], "--scenario", help="只保留指定场景（可重复指定）。不传则不过滤。"),
    temperature: List[float] = typer.Option([], "--temperature", help="只保留指定温度（可重复指定；浮点用近似匹配）。不传则不过滤。"),
    n_questions: List[int] = typer.Option([], "--n-questions", help="只保留指定题数（可重复指定）。不传则不过滤。"),
    model: List[str] = typer.Option([], "--model", help="只保留指定模型（可重复指定）。不传则不过滤。"),
    by_config: bool = typer.Option(
        True,
        "--by-config/--no-by-config",
        help="默认按 (scenario, temperature, n_questions, model) 分桶汇总/出图，避免混合不同实验设置。",
    ),
) -> None:
    import pandas as pd
    import numpy as np

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
        )
        .reset_index()
        .sort_values([*bucket_cols, "acc_mean"], ascending=[*([True] * len(bucket_cols)), False])
    )
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

    # Scatter: tokens vs acc（按 scenario 分图）
    for bucket_vals, sub in grp.groupby(bucket_cols, dropna=False):
        tag = _bucket_tag(bucket_cols, bucket_vals)
        title = _bucket_title(bucket_cols, bucket_vals)
        plt.figure(figsize=(8, 4))
        plt.scatter(sub["tokens_mean"], sub["acc_mean"])
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
        plt.xlabel("Avg tokens / question")
        plt.ylabel("Accuracy")
        plt.ylim(0, 1)
        plt.title(f"Accuracy vs Cost\n({title})")
        plt.tight_layout()
        out_path = out_dir / f"acc_vs_tokens_{tag}.png"
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



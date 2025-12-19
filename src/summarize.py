from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

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


app = typer.Typer(add_completion=False, help="汇总 results.csv，输出统计表与图（可选统计检验）。")


@app.command()
def main(
    results: Path = typer.Option(Path("outputs/results.csv"), help="eval_run 输出的 results.csv"),
    out_dir: Path = typer.Option(Path("outputs/figs"), help="图表输出目录"),
) -> None:
    import pandas as pd

    df = pd.read_csv(results)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 汇总表
    grp = (
        df.groupby(["scenario", "strategy"])
        .agg(
            n=("accuracy", "count"),
            acc_mean=("accuracy", "mean"),
            acc_std=("accuracy", "std"),
            tokens_mean=("avg_tokens", "mean"),
            calls_mean=("avg_calls", "mean"),
            latency_mean=("avg_latency_s", "mean"),
        )
        .reset_index()
        .sort_values(["scenario", "acc_mean"], ascending=[True, False])
    )
    grp.to_csv(out_dir / "summary_by_strategy.csv", index=False)
    typer.echo(f"Wrote summary -> {out_dir/'summary_by_strategy.csv'}")

    # 绘图
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        typer.echo(f"matplotlib not available: {e}")
        return

    for scenario, sub in grp.groupby("scenario"):
        sub = sub.sort_values("acc_mean", ascending=False)
        plt.figure(figsize=(10, 4))
        plt.bar(sub["strategy"], sub["acc_mean"], yerr=sub["acc_std"].fillna(0.0))
        plt.xticks(rotation=30, ha="right")
        plt.ylim(0, 1)
        plt.title(f"Accuracy by Strategy ({scenario})")
        plt.tight_layout()
        out_path = out_dir / f"acc_bar_{scenario}.png"
        plt.savefig(out_path, dpi=200)
        plt.close()

    # Scatter: tokens vs acc（按 scenario 分图）
    for scenario, sub in grp.groupby("scenario"):
        plt.figure(figsize=(6, 4))
        plt.scatter(sub["tokens_mean"], sub["acc_mean"])
        for _, row in sub.iterrows():
            plt.text(row["tokens_mean"], row["acc_mean"], str(row["strategy"]), fontsize=8)
        plt.xlabel("Avg tokens / question")
        plt.ylabel("Accuracy")
        plt.ylim(0, 1)
        plt.title(f"Accuracy vs Cost ({scenario})")
        plt.tight_layout()
        out_path = out_dir / f"acc_vs_tokens_{scenario}.png"
        plt.savefig(out_path, dpi=200)
        plt.close()

    typer.echo(f"Wrote figs -> {out_dir}")

    # 统计检验（可选）：Kruskal-Wallis + pairwise Mann-Whitney + BH
    try:
        from scipy.stats import kruskal, mannwhitneyu, shapiro  # type: ignore
    except Exception as e:
        typer.echo(f"scipy not available, skip stats tests: {e}")
        return

    stats_rows: List[Dict[str, object]] = []

    for scenario in sorted(df["scenario"].unique()):
        sdf = df[df["scenario"] == scenario]
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
                stats_rows.append({"scenario": scenario, "test": "shapiro", "strategy": s, "p": p})

        # Kruskal-Wallis
        try:
            p_kw = float(kruskal(*groups).pvalue)
        except Exception:
            p_kw = float("nan")
        stats_rows.append({"scenario": scenario, "test": "kruskal_wallis", "strategy": "ALL", "p": p_kw})

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
                    "scenario": scenario,
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



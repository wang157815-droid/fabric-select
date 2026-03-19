#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect paper-related tables into a single Markdown file for easier review and citation.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import typer

app = typer.Typer(add_completion=False, help="Collect paper tables into a single Markdown file.")


def _now_ts() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _escape_md(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s


def _fmt_float_default(x: float) -> str:
    ax = abs(float(x))
    if ax == 0.0:
        return "0"
    if ax < 1e-4:
        return f"{x:.2e}"
    if ax < 0.01:
        return f"{x:.4f}".rstrip("0").rstrip(".")
    if ax < 1:
        return f"{x:.3f}".rstrip("0").rstrip(".")
    if ax < 10:
        return f"{x:.3f}".rstrip("0").rstrip(".")
    if ax < 100:
        return f"{x:.2f}".rstrip("0").rstrip(".")
    if ax < 1000:
        return f"{x:.1f}".rstrip("0").rstrip(".")
    return f"{x:.0f}"


def _format_cell(value: Any, col: str) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        c = col.lower()
        v = float(value)
        # p-values: keep three significant digits to avoid truncating to 0.000
        if c == "p" or c.endswith("_p") or c.startswith("p_") or "pvalue" in c:
            return f"{v:.3g}"
        # Accuracy / margin: typically three decimals
        if "acc" in c or "margin" in c:
            return f"{v:.3f}"
        # Rates: avoid showing extremely small values as 0.000
        if "rate" in c:
            av = abs(v)
            if 0 < av < 0.001:
                return f"{v:.2e}"
            if av < 0.01:
                return f"{v:.4f}".rstrip("0").rstrip(".")
            return f"{v:.3f}"
        # Tokens: integers are easier to read
        if "token" in c:
            return f"{v:.0f}"
        # Calls: two decimals
        if "call" in c:
            return f"{v:.2f}"
        # Latency: two decimals
        if "latency" in c:
            return f"{v:.2f}"
        # Thresholds
        if "thresh" in c or "threshold" in c:
            return f"{v:.2f}"
        return _fmt_float_default(v)
    if isinstance(value, (int, bool)):
        return str(value)
    return str(value)


def _df_to_markdown(df: pd.DataFrame, max_rows: Optional[int] = None) -> str:
    df2 = df.copy()
    if max_rows is not None and len(df2) > max_rows:
        df2 = df2.head(max_rows)

    cols = [str(c) for c in df2.columns.tolist()]
    lines: List[str] = []
    lines.append("| " + " | ".join(_escape_md(c) for c in cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for _, row in df2.iterrows():
        cells = []
        for c in cols:
            cells.append(_escape_md(_format_cell(row[c], c)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _read_csv(path: Path) -> pd.DataFrame:
    # `utf-8-sig` keeps compatibility with BOM-prefixed CSV files.
    return pd.read_csv(path, encoding="utf-8-sig")


def _heading_shift(md: str, shift: int) -> str:
    out_lines: List[str] = []
    for line in md.splitlines():
        if line.startswith("#"):
            n = 0
            while n < len(line) and line[n] == "#":
                n += 1
            rest = line[n:]
            new_n = min(6, n + shift)
            out_lines.append("#" * new_n + rest)
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def _wrap_details(title: str, body: str, open_default: bool = False) -> str:
    open_attr = " open" if open_default else ""
    return f"<details{open_attr}>\n<summary>{title}</summary>\n\n{body}\n\n</details>\n"


def _table_section_csv(
    title: str,
    path: Path,
    table_id: Optional[str] = None,
    collapse_if_rows_ge: int = 80,
) -> str:
    df = _read_csv(path)
    header = f"### {table_id + ' ' if table_id else ''}{title}\n\n"
    meta = f"- **Source**: `{path.as_posix()}`  \n- **Rows**: {len(df)}  \n- **Columns**: {len(df.columns)}\n\n"
    table_md = _df_to_markdown(df)
    if len(df) >= collapse_if_rows_ge:
        table_md = _wrap_details(f"Expand table ({len(df)} rows)", table_md, open_default=False)
    return header + meta + table_md + "\n"


@app.command()
def main(
    main_dir: Path = typer.Option(Path("outputs/figs_main"), help="Directory containing main-result tables (`figs_main`)"),
    ablation_dir: Path = typer.Option(Path("outputs/figs_ablation"), help="Directory containing ablation tables (`figs_ablation`)"),
    out_md: Path = typer.Option(Path("PAPER_TABLES.md"), help="Output Markdown file"),
) -> None:
    pieces: List[str] = []
    pieces.append("# Paper Table Index (Auto-generated)\n")
    pieces.append(f"- Generated at: {_now_ts()}  \n- Script: `scripts/compile_paper_tables.py`\n")

    # Main results.
    pieces.append("## Main Results\n")
    main_order: List[Tuple[str, str, Optional[str]]] = [
        ("Table 1", "Overall result summary (mean±std, including cost/reliability metrics)", "paper_table1_overall"),
        ("Table 2", "Per-scenario result summary (mean±std for each scenario)", "summary_by_strategy"),
        ("Table 3", "Accuracy grouped by constraint type (mean±std)", "paper_acc_by_constraint"),
        ("Table A1", "Accuracy grouped by constraint type (per repeat/run)", "paper_acc_by_constraint_per_run"),
        ("Table 4", "Accuracy grouped by difficulty (mean±std)", "paper_acc_by_difficulty"),
        ("Table A2", "Accuracy grouped by difficulty (per repeat/run)", "paper_acc_by_difficulty_per_run"),
        ("Table 5", "Statistical tests (Kruskal-Wallis / Mann-Whitney U + BH-FDR)", "stats_tests"),
    ]

    # `paper_table1_overall` files may carry suffixes, so match by prefix.
    def pick_by_prefix(dir_path: Path, prefix: str) -> Optional[Path]:
        cand = sorted(dir_path.glob(prefix + "*.csv"))
        return cand[0] if cand else None

    for table_id, title, prefix in main_order:
        path = pick_by_prefix(main_dir, prefix)
        if not path:
            pieces.append(f"### {table_id} {title}\n\n- **Missing**: could not find `{prefix}*.csv` in `{main_dir.as_posix()}`\n\n")
            continue
        pieces.append(_table_section_csv(title=title, path=path, table_id=table_id))

    pieces.append("## Dataset\n")
    dataset_order: List[Tuple[str, str]] = [
        ("Table D1", "Dataset summary by scenario (margin / number of must constraints)"),
        ("Table D2", "Constraint-type counts by scenario"),
        ("Table D3", "Answer distribution (gold option counts)"),
    ]
    dataset_files: Dict[str, str] = {
        "Table D1": "paper_dataset_summary_by_scenario.csv",
        "Table D2": "paper_dataset_constraint_counts.csv",
        "Table D3": "paper_dataset_answer_dist.csv",
    }
    for table_id, title in dataset_order:
        fp = main_dir / dataset_files[table_id]
        if fp.exists():
            pieces.append(_table_section_csv(title=title, path=fp, table_id=table_id, collapse_if_rows_ge=200))
        else:
            pieces.append(f"### {table_id} {title}\n\n- **Missing**: could not find `{fp.as_posix()}`\n\n")

    # GPT-5 sanity-check subsets are stored under `outputs/figs_main_gpt5*`.
    extra_root = main_dir.parent
    gpt5_dirs = sorted([p for p in extra_root.glob("figs_main_gpt5*") if p.is_dir()])
    if gpt5_dirs:
        pieces.append("## Cross-model Sanity Check (GPT-5 subset)\n")
        for d in gpt5_dirs:
            pieces.append(f"### {d.name}\n")

            # At minimum keep the overall, per-scenario, and stats tables.
            v_table = pick_by_prefix(d, "paper_table1_overall")
            if v_table:
                pieces.append(_table_section_csv(title="Overall summary (GPT-5 sanity)", path=v_table, table_id=None))
            else:
                pieces.append(f"- **Missing**: could not find `paper_table1_overall*.csv` in `{d.as_posix()}`\n")

            v_sum = d / "summary_by_strategy.csv"
            if v_sum.exists():
                pieces.append(_table_section_csv(title="Per-scenario summary (GPT-5 sanity)", path=v_sum, table_id=None))
            else:
                pieces.append(f"- **Missing**: could not find `{v_sum.as_posix()}`\n")

            v_stats = d / "stats_tests.csv"
            if v_stats.exists():
                pieces.append(_table_section_csv(title="Stats tests (GPT-5 sanity)", path=v_stats, table_id=None, collapse_if_rows_ge=200))
            else:
                pieces.append(f"- **Missing**: could not find `{v_stats.as_posix()}`\n")

    # Ablation tables.
    pieces.append("## Ablation\n")
    ablation_md = ablation_dir / "ablation_report.md"
    if ablation_md.exists():
        md = ablation_md.read_text(encoding="utf-8")
        md = _heading_shift(md, shift=2)  # Nest ablation report headings under this section.
        pieces.append(md)
        pieces.append(f"\n- **Source**: `{ablation_md.as_posix()}`\n")
    else:
        pieces.append(f"- **Missing**: could not find `{ablation_md.as_posix()}`\n")

    # Also include the raw ablation CSV files for auditing.
    pieces.append("\n## Appendix: Ablation CSV Details\n")
    ablation_csvs = sorted(ablation_dir.glob("ablation_*.csv"))
    if not ablation_csvs:
        pieces.append(f"- **Missing**: could not find `ablation_*.csv` in `{ablation_dir.as_posix()}`\n")
    else:
        for p in ablation_csvs:
            title = p.name
            try:
                pieces.append(_table_section_csv(title=title, path=p, table_id=None, collapse_if_rows_ge=120))
            except Exception as e:
                pieces.append(f"### {title}\n\n- Read failed: {e}\n\n")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(pieces).rstrip() + "\n", encoding="utf-8")
    typer.echo(f"Wrote -> {out_md}")


if __name__ == "__main__":
    app()


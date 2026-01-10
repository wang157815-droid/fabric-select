#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把论文相关表格（CSV/MD）汇总到一个 Markdown 文件中，便于直接复制到论文主文/附录。

默认会扫描：
- outputs/figs_main/*.csv
- outputs/figs_ablation/*.csv
- outputs/figs_ablation/ablation_report.md

输出：
- outputs/paper_tables.md
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import typer

app = typer.Typer(add_completion=False, help="汇总论文表格到单个 Markdown 文件")


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
        # p 值：保留 3 位有效数字（避免 0.000 被截断）
        if c == "p" or c.endswith("_p") or c.startswith("p_") or "pvalue" in c:
            return f"{v:.3g}"
        # 准确率 / margin：通常 3 位小数
        if "acc" in c or "margin" in c:
            return f"{v:.3f}"
        # 各类 rate：如果非常小，避免被显示成 0.000
        if "rate" in c:
            av = abs(v)
            if 0 < av < 0.001:
                return f"{v:.2e}"
            if av < 0.01:
                return f"{v:.4f}".rstrip("0").rstrip(".")
            return f"{v:.3f}"
        # tokens：整数显示更清爽
        if "token" in c:
            return f"{v:.0f}"
        # calls：两位小数
        if "call" in c:
            return f"{v:.2f}"
        # latency：两位小数
        if "latency" in c:
            return f"{v:.2f}"
        # 阈值
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
    # utf-8-sig 兼容带 BOM 的 CSV
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
    meta = f"- **来源**: `{path.as_posix()}`  \n- **行数**: {len(df)}  \n- **列数**: {len(df.columns)}\n\n"
    table_md = _df_to_markdown(df)
    if len(df) >= collapse_if_rows_ge:
        table_md = _wrap_details(f"展开表格（{len(df)} 行）", table_md, open_default=False)
    return header + meta + table_md + "\n"


@app.command()
def main(
    main_dir: Path = typer.Option(Path("outputs/figs_main"), help="主实验表格目录（figs_main）"),
    ablation_dir: Path = typer.Option(Path("outputs/figs_ablation"), help="消融表格目录（figs_ablation）"),
    out_md: Path = typer.Option(Path("outputs/paper_tables.md"), help="输出 Markdown 文件"),
) -> None:
    pieces: List[str] = []
    pieces.append("# 论文表格汇总（自动生成）\n")
    pieces.append(f"- 生成时间：{_now_ts()}  \n- 脚本：`scripts/compile_paper_tables.py`\n")

    # ---------- Main tables ----------
    pieces.append("## 主实验（Main Results）\n")
    main_order: List[Tuple[str, str, Optional[str]]] = [
        ("Table 1", "总体结果汇总（mean±std，含成本/可靠性指标）", "paper_table1_overall"),
        ("Table 2", "分场景结果汇总（每场景 mean±std）", "summary_by_strategy"),
        ("Table 3", "按约束类型分组的准确率（mean±std）", "paper_acc_by_constraint"),
        ("Table A1", "按约束类型分组的准确率（每个 repeat/run）", "paper_acc_by_constraint_per_run"),
        ("Table 4", "按难度分组的准确率（mean±std）", "paper_acc_by_difficulty"),
        ("Table A2", "按难度分组的准确率（每个 repeat/run）", "paper_acc_by_difficulty_per_run"),
        ("Table 5", "统计检验（Kruskal–Wallis / Mann–Whitney U + BH-FDR）", "stats_tests"),
    ]

    # paper_table1_overall 文件名带很多后缀，做前缀匹配
    def pick_by_prefix(dir_path: Path, prefix: str) -> Optional[Path]:
        cand = sorted(dir_path.glob(prefix + "*.csv"))
        return cand[0] if cand else None

    for table_id, title, prefix in main_order:
        path = pick_by_prefix(main_dir, prefix)
        if not path:
            pieces.append(f"### {table_id} {title}\n\n- **缺失**：未找到 `{prefix}*.csv` 于 `{main_dir.as_posix()}`\n\n")
            continue
        pieces.append(_table_section_csv(title=title, path=path, table_id=table_id))

    pieces.append("## 数据集统计（Dataset）\n")
    dataset_order: List[Tuple[str, str]] = [
        ("Table D1", "数据集按场景摘要（margin / must 约束数量）"),
        ("Table D2", "各场景约束类型计数"),
        ("Table D3", "答案分布（gold 选项分布）"),
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
            pieces.append(f"### {table_id} {title}\n\n- **缺失**：未找到 `{fp.as_posix()}`\n\n")

    # ---------- Ablation tables ----------
    pieces.append("## 消融实验（Ablation）\n")
    ablation_md = ablation_dir / "ablation_report.md"
    if ablation_md.exists():
        md = ablation_md.read_text(encoding="utf-8")
        md = _heading_shift(md, shift=2)  # 把 ablation_report 的 # 变成 ###（嵌套在本章节下）
        pieces.append(md)
        pieces.append(f"\n- **来源**: `{ablation_md.as_posix()}`\n")
    else:
        pieces.append(f"- **缺失**：未找到 `{ablation_md.as_posix()}`\n")

    # 附录：把消融 CSV 也放进来（便于引用/复核）
    pieces.append("\n## 附录：消融 CSV 明细（可复核）\n")
    ablation_csvs = sorted(ablation_dir.glob("ablation_*.csv"))
    if not ablation_csvs:
        pieces.append(f"- **缺失**：未找到 `ablation_*.csv` 于 `{ablation_dir.as_posix()}`\n")
    else:
        for p in ablation_csvs:
            title = p.name
            try:
                pieces.append(_table_section_csv(title=title, path=p, table_id=None, collapse_if_rows_ge=120))
            except Exception as e:
                pieces.append(f"### {title}\n\n- 读取失败：{e}\n\n")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(pieces).rstrip() + "\n", encoding="utf-8")
    typer.echo(f"Wrote -> {out_md}")


if __name__ == "__main__":
    app()


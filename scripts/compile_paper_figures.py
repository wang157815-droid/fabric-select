#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把实验结果图片（PNG）汇总到一个 Markdown 文件中，便于写论文时统一管理/引用。

默认扫描（只扫 outputs/figs*，避免把 PDF 解析页之类的图片混进来）：
- outputs/figs_main/**/*.png
- outputs/figs_ablation/**/*.png
- outputs/figs_main_*/*.png（partial/tmp/test 等）
- outputs/figs/*.png（早期小规模试跑的图，单独放到 Appendix）

输出：
- PAPER_FIGURES.md（默认放在仓库根目录，方便被 Git 跟踪；`outputs/` 默认被 .gitignore 忽略）
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Dict, List, Tuple

import typer

app = typer.Typer(add_completion=False, help="汇总论文图片到单个 Markdown 文件")


def _now_ts() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _posix(p: Path) -> str:
    return p.as_posix()


def _nice_name(filename: str) -> str:
    """把文件名转成更像 caption 的形式（尽量不做过度猜测）。"""
    name = filename.replace(".png", "")
    name = name.replace("__", " / ")
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _scan_pngs(outputs_dir: Path) -> Dict[str, List[Path]]:
    """
    返回分组后的图片列表（key 为组名）。
    组名规则：
    - figs_main -> Main Results
    - figs_ablation -> Ablation
    - figs_main_* -> Main (aux)
    - figs -> Appendix (small runs)
    """
    groups: Dict[str, List[Path]] = {
        "Main Results (figs_main)": [],
        "Ablation (figs_ablation)": [],
        "Main Aux (figs_main_*)": [],
        "Appendix / Small Runs (figs)": [],
    }

    # main
    for p in sorted((outputs_dir / "figs_main").glob("**/*.png")):
        if p.is_file():
            groups["Main Results (figs_main)"].append(p)

    # ablation
    for p in sorted((outputs_dir / "figs_ablation").glob("**/*.png")):
        if p.is_file():
            groups["Ablation (figs_ablation)"].append(p)

    # main aux dirs: figs_main_partial / figs_main_tmp / figs_main_ps1_test / figs_main_tmp2 ...
    for d in sorted(outputs_dir.glob("figs_main_*")):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("**/*.png")):
            if p.is_file():
                groups["Main Aux (figs_main_*)"].append(p)

    # early figs
    for p in sorted((outputs_dir / "figs").glob("**/*.png")):
        if p.is_file():
            groups["Appendix / Small Runs (figs)"].append(p)

    # 去掉空组
    groups = {k: v for k, v in groups.items() if v}
    return groups


def _render_group(group_title: str, paths: List[Path], fig_prefix: str) -> str:
    lines: List[str] = []
    lines.append(f"## {group_title}\n")

    # 目录
    lines.append("### 目录\n")
    for i, p in enumerate(paths, start=1):
        fig_id = f"{fig_prefix}{i}"
        caption = _nice_name(p.name)
        anchor = re.sub(r"[^a-z0-9]+", "-", fig_id.lower()).strip("-")
        lines.append(f"- [{fig_id}](#{anchor}) - {caption}")
    lines.append("")

    # 正文
    for i, p in enumerate(paths, start=1):
        fig_id = f"{fig_prefix}{i}"
        caption = _nice_name(p.name)
        anchor = re.sub(r"[^a-z0-9]+", "-", fig_id.lower()).strip("-")
        rel = _posix(p)

        size_kb = None
        try:
            size_kb = p.stat().st_size / 1024.0
        except Exception:
            pass

        lines.append(f"### {fig_id}\n")
        lines.append(f"<a id=\"{anchor}\"></a>\n")
        lines.append(f"- **文件**: `{rel}`")
        if size_kb is not None:
            lines.append(f"- **大小**: {size_kb:.1f} KB")
        lines.append(f"- **说明**: {caption}\n")
        lines.append(f"![]({rel})\n")

    return "\n".join(lines).rstrip() + "\n"


def _wrap_details(title: str, body: str, open_default: bool = False) -> str:
    open_attr = " open" if open_default else ""
    return f"<details{open_attr}>\n<summary>{title}</summary>\n\n{body}\n\n</details>\n"


@app.command()
def main(
    outputs_dir: Path = typer.Option(Path("outputs"), help="outputs 目录"),
    out_md: Path = typer.Option(Path("PAPER_FIGURES.md"), help="输出 Markdown 文件"),
) -> None:
    groups = _scan_pngs(outputs_dir)

    pieces: List[str] = []
    pieces.append("# 论文图片汇总（自动生成）\n")
    pieces.append(f"- 生成时间：{_now_ts()}  \n- 脚本：`scripts/compile_paper_figures.py`\n")
    pieces.append("说明：本文件引用的是本地 `outputs/figs*` 下的 PNG；如果在 GitHub 上看不到图片，这是因为 `outputs/` 默认被 `.gitignore` 忽略。\n")

    # 固定前缀编号（更像论文引用）
    order: List[Tuple[str, str]] = [
        ("Main Results (figs_main)", "Fig.1-"),
        ("Ablation (figs_ablation)", "Fig.A-"),
        ("Main Aux (figs_main_*)", "Fig.S-"),
        ("Appendix / Small Runs (figs)", "Fig.X-"),
    ]

    for group_key, prefix in order:
        if group_key not in groups:
            continue
        body = _render_group(group_key, groups[group_key], prefix)
        # tmp/test/小规模试跑的图默认折叠，避免干扰主线
        if group_key in ("Main Aux (figs_main_*)", "Appendix / Small Runs (figs)"):
            body = _wrap_details(f"{group_key}（{len(groups[group_key])} 张）", body, open_default=False)
        pieces.append(body)

    out_md.write_text("\n".join(pieces).rstrip() + "\n", encoding="utf-8")
    typer.echo(f"Wrote -> {out_md}")


if __name__ == "__main__":
    app()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect experiment figures into a single Markdown file for easier review and citation.
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Dict, List, Tuple

import typer

app = typer.Typer(add_completion=False, help="Collect paper figures into a single Markdown file.")


def _now_ts() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _posix(p: Path) -> str:
    return p.as_posix()


def _nice_name(filename: str) -> str:
    """Turn a filename into a caption-like label without over-interpreting it."""
    name = filename.replace(".png", "")
    name = name.replace("__", " / ")
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _scan_pngs(outputs_dir: Path) -> Dict[str, List[Path]]:
    """
    Return grouped figure paths keyed by group name.

    Grouping rules:
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

    # auxiliary main-result directories
    for d in sorted(outputs_dir.glob("figs_main_*")):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("**/*.png")):
            if p.is_file():
                groups["Main Aux (figs_main_*)"].append(p)

    # early small-run figures
    for p in sorted((outputs_dir / "figs").glob("**/*.png")):
        if p.is_file():
            groups["Appendix / Small Runs (figs)"].append(p)

    # Drop empty groups.
    groups = {k: v for k, v in groups.items() if v}
    return groups


def _render_group(group_title: str, paths: List[Path], fig_prefix: str) -> str:
    lines: List[str] = []
    lines.append(f"## {group_title}\n")

    # Table of contents.
    lines.append("### Contents\n")
    for i, p in enumerate(paths, start=1):
        fig_id = f"{fig_prefix}{i}"
        caption = _nice_name(p.name)
        anchor = re.sub(r"[^a-z0-9]+", "-", fig_id.lower()).strip("-")
        lines.append(f"- [{fig_id}](#{anchor}) - {caption}")
    lines.append("")

    # Body.
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
        lines.append(f"- **File**: `{rel}`")
        if size_kb is not None:
            lines.append(f"- **Size**: {size_kb:.1f} KB")
        lines.append(f"- **Caption**: {caption}\n")
        lines.append(f"![]({rel})\n")

    return "\n".join(lines).rstrip() + "\n"


def _wrap_details(title: str, body: str, open_default: bool = False) -> str:
    open_attr = " open" if open_default else ""
    return f"<details{open_attr}>\n<summary>{title}</summary>\n\n{body}\n\n</details>\n"


@app.command()
def main(
    outputs_dir: Path = typer.Option(Path("outputs"), help="Path to the outputs directory"),
    out_md: Path = typer.Option(Path("PAPER_FIGURES.md"), help="Output Markdown file"),
) -> None:
    groups = _scan_pngs(outputs_dir)

    pieces: List[str] = []
    pieces.append("# Paper Figure Index (Auto-generated)\n")
    pieces.append(f"- Generated at: {_now_ts()}  \n- Script: `scripts/compile_paper_figures.py`\n")
    pieces.append(
        "Note: this file links to local PNG files under `outputs/figs*`. "
        "If images do not appear on GitHub, the usual reason is that `outputs/` "
        "is ignored by `.gitignore`.\n"
    )

    # Use stable figure IDs across runs.
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
        # Auxiliary groups stay folded by default.
        if group_key in ("Main Aux (figs_main_*)", "Appendix / Small Runs (figs)"):
            body = _wrap_details(f"{group_key} ({len(groups[group_key])} figures)", body, open_default=False)
        pieces.append(body)

    out_md.write_text("\n".join(pieces).rstrip() + "\n", encoding="utf-8")
    typer.echo(f"Wrote -> {out_md}")


if __name__ == "__main__":
    app()


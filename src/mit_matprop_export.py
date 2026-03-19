from __future__ import annotations

"""
Export MIT Fabric Properties Dataset measurements (matprop.xlsx) to a clean CSV.

The provided Excel typically contains measurements for 30 fabrics, including:
- Bending stiffness (lbf-in^2)
- Fabric thickness (in)
- Fabric density (lb/in^3)
- Fabric area weight (oz/yd^2)

We also compute a derived column:
- area_weight_gsm = oz/yd^2 * 33.905747  (exact conversion)

Usage (PowerShell):
  cd D:\\fabric-select-bench
  python -m src.mit_matprop_export --xlsx "material properties\\material_properties (2) 2\\matprop.xlsx" --out-csv data/real_validation/mit_matprop.csv
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
import typer


OZ_PER_YD2_TO_GSM = 33.905747  # 1 oz/yd^2 = 33.905747 g/m^2


def _norm_col(s: str) -> str:
    return " ".join(str(s).strip().split()).lower()


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    norm = {_norm_col(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_col(cand)
        if key in norm:
            return norm[key]
    return None


app = typer.Typer(add_completion=False, help="Export MIT fabric material properties Excel to CSV.")


@app.command()
def main(
    xlsx: Path = typer.Option(..., "--xlsx", help="Path to matprop.xlsx"),
    out_csv: Path = typer.Option(Path("data/real_validation/mit_matprop.csv"), "--out-csv", help="Output CSV path"),
) -> None:
    if not xlsx.exists():
        raise typer.BadParameter(f"XLSX not found: {xlsx}")

    df = pd.read_excel(xlsx)
    if df.empty:
        raise typer.BadParameter(f"Empty sheet: {xlsx}")

    # Common column names (as seen in the MIT release; keep fallbacks tolerant)
    col_fabric_num = _find_col(df, ["Fabric Number", "Fabric No", "Fabric #", "Fabric"])
    col_sample = _find_col(df, ["Sample"])
    col_bending = _find_col(
        df,
        [
            "Bending Stiffness (lbf-in^2)",
            "Bending Stiffness (lbf-in2)",
            "Bending Stiffness",
            "*Bending Stiffness (lbf-in^2)",
        ],
    )
    col_thickness = _find_col(df, ["Fabric Thickness (in)", "Thickness (in)", "Fabric Thickness"])
    col_density = _find_col(
        df,
        [
            "Fabric Density (lb/in^3)",
            "Fabric Density (lb/in3)",
            "Density (lb/in^3)",
            "Density (lb/in3)",
            "Fabric Density",
        ],
    )
    col_area_wt = _find_col(
        df,
        [
            "Fabric Area Weight (oz/yd^2)",
            "Fabric Area Weight (oz/yd²)",
            "Area Weight (oz/yd^2)",
            "Area Weight (oz/yd²)",
            "*Fabric Area Weight (oz/yd^2)",
        ],
    )
    col_conf = _find_col(
        df,
        [
            "Confidence Rating",
            "Confidence Rating (1 thru 4, where 1 is best-fit)",
            "Confidence",
        ],
    )

    missing: Dict[str, Any] = {}
    for name, col in {
        "fabric_number": col_fabric_num,
        "sample": col_sample,
        "bending_stiffness_lbf_in2": col_bending,
        "thickness_in": col_thickness,
        "density_lb_in3": col_density,
        "area_weight_oz_yd2": col_area_wt,
        "confidence_rating": col_conf,
    }.items():
        if col is None:
            missing[name] = True

    out = pd.DataFrame()
    if col_fabric_num is not None:
        out["fabric_number"] = df[col_fabric_num]
    if col_sample is not None:
        out["sample"] = df[col_sample]
    if col_bending is not None:
        out["bending_stiffness_lbf_in2"] = pd.to_numeric(df[col_bending], errors="coerce")
    if col_thickness is not None:
        out["thickness_in"] = pd.to_numeric(df[col_thickness], errors="coerce")
    if col_density is not None:
        out["density_lb_in3"] = pd.to_numeric(df[col_density], errors="coerce")
    if col_area_wt is not None:
        out["area_weight_oz_yd2"] = pd.to_numeric(df[col_area_wt], errors="coerce")
        out["area_weight_gsm"] = out["area_weight_oz_yd2"] * OZ_PER_YD2_TO_GSM
    if col_conf is not None:
        out["confidence_rating"] = pd.to_numeric(df[col_conf], errors="coerce")

    # Basic provenance columns
    out["source_name"] = "MIT Fabric Properties Dataset (Bouman et al., ICCV 2013)"
    out["source_file"] = str(xlsx)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")

    typer.echo(f"OK: wrote {len(out)} rows -> {out_csv}")
    if missing:
        typer.echo(f"[note] some expected columns were not found: {sorted(missing.keys())}")


if __name__ == "__main__":
    app()


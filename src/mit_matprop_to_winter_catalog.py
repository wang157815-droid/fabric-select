from __future__ import annotations

"""
Convert the MIT Fabric Properties dataset into a winter-style catalog.

The source data has measured GSM and thickness, so this script derives the
winter-facing fields needed by the external-validation pipeline.
"""

import math
from pathlib import Path

import pandas as pd
import typer

app = typer.Typer(add_completion=False, help="Convert MIT matprop CSV to a winter external-validation catalog.")


def _qcut_1to5(s: pd.Series, *, high_is_good: bool) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    if x.dropna().nunique() < 5:
        r = x.rank(method="average", pct=True)
        lvl = (r * 5.0).clip(1, 5).round().astype("Int64")
    else:
        lvl = pd.qcut(x, 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype("Int64")
    if not high_is_good:
        lvl = lvl.map(lambda v: (6 - int(v)) if pd.notna(v) else v).astype("Int64")
    return lvl


@app.command()
def main(
    in_csv: Path = typer.Option(..., "--in-csv", help="Input mit_matprop.csv (exported by mit_matprop_export)"),
    out_csv: Path = typer.Option(Path("data/real_validation/winter_catalog_mit.csv"), "--out-csv", help="Output catalog CSV"),
) -> None:
    if not in_csv.exists():
        raise typer.BadParameter(f"Input not found: {in_csv}")

    df = pd.read_csv(in_csv)
    req = {"fabric_number", "area_weight_gsm", "thickness_in"}
    missing = req - set(df.columns)
    if missing:
        raise typer.BadParameter(f"Missing required columns in {in_csv}: {sorted(missing)}")

    # Aggregate multiple samples per fabric_number
    agg = (
        df.groupby("fabric_number", as_index=False)
        .agg(
            area_weight_gsm=("area_weight_gsm", "mean"),
            thickness_in=("thickness_in", "mean"),
            density_lb_in3=("density_lb_in3", "mean") if "density_lb_in3" in df.columns else ("thickness_in", "mean"),
        )
        .copy()
    )

    # Derived winter fields.
    gsm = pd.to_numeric(agg["area_weight_gsm"], errors="coerce").fillna(agg["area_weight_gsm"].median())
    th_in = pd.to_numeric(agg["thickness_in"], errors="coerce").fillna(agg["thickness_in"].median())

    bulk_weight = _qcut_1to5(gsm, high_is_good=True)
    wind_blocking = _qcut_1to5(th_in, high_is_good=True)

    # loft_or_clo proxy: combine normalized gsm + thickness
    gsm_norm = gsm.rank(pct=True)
    th_norm = th_in.rank(pct=True)
    score = (0.55 * th_norm + 0.45 * gsm_norm).clip(0, 1)
    loft_or_clo = (0.8 + score * (2.6 - 0.8)).round(2)

    out = pd.DataFrame(
        {
            "id": agg["fabric_number"].map(lambda n: f"mit_{int(n):02d}"),
            "source_url": "",
            "source_name": "MIT Fabric Properties Dataset (Bouman et al., ICCV 2013)",
            "loft_or_clo": loft_or_clo,
            "wind_blocking": wind_blocking.astype("Int64"),
            "moisture_management": pd.Series([3] * len(agg), dtype="Int64"),
            "bulk_weight": bulk_weight.astype("Int64"),
            "care.machine_wash": [True] * len(agg),
            "compliance.pfas_free": "",
            "cost_level": "",
            "lead_time_level": "",
            # provenance / raw columns
            "area_weight_gsm": gsm.round(3),
            "thickness_in": th_in.round(6),
        }
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")
    typer.echo(f"OK: wrote n={len(out)} -> {out_csv}")


if __name__ == "__main__":
    app()


from __future__ import annotations

"""
Convert the Mendeley knitting dataset into a winter external-validation
catalog.

The script builds proxy winter fields such as `loft_or_clo`,
`wind_blocking`, `moisture_management`, and `bulk_weight`, then writes a CSV
compatible with `external_validation.py`.
"""

import math
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import typer


app = typer.Typer(add_completion=False, help="Map knitting_dataset.csv to a winter external-validation catalog.")


def _norm(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip()


def _to_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x)):
        return float(x)
    s = _norm(x)
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _quantile_levels(series: pd.Series, *, high_is_good: bool) -> pd.Series:
    """
    Map a numeric series to integer levels 1..5 using quintiles.
    """
    s = pd.to_numeric(series, errors="coerce")
    # robust: if too few unique values, fall back to rank-based bins
    if s.dropna().nunique() < 5:
        r = s.rank(method="average", pct=True)
        lvl = (r * 5.0).clip(1, 5).round().astype("Int64")
    else:
        lvl = pd.qcut(s, 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype("Int64")
    if not high_is_good:
        lvl = lvl.map(lambda x: (6 - int(x)) if pd.notna(x) else x).astype("Int64")
    return lvl


def _composition_score(comp: str) -> float:
    """
    Heuristic moisture-management prior from fiber composition.
    """
    c = comp.lower()
    # handle blanks
    if not c:
        return 0.0
    syn = any(k in c for k in ("poly", "nylon", "spandex", "elast", "acrylic", "modal", "viscose", "rayon"))
    cotton = "cotton" in c
    wool = "wool" in c
    if syn and not cotton:
        return 1.0
    if syn and cotton:
        return 0.7
    if wool and not cotton:
        return 0.75
    if wool and cotton:
        return 0.55
    if cotton:
        return 0.35
    return 0.5


def _construction_bonus(cons: str) -> float:
    """
    Small adjustment for moisture/airflow and thermal behavior.
    """
    c = cons.lower()
    if not c:
        return 0.0
    # meshes tend to be more breathable, less insulating
    if "mesh" in c:
        return 0.15
    # rib/interlock can be thicker / more structured
    if "interlock" in c or "rib" in c:
        return -0.05
    return 0.0


def _make_proxy_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    out = df.copy()

    gsm = pd.to_numeric(out.get("GSM"), errors="coerce")
    tight = pd.to_numeric(out.get("tightness_factor"), errors="coerce")
    comp = out.get("composition").astype(str) if "composition" in out.columns else pd.Series([""] * len(out))
    cons = out.get("construction").astype(str) if "construction" in out.columns else pd.Series([""] * len(out))

    # Higher tightness_factor usually means better wind blocking.
    out["wind_blocking"] = _quantile_levels(tight.fillna(tight.median()), high_is_good=True).astype("Int64")

    # Store bulk_weight as 1=light/thin, 5=heavy/bulky.
    out["bulk_weight"] = _quantile_levels(gsm.fillna(gsm.median()), high_is_good=True).astype("Int64")

    # Moisture-management proxy from composition, structure, and tightness.
    base = comp.map(_composition_score).astype(float)
    adj = cons.map(_construction_bonus).astype(float)
    tight_norm = (tight.rank(pct=True) if tight.notna().any() else pd.Series([0.5] * len(out))).fillna(0.5).astype(float)
    moist_score = base + adj + (0.05 * (1.0 - tight_norm))
    out["moisture_management"] = _quantile_levels(moist_score, high_is_good=True).astype("Int64")

    # Continuous loft/clo proxy from GSM and tightness_factor.
    gsm_norm = (gsm.rank(pct=True) if gsm.notna().any() else pd.Series([0.5] * len(out))).fillna(0.5).astype(float)
    loft_score = 0.7 * gsm_norm + 0.3 * tight_norm
    # Match the range used in the benchmark normalization.
    out["loft_or_clo"] = (0.8 + loft_score.clip(0, 1) * (2.6 - 0.8)).round(2)

    report: Dict[str, Any] = {
        "n_rows_in": int(len(df)),
        "gsm_stats": {
            "min": float(gsm.min()) if gsm.notna().any() else None,
            "p50": float(gsm.quantile(0.5)) if gsm.notna().any() else None,
            "max": float(gsm.max()) if gsm.notna().any() else None,
        },
            "notes": "Proxy fields derived from GSM, tightness_factor, composition, and construction.",
    }
    return out, report


@app.command()
def main(
    in_csv: Path = typer.Option(..., "--in-csv", help="Path to knitting_dataset.csv"),
    out_csv: Path = typer.Option(Path("data/real_validation/winter_catalog.csv"), "--out-csv", help="Output catalog CSV path"),
    n_samples: int = typer.Option(80, "--n-samples", help="How many fabrics to sample into the catalog"),
    seed: int = typer.Option(42, "--seed", help="Sampling seed"),
    min_gsm: float = typer.Option(120.0, "--min-gsm", help="Filter: minimum GSM"),
    max_gsm: float = typer.Option(320.0, "--max-gsm", help="Filter: maximum GSM"),
) -> None:
    if not in_csv.exists():
        raise typer.BadParameter(f"Input CSV not found: {in_csv}")

    # This dataset commonly uses Windows-1252 with non-breaking spaces.
    df = pd.read_csv(in_csv, encoding="cp1252")

    if "GSM" not in df.columns:
        raise typer.BadParameter("Expected column 'GSM' not found in knitting_dataset.csv")
    if "tightness_factor" not in df.columns:
        raise typer.BadParameter("Expected column 'tightness_factor' not found in knitting_dataset.csv")

    df["GSM"] = pd.to_numeric(df["GSM"], errors="coerce")
    df["tightness_factor"] = pd.to_numeric(df["tightness_factor"], errors="coerce")

    # Filter to a plausible "midlayer-like" GSM range (avoid extreme heavy/industrial knits).
    pool = df[(df["GSM"].notna()) & (df["GSM"] >= float(min_gsm)) & (df["GSM"] <= float(max_gsm))].copy()
    if pool.empty:
        raise typer.BadParameter(f"No rows after GSM filter [{min_gsm}, {max_gsm}]. Try widening the range.")

    # Deduplicate by (composition, construction, GSM bucket) to reduce near-duplicates.
    pool["gsm_bucket"] = pd.cut(pool["GSM"], bins=[0, 140, 180, 220, 260, 320, 10000], labels=False, include_lowest=True)
    pool["dedupe_key"] = (
        pool.get("composition", "").astype(str).str.lower().str.strip()
        + "|"
        + pool.get("construction", "").astype(str).str.lower().str.strip()
        + "|"
        + pool["gsm_bucket"].astype(str)
    )
    pool = pool.drop_duplicates(subset=["dedupe_key"]).copy()

    # Sample
    n = min(int(n_samples), int(len(pool)))
    sampled = pool.sample(n=n, random_state=int(seed)).reset_index(drop=True)

    # Add proxy winter fields
    sampled, report = _make_proxy_fields(sampled)

    # Build output rows aligned with our external validation CSV template
    rows = pd.DataFrame(
        {
            "id": [f"knit_{i+1:05d}" for i in range(len(sampled))],
            "source_url": "",
            "source_name": "Knitting Dataset (Mendeley)",
            "loft_or_clo": sampled["loft_or_clo"],
            "wind_blocking": sampled["wind_blocking"].astype("Int64"),
            "moisture_management": sampled["moisture_management"].astype("Int64"),
            "bulk_weight": sampled["bulk_weight"].astype("Int64"),
            # Keep machine_wash populated so the winter rule can stay active.
            "care.machine_wash": [True] * len(sampled),
            # Leave unavailable fields blank so coverage filtering can drop them.
            "compliance.pfas_free": "",
            "cost_level": "",
            "lead_time_level": "",
            # Extra source columns are fine here; external_validation.py ignores them.
            "GSM": sampled["GSM"],
            "tightness_factor": sampled["tightness_factor"],
            "composition": sampled.get("composition", ""),
            "construction": sampled.get("construction", ""),
            "body_part": sampled.get("body_part", ""),
        }
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(out_csv, index=False, encoding="utf-8")

    # Write a small sidecar report.
    meta_path = out_csv.with_suffix(".meta.json")
    meta_path.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"OK: wrote winter catalog n={len(rows)} -> {out_csv}")
    typer.echo(f"meta -> {meta_path}")


if __name__ == "__main__":
    app()


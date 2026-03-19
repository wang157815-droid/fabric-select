from __future__ import annotations

"""
Parse RBTR datasheet PDFs into a compact CSV for outdoor external validation.

The parser extracts a small set of measurements from the first pages of each
PDF and leaves the raw values in `*_raw` columns for later mapping.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer


def _read_pdf_text_first_pages(pdf: Path, max_pages: int = 2) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf)
    end = min(int(max_pages), int(doc.page_count))
    parts: List[str] = []
    for i in range(end):
        parts.append(doc.load_page(i).get_text("text") or "")
    return "\n".join(parts)


def _first_match_float(text: str, patterns: List[str]) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if not m:
            continue
        s = (m.group(1) or "").strip().replace(",", "")
        try:
            return float(s)
        except Exception:
            continue
    return None


def _first_match_int(text: str, patterns: List[str]) -> Optional[int]:
    v = _first_match_float(text, patterns)
    if v is None:
        return None
    try:
        return int(round(v))
    except Exception:
        return None


def _clean_id_from_filename(pdf: Path) -> str:
    stem = pdf.stem
    stem = re.sub(r"[^a-zA-Z0-9]+", "_", stem).strip("_")
    return stem[:80] if stem else "rbtr_item"


def _parse_rbtr(text: str) -> Dict[str, Any]:
    # Prefer gsm values, but fall back to grams shown on product-page PDFs.
    weight_gsm = _first_match_float(
        text,
        [
            r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*g\s*/\s*m(?:\u00b2|\^2)\s*\)",
            r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*gsm\s*\)",
            r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*grams?\s*\)",
            r"\bWeight\b.*?\(\s*([0-9]+(?:\.[0-9]+)?)\s*grams?\s*\)",
        ],
    )

    # Air permeability in CFM.
    breathability_cfm = _first_match_float(
        text,
        [
            r"Air Permeability.*?([0-9]+(?:\.[0-9]+)?)\s*ft[^\n]*\(\s*CFM\s*\)",
            r"\(\s*CFM\s*\)\s*([0-9]+(?:\.[0-9]+)?)",
            # product-page tables may show "Air Permeability ... 0 ft³/ft²/min (CFM)" in one line
            r"\bCFM\b\)\s*[\r\n]*\s*([0-9]+(?:\.[0-9]+)?)",
        ],
    )

    # Hydrostatic head in mm.
    hydro_mm = _first_match_int(
        text,
        [
            r"Hydrostatic Head\s*\(pre-wash\).*?~\s*([0-9,]+)\s*mm",
            r"Hydrostatic Head\s*\(pre-wash\).*?([0-9,]+)\s*mm",
            r"Hydrostatic Head.*?~\s*([0-9,]+)\s*mm",
            r"Hydrostatic Head.*?([0-9,]+)\s*mm",
            r"waterproof rating\).*?~\s*([0-9,]+)\s*mm",
        ],
    )

    # Abrasion resistance in revolutions.
    abrasion_rev = _first_match_int(
        text,
        [
            r"Abrasi[ao]n\s+Resistance.*?>\s*([0-9,]+)\s*Revolution",
            r"Abrasi[ao]n\s+Resistance.*?([0-9,]+)\s*Revolution",
        ],
    )

    # Denier such as "20D" or "70D".
    denier = _first_match_int(text, [r"\b([0-9]{2,3})\s*D\b"])

    # Lightweight flags kept in the notes column.
    cal = bool(re.search(r"\bcalendered\b", text, flags=re.IGNORECASE))
    dwr = bool(re.search(r"\bDWR\b", text, flags=re.IGNORECASE))
    pu = bool(re.search(r"\bPU\b", text, flags=re.IGNORECASE))

    return {
        "weight_gsm": weight_gsm,
        "breathability_raw": breathability_cfm,
        "water_repellency_raw": hydro_mm,
        "abrasion_raw": abrasion_rev,
        "denier": denier,
        "notes": "; ".join([p for p in (("calendered" if cal else ""), ("dwr" if dwr else ""), ("pu" if pu else "")) if p]),
    }


app = typer.Typer(add_completion=False, help="Parse RBTR datasheet PDFs into a CSV for external validation.")


@app.command()
def main(
    pdf_dir: Path = typer.Option(..., "--pdf-dir", help="Directory containing RBTR datasheet PDFs."),
    out_csv: Path = typer.Option(Path("data/real_validation/outdoor_catalog.csv"), "--out-csv", help="Output CSV path."),
    source_name: str = typer.Option("RBTR", "--source-name", help="Value for source_name column."),
    scenario: str = typer.Option("outdoor_dwr_windbreaker", "--scenario", help="Scenario label to write (informational)."),
    max_pages: int = typer.Option(2, "--max-pages", help="Max PDF pages to read for text extraction."),
) -> None:
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        raise typer.BadParameter(f"pdf_dir not found: {pdf_dir}")

    pdfs = sorted([p for p in pdf_dir.rglob("*.pdf") if p.is_file()])
    if not pdfs:
        raise typer.BadParameter(f"No PDFs found under: {pdf_dir}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id",
        "source_url",
        "source_name",
        "weight_gsm",
        "water_repellency",
        "breathability",
        "abrasion",
        "handfeel_noise",
        "compliance.pfas_free",
        "cost_level",
        "lead_time_level",
        "water_repellency_raw",
        "breathability_raw",
        "abrasion_raw",
        "notes",
        "pdf_path",
        "scenario",
    ]

    rows: List[Dict[str, Any]] = []
    for pdf in pdfs:
        text = _read_pdf_text_first_pages(pdf, max_pages=max_pages)
        parsed = _parse_rbtr(text)
        rows.append(
            {
                "id": _clean_id_from_filename(pdf),
                "source_url": "",
                "source_name": source_name,
                "weight_gsm": parsed.get("weight_gsm") or "",
                # leave 1..5 ordinals empty; prefer using *_raw then derive in external_validation.py
                "water_repellency": "",
                "breathability": "",
                "abrasion": "",
                "handfeel_noise": "",
                "compliance.pfas_free": "",
                "cost_level": "",
                "lead_time_level": "",
                "water_repellency_raw": parsed.get("water_repellency_raw") or "",
                "breathability_raw": parsed.get("breathability_raw") or "",
                "abrasion_raw": parsed.get("abrasion_raw") or "",
                "notes": parsed.get("notes") or "",
                "pdf_path": str(pdf),
                "scenario": scenario,
            }
        )

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    typer.echo(f"OK: parsed {len(rows)} PDFs -> {out_csv}")


if __name__ == "__main__":
    app()


from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


app = typer.Typer(add_completion=False, help="Extract text and render pages from a PDF into images.")


@app.command()
def main(
    pdf: Path = typer.Option(..., "--pdf", help="Path to the PDF file."),
    out_dir: Path = typer.Option(Path("outputs/papers/pdf_extract"), "--out-dir", help="Output directory."),
    dpi: int = typer.Option(150, "--dpi", help="Render DPI for page images."),
    max_pages: int = typer.Option(
        0,
        "--max-pages",
        help="Max pages to process. 0 means all pages.",
    ),
    text: bool = typer.Option(True, "--text/--no-text", help="Extract page text to a Markdown file."),
    images: bool = typer.Option(True, "--images/--no-images", help="Render each page to PNG."),
    password: Optional[str] = typer.Option(None, "--password", help="Password for encrypted PDFs (if any)."),
) -> None:
    """
    Outputs:
      - text.md (optional): extracted text with page headings
      - page_XXX.png (optional): rendered page images
    """
    try:
        import fitz  # PyMuPDF
    except Exception as e:  # pragma: no cover
        raise typer.BadParameter(
            "PyMuPDF is required. Install with: pip install PyMuPDF"
        ) from e

    if not pdf.exists():
        raise typer.BadParameter(f"PDF not found: {pdf}")

    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf)
    if doc.needs_pass:
        if not password:
            raise typer.BadParameter("PDF is encrypted; pass --password")
        if not doc.authenticate(password):
            raise typer.BadParameter("PDF password authentication failed")

    n_pages = int(doc.page_count)
    end = n_pages if max_pages <= 0 else min(int(max_pages), n_pages)

    scale = float(dpi) / 72.0
    mat = fitz.Matrix(scale, scale)

    md_parts = []
    for i in range(end):
        page = doc.load_page(i)

        if text:
            page_text = page.get_text("text") or ""
            md_parts.append(f"\n\n## Page {i+1}\n\n{page_text}".rstrip() + "\n")

        if images:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_path = out_dir / f"page_{i+1:03d}.png"
            pix.save(str(img_path))

    if text:
        (out_dir / "text.md").write_text("".join(md_parts).lstrip(), encoding="utf-8")

    meta = {
        "pdf": str(pdf),
        "out_dir": str(out_dir),
        "dpi": int(dpi),
        "pages_total": n_pages,
        "pages_processed": end,
        "wrote_text": bool(text),
        "wrote_images": bool(images),
    }
    (out_dir / "meta.json").write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"OK: processed {end}/{n_pages} pages -> {out_dir}")


if __name__ == "__main__":
    app()


















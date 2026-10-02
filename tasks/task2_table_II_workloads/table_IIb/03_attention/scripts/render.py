#!/usr/bin/env python3
"""Render the final PDF for visual review; never marks a PDF reviewed automatically."""
import hashlib
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parents[1]
PDF = HERE / "output/report.zh.pdf"
OUT = HERE / "tmp/pdfs"
OUT.mkdir(parents=True, exist_ok=True)
document = pdfium.PdfDocument(PDF)
assert 2 <= len(document) <= 3, f"Expected 2-3 pages; got {len(document)}"
for stale in OUT.glob("page-*.png"):
    if stale.stem.removeprefix("page-").isdigit() and int(stale.stem.removeprefix("page-")) > len(document):
        stale.unlink()
for number, page in enumerate(document, 1):
    path = OUT / f"page-{number:02d}.png"
    page.render(scale=1.5).to_pil().save(path)
    print(f"{number}: {path.relative_to(HERE)} {hashlib.sha256(path.read_bytes()).hexdigest()}")
print(f"Rendered {len(document)} pages; inspect every page before writing data/pdf_qa.json")

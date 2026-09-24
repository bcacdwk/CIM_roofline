#!/usr/bin/env python3
"""Render the pilot PDF for visual inspection; does not claim human QA."""
from pathlib import Path
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'tmp/pdfs'
target.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(ROOT/'output/pilot.zh.pdf')
for old in target.glob('page-*'):
    if old.suffix in ['.png','.txt'] and old.stem[5:].isdigit(): old.unlink()
for i,page in enumerate(doc,1):
    page.render(scale=1.5).to_pil().save(target/f'page-{i:02d}.png')
    (target/f'page-{i:02d}.txt').write_text(page.get_textpage().get_text_bounded())
print(f'Rendered {len(doc)} pages; inspect images before recording data/pdf_qa.json')

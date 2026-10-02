#!/usr/bin/env python3
"""Render current II(a); visual acceptance is recorded separately."""
from pathlib import Path
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'tmp/pdfs';out.mkdir(parents=True,exist_ok=True)
for old in out.glob('page-*'):
    if old.suffix in ['.png','.txt'] and old.stem[5:].isdigit():old.unlink()
doc=pdfium.PdfDocument(ROOT/'output/table_IIa.pdf')
for i,page in enumerate(doc,1):
    page.render(scale=2).to_pil().save(out/f'page-{i:02d}.png')
    (out/f'page-{i:02d}.txt').write_text(page.get_textpage().get_text_bounded())
print(f'Rendered {len(doc)} pages; inspect before updating data/pdf_qa.json')

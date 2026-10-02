#!/usr/bin/env python3
"""Render all final pages; record QA only after image inspection."""
from pathlib import Path
import pypdfium2 as pdfium
HERE=Path(__file__).resolve().parents[1];target=HERE/'tmp/pdfs'
target.mkdir(parents=True,exist_ok=True)
for old in target.glob('page-*'):
    if old.suffix in ['.png','.txt']:old.unlink()
doc=pdfium.PdfDocument(HERE/'output/attention.zh.pdf')
for i,page in enumerate(doc,1):
    page.render(scale=1.5).to_pil().save(target/f'page-{i:02d}.png')
    (target/f'page-{i:02d}.txt').write_text(page.get_textpage().get_text_bounded())
print(f'Rendered {len(doc)} pages for inspection')

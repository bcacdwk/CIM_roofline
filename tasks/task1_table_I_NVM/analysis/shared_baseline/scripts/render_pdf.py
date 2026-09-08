#!/usr/bin/env python3
"""Render the delivered PDF for visual QA using installed pypdfium2/Pillow.

This is optional for numeric checks; no dependency download is performed.
"""
from pathlib import Path
import pypdfium2 as pdfium

base = Path(__file__).resolve().parents[1]
target = base / 'tmp/pdfs/rendered'
target.mkdir(parents=True, exist_ok=True)
document = pdfium.PdfDocument(base / 'output/shared_baseline.pdf')
for i, page in enumerate(document):
    page.render(scale=1.8).to_pil().save(target / f'page-{i+1:02d}.png')
    text = page.get_textpage().get_text_bounded()
    (target / f'page-{i+1:02d}.txt').write_text(text)
    print(f'page {i+1}: {len(text)} characters; rendered')
print(f'{len(document)} pages in {target}')

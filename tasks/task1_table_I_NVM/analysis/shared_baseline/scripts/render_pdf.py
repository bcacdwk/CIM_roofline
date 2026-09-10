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
# Discard page renders outside the current PDF page range.
for old in target.glob('page-*'):
    if old.suffix in {'.png', '.txt'} and old.stem[5:].isdigit():
        if int(old.stem[5:]) > len(document):
            old.unlink()
for i, page in enumerate(document):
    page.render(scale=1.8).to_pil().save(target / f'page-{i+1:02d}.png')
    text = page.get_textpage().get_text_bounded()
    (target / f'page-{i+1:02d}.txt').write_text(text)
    print(f'page {i+1}: {len(text)} characters; rendered')
print(f'{len(document)} pages in {target}')

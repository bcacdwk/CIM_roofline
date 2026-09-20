#!/usr/bin/env python3
"""Render the final PDF and extract page text for visual QA."""
from pathlib import Path
import pypdfium2 as pdfium

base=Path(__file__).resolve().parents[1]
target=base/'tmp/pdfs/rendered'
target.mkdir(parents=True,exist_ok=True)
document=pdfium.PdfDocument(base/'output/fenor_3d.pdf')
for i,page in enumerate(document):
    page.render(scale=1.65).to_pil().save(target/f'page-{i+1:02d}.png')
    (target/f'page-{i+1:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    print(f'page {i+1}: rendered')

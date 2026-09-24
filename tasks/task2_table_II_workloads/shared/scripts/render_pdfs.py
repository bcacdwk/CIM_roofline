#!/usr/bin/env python3
"""Render both deliverables and extract page text for human visual QA."""
from pathlib import Path
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[2]
for folder,name in [('shared','counting_method.zh'),('table_IIa','table_IIa')]:
    target=ROOT/folder/'tmp/pdfs';target.mkdir(parents=True,exist_ok=True)
    doc=pdfium.PdfDocument(ROOT/folder/'output'/f'{name}.pdf')
    for old in target.glob('page-*'):
        if old.suffix in ['.png','.txt'] and old.stem[5:].isdigit():old.unlink()
    for i,page in enumerate(doc,1):
        page.render(scale=1.5).to_pil().save(target/f'page-{i:02d}.png')
        (target/f'page-{i:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    print(f'{folder}: rendered {len(doc)} pages')

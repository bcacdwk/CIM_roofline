#!/usr/bin/env python3
"""Render every page for inspection; does not itself claim visual QA."""
from pathlib import Path
import pypdfium2 as pdfium

LOCAL=Path(__file__).resolve().parents[1]
target=LOCAL/'tmp/pdfs';target.mkdir(parents=True,exist_ok=True)
for old in target.glob('page-*'):
    if old.suffix in ['.png','.txt'] and old.stem[5:].isdigit():old.unlink()
doc=pdfium.PdfDocument(LOCAL/'output/ffn_moe.zh.pdf')
for index,page in enumerate(doc,1):
    page.render(scale=1.5).to_pil().save(target/f'page-{index:02d}.png')
    (target/f'page-{index:02d}.txt').write_text(page.get_textpage().get_text_bounded())
print(f'Rendered {len(doc)} pages; view every PNG before updating data/pdf_qa.json')

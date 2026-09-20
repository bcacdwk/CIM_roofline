#!/usr/bin/env python3
from pathlib import Path
import pypdfium2 as pdfium
base=Path(__file__).resolve().parents[1]
target=base/'tmp/pdfs/rendered'
target.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(base/'output/feram_hfo2.pdf')
for i,page in enumerate(doc):
    page.render(scale=1.6).to_pil().save(target/f'page-{i+1:02d}.png')
    (target/f'page-{i+1:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    print(f'Rendered page {i+1}')

#!/usr/bin/env python3
"""Render final PDF locally for visual inspection; no original PDF is altered."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'tmp/pdfs/rendered';OUT.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(BASE/'output/pdf/rram.pdf')
thumbs=[]
for i,page in enumerate(doc):
    im=page.render(scale=1.5).to_pil().convert('RGB')
    im.save(OUT/f'page-{i+1:02d}.png')
    thumb=im.copy();thumb.thumbnail((420,594))
    tile=Image.new('RGB',(440,624),'#dddddd');tile.paste(thumb,((440-thumb.width)//2,20))
    ImageDraw.Draw(tile).text((10,605),str(i+1),fill='black');thumbs.append(tile)
for start in range(0,len(thumbs),6):
    items=thumbs[start:start+6];sheet=Image.new('RGB',(3*440,((len(items)+2)//3)*624),'white')
    for j,t in enumerate(items):sheet.paste(t,((j%3)*440,(j//3)*624))
    sheet.save(OUT/f'contact-{start//6+1}.png')
print(f'Rendered {len(doc)} pages to {OUT}')

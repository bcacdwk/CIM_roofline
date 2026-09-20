#!/usr/bin/env python3
"""Render every final page; the temporary output is ignored."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parents[1]
out=base/'tmp/pdfs/final';out.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(base/'output/nor_2d.pdf');thumbs=[]
for i,page in enumerate(doc):
    im=page.render(scale=1.5).to_pil().convert('RGB')
    im.save(out/f'page-{i+1:02}.png')
    im.thumbnail((395,570))
    thumb=Image.new('RGB',(415,600),'#e6e8eb');thumb.paste(im,((415-im.width)//2,18))
    ImageDraw.Draw(thumb).text((15,580),f'Page {i+1}',fill='black');thumbs.append(thumb)
contact=Image.new('RGB',(830,((len(thumbs)+1)//2)*600),'white')
for i,im in enumerate(thumbs):contact.paste(im,((i%2)*415,(i//2)*600))
contact.save(out/'contact.png')
print(f'Rendered {len(doc)} pages: {out}')

#!/usr/bin/env python3
"""Render the final PDF and extract page text for visual QA."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

base=Path(__file__).resolve().parents[1]
target=base/'tmp/pdfs/rendered'
target.mkdir(parents=True,exist_ok=True)
document=pdfium.PdfDocument(base/'output/fenor_3d.pdf')
thumbnails=[]
for i,page in enumerate(document):
    rendered=page.render(scale=1.65).to_pil()
    rendered.save(target/f'page-{i+1:02d}.png')
    thumbnail=rendered.copy()
    thumbnail.thumbnail((480,680))
    thumbnails.append(thumbnail)
    (target/f'page-{i+1:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    print(f'page {i+1}: rendered')
contact=Image.new('RGB',(3*500,((len(thumbnails)+2)//3)*720),'#dddddd')
draw=ImageDraw.Draw(contact)
for i,thumbnail in enumerate(thumbnails):
    x,y=(i%3)*500+10,(i//3)*720+10
    contact.paste(thumbnail,(x,y))
    draw.text((x,y+686),f'Page {i+1}',fill='black')
contact.save(target/'contact.png')

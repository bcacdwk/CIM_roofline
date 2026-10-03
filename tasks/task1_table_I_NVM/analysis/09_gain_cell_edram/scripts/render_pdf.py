#!/usr/bin/env python3
"""Render the actual delivered PDF and refresh its exact-page contact sheet."""
from pathlib import Path
import hashlib, math
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
base=Path(__file__).resolve().parents[1]
target=base/'tmp/pdfs/rendered'
target.mkdir(parents=True,exist_ok=True)
pdf=base/'output/gain_cell_edram.pdf'
doc=pdfium.PdfDocument(pdf)
cols=min(3,len(doc)); contact=Image.new('RGB',(520*cols,760*math.ceil(len(doc)/cols)),'#e6e6e6')
for i,page in enumerate(doc):
    im=page.render(scale=1.8).to_pil().convert('RGB')
    im.save(target/f'page-{i+1:02d}.png')
    (target/f'page-{i+1:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    im.thumbnail((520,735));contact.paste(im,((i%cols)*520,(i//cols)*760))
    ImageDraw.Draw(contact).text(((i%cols)*520+8,(i//cols)*760+740),f'Page {i+1}',fill='black')
contact.save(target/'contact.png')
print('Pages:',len(doc),'SHA256:',hashlib.sha256(pdf.read_bytes()).hexdigest())
print('Current contact:',target/'contact.png')

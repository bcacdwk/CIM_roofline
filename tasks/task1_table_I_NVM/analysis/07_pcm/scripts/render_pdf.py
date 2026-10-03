#!/usr/bin/env python3
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parents[1]
target=base/'tmp/pdfs/rendered'; target.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(base/'output/pcm.pdf')
thumbs=[]
for i,page in enumerate(doc):
    page.render(scale=1.6).to_pil().save(target/f'page-{i+1:02d}.png')
    (target/f'page-{i+1:02d}.txt').write_text(page.get_textpage().get_text_bounded())
    im=page.render(scale=.8).to_pil().convert('RGB');im.thumbnail((396,560))
    canvas=Image.new('RGB',(416,590),'#dddddd');canvas.paste(im,((416-im.width)//2,10));ImageDraw.Draw(canvas).text((10,571),f'Page {i+1}',fill='black');thumbs.append(canvas)
    print(f'Rendered page {i+1}')
sheet=Image.new('RGB',(3*416,((len(thumbs)+2)//3)*590),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%3)*416,(i//3)*590))
sheet.save(target/'contact.png')

#!/usr/bin/env python3
from pathlib import Path
import json
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw
base=Path(__file__).resolve().parents[1]
out=base/'tmp/pdfs/rendered'
out.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(base/'output/nand_3d.pdf')
thumbs=[];manifest=[]
for i,page in enumerate(doc):
    im=page.render(scale=1.6).to_pil().convert('RGB')
    path=out/f'page-{i+1:02}.png'; im.save(path)
    manifest.append(dict(page=i+1,image=str(path.relative_to(base)),size=im.size))
    t=im.copy();t.thumbnail((396,560));canvas=Image.new('RGB',(416,590),'#dddddd');canvas.paste(t,((416-t.width)//2,15));ImageDraw.Draw(canvas).text((12,572),f'Page {i+1}',fill='black');thumbs.append(canvas)
sheet=Image.new('RGB',(3*416,((len(thumbs)+2)//3)*590),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%3)*416,(i//3)*590))
sheet.save(out/'contact-sheet.png')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Rendered {len(doc)} pages to {out}')

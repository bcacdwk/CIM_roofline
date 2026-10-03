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

# The contact sheet includes exactly the freshly rendered pages in this PDF.
from PIL import Image, ImageDraw
import hashlib, math
cols=min(3,len(doc)); rows=math.ceil(len(doc)/cols)
contact=Image.new('RGB',(cols*520,rows*760),'#e6e6e6')
for i in range(len(doc)):
    im=Image.open(target/f'page-{i+1:02d}.png').convert('RGB')
    im.thumbnail((520,735))
    contact.paste(im,((i%cols)*520,(i//cols)*760))
    ImageDraw.Draw(contact).text(((i%cols)*520+8,(i//cols)*760+740),f'Page {i+1}',fill='black')
contact.save(target/'contact.png')
print('PDF pages:',len(doc),'SHA256:',hashlib.sha256((base/'output/feram_hfo2.pdf').read_bytes()).hexdigest())
print('Current contact:',target/'contact.png')

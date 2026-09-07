#!/usr/bin/env python3
"""Copy final PDF, render every page, and report bounding boxes and TeX dimensions.

Uses existing pdfplumber (pypdfium2 rendering); no OCR and no environment changes.
"""
from pathlib import Path
import hashlib
import json
import logging
import re
import shutil
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]
logging.getLogger("pdfminer").setLevel(logging.ERROR)
source=ROOT/"tex/build/table_i_standalone.pdf"
target=ROOT/"output/table_i.pdf"
log=(ROOT/"tex/build/table_i_standalone.log").read_text()
for pattern in [r"Citation .* undefined", "There were undefined references", "Overfull "]:
    assert not re.search(pattern,log),pattern
shutil.copyfile(source,target)
pages=[]
with pdfplumber.open(target) as pdf:
    for i,p in enumerate(pdf.pages):
        text=p.extract_text() or ""
        assert "[?]" not in text
        assert p.chars
        bbox=[min(c["x0"] for c in p.chars),min(c["top"] for c in p.chars),
              max(c["x1"] for c in p.chars),max(c["bottom"] for c in p.chars)]
        assert 0<=bbox[0]<bbox[2]<=p.width and 0<=bbox[1]<bbox[3]<=p.height
        png=ROOT/f"output/table_i_page_{i+1}.png"
        p.to_image(resolution=170).save(png)
        pages.append(dict(page=i+1,width_pt=p.width,height_pt=p.height,content_bbox_pdf_pt=bbox,
            content_width_mm=(bbox[2]-bbox[0])*25.4/72,content_height_mm=(bbox[3]-bbox[1])*25.4/72,
            png=png.relative_to(ROOT).as_posix(),body_font_pt=8.5 if i==0 else None))
        (ROOT/f"output/table_i_page_{i+1}.txt").write_text(text+"\n")
width=float(re.search(r"T1_BODY_WIDTH_PT=([\d.]+)pt",log).group(1))
height=float(re.search(r"T1_BODY_HEIGHT_PT=([\d.]+)pt",log).group(1))
depth=float(re.search(r"T1_BODY_DEPTH_PT=([\d.]+)pt",log).group(1))
report=dict(status="PASS_AUTOMATED_LAYOUT_CHECKS",pages=pages,
    table_body_including_notes=dict(width_TeX_pt=width,height_plus_depth_TeX_pt=height+depth,
        width_mm=width*25.4/72.27,height_mm=(height+depth)*25.4/72.27),
    font_policy="8.5pt body and notes, no resizebox/scalebox; mathematical subscripts retain normal TeX sizing.",
    unresolved_citations=0,overfull_boxes=0,
    sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    visual_review="Page PNGs must also be inspected; see AUDIT.md for human-readable review.")
(ROOT/"output/pdf_qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report["table_body_including_notes"],indent=2))

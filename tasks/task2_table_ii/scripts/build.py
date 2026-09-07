"""Task-local build, PDF rendering and mechanical layout/reference QA."""
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]


def main():
    (ROOT/"build").mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(ROOT/"scripts/generate.py")],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/verify_exports.py")],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/summarize.py")],check=True,cwd=ROOT)
    test=subprocess.run([sys.executable,str(ROOT/"scripts/test_counts.py")],text=True,capture_output=True,cwd=ROOT)
    (ROOT/"output/tests.txt").write_text(test.stdout+test.stderr)
    if test.returncode: raise SystemExit(test.stdout+test.stderr)
    cmd=["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-outdir=../build","table_ii_standalone.tex"]
    res=subprocess.run(cmd,cwd=ROOT/"tex",capture_output=True,text=True)
    (ROOT/"build/build_stdout.txt").write_text(res.stdout+res.stderr)
    if res.returncode: raise SystemExit(res.stdout+res.stderr)
    log=(ROOT/"build/table_ii_standalone.log").read_text()
    forbidden=["undefined","Overfull","Extra alignment","LaTeX Error"]
    errors=[line for line in log.splitlines() if any(s in line for s in forbidden)]
    assert not errors,errors
    shutil.copy2(ROOT/"build/table_ii_standalone.pdf",ROOT/"output/table_ii.pdf")
    pdf=pdfium.PdfDocument(ROOT/"output/table_ii.pdf")
    for i,page in enumerate(pdf): page.render(scale=2).to_pil().save(ROOT/f"build/page_{i+1}.png")
    with pdfplumber.open(ROOT/"output/table_ii.pdf") as doc:
        text="\n".join(p.extract_text() or "" for p in doc.pages)
        assert "TABLEII" in (doc.pages[0].extract_text() or "").replace(" ","")
        assert "REFERENCES" in text and "[9]" in text and "[?]" not in text
        assert all(p.chars for p in doc.pages),"unexpected blank page"
        sizes=Counter(round(c["size"],2) for c in doc.pages[0].chars)
        bounds=[]
        for p in doc.pages:
            bounds.append({"width_pt":p.width,"height_pt":p.height,"text_left":min(c["x0"] for c in p.chars),"text_right":max(c["x1"] for c in p.chars),"text_top":min(c["top"] for c in p.chars),"text_bottom":max(c["bottom"] for c in p.chars)})
        qa={"pages":len(doc.pages),"fonts_first_page_size_counts":dict(sizes),"page_bounds":bounds,"undefined_citations":False,"overfull_boxes":False,"renderer":"existing pypdfium2 / PDFium; Poppler unavailable","manual_visual_review":"see AUDIT.md"}
    (ROOT/"output/pdf_qa.json").write_text(json.dumps(qa,indent=2)+"\n")
    (ROOT/"output/table_ii_extracted.txt").write_text(text+"\n")
    print(json.dumps(qa,indent=2))


if __name__=="__main__": main()

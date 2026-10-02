#!/usr/bin/env python3
"""Render pages and verify a recorded visual review; --record-review takes one note per page."""
import argparse
import hashlib
import json
from pathlib import Path
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-review", nargs="+", metavar="PAGE_NOTE")
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args()
    pdf_path = HERE / "output/report.zh.pdf"
    document = pdfium.PdfDocument(str(pdf_path))
    count = len(document)
    if not 1 <= count <= 3:
        raise SystemExit(f"Unexpected page count {count}")
    pages = []
    for index in range(count):
        path = HERE / f"tmp/pdfs/page-{index+1:02d}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        document[index].render(scale=1.7).to_pil().save(path)
        pages.append({"page": index+1, "png": str(path.relative_to(HERE)), "sha256": sha(path)})
    qa_path = HERE / "data/pdf_qa.json"
    if args.record_review:
        if len(args.record_review) != count:
            raise SystemExit("Exactly one inspection note is required per page")
        for page, note in zip(pages, args.record_review):
            page["notes"] = note
        qa = {"status": "PASS", "pdf": "output/report.zh.pdf", "sha256": sha(pdf_path),
              "page_count": count, "page_reviews": pages}
        qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("PASS: explicit visual-review notes recorded")
    elif qa_path.exists() and not args.render_only:
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        assert qa["status"] == "PASS" and qa["sha256"] == sha(pdf_path) and qa["page_count"] == count
        assert [{k: r[k] for k in ["page", "png", "sha256"]} for r in qa["page_reviews"]] == pages
        print("PASS: rendered pages match the recorded visual review")
    else:
        print(json.dumps({"status": "REVIEW_REQUIRED", "page_count": count, "pages": pages}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

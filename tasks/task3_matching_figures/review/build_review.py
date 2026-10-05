#!/usr/bin/env python3
"""Assemble the five vector candidates and render the final review PDF."""
from pathlib import Path
import hashlib
import json
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
CANDIDATES = [
    ("A", "Hardware and reuse", "01_hardware_overlay/figure.pdf"),
    ("B", "Absolute QKV demand", "02_demand_dual/output/figure.pdf"),
    ("C", "Critical reuse", "03_reuse_threshold/output/figure.pdf"),
    ("D", "Approaching the ceiling", "04_normalized_response/output/figure.pdf"),
    ("E", "Bottleneck-directed improvement", "05_improvement_payoff/output/figure.pdf"),
]


def main():
    rendered = HERE / "rendered"
    rendered.mkdir(exist_ok=True)
    merged = pdfium.PdfDocument.new()
    records = []
    for letter, title, rel in CANDIDATES:
        path = TASK / rel
        src = pdfium.PdfDocument(path)
        assert len(src) == 1, path
        merged.import_pages(src)
        src.close()
        records.append({"candidate": letter, "title": title,
                        "source": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    out = HERE / "candidates.pdf"
    merged.save(out)
    merged.close()
    final = pdfium.PdfDocument(out)
    assert len(final) == 5
    previews = []
    for page_index, record in enumerate(records):
        page = final[page_index]
        size = page.get_size()
        record["paper_inches"] = [v / 72 for v in size]
        record["page"] = page_index + 1
        img = page.render(scale=2).to_pil().convert("RGB")
        img.save(rendered / f"candidate_{record['candidate']}.png")
        record["render_dpi"] = 144
        record["extracted_text_characters"] = len(page.get_textpage().get_text_range())
        previews.append(img.copy())
        page.close()
    final.close()

    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font = ImageFont.truetype(font_path, 25)
    small = ImageFont.truetype(font_path, 20)
    canvas = Image.new("RGB", (1800, 1810), "#f0f3f6")
    draw = ImageDraw.Draw(canvas)
    draw.text((34, 22), "Task III | Five candidate figures", font=font, fill="#182838")
    draw.text((34, 60), "A-C: capacity and demand; D-E: reuse response and improvement", font=small, fill="#657382")
    cell_w, cell_h = 865, 555
    for i, (preview, record) in enumerate(zip(previews, records)):
        col, row = i % 2, i // 2
        x, y = 24 + col * 887, 105 + row * 562
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=10, fill="white")
        draw.text((x + 16, y + 12), f"{record['candidate']}  {record['title']}", font=font, fill="#182838")
        preview.thumbnail((cell_w - 24, cell_h - 55), Image.Resampling.LANCZOS)
        canvas.paste(preview, (x + (cell_w - preview.width) // 2, y + 48 + (cell_h - 55 - preview.height) // 2))
    draw.text((935, 1340), "Review before choosing up to two figures", font=font, fill="#182838")
    draw.text((935, 1390), "Native full-load reuse reference: A / C / D / E", font=small, fill="#657382")
    draw.text((935, 1425), "Explicit 128 x 128 tile mapping: B", font=small, fill="#657382")
    canvas.save(HERE / "overview.png")
    qa = {"status": "rendered_for_supervisor_review", "page_count": 5,
          "combined_pdf_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
          "vector_pages_preserved": True, "pages": records}
    (HERE / "pdf_qa.json").write_text(json.dumps(qa, indent=2) + "\n")
    print("Built five-page vector PDF, five 144 dpi page renders, and overview.png")


if __name__ == "__main__":
    main()

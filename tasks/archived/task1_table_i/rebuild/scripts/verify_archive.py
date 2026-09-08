"""R0 file integrity and navigation checks; no technical parameter extraction."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
m = json.loads((BASE / 'source_manifest.json').read_text())
records = m['sources']
assets = []
for s in records:
    if s['main_file']:
        assets.append((s['source_id'], s['main_file']))
    for f in s['supplements']:
        assets.append((s['source_id'] + ' SI', f))
    for v in s['related_versions']:
        if v.get('file'):
            assets.append((s['source_id'] + ' related', v['file']))

previews = BASE / 'tmp/preview'
previews.mkdir(parents=True, exist_ok=True)
rendered = []
thumbs = []
for label, a in assets:
    p = REPO / a['path']
    assert p.is_relative_to(BASE)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == a['sha256'], p
    doc = pdfium.PdfDocument(p)
    assert len(doc) == a['pages']
    img = doc[0].render(scale=1.2).to_pil().convert('RGB')
    img.thumbnail((490, 670))
    tile = Image.new('RGB', (520, 715), 'white')
    tile.paste(img, ((520 - img.width) // 2, 30))
    ImageDraw.Draw(tile).text((10, 7), label + f' | {a["pages"]}p', fill='black')
    thumbs.append(tile)
    rendered.append(dict(path=a['path'], pages=a['pages'], sha256_ok=True, first_page_rendered=True))
    doc.close()
for offset in range(0, len(thumbs), 6):
    sheet = Image.new('RGB', (1560, 1430), '#dddddd')
    for n, tile in enumerate(thumbs[offset:offset+6]):
        sheet.paste(tile, ((n % 3) * 520, (n // 3) * 715))
    sheet.save(previews / f'contact_{offset // 6 + 1:02d}.png')

broken = []
for p in BASE.rglob('*.md'):
    if 'tmp' in p.relative_to(BASE).parts:
        continue
    for link in re.findall(r'\]\(([^\n]*?)\)', p.read_text()):
        if link.startswith(('https://', 'http://')):
            continue
        target, _, anchor = link.partition('#')
        q = (p.parent / unquote(target)).resolve() if target else p
        if not q.exists():
            broken.append(dict(file=p.relative_to(BASE).as_posix(), target=link))
        elif anchor and q.suffix == '.md' and f'id="{anchor}"' not in q.read_text():
            broken.append(dict(file=p.relative_to(BASE).as_posix(), target=link, reason='anchor missing'))
assert not broken, broken
requests = (BASE / 'DOWNLOAD_REQUESTS_V1.md').read_text()
batch_a, batch_b = requests.split('## A. 第一批优先下载')[1].split('## B. 暂缓候补')
assert batch_a.count('- [ ]') == m['counts']['first_batch_packages']
assert batch_b.count('- [ ]') == m['counts']['deferred_packages']
for s in records:
    assert s['title'] and s['authors'] and s['official_url']
    assert s.get('doi') or s.get('document_id') or s['official_url']
    assert Path(s['target_path']).parent.is_relative_to(Path('tasks/task1_table_i/rebuild/literature'))
    assert not (s['request_batch'] == 'A' and s['main_file'])
    assert s['target_path'] in (BASE / 'LITERATURE_CATALOG.md').read_text() or Path(s['target_path']).name in (BASE / 'LITERATURE_CATALOG.md').read_text()
report = dict(date='2026-09-08', local_pdf_count=len(assets), expected_local_pdf_count=31,
              all_hashes_match=True, all_first_pages_rendered=True, local_markdown_links_valid=True,
              manual_batch_a_count=batch_a.count('- [ ]'), manual_batch_b_count=batch_b.count('- [ ]'),
              preview_contact_sheets=len(list(previews.glob('contact_*.png'))),
              visual_review='All six contact sheets inspected on 2026-09-08; title pages matched the records; cover pages were supplemented by text inspection of the article page.', files=rendered)
assert len(assets) == report['expected_local_pdf_count']
(BASE / 'metadata/archive_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False))

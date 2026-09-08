"""核验当前 V3 资料归档与导航，不联网、不修改 Git。"""
from pathlib import Path
from urllib.parse import unquote
from collections import Counter
import hashlib,json,re,subprocess
import pypdfium2 as pdfium

B=Path(__file__).resolve().parents[1];R=B.parents[2]
m=json.loads((B/'source_manifest.json').read_text());assert len(m['sources'])==62
assets=[]
for s in m['sources']:
    assert s['identity_verified'] and s['title'] and s['authors'] and s['official_url']
    if s['main_file']:
        assert s['target_path']==s['main_file']['path']
        assert s['review_status']=='fulltext_suitability_reviewed'
        assets.append(s['main_file'])
    else:assert s['source_id'] in ['SDCIM-04','SDCIM-05'] and not (R/s['target_path']).exists()
    assets+=s['supplements']
    assets +=[v['file'] for v in s['related_versions'] if v.get('file')]
assert len(assets)==69
registered={(R/a['path']).resolve() for a in assets}
assert registered=={p.resolve() for p in (B/'literature').rglob('*.pdf')}
checks=[]
for a in assets:
    p=R/a['path'];assert p.is_relative_to(B)
    blob=p.read_bytes();assert blob.startswith(b'%PDF-') and len(blob)==a['bytes']
    assert hashlib.sha256(blob).hexdigest()==a['sha256']
    d=pdfium.PdfDocument(p);assert len(d)==a['pages']
    for i in range(len(d)):
        pg=d[i];assert min(pg.get_size())>0;pg.close()
    for i in [0,len(d)-1]:pg=d[i];pg.render(scale=.2).to_pil();pg.close()
    d.close();checks.append(dict(path=a['path'],pages=a['pages'],sha256=a['sha256'],hash_signature_pages_render_ok=True))
assert len({a['sha256'] for a in assets})==69
incoming=json.loads((B/'metadata/intake_v2_completed.json').read_text());assert len(incoming)==5
for a in incoming:assert hashlib.sha256((R/a['to_path']).read_bytes()).hexdigest()==a['sha256']
assert len(m['pending_downloads'])==2
v3=(B/'DOWNLOAD_REQUESTS_V1.md').read_text();assert v3.startswith('# 人工下载清单 V3') and v3.count('- [ ]')==2
for x in m['pending_downloads']:assert x['target_path'] in v3 and not (R/x['target_path']).exists()
assert (B/'history/r1_v2/DOWNLOAD_REQUESTS_V1.md').read_text().count('- [ ]')==5
bad=[]
for p in list(B.glob('*.md'))+list((B/'literature').glob('*/README.md')):
    for l in re.findall(r'\]\(([^\n]*?)\)',p.read_text()):
        if l.startswith(('https://','http://')):continue
        t,_,a=l.partition('#');q=(p.parent/unquote(t)).resolve() if t else p
        if not q.exists():bad.append((p.name,l,'file'))
        elif a and q.suffix=='.md' and f'id="{a}"' not in q.read_text():bad.append((p.name,l,'anchor'))
assert not bad,bad
assert '*.pdf' not in (B/'.gitignore').read_text()
for p in registered:assert subprocess.run(['git','check-ignore','--quiet',str(p)],cwd=R).returncode==1
for sid in ['FENOR-01','FENOR-02']:
    s=next(s for s in m['sources'] if s['source_id']==sid)
    assert hashlib.sha256((R/s['copy_provenance']['original_path']).read_bytes()).hexdigest()==s['main_file']['sha256']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert head=='5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c'
outside=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines();assert set(outside)<={'.DS_Store','tasks/.DS_Store'}
out=dict(date='2026-09-08',version=3,source_records=62,source_packages=61,local_main=60,local_pdf=69,
         v2_received_packages=5,v2_missing_packages=0,v3_pending_packages=2,
         sram_dcim_candidates=5,sram_dcim_main_available=3,all_local_assets_valid=True,
         renamed_user_files_byte_unchanged=5,unregistered_pdf=0,duplicate_pdf_hashes=0,
         current_markdown_links_valid=True,user_pdf_git_policy_preserved=True,zhou_root_originals_unchanged=True,
         pdf_downloaded_this_round=0,head=head,tracked_changes_outside_task=outside,
         visual_review='本轮五个用户来件首页及 RRAM-06 Fig.9/10、PCM-04-SI Fig.S6、SACIM-05 Fig.6/10 已看图；结合正文/Methods 核查用途。所有 PDF 首尾可渲染。',files=checks)
for fn in ['archive_validation_v3.json','archive_validation.json']:(B/'metadata'/fn).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='files'},ensure_ascii=False,indent=2))

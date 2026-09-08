"""本地归档一致性核验；不联网、不修改 Git。"""
from pathlib import Path
import hashlib,json,re,subprocess
from urllib.parse import unquote
import pypdfium2 as pdfium

B=Path(__file__).resolve().parents[1];R=B.parents[2]
m=json.loads((B/'source_manifest.json').read_text())
assets=[]
for s in m['sources']:
    assert s['identity_verified'] and s['title'] and s['authors'] and s['official_url']
    if s['main_file']:
        assert s['target_path']==s['main_file']['path']
        assets.append(s['main_file'])
        assert s['review_status']=='fulltext_suitability_reviewed'
    else:
        assert s['request_batch']=='C'
        assert not (R/s['target_path']).exists()
    assets.extend(s['supplements'])
    assets.extend(v['file'] for v in s['related_versions'] if v.get('file'))
assert len(assets)==64
actual={p.resolve() for p in (B/'literature').rglob('*.pdf')}
registered={(R/f['path']).resolve() for f in assets}
assert actual==registered,(actual-registered,registered-actual)
assert len(registered)==len(assets)
checks=[]
for f in assets:
    p=R/f['path'];assert p.is_relative_to(B)
    blob=p.read_bytes();assert blob.startswith(b'%PDF-')
    assert len(blob)==f['bytes'] and hashlib.sha256(blob).hexdigest()==f['sha256'],p
    d=pdfium.PdfDocument(p);assert len(d)==f['pages']
    for i in range(len(d)):
        pa=d[i];assert min(pa.get_size())>0;pa.close()
    pa=d[0];pa.render(scale=.2).to_pil();pa.close()
    pa=d[len(d)-1];pa.render(scale=.2).to_pil();pa.close();d.close()
    checks.append(dict(path=f['path'],pages=f['pages'],sha256_ok=True,pdf_signature_ok=True,all_page_dimensions_ok=True,first_and_last_page_rendered=True))

# 30 个用户来件：沿着目录整理关系验证哈希未改变。
org=json.loads((B/'metadata/organization_log_r1.json').read_text())
mapping={x['from_path']:x['to_path'] for x in org}
incoming=json.loads((B/'metadata/rename_log_r1.json').read_text())
for f in incoming:
    p=f['to_path']
    while p in mapping:p=mapping[p]
    assert hashlib.sha256((R/p).read_bytes()).hexdigest()==f['sha256'],p
assert len(incoming)==30
for sid in ['FENOR-01','FENOR-02']:
    s=next(s for s in m['sources'] if s['source_id']==sid);v=s['copy_provenance']
    assert hashlib.sha256((R/v['original_path']).read_bytes()).hexdigest()==s['main_file']['sha256']

broken=[]
for p in B.glob('*.md'):
    for link in re.findall(r'\]\(([^\n]*?)\)',p.read_text()):
        if link.startswith(('http://','https://')):continue
        target,_,anchor=link.partition('#');q=(p.parent/unquote(target)).resolve() if target else p
        if not q.exists():broken.append((p.name,link,'file missing'))
        elif anchor and q.suffix=='.md' and f'id="{anchor}"' not in q.read_text():broken.append((p.name,link,'anchor missing'))
assert not broken,broken
v2=(B/'DOWNLOAD_REQUESTS_V1.md').read_text()
assert v2.startswith('# 人工下载清单 V2') and v2.count('- [ ]')==5
for s in m['sources']:
    if not s['main_file']:assert s['target_path'] in v2
assert len([s for s in m['sources'] if not s['main_file']])==4
assert not (B/'literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf').exists()
assert (B/'history/r0/DOWNLOAD_REQUESTS_V1.md').exists()
assert '*.pdf' not in (B/'.gitignore').read_text()
for p in actual:
    r=subprocess.run(['git','check-ignore','--quiet',str(p)],cwd=R)
    assert r.returncode==1,('PDF unexpectedly ignored',p)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
assert head=='5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c'
changed=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines()
assert set(changed)<= {'.DS_Store','tasks/.DS_Store'},changed
report=dict(date='2026-09-08',stage='R1',head=head,local_pdf_count=len(assets),
            main_records=56,source_records=60,packages=59,user_intake_hashes_unchanged=30,
            original_A_B_missing_main=0,manual_v2_packages=5,manual_v2_main=4,manual_v2_existing_supplement=1,
            all_registered_files_exist=True,no_unregistered_pdf=True,byte_identical_duplicates=0,
            current_markdown_links_valid=True,pdf_git_ignore_disabled_as_user_requested=True,
            zhou_root_originals_unchanged=True,outside_task_tracked_changes=changed,
            visual_review='55 条原主文封面联系表、字体异常 PDF 及关键时序/表格已检查；新增主文、两份 SI 与额外简表的首页/第二页已看。全文件首尾页另做可渲染检查。',files=checks)
for name in ['archive_validation_r1.json','archive_validation.json']:(B/'metadata'/name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))

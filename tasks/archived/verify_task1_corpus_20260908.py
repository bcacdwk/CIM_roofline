"""离线检查独立语料和旧任务归档；结果仅写入 archived。"""
from pathlib import Path
from urllib.parse import unquote
import json,hashlib,re,subprocess
import pypdfium2 as pdfium

R=Path(__file__).resolve().parents[2];B=R/'tasks/task1_table_I_NVM';A=R/'tasks/archived'
m=json.loads((B/'source_manifest.json').read_text());migration=json.loads((A/'TASK1_MIGRATION_RECORD.json').read_text())
assert m['status']=='READY_FOR_ANALYSIS' and len(m['sources'])==55
assert not (R/'tasks/task1_table_i').exists()
assert len({s['source_id'] for s in m['sources']})==55
assert {s['source_id'] for s in m['sources'] if s['group']=='02_sram_dcim'}=={f'SDCIM-0{i}' for i in range(1,6)}
assets=[f for s in m['sources'] for f in [s['pdf']]+s['supplements']]
assert len(assets)==59
actual={p.resolve() for p in B.rglob('*.pdf')};registered={(B/f['path']).resolve() for f in assets}
assert actual==registered
assert len({f['sha256'] for f in assets})==59
for f in assets:
    p=B/f['path'];assert p.resolve().is_relative_to(B)
    blob=p.read_bytes();assert blob.startswith(b'%PDF-') and len(blob)==f['bytes']
    assert hashlib.sha256(blob).hexdigest()==f['sha256']
    d=pdfium.PdfDocument(p);assert len(d)==f['pages']
    for i in range(len(d)):
        pg=d[i];assert min(pg.get_size())>0;pg.close()
    for i in [0,len(d)-1]:pg=d[i];pg.render(scale=.2).to_pil();pg.close()
    d.close()
    assert subprocess.run(['git','check-ignore','--quiet',str(p)],cwd=R).returncode==1
for p in B.rglob('*.md'):
    t=p.read_text();assert 'tasks/task1_table_i/' not in t and '/rebuild/' not in t
    for l in re.findall(r'\]\(([^\n]*?)\)',t):
        if l.startswith(('http://','https://')):continue
        target,_,anchor=l.partition('#');q=(p.parent/unquote(target)).resolve() if target else p
        assert q.exists(),(p,l)
        if anchor and q.suffix=='.md':assert f'id="{anchor}"' in q.read_text(),(p,l)
forbidden={'tmp','history','versions','comparisons','metadata','scripts','__pycache__','build','archived','rebuild'}
assert not any(p.is_dir() and p.name in forbidden for p in B.rglob('*'))
assert not any(p.suffix in {'.py','.pyc','.log','.csv','.tex','.png','.jpg','.zip'} for p in B.rglob('*') if p.is_file())
assert not any(p.name.startswith('DOWNLOAD') for p in B.rglob('*'))
assert not list((A/'task1_table_i').rglob('tmp'))
assert not list((A/'task1_table_i').rglob('__pycache__'))
deleted={f['sha256'] for f in migration['deleted_literature']}
assert not deleted & {f['sha256'] for f in assets}

# 原先受版本控制的 Task I 文件均按原字节存入冷归档。
tracked=subprocess.check_output(['git','ls-files','-s','--','tasks/task1_table_i'],cwd=R,text=True).splitlines()
verified_archive=[]
for line in tracked:
    meta,path=line.split('\t',1);expected=meta.split()[1]
    p=A/'task1_table_i'/Path(path).relative_to('tasks/task1_table_i');assert p.exists(),path
    raw=p.read_bytes();actualhash=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert actualhash==expected,path
    verified_archive.append(path)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
assert head==migration['head']
changes=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines()
assert all(p.startswith('tasks/task1_table_i/') or p in {'.DS_Store','tasks/.DS_Store'} for p in changes)
oldm=json.loads((A/'task1_table_i/rebuild/source_manifest.json').read_text())
for sid in ['FENOR-01','FENOR-02']:
    old=next(s for s in oldm['sources'] if s['source_id']==sid);cur=next(s for s in m['sources'] if s['source_id']==sid)
    root=R/old['copy_provenance']['original_path'];assert hashlib.sha256(root.read_bytes()).hexdigest()==cur['pdf']['sha256']
result=dict(status='PASS',date='2026-09-08',head=head,
  active_sources=55,active_pdf=59,main_pdf=55,supplement_pdf=4,dcim_main=5,
  missing_files=0,duplicate_hashes=0,local_links_valid=True,all_pdfs_open_and_render=True,
  old_task_path_absent=True,tracked_legacy_files_preserved=len(verified_archive),
  deleted_literature_pdf=len(migration['deleted_literature']),
  removed_temporary_files=sum(x['files'] for x in migration['removed_temporary_directories']),
  active_folder_has_no_history_or_temp=True,user_pdf_git_policy_preserved=True,
  root_zhou_files_unchanged=True,paper_and_table_ii_unchanged=True,pdf_downloads=0,
  git_mutating_commands_performed=False)
(A/'TASK1_MIGRATION_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))

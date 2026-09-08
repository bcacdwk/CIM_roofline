"""Explicit R1 intake; never infer identity from a reference-list DOI."""
from pathlib import Path
import collections, hashlib, json, logging, re, shutil, subprocess
import pdfplumber

logging.getLogger('pdfminer').setLevel(logging.ERROR)
B=Path(__file__).resolve().parents[1]
R=B.parents[2]
H=B/'history/r0'
H.mkdir(parents=True,exist_ok=True)
for name in ['README.md','LITERATURE_CATALOG.md','DOWNLOAD_REQUESTS_V1.md','COVERAGE.md','source_manifest.json']:
    if not (H/name).exists():shutil.copy2(B/name,H/name)
histmeta=H/'metadata';histmeta.mkdir(exist_ok=True)
for name in ['VERIFICATION.md','archive_validation.json']:
    if not (histmeta/name).exists():shutil.copy2(B/'metadata'/name,histmeta/name)

m=json.loads((H/'source_manifest.json').read_text())
byid={s['source_id']:s for s in m['sources']}
incoming={
 'CMOS-03':'SRAM_Assist_Techniques*', 'CMOS-04':'A_28_nm_Dual-Port*', 'CMOS-05':'A_28-nm_8-Bit*',
 'SACIM-03':'A_28nm_32Kb_SRAM*','SACIM-04':'A_Charge_Domain*',
 'SDCIM-02':'A_Digital_Bit-Reconfigurable*','SDCIM-03':'A_1.041-Mb*',
 'NOR-01':'infineon-s29gl01gs*', 'NAND-01':'3d-nand-flyer.pdf', 'NAND-02':'A_2Tb_4b*',
 'NAND-03':'A_321-Layer*','NAND-04':'System-Technology*','NAND-05':'Optimal_Design*',
 'RRAM-05':'A_28-nm_RRAM*','MRAM-02':'s41928-023-00994-0.pdf','MRAM-03':'A_1-Mb_28*',
 'MRAM-04':'A_28nm_32Kb_embedded*','MRAM-05':'EMxxxLX_B_HR Datasheet v3.7_0.pdf',
 'PCM-03':'A_40-nm_2M-Cell*','PCM-04':'science.aao3212.pdf',
 'FERAM-02':'Low_Voltage*','FERAM-03':'SoC_Compatible*','FERAM-04':'NVDRAM*',
 'GC-02':'An_800-MHz*','GC-04':'A_4-bit_Calibration-Free*','GC-05':'An_Integer-Floating*',
 'FENOR-03':'First_Demonstration*','FENOR-04':'Efficient_Large*','FENOR-06':'Gate_Stack*',
}
log=[]
for sid, pattern in incoming.items():
    s=byid[sid]
    if sid=='MRAM-05':
        s.update(year=2026,publication_date='2026-07-23',short_title='EMxxxLX_B_HR_v3p7',
                 title='EMxxxLX/B/HR — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory',
                 venue='Everspin datasheet, EMxxxLX/B/HR v3.7',document_id='EMxxxLX/B/HR v3.7, July 23, 2026')
        s['target_path']='tasks/task1_table_i/rebuild/literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf'
    target=R/s['target_path']
    matches=list(target.parent.glob(pattern))
    if target.exists() and not matches:continue
    assert len(matches)==1,(sid,matches)
    origin=matches[0]
    assert origin.read_bytes().startswith(b'%PDF-'),origin
    with pdfplumber.open(origin) as p:
        assert len(p.pages)>0
        pages=len(p.pages)
    sha=hashlib.sha256(origin.read_bytes()).hexdigest()
    log.append(dict(source_id=sid,from_path=origin.relative_to(R).as_posix(),to_path=s['target_path'],
                    sha256=sha,pages=pages,identity_basis='Filename plus actual PDF title/authors, DOI where present; visually verify malformed text-layer papers',
                    intake='user_A_B_2026-09-08'))
    assert not target.exists(),target
    origin.rename(target)
extra_origin=B/'literature/06_mram/EMxxLX Product Brief v2.1.pdf'
extra_target=B/'literature/06_mram/MRAM-05_2023_EMxxLX_ProductBrief_v2p1.pdf'
if extra_origin.exists():
    assert not extra_target.exists()
    sha=hashlib.sha256(extra_origin.read_bytes()).hexdigest()
    log.append(dict(source_id='MRAM-05',from_path=extra_origin.relative_to(R).as_posix(),
                    to_path=extra_target.relative_to(R).as_posix(),sha256=sha,pages=2,
                    identity_basis='Product Brief footer 9/2023; user filename v2.1 retained as supplied version',intake='user_extra_product_brief'))
    extra_origin.rename(extra_target)
if log:(B/'metadata/rename_log_r1.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')

texts=B/'tmp/r1_text';texts.mkdir(parents=True,exist_ok=True)
inventory=[]
for s in m['sources']:
    path=R/s['target_path']
    if not path.exists():
        inventory.append(dict(source_id=s['source_id'],missing=True));continue
    pages=[];decoding=[]
    with pdfplumber.open(path) as p:
        for i,page in enumerate(p.pages):
            t=page.extract_text() or ''
            if t.count('(cid:')>30:
                # These two IEEE PDFs lack a ToUnicode map; ASCII glyphs use a +29 offset.
                # This is an aid only. Rendered pages are authoritative, especially symbols.
                t=re.sub(r'\(cid:(\d+)\)',lambda a:chr(int(a[1])+29) if 0<=int(a[1])<=97 else f'[glyph:{a[1]}]',t)
                decoding.append(i+1)
            pages.append(t)
    (texts/(s['source_id']+'.json')).write_text(json.dumps(dict(source_id=s['source_id'],path=s['target_path'],pages=pages,ascii_glyph_decode_pages=decoding),ensure_ascii=False))
    s['main_file']=dict(path=s['target_path'],pages=len(pages),bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    inventory.append(dict(source_id=s['source_id'],missing=False,**s['main_file'],ascii_glyph_decode_pages=decoding))
    if s['source_id'] in incoming:
        s['access_status']='user_fulltext_received';s['access_status_zh']='用户补充主文，身份已核验；全文用途复核中'
        s['intake_path']=next((x['from_path'] for x in log if x['source_id']==s['source_id']),None)
    s['previous_request_batch']=s['request_batch'];s['request_batch']=None
    s['review_status']='pending_fulltext_review'
allfiles=list(B.glob('literature/**/*.pdf'))
hashes=collections.defaultdict(list)
for f in allfiles:hashes[hashlib.sha256(f.read_bytes()).hexdigest()].append(f.relative_to(R).as_posix())
report=dict(date='2026-09-08',initial_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            catalog_main_expected=55,main_received=sum(not x['missing'] for x in inventory),
            missing_main=[x['source_id'] for x in inventory if x['missing']],user_new_pdf_count=len(log),
            all_local_pdf_count=len(allfiles),byte_identical_duplicates=[v for v in hashes.values() if len(v)>1],files=inventory,
            user_git_preference='User removed PDF ignore rule; preserve it; no git add/commit/push.')
(B/'metadata/intake_r1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
m['stage']='R1';m['status']='R1 到件核验与全文筛选进行中'
(B/'source_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))

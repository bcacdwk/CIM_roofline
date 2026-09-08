"""R1 文献归档与人工审阅文档生成；只操作 rebuild，不联网，不计算吞吐。"""
from pathlib import Path
from collections import Counter
import hashlib, json, shutil
import pypdfium2 as pdfium
from review_data_r1 import REVIEWS

B = Path(__file__).resolve().parents[1]
R = B.parents[2]
PREFIX = B.relative_to(R).as_posix()
def dump(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n')
def asset(p):
    p = Path(p)
    if not p.is_absolute(): p = R/p
    data=p.read_bytes()
    assert data.startswith(b'%PDF-'),p
    d=pdfium.PdfDocument(p); n=len(d); d.close()
    return dict(path=p.relative_to(R).as_posix(), pages=n, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
def local(p): return Path(p).relative_to(Path(PREFIX)).as_posix()
def pdf_link(p, label='本地 PDF'): return f'[{label}]({local(p)})'
def sl(sid): return f'[{sid}](LITERATURE_CATALOG.md#{sid})'
def refs(ids): return '、'.join(sl(i) for i in (ids.split() if isinstance(ids,str) else ids))

m=json.loads((B/'source_manifest.json').read_text())
snapshot=B/'history/r1_intake/source_manifest.json'
if not snapshot.exists(): dump(snapshot,m)
ss={s['source_id']:s for s in m['sources']}
movelog=[]
def move(old,new,why):
    src=R/old; dst=R/new
    assert src.is_relative_to(B) and dst.is_relative_to(B)
    if src.exists():
        oldhash=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        assert not dst.exists(),dst
        src.rename(dst)
        assert hashlib.sha256(dst.read_bytes()).hexdigest()==oldhash
        movelog.append(dict(from_path=old,to_path=new,reason=why,sha256=oldhash))
    else: assert dst.exists(),dst
    return new

# 退出有效证据目录的版本／结构对照仍保留原字节与来源关系。
for sid in ['SACIM-03','SDCIM-03']:
    for v in ss[sid]['related_versions']:
        if v.get('file') and '/versions/' not in v['file']['path']:
            old=v['file']['path'];new=str(Path(old).parent/'versions'/Path(old).name)
            v['original_archive_path']=old
            v['file']['path']=move(old,new,'同一论文前作／作者报告，归入版本目录，不另计独立证据')
    if sid=='SACIM-03': ss[sid]['related_versions'][0]['relation']='2023 期刊 p.2 明确扩展本会议稿并新增流片测量；会议仿真与期刊测量不是两个独立芯片。'
    else: ss[sid]['related_versions'][0]['relation']='正式主文已经到件；35 页作者报告保留用于读图和解释，属于同一来源。'

s=ss['FENOR-03']
if '/versions/' not in s['target_path']:
    old=s['target_path'];new=str(Path(old).parent/'versions'/Path(old).name)
    s['original_archive_path']=old;s['target_path']=move(old,new,'FENOR-04 p.2 明确为本会议稿扩展版，同一证据包')
    s['main_file']['path']=new
s['version_of']='FENOR-04';s['independent_evidence']=False;s['package_id']='FENOR-04'
ss['FENOR-04']['package_id']='FENOR-04'
ss['FENOR-04']['related_source_ids']=['FENOR-03']
s=ss['FENOR-05']
if '/comparisons/' not in s['target_path']:
    old=s['target_path'];new=f'{PREFIX}/literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND.pdf'
    s['original_archive_path']=old;s['target_path']=move(old,new,'实际为 FeNAND，退出 FeNOR 核心，保留直接结构对照')
    s['main_file']['path']=new
    for f in s['supplements']:
        old=f['path'];new=f'{PREFIX}/literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND_Supplement.pdf'
        f['original_archive_path']=old;f['path']=move(old,new,'FeNAND 的 SI 随同主文归入对照包')
s['core_eligible']=False
s=ss['MRAM-05']
brief=f'{PREFIX}/literature/06_mram/MRAM-05_2023_EMxxLX_ProductBrief_v2p1.pdf'
new=f'{PREFIX}/literature/06_mram/versions/MRAM-05_2023_EMxxLX_ProductBrief_v2p1.pdf'
if not any(v.get('file',{}).get('path')==new for v in s['related_versions']):
    move(brief,new,'2023 粗略 product brief 已被 v3.7 datasheet 覆盖，退出有效证据计数')
    s['related_versions'].append(dict(title='EMxxLX Product Brief',year=2023,version='v2.1（版本号来自用户原文件名；PDF 页脚 9/2023）',relation='冗余产品简表；仅留用户来件记录，不作为技术证据。',file=asset(new),access_status='archived_redundant',original_archive_path=brief))

def meta_source(sid,group,short,priority,purpose,roles,level,process):
    j=json.loads((B/'metadata'/f'{sid}_crossref.json').read_text())
    d=j.get('published',j.get('issued',{})).get('date-parts',[[None]])[0]
    year=d[0];doi=j['DOI']; title=j['title'][0]
    s=dict(source_id=sid,group=group,title=title,year=year,short_title=short,
           authors=[(a.get('given','')+' '+a.get('family','')).strip() for a in j.get('author',[])],
           venue='; '.join(j.get('container-title',[])),publication_dates={k:j[k] for k in ['published','published-online','published-print'] if k in j},
           doi=doi,doi_url='https://doi.org/'+doi,official_url='https://doi.org/'+doi,
           metadata_file=f'{PREFIX}/metadata/{sid}_crossref.json',identity_verified=True,
           identity_basis='出版登记 Crossref 与出版社／作者机构页面；有 PDF 时核对实际题名、作者与正文。',
           verified_on='2026-09-08',roles=roles,evidence_level=level,process_class=process,
           priority=priority,purpose=purpose,package_id=sid,target_path=f'{PREFIX}/literature/{group}/{sid}_{year}_{short}.pdf',
           main_file=None,copy_provenance=None,related_versions=[],supplements=[],shared_with=[],access_urls=[],
           request_batch='C',discovered_in='R1_C_search',review_status='awaiting_main_fulltext',
           version='拟获取正式主文或内容完整的合法作者稿',access_status='manual_needed',
           access_status_zh='身份已核验；主文未到，尚不能确认完整时序',fulltext_suitability='出版社／作者摘要预判，待主文复核',
           confirmed_content='身份与摘要已核验；预期用途尚未由主文确认。',
           supplement_status='请主文与出版社列出的技术 SI 一并获取；已归档的 SI 无需重复。')
    ss[sid]=s
    return s

if 'CMOS-07' not in ss:
    s=meta_source('CMOS-07','00_cmos_periphery','LowPower_DualPort_SRAM','P1','补共同 SRAM 普通读写服务与 WL/SA/mux 的局部边界。',['28 nm 外围服务','读写周期与端口条件'],'局部 SRAM macro／外围实测','直接 28 nm eFlash CMOS 平台证据；特殊高阈值条件保留')
    old=s['target_path'];new=old.replace('.pdf','_AuthorRevision.pdf');move(old,new,'明确标注公开作者修订稿版本')
    s['target_path']=new;s['main_file']=asset(new);s['request_batch']=None
    s['access_status']='downloaded_in_r1_before_stop';s['access_urls']=['https://www-vlsi.es.kit.ac.jp/thesis/papers/pdfs/JSSC-22-0279.R2.pdf']
    s['version']='作者机构公开 R2 修订稿；无正式出版页码／接受日期；与 2023 JSSC 记录建立关系'
    s['identity_note']='实际作者稿题名为 Dualport，正式登记 Dual-Port；作者五人一致。年份采用 JSSC 58(7), 2098–2108 (2023)，不采用稿内占位日期。'
    s['shared_with']=['01_sram_acim','02_sram_dcim'];s['independence_note']='与 CMOS-04 部分作者重叠；新的工艺/宏验证，非完全独立团队。'

if 'SACIM-05' not in ss:
    s=meta_source('SACIM-05','01_sram_acim','GlobalBitlineCombining_8bit','P1','SACIM-03 实测只覆盖 4-bit；补独立结构的 28 nm 8-bit 输入/权重、ADC 共享与完整输出服务。',['28 nm 外围服务','完整精度求值','ADC 共享'],'局部 macro（流片属性由官方摘要确认）','直接 28 nm 候选，具体服务待正文')
    s['publication_date']='2023-11-09';s['publication_note']='IEEE 页面首次发表 2023-11-09；期刊卷期为 2024-04，文件名使用卷期年。'
    s['access_urls']=['https://ieeexplore.ieee.org/document/10314139/']
    s['manual_request_contents']='主文 5 页（2304–2308）；若页面另列技术附件，一并保存。'
    s['gap_from_review']='SACIM-03 pp.2–4 和 CMOS-05 p.4：实际 CIM 输入负载与完整多位服务比通用 RF DAC headline 更相关。'
    s['independence_note']='NTHU/ITRI 系列，与 SRAM-DCIM、PCM 部分候选团队有关；收到全文后核对其与已有 384-kb 前作的版本关系，不重复请求前作。'
if 'RRAM-06' not in ss:
    s=meta_source('RRAM-06','05_rram','AutoForming_AutoWrite','P1','补完整 page RESET/SET 与 hidden-RESET 的步骤及代价，核查并行写粒度。',['完整写入周期','局部并行','RESET/SET 控制'],'实际存储 macro（官方摘要确认）','40 nm 专用外围；其他工艺交叉参考')
    s['access_urls']=['https://research.tsmc.com/page/rram/1.html','https://ieeexplore.ieee.org/document/8776540/']
    s['manual_request_contents']='VLSI 2019 主文 T232–T233（2 页）；勿只保存会议摘要。'
    s['gap_from_review']='RRAM-02 p.5 主要给脉冲数改善，RRAM-05 p.7 只有读侧完整时序；普通产品 RRAM-04 的封装写周期不能补局部 page 操作。'
    s['retention_reason']='保留 2019 资料是因为官方摘要明确讨论完整 page SET/RESET 与隐藏擦除，而非仅器件脉冲。'
    s['independence_note']='产业/NTHU 同技术生态，作步骤补充；99% 改善不能先写成绝对周期，也不能遗漏被移入 standby 的 RESET。'
if 'PCM-06' not in ss:
    s=meta_source('PCM-06','07_pcm','RowWise_ClosedLoopProgramming','P1','顺着 PCM-02 Methods 的 ref.4 补 512 权重并行闭环编程电路、迭代终点与外围调度。',['写入闭环','并行粒度','编程控制与读验'],'局部 tile／实际芯片（官方摘要确认）','14 nm PCM 专用外围，非共同 28 nm')
    s['access_urls']=['https://research.ibm.com/publications/fully-on-chip-mac-at-14-nm-enabled-by-accurate-row-wise-programming-of-pcm-based-weights-and-parallel-vector-transport-in-duration-format','https://ieeexplore.ieee.org/document/9566604/']
    s['manual_request_contents']='TED 68(12), 6629–6636（8 页）期刊主文；不再另取同题 VLSI 2021 会议版。'
    s['gap_from_review']='PCM-02 pp.9–10 的 row-wise closed-loop programming 转引该文，实际是明确的正文追溯缺口。'
    s['independence_note']='与 PCM-02 同一 IBM 技术线，提供方法细节，不新增独立工艺交叉证据。'
if 'MRAM-06' not in ss:
    s=meta_source('MRAM-06','06_mram','LosslessParallelSpintronicCIM','P1','补 bitcell 内乘法/数字化的 STT-MRAM CIM，以区别 Jung 模拟电阻求和和 Chiu near-memory 数字路径。',['CIM 求值桥接','互补权重写入步骤','独立团队核查'],'局部 64-kb macro（摘要）及实有补充材料','40 nm STT-MRAM；其他工艺条件保留')
    s['publication_date']='2025-10-16';s['access_urls']=['https://www.nature.com/articles/s41928-025-01479-y']
    s['manual_request_contents']='主文 1046–1058 及随正文附带的 Extended Data；15 页 Supplementary Information 已有，不用重复下载。'
    s['gap_from_review']='MRAM-02 p.2 正文实际是 near-memory；新文官方摘要明确 bitcell 内数字乘法，已取得 SI Fig.2 也显示两阶段写互补 MTJ。'
    s['confirmed_content']='主文未到。官方摘要确认 40 nm、数字 bitcell 乘法；本地 SI p.4 Fig.2 已确认先两 MTJ 写 0 再目标写 1 的流程，绝对完整周期待主文。'
    s['review_status']='supplement_reviewed_main_pending';s['fulltext_suitability']='已审 SI p.4 Fig.2 及 Note 1；主文仍须核查完整服务和测试条件。'
    s['independence_note']='Li/Chai 等团队不同于 Jung/Samsung 和 Chiu/TSMC，提供机制互补，不能将其 headline 与前两者平均。'

# 更新正文复核后的事实，清除 R0 “尚未访问主文”的陈旧状态。
for sid,review in REVIEWS.items():
    s=ss[sid];s['review']=review;s['review_status']='fulltext_suitability_reviewed'
    s['fulltext_suitability']='已完成 R1 正文适用性筛选；不是完整参数分析'
    s['confirmed_content']=review['findings'];s['limitations']=review['limits']
    s['priority']='P1' if review['decision']=='核心' else ('P3' if review['decision'] in ['版本归并','结构对照'] else 'P2')
    s['access_status_zh']='本地主文已核验，正文用途已复核'
    s['request_batch']=None;s['core_eligible']=review['decision']=='核心'
    s['purpose']=review['findings']
    if s.get('previous_request_batch') or s.get('intake_path'):
        s['version']='用户补充正式主文；已核对题名、页数与出版身份'
        s['identity_note']='R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。'
    s['manual_request_reason']=None;s['manual_request_contents']=None
    s['supplement_status']='R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。'
    if s.get('supplements'): s['supplement_status']='已归档技术 Supplementary Information；见附件链接。'

ss['CMOS-05']['evidence_level']='外围电路（实测 DAC，非 CIM 负载）'
ss['SACIM-03']['evidence_level']='28 nm 实测局部 macro；2022 会议前作仿真'
ss['SACIM-03']['process_class']='直接的 28 nm 实测证据（期刊扩展版）'
ss['NAND-02']['affiliations']=['Sandisk','KIOXIA'];ss['NAND-02']['state_mode']='QLC 4b/c，6-plane；另含 SLC burst 操作模式，分别使用'
ss['NAND-05']['state_mode']='实际 16-layer 64 Gb SLC SGVC 器件，multi-bit 用 SLC 复制/选择编码'
ss['RRAM-05']['state_mode']='binary HRS/LRS；2T1R 晶体管尺寸与多 subarray 的空间权重映射'
ss['MRAM-02']['state_mode']='22 nm STT-MRAM；sense 后 near-memory 数字计算；PUF 与数据模式分开'
ss['MRAM-02']['evidence_level']='存储 array／近存数字计算 macro；不是模拟 crossbar 累加'
ss['GC-05']['state_mode']='16 nm 4T gain-cell 存储 + 7T stationary unit；数字 INT/FP，分模式'
ss['FENOR-04']['state_mode']='ZnO/MFMIS 3D FeNOR；小阵列测量 + 大阵列网络模拟'
ss['PCM-03']['title_registered']=ss['PCM-03']['title'];ss['PCM-03']['title']=ss['PCM-03']['title'].replace('Tiny-Al','Tiny-AI')
s=ss['MRAM-05'];s['version']='用户提供 v3.7（2026-07-23），替代 V1 请求的 v3.4'
s['identity_note']='修订史 pp.81–82 确认 v3.7 日期；部分内页沿用 ©2025 页脚，以版本史为准。不得将 v3.4 下载入口当作 v3.7 身份证据。'
s['official_url']='https://www.everspin.com/design-support';s['access_urls']=[]
s['superseded_request']=dict(version='v3.4 (2025)',url='https://www.everspin.com/file/158451/download',status='由用户 v3.7 替代，无需补旧版')

for sid,fn,url in [
 ('MRAM-02','MRAM-02_2023_SecureSpintronicCIM_Supplement.pdf','https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41928-023-00994-0/MediaObjects/41928_2023_994_MOESM1_ESM.pdf'),
 ('MRAM-06','MRAM-06_2025_LosslessParallelSpintronicCIM_Supplement.pdf','https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41928-025-01479-y/MediaObjects/41928_2025_1479_MOESM1_ESM.pdf')]:
    s=ss[sid];p=f'{PREFIX}/literature/06_mram/{fn}'
    if not any(f['path']==p for f in s['supplements']):
        a=asset(p);a.update(url=url,obtained_in='R1_before_user_stop_download',validation='PDF signature、页数、实际题名／DOI 与相关 SI 正文');s['supplements'].append(a)
    s['supplement_status']='SI 已补齐并核验；无需用户重复下载。'
for sid in ['RRAM-01','PCM-02']:
    ss[sid]['supplement_status']='2026-09-08 官方出版页未列独立技术 SI PDF；本地包含 Methods/Extended Data，V2 不请求不存在于页面的通用附件。'
for sid in ['MRAM-01','PCM-01']:
    ss[sid]['supplement_status']='官方页面附件为演示视频，未列另一份技术 SI PDF；关键 Methods/Extended Data 已有。视频不影响本轮用途判断，不请求。'
ss['PCM-04']['supplement_status']='缺 Materials and Methods、Figs.S1–S11；已列 V2，主文不用重复。'

introductions={
 '00_cmos_periphery':'共同外围分别由实测 SAR、CIM 内输入/读出路径、SRAM 局部服务与数字宏支持。通用 DAC 产品简表和 RF DAC 只作补充；CMOS-07 新增实际 28 nm SRAM 服务，但其 eFlash 工艺条件须保留。',
 '04_nand_3d':'现有正文已覆盖 Micron MLC/TLC、两家新 QLC 芯片以及实际 SLC SGVC 器件。SLC 专用完整 program/erase 服务和 plane 命令约束仍有缺口；不是完全没有 SLC 证据。模型/RC 结果与制造商实测明确分开。',
 '06_mram':'Jung 的电阻求和与 Chiu 的 near-memory 数字引擎是不同机制，不能拼为一个实现。存储 macro 补读写步骤，新增 MRAM-06 用于核查 bitcell 内数字计算；互补 MTJ、PUF 与普通数据路径分别记录。',
 '08_feram_hfo2':'SK hynix、Sony 与 Micron 正文确认 HfO₂ 系 1T1C 阵列及读后恢复；Micron NVDRAM 并非仅有 LPDDR5 总线数据。C2FeRAM 给非破坏读桥接但大阵列为模型；混合 FeCAP/memristor 只保留 FeCAP 本身的证据。',
 '09_gain_cell_edram':'现有全文形成 2T1C 模拟、4T 普通存储、3T1C 多级电流写入与 4T+stationary 数字 CIM 的互补来源。保持分布、刷新占用、粗写/精写以及 storage 更新与计算权重更新的区别必须保留。',
 '10_fenor_3d':'Zhou 2025 NOR-type 与 2026 AND-type 原文件均已核验，根目录不动。Feng 会议/期刊合为一个证据包；POSTECH FeNAND 退出 FeNOR 核心并移入 comparisons，仅作为直接拓扑对照。'
}
for g in m['groups']:
    if g['directory'] in introductions:g['introduction']=introductions[g['directory']]
    if g['directory'] in ['01_sram_acim','02_sram_dcim'] and 'CMOS-07' not in g['shared_sources']:g['shared_sources'].append('CMOS-07')
    if g['directory']=='00_cmos_periphery':g['shared_sources']=['SACIM-03','SDCIM-01','SDCIM-03','SACIM-05']

m['sources']=sorted(ss.values(),key=lambda s:(s['group'],s['source_id']))
m['schema_version']='1.1-r1';m['stage']='R1';m['status']='R1 全文适用性筛选完成；V2 下载清单已覆盖原路径，等待用户补充'
m['scope']='到件、重命名、正文用途筛选、版本归并与 C 轮定向检索；未开始正式参数分析、最终范围或 Table I。'
m['download_policy']='用户 2026-09-08 最新指令：全文下载全部由用户负责；代理不再下载。此前已取得的 1 份主文和 2 份 SI 保留，不重复请求。'
m['baseline_r1']=dict(head='5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c',initial_tracked_changes=['.DS_Store','tasks/.DS_Store'],git_mutations_performed=False,allowed_write_root=PREFIX)
decisions=Counter(r['decision'] for r in REVIEWS.values())
m['counts_r0']=m.get('counts_r0',m['counts'])
m['counts']=dict(candidate_records=len(ss),source_packages=len({s['package_id'] for s in ss.values()}),
                r0_main_local=26,user_received_main=29,user_received_extra=1,r0_requested_main_complete=55,
                r0_missing_main=0,local_main=sum(bool(s['main_file']) for s in ss.values()),
                r1_auto_main_before_stop=1,r1_auto_supplements_before_stop=2,local_pdf_count=len(list((B/'literature').rglob('*.pdf'))),
                new_c_candidates=5,c_manual_main=4,c_manual_supplement_packages=1,v2_manual_packages=5,
                fulltext_reviewed=len(REVIEWS),decisions=dict(decisions),wholly_irrelevant_main_removed=0,redundant_extra_archived=1)
m['download_requests_version']=2
m['download_requests_file']=f'{PREFIX}/DOWNLOAD_REQUESTS_V1.md'
m['pending_downloads']=[dict(request_id=sid,source_id=sid,kind='main',batch='C',priority='P1',status='user_download_required',
                             target_path=ss[sid]['target_path'],doi=ss[sid]['doi'],official_urls=ss[sid]['access_urls'],
                             contents=ss[sid]['manual_request_contents'],reason=ss[sid]['gap_from_review'])
                        for sid in ['PCM-06','RRAM-06','SACIM-05','MRAM-06']]
m['pending_downloads'].append(dict(request_id='PCM-04-SI',source_id='PCM-04',kind='supplement',batch='C',priority='P2',
    status='user_download_required',target_path=f'{PREFIX}/literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf',
    doi=ss['PCM-04']['doi'],official_urls=['https://www.science.org/doi/10.1126/science.aao3212','https://www.science.org/doi/suppl/10.1126/science.aao3212'],
    contents='Materials and Methods、Figs.S1–S11、References 42–52；只要 SI，不重复主文',reason='主文 p.4 将方法与 RESET 补充图列在 SI，需核实脉冲/装置与写入终点。'))
dump(B/'source_manifest.json',m)
dump(B/'metadata/fulltext_reviews_r1.json',REVIEWS)
if movelog:dump(B/'metadata/organization_log_r1.json',movelog)

# 目录：每条来源给出当前判断与准确的点击入口。
cat=['# 文献目录（R1 正文复核版）','',
     '更新：2026-09-08。A/B 主文 **55/55 到齐**；现登记 60 条来源（59 个去重资料包），其中 56 条本地主文可读。',
     '已对 56 条本地主文完成面向估算用途的正文筛选；新 C 候选中 4 篇仍待主文。证据确认只涉及下列用途，并不代表已经完成参数换算。',
     '', '[下载清单 V2（沿用 V1 文件路径）](DOWNLOAD_REQUESTS_V1.md) · [逐篇正文判断](FULLTEXT_REVIEW_R1.md) · [到件与重命名](INTAKE_AUDIT_R1.md) · [覆盖矩阵](COVERAGE.md)','',
     '优先级：P1 核心／关键缺口；P2 条件补充；P3 版本或结构对照。核心并非按性能高低选取，simulation 只在明确条件下提供方法依据。','']
for g in m['groups']:
    cat += ['## '+g['title'],'',g['introduction'],'']
    if g['shared_sources']:cat+=['共享：'+refs(g['shared_sources'])+'。不复制主文件，也不重复计数。','']
    for s in [x for x in m['sources'] if x['group']==g['directory']]:
        sid=s['source_id'];rv=s.get('review');d=rv['decision'] if rv else 'C 候选，主文待审'
        cat += [f'<a id="{sid}"></a>',f'### {sid} — {s["title"]}','',
                f'- 身份：{s["year"] or "未署日期"}；{s["venue"]}；'+('、'.join(s['authors'][:3])+(' 等' if len(s['authors'])>3 else ''))+'。',
                '- 链接：'+(f'[DOI](https://doi.org/{s["doi"]}) · ' if s.get('doi') else '')+f'[官方页面]({s["official_url"]})。',
                f'- 判断：**{d} / {s["priority"]}**；层级：{s["evidence_level"]}。',
                '- 用途标签：'+'；'.join(s['roles'])+'。',
                '- 工艺／状态：'+(s.get('process_class') or '介质专用器件／阵列条件，不自行认定 28 nm')+'；'+(s.get('state_mode') or '精度／模式按正文限定')+'。',
                '- 已确认／预判：'+s['confirmed_content'],
                '- 限制：'+(rv['limits'] if rv else '主文尚未到件；摘要和 SI 不替代完整时序、负载与操作条件审阅。'),
                '- 状态：'+s['access_status_zh']+'；'+(pdf_link(s['target_path']) if s['main_file'] else '拟下载主文')+'。',
                f'- 保存路径：`{s["target_path"]}`。']
        if rv:cat+=['- 正文定位：'+rv['anchors']+'（本地 PDF 页序）。']
        if s.get('publication_note'):cat+=['- 年份/日期：'+s['publication_note']]
        if s.get('identity_note'):cat+=['- 版本核验：'+s['identity_note']]
        if s.get('copy_provenance'):cat+=['- 复制关系：`'+str(s['copy_provenance'])+'`。']
        if s.get('original_archive_path'):cat+=['- 本轮原归档路径：`'+s['original_archive_path']+'`（已按上述路径整理）。']
        for f in s['supplements']:cat+=['- 附件：'+pdf_link(f['path'],'Supplementary Information')+f'（{f["pages"]} 页）。']
        for v in s['related_versions']:
            if v.get('file'):cat+=['- 相关版本：'+pdf_link(v['file']['path'],v['title'])+'；'+v.get('relation','')]
        cat+=['- 附件情况：'+s['supplement_status']]
        if s.get('independence_note'):cat+=['- 独立性：'+s['independence_note']]
        cat+=['']
(B/'LITERATURE_CATALOG.md').write_text('\n'.join(cat)+'\n')

review=['# R1 正文适用性审阅','',
        '2026-09-08。本轮依据实际正文、Methods、关键时序图及比较表判断用途，不只依据题名和摘要。以下页码均从本地 PDF 第 1 页起算（含封面）；不是对每篇进行逐式审稿，也未生成最终参数表。',
        '', '**原 55 条主文：38 核心、13 补充、2 条件保留、1 版本归并、1 结构对照。没有整篇完全无关的主文，因此主文删除 0 份。** 另有一份旧 Everspin 简表被更新 datasheet 覆盖，已退出有效证据、移入 versions。C 轮公开取得 CMOS-07 后，本地审阅总数为 56、核心 39。',
        '', '## 最影响后续工作的变化','',
        '- SACIM-03 的 2023 期刊增加实际流片测量，提升为共同 28 nm 输入／求值核心；旧会议稿只保留版本关系。',
        '- CMOS-04 的 shmoo 横轴是 clock skew；CMOS-05 的 RF DAC 负载不同于 CIM，均降为补充。新增 CMOS-07 有实际 28 nm SRAM 服务，但 eFlash 工艺条件须保留。',
        '- RRAM-05 的实测完整读与优化估计不同；RRAM-04 的慢内部提交周期是真实产品事实，不因数值慢就删除。',
        '- MRAM-02 实际为 near-memory 数字引擎；新 MRAM-06 是另一种 bitcell 数字路径，不能混算。',
        '- FeRAM 三个实际阵列均需检查读后恢复；NVDRAM 的短 tWR 伴随 precharge 写回，不能遗漏这一步。',
        '- GC-04 粗写不是完整多级写；GC-05 storage 更新与 stationary 计算权重更新是不同动作。',
        '- FENOR-03/04 正文确认会议/期刊关系；FENOR-05 是 FeNAND，仅保留拓扑对照。Zhou 2026 的 AND 结构以及器件测量/大阵列仿真分别记录。',
        '', '## 逐篇判断','']
for g in m['groups']:
    review+=['### '+g['title'],'']
    for s in [x for x in m['sources'] if x['group']==g['directory'] and x['source_id'] in REVIEWS]:
        sid=s['source_id'];v=REVIEWS[sid]
        review += [f'**{sl(sid)} — {v["decision"]}** · '+pdf_link(s['target_path']),
                   '', '**正文定位：** '+v['anchors']+'。',
                   '', '**保留用途：** '+v['findings'],
                   '', '**不能据此声称：** '+v['limits'],
                   '', '**本轮处理：** '+v['change_from_r0'],'']
review+=['## C 轮仍需主文的来源','',
         'SACIM-05、RRAM-06、PCM-06、MRAM-06 的出版身份已核验，适用性仍待主文。MRAM-06 已有 SI，正文定位仅限 SI；不把它标为完成主文审阅。PCM-04 只缺方法与补充图。详见 [V2 下载清单](DOWNLOAD_REQUESTS_V1.md)。','']
(B/'FULLTEXT_REVIEW_R1.md').write_text('\n'.join(review))

# V2 覆盖用户指定的 V1 路径；不制造两个不同的待办入口。
dl=['# 人工下载清单 V2（C 轮）','',
    '更新：2026-09-08。**本文件按用户要求覆盖 `DOWNLOAD_REQUESTS_V1.md`；内容版本为 V2，路径不变。** [V1 原始快照](history/r0/DOWNLOAD_REQUESTS_V1.md)只供历史核对，不再执行其中 A/B 任务。',
    '', 'A/B 主文 **55/55 已到齐，缺主文 0 份**；用户本轮补充 29 份主文和 1 份产品简表。Everspin v3.7 已替代原请求 v3.4，不用找旧版。',
    '目前本地共 **64 份 PDF**：56 份主文记录（含归并的会议版）、5 份 SI、3 份相关版本/简表。代理在收到停止下载指令前额外取得 1 份主文与 2 份 SI；以下均已排除这些文件。**今后下载全部由用户负责，代理不再下载。**',
    '', '**本次仅需 5 个资料包：4 篇主文 + 1 份已有论文的补充材料。** 路径均相对仓库根目录；照给定文件名存放即可，不必再次下载 A/B。优先取得前 3 包，其余 2 包同批可一起补齐。',
    '', '## 优先下载','']
order=['PCM-06','RRAM-06','SACIM-05','MRAM-06']
for sid in order:
    s=ss[sid]
    dl += [f'- [ ] **{sid} — {s["title"]}**；{s["year"]}；{s["venue"]}',
           f'  - DOI：[https://doi.org/{s["doi"]}](https://doi.org/{s["doi"]})。',
           '  - 官方／备用合法入口：'+'；'.join(f'[入口 {i+1}]({u})' for i,u in enumerate(s['access_urls']))+'。',
           f'  - 建议保存路径：`{s["target_path"]}`',
           '  - 为何需要：'+s['gap_from_review'],
           '  - 下载内容：'+s['manual_request_contents'],
           '  - 当前情况：'+s['confirmed_content']+' 官方主文直接访问未取得 PDF，需要用户权限／手动访问。',
           '  - 避免重复／误用：'+s.get('independence_note','')]
    if s.get('publication_note'):dl+=['  - 年份说明：'+s['publication_note']]
    dl+=['']
s=ss['PCM-04'];supp=f'{PREFIX}/literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf'
dl += [f'- [ ] **PCM-04-SI — {s["title"]}：Supplementary Materials**；2017；Science',
       f'  - DOI：[https://doi.org/{s["doi"]}](https://doi.org/{s["doi"]})。',
       '  - 官方入口：[Science 论文页](https://www.science.org/doi/10.1126/science.aao3212) → Supplementary Materials；[原文列出的 DC1 入口](https://www.science.org/doi/suppl/10.1126/science.aao3212)。',
       f'  - 建议保存路径：`{supp}`',
       '  - 为何需要：主文 p.4 将 Materials and Methods 放在附件，RESET 的 Fig.S6、脉冲/器件/测量终点条件不能从 headline 判断。',
       '  - 下载内容：**只取补充材料**，应含 Materials and Methods、Figs.S1–S11、References 42–52。主文已经有，不重复。',
       '  - 当前情况：主文 5 页完整；Science 访问返回限制页，未得到 SI。亚纳秒结果暂仅作材料条件对照，未用作完整阵列写时间。','',
       '## 已补齐，不需要下载','',
       '- '+sl('CMOS-07')+'：11 页公开作者修订稿已在本地，补普通 28 nm SRAM 服务；不再请求内容相同的正式版。',
       '- '+sl('MRAM-02')+'：13 页 SI 已补齐，并已核查感测与 PUF/普通写回的区别。',
       '- '+sl('MRAM-06')+'：15 页 SI 已归档；本次只补主文。',
       '- NeuRRAM、Jung MRAM、IBM 两篇 PCM 主文的 Methods/Extended Data 已有。核查出版页后，未发现还需另取的技术 SI PDF；演示视频不作为缺件请求。','',
       '## 暂不扩充的真实缺口','',
       '- **3D NAND SLC 完整 program/erase 与 plane 命令约束**：已有 SLC 器件（NAND-05）及 SLC burst（NAND-02），但没有核实到一份公开完整、明确属于目标 3D SLC 产品的部件 datasheet。保留缺口，不让用户猜产品，也不混入普通 2D SLC 资料。',
       '- **通用 28 nm SRAM compiler 全时序库**：未取得官方公开完整库；CMOS-03、CMOS-07 与实际 CIM macro 可支持明确假设的参考服务。未把第三方转载的商业 databook 列为请求。',
       '- **阵列尺寸、精度、ADC 共享及介质状态模式**：这些是后续参考情景的选择，不能单靠继续增加论文解决。本轮不先固定数值。',
       '', 'C 轮没有为了各类平均凑数再发一长串候补。检索去留记录见 [C_SEARCH_LOG.md](C_SEARCH_LOG.md)，现有全文处理见 [FULLTEXT_REVIEW_R1.md](FULLTEXT_REVIEW_R1.md)。','']
(B/'DOWNLOAD_REQUESTS_V1.md').write_text('\n'.join(dl))

audit=['# A/B 到件、身份与重命名核验（R1）','',
       '2026-09-08。原清单 55 条主文记录全部齐全；原 18 个 A 包、10 个 B 包及 FENOR-03 关联会议稿都已核对。没有缺主文、登录 HTML 假 PDF 或相同字节的重复文件。',
       '', '## 来件与版本','',
       '- R0 本地主文 26；本轮用户新增主文 29、额外简表 1。30 个来件均按稳定 ID 重命名。',
       '- Everspin 来件为 v3.7，修订史日期 2026-07-23；比原请求 v3.4 更新，已接受替代并修正年份/路径。',
       '- FERAM-04、FENOR-03 的文字层存在字体编码问题，已渲染确认内容正常。仅在忽略的 tmp 中作文字解码辅助；PDF 原字节未修改，不需重下。',
       '- 55 条旧主文的题名、正文与角色已核对；新补 CMOS-07 作者稿也已复核。所有 PDF 签名、页数、哈希与可打开性以 metadata 核验记录为准。',
       '- 目前唯一明确缺失的已有论文技术附件是 PCM-04-SI；新增 MRAM-06 已有 SI，仍缺主文。',
       '', '## 整理及剔除','',
       '整篇无关主文删除 **0**。剔除的是不适合承担的证据角色：FENOR-05 退出 FeNOR 核心；FENOR-03 与 FENOR-04 归并；旧 Everspin brief 退出有效证据。原文件字节保留在 comparisons/versions，便于回溯，不算重复核心来源。',
       '', '30 个来件的原名→新名及 SHA-256 见 [rename_log_r1.json](metadata/rename_log_r1.json)。后续版本/对照目录整理见 [organization_log_r1.json](metadata/organization_log_r1.json)。原 R0 目录和清单见 history/r0，根目录 Zhou 两篇与此前任务材料均未移动或覆盖。',
       '', '## 主文逐项到件表','', '| ID | 来源 | 当前文件 | 页数 | SHA-256 前 12 位 | 正文判断 |','|---|---|---|---:|---|---|']
for s in m['sources']:
    if not s['main_file']:continue
    f=s['main_file'];origin='用户 A/B' if s.get('intake_path') else ('C 轮停止指令前取得' if s['source_id']=='CMOS-07' else 'R0 已有')
    audit += [f'| {sl(s["source_id"])} | {origin} | {pdf_link(f["path"],Path(f["path"]).name)} | {f["pages"]} | `{f["sha256"][:12]}` | {s["review"]["decision"]} |']
audit+=['','HEAD：`5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c`。开始时已有 `.DS_Store`、`tasks/.DS_Store` 修改，未清理。未执行 Git 暂存/提交/推送/回退；用户开放 PDF 的本任务 `.gitignore` 设置保留。','']
(B/'INTAKE_AUDIT_R1.md').write_text('\n'.join(audit))
print(json.dumps(m['counts'],ensure_ascii=False))

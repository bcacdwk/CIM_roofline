"""一次性本地迁移记录：构建独立文献语料；归档旧任务；无网络/Git 写操作。"""
from pathlib import Path
from collections import Counter
import json,hashlib,shutil,re,subprocess
import pypdfium2 as pdfium

R=Path(__file__).resolve().parents[2]
OLD=R/'tasks/task1_table_i'
B=OLD/'rebuild'
NEW=R/'tasks/task1_table_I_NVM'
ARC=R/'tasks/archived'
LEGACY=ARC/'task1_table_i'
assert OLD.exists() and not NEW.exists() and not LEGACY.exists()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def info(p):
    blob=p.read_bytes();assert blob.startswith(b'%PDF-'),p
    d=pdfium.PdfDocument(p);n=len(d);d.close()
    return dict(pages=n,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())

oldm=json.loads((B/'source_manifest.json').read_text())
ss={s['source_id']:s for s in oldm['sources']}
log=dict(date='2026-09-08',head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
         authorization='用户明确要求新建独立任务目录、归档旧任务、删除不需要的文献和 tmp；不提交 Git。',
         original_root=str(OLD.relative_to(R)),new_root=str(NEW.relative_to(R)),archive_root=str(LEGACY.relative_to(R)),
         moved_files=[],deleted_literature=[],removed_temporary_directories=[],removed_cache_files=[])

# 两份刚收到的正式全文：题名/DOI/正文与图表已经人工核验。
for sid in ['SDCIM-04','SDCIM-05']:
    j=json.loads((B/'tmp/final_intake'/f'{sid}.json').read_text());p=R/j['path']
    ss[sid]['main_file']=dict(path=j['path'],**info(p))
    ss[sid]['target_path']=j['path']
ss['SDCIM-04']['review']=dict(decision='补充',
    anchors='pp.1–3，II-A/III-A、Figs.1–6；p.4，Figs.7/10、Table I',
    findings='28 nm 16-kb compact-6T 数字 MAC：128×128-bit SRAM 分为一个 signed-weight bank 与七个 unsigned-weight banks，128×2-bit 输入 buffer；8-bit 输入分四拍完成 signed INT8 MAC。ALC=0 是完整精度，其余配置控制近似加法器。memory 与 compute 模式分开。',
    limits='Fig.7 分列完整精度 6.4 ns 与近似 5.6 ns；不能把 5.6 ns 记为无损模式。摘要/正文及 Fig.10 内使用 fabricated/measured，但 IV-C 标题和 Fig.10 图注又标 simulation：性能来源标签不一致，保留作者报告，不能作为无歧义的独立硅测定值。普通写入绝对周期未给出。')
ss['SDCIM-04']['evidence_level']='局部 DCIM 电路研究；作者报告芯片/测试，性能图仿真与实测标签混用'
ss['SDCIM-04']['process_class']='28 nm 设计/作者报告；无歧义证据为结构、模式和四拍展开'
ss['SDCIM-04']['publication_date']='2024-07-03'
ss['SDCIM-04']['state_mode']='signed INT8，2-bit 输入/拍；完整/近似 adder 分模式'
ss['SDCIM-05']['review']=dict(decision='核心',
    anchors='pp.3–5，III、Figs.4–7；pp.9–11，VI、Figs.19–23、Table III',
    findings='实际 28 nm 数字 transpose SRAM；上下两组 cyclic-weight-mapping SRAM 与 bit-parallel MAC，共用 FF/BP 数据通路。普通读写为 32-bit 端口，计算时提供 256-bit 驻留向量；INT4/FP8 一 MAC 拍，INT8/BF16 将输入分段用两 MAC 拍。有 die photo、测试平台与按模式区分的结果。',
    limits='Fig.6 省略 write 电路，32-bit 端口不直接给完整写周期。正文多处写 32 kB，但 Table III 写 32 Kb，后者与图示两组 64×64 个 4-bit cell 的局部结构一致；边界/容量换算须显式说明此差异。p.10 文字与 Table III 对 FP8 的 2.5/2.7 ns 精确/近似归属相反，不拼接模式指标。AHB/APB 外部服务与本地 MAC 分开。')
ss['SDCIM-05']['evidence_level']='28 nm 实测局部数字 SRAM macro；部分容量/模式标注有内部差异'
ss['SDCIM-05']['process_class']='直接 28 nm 实测证据；配置/单位须服从明确的局部结构'
ss['SDCIM-05']['publication_date']='2026-04-07'
ss['SDCIM-05']['state_mode']='INT4/8、FP8、BF16；FF/BP；accurate/approximate 分模式'

# 删除无必要的源，而不是搬进新目录的 versions/候补区。
drop={
 'CMOS-01':'粗略 DAC IP 简表没有 CIM 负载建立条件；输入服务已有 SACIM-03/05 的实际 macro，增量依据不足。',
 'CMOS-04':'主要是双端口 disturb 筛选；普通 SRAM 局部服务由 CMOS-03/07 保留，当前估算不需要再维护这一独立来源。',
 'CMOS-05':'RF 交织 DAC/100-ohm 负载与目标 CIM 输入服务关系弱；由实际 CIM 内驱动依据替代。',
 'CMOS-06':'高速 SAR 仿真交叉候选；已有实测 ADC 与实际 CIM 读出，不需要再维护其未流片速度作为参考端点。',
 'MRAM-02':'安全/PUF 与 near-memory 数字引擎为主；MRAM-01/06 覆盖 CIM，MRAM-03/04/05 覆盖普通读写，保留价值不足以抵消机制混淆。',
 'FENOR-03':'同一工作期刊 FENOR-04 已完整保留；会议版不另作独立证据。',
 'FENOR-05':'实际是串联 FeNAND，当前 FeNOR/AND/vertical 参考结构已有直接来源，不继续保留弱拓扑对照。'
}
deletions=[]
for sid,s in ss.items():
    if sid in drop:
        deletions.append((s['main_file']['path'],sid,drop[sid]))
        deletions.extend((f['path'],sid,drop[sid]+' 删除对应 SI。') for f in s['supplements'])
    for v in s['related_versions']:
        if v.get('file'):
            deletions.append((v['file']['path'],sid,'同内容前作/作者 slides 或被完整 datasheet 覆盖的产品简表，不再保留文件。'))
assert len(deletions)==12
deleted_hashes={}
for path,sid,why in deletions:
    p=R/path;assert p.is_relative_to(OLD) and p.exists()
    a=info(p);deleted_hashes[a['sha256']]=sid
    log['deleted_literature'].append(dict(path=path,source_id=sid,reason=why,**a))

# 保存精简的、只描述当前证据的事实，清除操作历史用语。
override={
 'CMOS-07':(
  '实际 28 nm eFlash CMOS 平台上的同步 2RW 8T SRAM，区分 clock、WL 脉冲、read access 与端口操作；Table II 有 macro 配置、频率和读写测试条件。',
  '该工艺针对 eFlash 优化、core/SRAM 阈值较高，不能等同所有 28 nm logic compiler。当前采用机构公开作者修订稿，内容完整但有排版占位；仅用明确的 28 nm 条件。'),
 'MRAM-05':(
  'Everspin EMxxxLX/B/HR v3.7（2026-07-23）正式 datasheet：back-to-back 写、无页跨越限制，读写命令、恢复条件和直接更新语义明确。',
  'xSPI 是封装接口，不是局部 cell 服务。ERASE 是兼容命令，不能由命令名断言 STT 介质必须先物理擦除；该文件不证明 28 nm。'),
 'SACIM-03':(None,
  '4-bit ADC 输出不等于完整无损 MAC 精度；普通权重写入绝对周期仍未闭合。电荷复位、建立、稀疏判读与 MAC 读出必须按 Fig.5 区分。'),
 'SDCIM-03':(None,
  '引言的普通 SRAM 小于 1 ns 是背景陈述；测得 clock 与完整精度输出须区分。memory 权重装载与 CIM 求值不自动重叠。'),
 'RRAM-01':(None,
  '1–10 ns 控制脉冲能力不能替代 Methods 中实际微秒级 program/verify 配置；网络级效果与 local MVM 分开。主文含所需 Methods/Extended Data。'),
 'MRAM-01':(None,
  '互补权重的两次写、read resistance sum 和普通 STT RAM 感测是不同机制；scaling 小节属于分析，不能作为追加实测样本。'),
 'PCM-01':(None,
  '部分 latency 由 RTL 得到，不能全部称直接测量；14 nm、四 PCM/cell 与其他芯片条件不同。'),
 'FENOR-01':(None,
  'NN benchmark 与大阵列延时为模拟；单 cell/小阵列测试不等于全精度 macro 周期。'),
}
keep=[s for s in ss.values() if s['source_id'] not in drop]
assert len(keep)==55 and all(s['main_file'] for s in keep)
NEW.mkdir()
active=[]
for s in sorted(keep,key=lambda s:(s['group'],s['source_id'])):
    sid=s['source_id'];g=s['group'];folder=NEW/'literature'/g;folder.mkdir(parents=True,exist_ok=True)
    filename=Path(s['target_path']).name
    if sid in ['SDCIM-04','SDCIM-05']:filename=f'{sid}_{s["year"]}_{s["short_title"]}.pdf'
    if sid=='NAND-02':filename='NAND-02_2026_Sandisk_KIOXIA_6Plane_QLC.pdf'
    p=R/s['main_file']['path'];dst=folder/filename;a=info(p);p.rename(dst);assert sha(dst)==a['sha256']
    log['moved_files'].append(dict(source_id=sid,kind='main',from_path=str(p.relative_to(R)),to_path=str(dst.relative_to(R)),**a))
    supplements=[]
    for f in s['supplements']:
        p=R/f['path'];dsts=folder/p.name;sa=info(p);p.rename(dsts);assert sha(dsts)==sa['sha256']
        supplements.append(dict(path=str(dsts.relative_to(NEW)),**sa))
        log['moved_files'].append(dict(source_id=sid,kind='supplement',from_path=str(p.relative_to(R)),to_path=str(dsts.relative_to(R)),**sa))
    rv=s['review'];evidence=rv['findings'];limits=rv['limits']
    if sid in override:
        ev,lim=override[sid];evidence=ev or evidence;limits=lim or limits
    # 这些是操作记录，不是证据内容。
    evidence=evidence.replace('V2 正文','正文').replace('V2 主文','主文').replace('新到 ','')
    limits=limits.replace('V2 主文','主文')
    record=dict(source_id=sid,group=g,title=s['title'],authors=s['authors'],year=s['year'],venue=s['venue'],
       publication_date=s.get('publication_date'),publication_dates=s.get('publication_dates'),doi=s.get('doi'),
       official_url=s['official_url'],document_id=s.get('document_id'),
       document_version='完整正式论文/技术资料' if s.get('intake_path') or sid in ['SDCIM-04','SDCIM-05'] else s.get('version','本地全文'),
       priority='核心' if rv['decision']=='核心' else '补充',roles=s['roles'],evidence_level=s['evidence_level'],
       process_condition=s.get('process_class') or '介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围',
       state_mode=s.get('state_mode'),confirmed_evidence=evidence,limitations=limits,anchors=rv['anchors'],
       pdf=dict(path=str(dst.relative_to(NEW)),**a),supplements=supplements,
       notes=f'literature/{g}/NOTES.zh.md#{sid}',fulltext_review='正文/Methods/相关图表已按估算用途审阅')
    if sid=='CMOS-07':record['document_version']='作者机构公开修订稿；当前唯一采用版本，内容足以支撑所列用途'
    if sid=='SACIM-02':record['document_version']='与 2025 期刊对应的 2024 作者稿；正文有实际芯片测量，引用正式期刊 DOI'
    if sid=='FERAM-01':record['document_version']='作者接受稿；实际离散器件实验和电路/架构模型分开使用'
    if sid=='PCM-01':record['document_version']='与 2023 正式论文对应的作者稿，包含 Methods/Extended Data'
    if sid=='MRAM-05':record['document_version']='Everspin v3.7；修订史 2026-07-23，部分内页仍沿用 ©2025'
    active.append({k:v for k,v in record.items() if v is not None})

byid={s['source_id']:s for s in active}
def reflink(sid,from_root=True):
    s=byid[sid];path=s['notes'] if from_root else f'../../{s["group"]}/NOTES.zh.md#{sid}'
    return f'[{sid}]({path})'
def ids(x):return '、'.join(reflink(i) for i in x.split())
groups=[
 ('00_cmos_periphery','00 — 28 nm CMOS 外围参考',
  '用实测 SAR、普通 SRAM 局部服务和实际 CIM 宏共同建立外围参考。此组保留 3 份主文件，并复用 5 份 CIM 主文，形成 8 份共同依据；转换率、输入建立和完整求值周期不互相替代。',
  'SACIM-03 SACIM-05 SDCIM-01 SDCIM-03 SDCIM-05'),
 ('01_sram_acim','01 — SRAM ACIM','电荷域 macro 补输入方式、转换共享、复位/建立和规定输出。不同工艺仅用作结构与条件交叉；普通 SRAM 写服务由共同组支持。','CMOS-03 CMOS-07'),
 ('02_sram_dcim','02 — SRAM DCIM','五篇全文覆盖位串行、两位/四位输入展开、动态逻辑、可调加法器及转置访问。把 clock、完整精度服务、memory 模式写入和精确/近似结果分别记录。','CMOS-03 CMOS-07'),
 ('03_nor_2d','03 — 2D NOR Flash','正式厂商资料提供字/页/sector 与内部 program/erase/BUSY，原始模拟 NOR 研究补细调与 CIM 联系。存储接口与阵列模拟读出是不同层级。',''),
 ('04_nand_3d','04 — 3D NAND Flash','MLC/TLC、QLC 与 SLC 器件/模式分开。制造商芯片、实际 SLC 器件和 RC/外围模型互补；不使用 SSD 带宽代表 local NAND 服务。',''),
 ('05_rram','05 — RRAM','CIM 宏、产业 raw/P&V 与正式产品资料覆盖读出、写验、脉冲/终止和操作层级。binary 与模拟目标、SET/RESET、FORMING 与日常更新分开。',''),
 ('06_mram','06 — MRAM','电阻求和和 bitcell 数字 CIM 分成不同参考机制；普通存储宏和正式 datasheet 支持读写与更新语义。互补 MTJ、两步写入、读验与位串行不能略去。',''),
 ('07_pcm','07 — PCM','两类 IBM 芯片及逐行闭环、混合 SLC/MLC 宏和独立材料/器件测量互补。SET/RESET、连续模拟权重、离散状态及脉冲测试终点分别使用。',''),
 ('08_feram_hfo2','08 — FeRAM（HfO₂-based）','主体为真实 HfO₂ 系 1T1C 电容阵列、C2FeRAM 机制与电容器件测量。破坏性读后恢复、两步行更新与混合 FeCAP/memristor 中的 FeCAP 证据分别标明。',''),
 ('09_gain_cell_edram','09 — Gain-cell eDRAM','2T1C/4T/3T1C 结构、硅/oxide 通道、模拟/数字求值分别处理。保持分布、刷新占用与 storage/stationary 更新关系共同约束服务。',''),
 ('10_fenor_3d','10 — 3D FeNOR／vertical FeFET','保留四篇直接相关的器件/小阵列和栅堆栈研究，包括指定的 Zhou 2025/2026。NOR 与 AND 拓扑、半选/相邻扰动、器件脉冲与宏级模拟分开。','')
]
dependencies={
 'NAND-04':'与 NAND-05 的 Macronix 器件依据有关联；模型和器件测量不是两次独立硅验证。',
 'NAND-05':'器件结果与 NAND-04 建模存在来源关系。',
 'NOR-04':'与 NOR-05 同团队/技术线；两篇分别补系统求值与细调方法。',
 'NOR-05':'与 NOR-04 同技术线；不重复计为独立器件交叉证据。',
 'PCM-01':'与 PCM-02/06 同为 IBM 相关技术生态；不同芯片/编程组织不代表完全独立的材料工艺证据。',
 'PCM-02':'PCM-06 是本工作明确引用的逐行编程依据，同技术线作方法补充。',
 'PCM-06':'为 PCM-02 的编程方法支撑，不另算独立工艺交叉验证。',
 'FENOR-01':'与 FENOR-02/06 同团队；逐篇保留不同结构、栅堆栈和测试条件。',
 'FENOR-02':'与 FENOR-01/06 同团队；最新结果不替代不同器件条件下的证据。',
 'FENOR-06':'与 FENOR-01/02 同团队；FENOR-04 提供另一团队/结构的直接交叉。',
 'FENOR-04':'以当前期刊全文作为该工作的唯一资料文件。'
}
for s in active:
    if s['source_id'] in dependencies:s['evidence_relationship']=dependencies[s['source_id']]

manifest=dict(schema_version='analysis-corpus-1.0',status='READY_FOR_ANALYSIS',prepared_on='2026-09-08',
  corpus_scope='统一 28 nm 外围参考条件下的小规模 CIM 参考设计估算；十类介质，不含独立 DRAM 行',
  policy='以本地已审全文开展后续分析，不再自动检索/下载；缺少的定值作为边界、模型假设或不确定性明确处理。',
  counts=dict(sources=len(active),main_pdfs=len(active),supplement_pdfs=sum(len(s['supplements']) for s in active),
              total_pdfs=len(log['moved_files']),core_sources=sum(s['priority']=='核心' for s in active),support_sources=sum(s['priority']=='补充' for s in active),missing_required_files=0),
  groups=[dict(directory=g,title=t,meaning=desc,shared_sources=shared.split()) for g,t,desc,shared in groups],sources=active)
dump(NEW/'source_manifest.json',manifest)

catalog=['# 文献目录','',
 '本地资料集已整理就绪：**55 份主文、4 份技术补充，共 59 份 PDF**。下表只列保留来源；全部主文已按估算用途审阅。点击 ID 查看正文要点，点击 PDF 直接阅读。',
 '', '固定 ID 是引用标识，不要求连续；跳号不表示缺件。核心与补充表示支撑作用，均为有效资料；有参考价值不等于其所有数字都可直接用于统一设计。','']
for g,title,desc,shared in groups:
    catalog += ['## '+title,'',desc,'']
    if shared:catalog+=['共享主文：'+ids(shared)+'。这些 PDF 只保存一份。','']
    catalog+=['| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |','|---|---|---|---|---|']
    for s in [s for s in active if s['group']==g]:
        ident=f'{s["year"]} · '+(', '.join(s['authors'][:2])+(' et al.' if len(s['authors'])>2 else ''))
        citation=f'[{s["title"]}](https://doi.org/{s["doi"]})' if s.get('doi') else f'[{s["title"]}]({s["official_url"]})'
        files=f'[PDF]({s["pdf"]["path"]})'
        for f in s['supplements']:files+=f' · [SI]({f["path"]})'
        catalog += [f'| {reflink(s["source_id"])} | {citation}<br>{ident}<br>{s["venue"]} | '+ '、'.join(s['roles'])+f' | {s["priority"]} | {files} |']
    catalog+=['']
    notes=['# '+title,'',desc,'',
           '以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。','']
    if shared:notes+=['共同/共享依据：'+'、'.join(f'[{sid}](../{byid[sid]["group"]}/NOTES.zh.md#{sid})' for sid in shared.split())+'。','']
    for s in [s for s in active if s['group']==g]:
        sid=s['source_id'];notes += [f'<a id="{sid}"></a>',f'## {sid} — {s["title"]}','',
          f'**{s["priority"]}** · {s["year"]} · {s["venue"]} · [全文]({Path(s["pdf"]["path"]).name})',
          '', '**身份与版本：** '+', '.join(s['authors'])+'。'+s['document_version']+'。',
          '', '**用途与结构：** '+s['confirmed_evidence'],
          '', '**正文定位：** '+s['anchors']+'。',
          '', '**工艺/模式：** '+s['process_condition']+'；'+s.get('state_mode','精度按正文条件限定')+'。',
          '', '**使用限制：** '+s['limitations']]
        if s.get('evidence_relationship'):notes+=['','**证据关系：** '+s['evidence_relationship']]
        if s.get('doi'):notes+=['',f'**出版标识：** [DOI](https://doi.org/{s["doi"]})。']
        elif s.get('document_id'):notes+=['','**文档编号：** '+s['document_id']+'。']
        for f in s['supplements']:notes+=['',f'**技术补充：** [SI]({Path(f["path"]).name})，{f["pages"]} 页，已归档。']
        notes+=['']
    (NEW/'literature'/g/'NOTES.zh.md').write_text('\n'.join(notes)+'\n')
(NEW/'LITERATURE_CATALOG.md').write_text('\n'.join(catalog))

(NEW/'README.md').write_text('''# Table I · CIM / NVM 文献资料集

**READY FOR ANALYSIS — 文献准备完成，可直接开展后续参考设计分析。**

统一目标：在明确的小规模 sub-array/local macro 边界，使用共同的 **28 nm CMOS 外围参考条件**，结合各介质的实际器件/阵列约束，形成可解释、可复算的量级范围。这是文献支持的参考设计，不是已制造芯片的性能排名。

## 从这里开始

1. [分析约定与交接](AGENTS.md)：后续工作的边界、口径和顺序。
2. [文献目录](LITERATURE_CATALOG.md)：全部有效来源、DOI、PDF 和正文笔记入口。
3. [证据覆盖](COVERAGE.md)：各组能支持什么、哪些条件需要在建模时声明。
4. [机器清单](source_manifest.json)：身份、工艺/状态、用途、正文定位、路径与哈希。

## 资料结构

```text
task1_table_I_NVM/
  README.md
  AGENTS.md
  LITERATURE_CATALOG.md
  COVERAGE.md
  source_manifest.json
  literature/
    00_cmos_periphery/
    01_sram_acim/
    02_sram_dcim/
    03_nor_2d/
    04_nand_3d/
    05_rram/
    06_mram/
    07_pcm/
    08_feram_hfo2/
    09_gain_cell_edram/
    10_fenor_3d/
```

每个分类目录只有一份 `NOTES.zh.md` 和有效 PDF。**55 份主文 + 4 份 SI，共 59 份 PDF**；44 份核心来源、11 份补充来源。SRAM DCIM 五篇全文均已齐全。共享来源只保存一份，没有历史版本、下载清单、搜索记录、脚本、旧表或临时文件。

**后续 Agent 使用本地资料即可，不再自动检索或下载文献。** 文件齐全不等于所有参数都有无歧义的直接实测值：已把器件/宏/系统层级、仿真与实测、读后恢复、写验及文内标注差异写进笔记。遇到这些限制，应明确参考情景与假设，不补造数字。

固定 source_id 用于跨文档引用，不要求连续。只使用本目录列出的来源和当前分析约定；不从旧表的数字反推目标范围。

本次交付止于资料准备；未计算最终 ρ、τ、RI*，未制作新 Table I，未改主论文或 Table II。
''')
(NEW/'AGENTS.md').write_text('''# 后续分析的工作约定

本目录是当前 Table I 参考设计估算的独立输入集。先读 README、COVERAGE，再按 LITERATURE_CATALOG 打开每类 NOTES.zh.md 和实际 PDF。笔记提供入口与限制，原始正文/图表才是证据。source_manifest 的路径均相对本目录。

## 范围与资料使用

- 只分析目录列出的十类对象：SRAM ACIM、SRAM DCIM、2D NOR、3D NAND、RRAM、MRAM、PCM、HfO₂-based FeRAM、Gain-cell eDRAM、3D FeNOR/vertical FeFET。共同 CMOS 外围单独成组；不新增独立 DRAM 行。
- 文献准备已经完成。**不要自动发起文献检索、下载或人工下载清单；不要遍历归档目录寻找旧数字。** 如果某项未报告，使用已保留的互补证据和明确的建模选择，或说明该情景的限制。
- 优先核心来源，补充来源仅用于标明的条件/方法/交叉检查。没有同一芯片的完整两路实测配对，不是禁止估算的理由；也不能把不同芯片的最快数值说成同一实现。
- 同技术线和同团队的关系在笔记中标出，不能重复计为独立验证。一个主文件可支持多个类别，不复制成多个来源。
- 不回退理论检查点、不清理用户其他修改；由用户负责 Git 暂存/提交/推送。未经新的任务指令，不修改主论文、Table II 或共享文档。

## 已采用的计量口径

用户已确认 resident–streaming 理论基线。后续估算保持下列约定，不需要重新从旧分析开始：

- 固定同一个服务边界、配置、状态模式和逻辑精度。Q_S 为累计服务的逻辑 streaming 输入 Byte；Q_R 为建立、更新、重载可计算 resident 状态的逻辑写入 Byte。
- 广播、位串行、位切片、互补 cell、多次 ADC、program/verify 与内部编码不重复增加同一次逻辑 payload；它们进入服务周期/资源占用。一次新的逻辑服务发生重放或重载时，需求重新计数。
- ρ 是完成规定求值和输出的输入 payload 服务能力，τ 是使 resident payload 可计算的写入服务能力。输出 Byte 不直接加到 Q_S，但必要 sensing/转换/数字累加/读出必须计入服务。
- latency 与稳态服务间隔分别处理；流水线不是简单取 latency 倒数。共享资源、重叠条件和有限窗口的填充/排空不能忽略。
- refresh、破坏性读后的 restore 是内部维护代价，不伪装成 workload 更新。耐久/寿命是另列可行性约束，不混入瞬时 τ。
- 原文参数保留原值和偏置、精度、负载、温度、误差/终点条件；清晰标注实测、仿真、模型假设、推导和文内不一致。完整逻辑写入不等于单脉冲。
- 1 Byte=8 bit；GB=10^9 Byte；GiB=2^30 Byte；稠密有用工作 1 MAC=2 OP。b_S 与 b_R 分别声明，8-bit 逻辑权重不表示一个物理 cell 存 8 bit。
- 模型使用 P=Q_S/T、RI=Q_S/Q_R、P≤min(ρ,τ·RI)、RI*=ρ/τ；Q_R=0 时为静态分支 RI=∞、P≤ρ。上界成立不保证两路独立峰值可同时达到。

## 后续顺序

1. 用共同组及共享宏选择少量可解释的 28 nm 转换、输入驱动、局部感测和数字服务条件。
2. 写通用的两路吞吐估算方法，明确直接更新与先擦/RESET再编程、闭环校验的不同步骤。
3. 中文逐节分析十类介质，区分共同外围、介质响应和专用驱动/维护；建立自洽情景与量级范围。
4. 检查共享参数/模式变化的影响，再生成英文 Table I 与精简说明。

服务边界、逻辑尺寸/精度、ADC 共享、状态精度和更新方式尚由后续建模选择；本交付未替这些条件预设数值。不得重造没有依据的精细延时链，也不得要求结果靠拢某种介质或旧表。
''')

rows=[
 ('00 CMOS','CMOS-02 CMOS-07','CMOS-03 CMOS-07','CMOS-07 SDCIM-05','SACIM-03 SACIM-05 SDCIM-01 SDCIM-03','CMOS-02 的有效精度/采样输入、CMOS-07 的 eFlash 平台条件保留；不能认为已获得通用 compiler 全库。'),
 ('SRAM ACIM','SACIM-01 SACIM-02 SACIM-03 SACIM-04 SACIM-05','CMOS-03 CMOS-07 SACIM-05','SACIM-01 SACIM-03 SACIM-05','SACIM-03 SACIM-04 SACIM-05','独立 DAC 的 rate 与 CIM 负载建立不同；memory 写周期不能用 MAC 周期代替。'),
 ('SRAM DCIM','SDCIM-01 SDCIM-02 SDCIM-03 SDCIM-04 SDCIM-05','CMOS-03 CMOS-07 SDCIM-01 SDCIM-05','SDCIM-01 SDCIM-03 SDCIM-04 SDCIM-05','SDCIM-01 SDCIM-03 SDCIM-05','SDCIM-04 性能标签混用；SDCIM-05 有容量和 AP/AC 标注差异。用明确结构/模式，不能静默修正。'),
 ('2D NOR','NOR-01 NOR-02 NOR-03 NOR-04','NOR-01 NOR-02 NOR-03 NOR-05','NOR-01 NOR-02 NOR-03','NOR-04 NOR-05','普通 binary program/erase 与模拟精细调谐是不同服务；buffer 摊销不等于单 word latency。'),
 ('3D NAND','NAND-01 NAND-02 NAND-03 NAND-05','NAND-01 NAND-03','NAND-02 NAND-03 NAND-05','NAND-04 NAND-05','SLC 器件与 burst 有依据，但完整专用 SLC program/erase 和 plane 约束未由单一手册闭合；不得混用 TLC/QLC。'),
 ('RRAM','RRAM-01 RRAM-02 RRAM-05','RRAM-01 RRAM-02 RRAM-04 RRAM-06','RRAM-02 RRAM-06','RRAM-01 RRAM-02 RRAM-05','RRAM-06 时间归一化；RRAM-04 是慢封装产品提交；脉冲、verify 和整体更新按所选情景组织。'),
 ('MRAM','MRAM-01 MRAM-03 MRAM-04 MRAM-06','MRAM-01 MRAM-03 MRAM-05 MRAM-06','MRAM-01 MRAM-06','MRAM-01 MRAM-06','电阻求和与 bitcell 数字路径分别估算；互补两步写/row verify/错误率条件不能省去。'),
 ('PCM','PCM-01 PCM-02 PCM-03','PCM-01 PCM-02 PCM-05 PCM-06','PCM-01 PCM-02 PCM-06','PCM-01 PCM-02 PCM-03 PCM-06','SET/RESET、闭环与 FPGA 调度分开；PCM-04 亚纳秒仅材料对照，2 ms 是测试间隔而非必需服务。'),
 ('HfO₂ FeRAM','FERAM-02 FERAM-03 FERAM-04','FERAM-01 FERAM-02 FERAM-03 FERAM-04','FERAM-02 FERAM-03 FERAM-04','FERAM-01','读后恢复是核心代价；FERAM-05 是器件补充，FERAM-06 仅取 FeCAP 证据，不归入纯 FeRAM 推理成绩。'),
 ('Gain-cell eDRAM','GC-01 GC-02 GC-04 GC-05','GC-02 GC-04 GC-05','GC-02 GC-03 GC-05','GC-01 GC-03 GC-04 GC-05','保持分布/允许错误与刷新占用同时声明；粗写不是完整多级写，storage 更新不等于 stationary 更新。'),
 ('3D FeNOR/vertical FeFET','FENOR-01 FENOR-02 FENOR-04','FENOR-01 FENOR-02 FENOR-04 FENOR-06','FENOR-02 FENOR-04','FENOR-01 FENOR-02 FENOR-04','NOR/AND、栅堆栈、偏置和 MW 终点分开；小阵列测量与大规模 TCAD/SPICE/CIM 模型区分。')
]
coverage=['# 证据覆盖与建模边界','','**所列主文及必要附件全部可本地打开；没有待下载文件。** 下表是证据作用矩阵，不是数值 Table I。未直接报告的定值属于后续参考情景的假设/不确定性，不再自动转换为下载任务。','',
 '| 对象 | 读侧 | 写侧 | 粒度/并行 | 外围/求值桥接 | 必须保留的限制 |','|---|---|---|---|---|---|']
for name,read,write,gran,bridge,limit in rows:coverage += [f'| {name} | {ids(read)} | {ids(write)} | {ids(gran)} | {ids(bridge)} | {limit} |']
coverage += ['','## 先声明的共同条件','',
 '- sub-array/macro 的确切服务边界、参与 bank 和包含的局部外围。',
 '- 逻辑尺寸与 b_S/b_R、规定输出精度/误差；精确与近似模式分别命名。',
 '- ADC/输入驱动的共享、必要串行步骤、可重叠阶段以及稳态服务间隔。',
 '- binary/多级/连续模拟目标，整页或局部更新、擦除/RESET、闭环终点和专用驱动。',
 '- 读后恢复、刷新、保持/错误率与可用服务占用的处理。','',
 '这些决定可由本地互补证据构造少量情景；不要求单篇文献同时给出完整两路吞吐。原始量与选择的假设分别记录。','']
(NEW/'COVERAGE.md').write_text('\n'.join(coverage))

# 先验证干净集完整，再永久删除明确剔除资料与临时文件，最后整体归档旧任务。
assert len(list((NEW/'literature').rglob('*.pdf')))==59
for s in active:
    for a in [s['pdf']]+s['supplements']:assert sha(NEW/a['path'])==a['sha256']
for p in NEW.rglob('*.md'):
    text=p.read_text()
    assert 'tasks/task1_table_i/' not in text and '/rebuild/' not in text
    for u in re.findall(r'\]\(([^\n]*?)\)',text):
        if u.startswith(('http://','https://')):continue
        f,_,anchor=u.partition('#');q=(p.parent/f).resolve() if f else p
        assert q.exists(),(p,u)
        if anchor and q.suffix=='.md':assert f'id="{anchor}"' in q.read_text(),(p,u)
for path,sid,why in deletions:
    p=R/path;assert sha(p) in deleted_hashes;p.unlink()

# 删除旧任务内同字节的剔除 PDF 副本，保留根目录和其他任务不动。
for p in OLD.rglob('*.pdf'):
    if any(part in ['tmp','__pycache__'] for part in p.relative_to(OLD).parts):continue
    h=sha(p)
    if h in deleted_hashes:
        log['deleted_literature'].append(dict(path=str(p.relative_to(R)),source_id=deleted_hashes[h],reason='剔除来源的相同字节副本',**info(p)));p.unlink()
for name in ['tmp','__pycache__']:
    dirs=sorted([p for p in OLD.rglob(name) if p.is_dir()],key=lambda p:len(p.parts))
    for p in dirs:
        if not p.exists():continue
        files=[q for q in p.rglob('*') if q.is_file()]
        log['removed_temporary_directories'].append(dict(path=str(p.relative_to(R)),files=len(files),bytes=sum(q.stat().st_size for q in files)))
        shutil.rmtree(p)
for p in OLD.rglob('*'):
    if p.is_file() and (p.name=='.DS_Store' or p.suffix=='.pyc'):
        log['removed_cache_files'].append(str(p.relative_to(R)));p.unlink()

OLD.rename(LEGACY)
log['counts']=manifest['counts']
log['old_path_absent']=not OLD.exists()
dump(ARC/'TASK1_MIGRATION_RECORD.json',log)
(ARC/'README.md').write_text('''# 历史归档

`task1_table_i/` 保存此前任务、旧表、下载/搜索历史、旧目录和中间脚本。该目录是冷归档，不是后续分析输入；其中相对路径/脚本保留历史语义，不要运行来重建当前数据。

**当前独立资料入口：** [task1_table_I_NVM](../task1_table_I_NVM/README.md)。

迁移、剔除与完整性记录见 [TASK1_MIGRATION_RECORD.json](TASK1_MIGRATION_RECORD.json)。被判断无需保留的论文、重复版本和简表已直接删除；tmp、提取文本/预览及 Python 缓存已清理。其余历史材料集中保留于本目录。

原 `tasks/task1_table_i/` 路径已移除。此次未修改主论文或 Table II，未执行 Git 暂存/提交/推送。
''')
print(json.dumps(dict(new_root=str(NEW.relative_to(R)),archive=str(LEGACY.relative_to(R)),counts=manifest['counts'],deleted_pdfs=len(log['deleted_literature']),removed_tmp_files=sum(x['files'] for x in log['removed_temporary_directories']),old_path_absent=not OLD.exists()),ensure_ascii=False,indent=2))

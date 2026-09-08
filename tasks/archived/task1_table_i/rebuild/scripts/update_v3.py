"""V2 来件核验后的本地登记、审阅与 V3 清单；不联网、不下载。"""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,re
import pypdfium2 as pdfium

B=Path(__file__).resolve().parents[1];R=B.parents[2];P=B.relative_to(R).as_posix()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def asset(p):
    p=Path(p);p=p if p.is_absolute() else R/p
    raw=p.read_bytes();assert raw.startswith(b'%PDF-')
    d=pdfium.PdfDocument(p);n=len(d);d.close()
    return dict(path=p.relative_to(R).as_posix(),pages=n,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def link(path,label='本地 PDF'):return f'[{label}]({Path(path).relative_to(Path(P)).as_posix()})'
def sl(sid):return f'[{sid}](LITERATURE_CATALOG.md#{sid})'

m=json.loads((B/'source_manifest.json').read_text())
snap=B/'history/r1_v2';snap.mkdir(parents=True,exist_ok=True)
for fn in ['README.md','DOWNLOAD_REQUESTS_V1.md','LITERATURE_CATALOG.md','COVERAGE.md','FULLTEXT_REVIEW_R1.md','C_SEARCH_LOG.md','INTAKE_AUDIT_R1.md','source_manifest.json']:
    if not (snap/fn).exists():shutil.copy2(B/fn,snap/fn)
(snap/'metadata').mkdir(exist_ok=True)
for fn in ['archive_validation_r1.json','fulltext_reviews_r1.json']:
    if not (snap/'metadata'/fn).exists():shutil.copy2(B/'metadata'/fn,snap/'metadata'/fn)
ss={s['source_id']:s for s in m['sources']}
intake=[]
for req in json.loads((snap/'source_manifest.json').read_text())['pending_downloads']:
    sid=req['source_id'];rid=req['request_id'];dest=R/req['target_path']
    if dest.exists():continue
    entries=[json.loads(x.read_text()) for x in (B/'tmp/v2_intake').glob('*.json')]
    marker={'SACIM-05':'Global_Bitline','RRAM-06':'Auto-FORMING','PCM-06':'Fully_On-Chip','MRAM-06':'s41928-025-01479-y','PCM-04-SI':'aao3212_rao_sm'}[rid]
    entry=next(x for x in entries if marker in x['path'])
    src=R/entry['path'];a=asset(src);assert len(entry['pages'])==a['pages']
    # 身份实际首面已人工核对；仅更名，不重写 PDF。
    dest.parent.mkdir(parents=True,exist_ok=True);src.rename(dest);z=asset(dest);assert z['sha256']==a['sha256']
    intake.append(dict(request_id=rid,source_id=sid,kind=req['kind'],from_path=entry['path'],to_path=z['path'],pages=z['pages'],sha256=z['sha256'],identity='实际题名、作者、DOI（如印于文中）、页数与 V2 请求相符；首页及相关正文/图表已看'))
    if req['kind']=='main':
        s=ss[sid];s['main_file']=z;s['intake_path']=entry['path'];s['received_in']='V2_user_batch'
        s['access_status']='user_fulltext_received';s['version']='用户提供正式主文（含原文件中的 Methods/Extended Data）'
    else:
        z.update(obtained_in='V2_user_batch',original_intake_path=entry['path'],validation='18 页 SI，题名/DOI 与主文对应，Materials and Methods、Figs.S1–S11 齐')
        ss[sid]['supplements'].append(z)
if intake:dump(B/'metadata/intake_v2_completed.json',intake)

updates={
 'SACIM-05':dict(decision='核心',anchors='p.2 III-A/B、Fig.4；pp.3–4 III-C/D、IV、Figs.5–10；p.5 Fig.11',
  findings='28 nm 实测 6T SRAM macro；32 个 cell 共享 HIPCC，本地/全局 BL 与普通读写路径明确。8-bit 输入分成四组 2-bit DAC 电压并行输入；GBL-comb 将同位权部分和合并，SAR 数量由 96 减到 69，并以数字移位累加形成输出。',
  limits='不是一个独立 8-bit DAC 直接驱动全部字线。voltage-stacking 有初始化、采样、叠加三阶段；输出数字位数不代表模拟无误精度；仍未明确普通写入的绝对完整服务周期。',
  change_from_r0='V2 主文已到，实际提供共同 28 nm 输入/ADC 共享、局部读写和完整求值桥接，正式保留。'),
 'RRAM-06':dict(decision='核心',anchors='p.1 AF/ARST/ASET 与测量小节；p.2 Figs.3–10',
  findings='实际 40 nm 2 Mb bipolar ReRAM；两组 IO/column 控制、等待组内完成、地址跳过、timeout 和 FORMING/SET/RESET 终止机制清楚。HRPW 把 page RESET 放在 idle，再对所需 cell SET，支持显式更新步骤/资源占用建模。',
  limits='Fig.9 使用 normalized time unit，Fig.10 也是归一化时间/相对改善；全文没有因此补出绝对 page 延时。99% 改善包含 hidden-RESET，不能解释为省掉 RESET，FORMING 也不能算作每次更新。',
  change_from_r0='V2 正文确认方法有用；纠正“可能补齐绝对 page 时间”的期待，仅将归一化结果用于方法/比例参考。'),
 'PCM-06':dict(decision='核心',anchors='pp.3–5 III/IV、Figs.2–9；p.4 Fig.6；p.5 闭环算法',
  findings='14 nm PCM 原始逐行 CLT；同一 row 的 512 列共享幅度 DAC而各列使用独立脉宽。每次脉冲后读验，FPGA 算误差并装入下一轮脉宽；次级 PCM 可补偿过冲，器件/周期差异有实际测量。',
  limits='“Fully on-chip MAC”不代表闭环调谐控制全部片上。60/120/240 ns 是示例脉冲，1.2 ns/tick 是读数编码；都不是完整写入周期。原文明确为连续模拟目标，不是固定离散级的商品 MLC。与 PCM-02 同技术线，不新增独立工艺证据。',
  change_from_r0='V2 主文补齐 PCM-02 ref.4 的实际算法与外围调度，保留核心方法证据。'),
 'MRAM-06':dict(decision='核心',anchors='pp.2–5 Figs.2/3；pp.8–9 Methods；p.15 Extended Data Fig.2；已归档 SI Fig.2',
  findings='实际 40 nm STT-MRAM 数字 CIM；bitcell 内乘法/数字化，64 bank 各 256×4，输入 MSB-first 位串行、bank 内并行乘加，多精度由累加和 bank 合并实现。写互补 MTJ 分两步，测试按 row 写后读验，错误 row 重写。',
  limits='“Fully parallel”不是任意多位 MVM 一拍完成：4-bit 输入用四拍。数字无损算术也不保证所有电压下存储读无误；p.4 区分低压实测读错误与较高电压无观测错误。不能将最佳能效、时钟及无错条件拼接为同一工作点；未给出完整写验绝对周期。',
  change_from_r0='V2 正文与 SI 齐，作为区别 Jung 模拟求和/Chiu near-memory 的核心机制；补正摘要可能引出的单周期印象。'),
 'PCM-04':dict(decision='补充',anchors='主文 pp.2–4；SI p.2 §2、p.8 Fig.S5、p.9 Fig.S6',
  findings='补充材料确认 0.13 μm 平台、190 nm BEC 的 T-shaped 器件、外部源表/脉冲发生器和示波器；亚纳秒为特定材料/偏置下的器件 SET 结果，适合作材料时间尺度对照。',
  limits='SI Fig.S6 刻意采用 2 ms 脉冲间隔避免累积作用，既不能把脉宽当连续写服务，也不能把 2 ms 当介质必需延时。S5/S6 的 700 ps 示例偏置不同，应保留各自条件；不支持整阵列或多级闭环写入速度。',
  change_from_r0='18 页 SI 已补齐，移除缺件/等待标签；有用但只留材料对照，不作为 PCM 完整写入核心。')
}
for sid,v in updates.items():
    s=ss[sid];v['review_method']='实际正文、Methods/技术 SI 与关键图表的用途筛选；未计算吞吐范围'
    v['review_round']='R1_V3';s['review']=v;s['review_status']='fulltext_suitability_reviewed'
    s['fulltext_suitability']='V2 全文/附件已复核；确认的证据作用与限制见 review'
    s['confirmed_content']=v['findings'];s['purpose']=v['findings'];s['limitations']=v['limits']
    s['priority']='P1' if v['decision']=='核心' else 'P2';s['core_eligible']=v['decision']=='核心'
    s['access_status_zh']='V2 用户文件已到，身份及正文用途已核验';s['request_batch']=None
    s['manual_request_contents']=None;s['manual_request_reason']=None;s['gap_from_review']=None
    s['supplement_status']='已有主文及所需技术 SI；未识别新的必需附件。' if s['supplements'] else '完整主文已到，未识别另需索取的技术 SI。'
ss['SACIM-05']['evidence_level']='28 nm 实测 SRAM 局部 macro 与读写/转换外围'
ss['SACIM-05']['process_class']='直接的 28 nm 实测证据；普通写入绝对周期仍未闭合'
ss['MRAM-06']['evidence_level']='实测 STT-MRAM bitcell 数字 CIM／局部 bank/macro'
ss['MRAM-06']['state_mode']='binary 互补 2T2MTJ；输入位串行、bank 内并行，4/8/12/16-bit 分模式'
ss['RRAM-06']['evidence_level']='实测普通 ReRAM macro；时序图/归一化测量'
ss['PCM-06']['state_mode']='连续模拟电导与 4 PCM/weight；CLT 与 FPGA 控制，非固定离散 MLC'
ss['PCM-04']['supplement_status']='18 页 Materials and Methods/Figs.S1–S11 已核验，缺件关闭。'
ss['PCM-02']['supplement_status']='Methods/Extended Data 在主文；关键编程转引 PCM-06 也已到件。未识别新的必需技术 SI。'
ss['SACIM-05']['independence_note']='与已列 SACIM-03/04 为不同工作；同文引用 2021 的 384-kb 前作，未据容量相同认定独立芯片交叉证据，亦不追加前作下载。'

for sid,year,short,firstdate,urls,why in [
 ('SDCIM-04',2024,'SignExtensionLess_DigitalCIM','2024-07-03',
  ['https://ieeexplore.ieee.org/document/10582884/'],
  '现有 D6CIM/动态逻辑主要解释逐位展开；这篇补有符号整数乘法、符号扩展处理和 accuracy-adjustable adder 的完整服务，核查精度模式而非只对比能效。'),
 ('SDCIM-05',2026,'DigitalTranspose_AccurateApprox',None,
  ['https://ieeexplore.ieee.org/document/11475654/','https://sscs.ieee.org/category/ieee-journal-of-solid-state-circuits/ieee-journal-of-solid-state-circuits-early-access/page/16/','https://sasasatori.github.io/'],
  '补数字 SRAM 矩阵转置、FF/BP 的局部访问方向与 MAC 电路复用，以及精确/近似和整数/浮点控制。写入路径仍须正文确认，不能由题名“training”推断写周期。')]:
    if sid in ss:continue
    j=json.loads((B/'metadata'/f'{sid}_crossref.json').read_text());doi=j['DOI']
    s=dict(source_id=sid,group='02_sram_dcim',title=j['title'][0],year=year,short_title=short,
           authors=[(a.get('given','')+' '+a.get('family','')).strip() for a in j['author']],
           venue=j['container-title'][0],volume=j.get('volume'),issue=j.get('issue'),pages=j.get('page'),
           publication_date=firstdate,publication_dates={k:j[k] for k in ['published','published-print','published-online'] if k in j},
           doi=doi,doi_url='https://doi.org/'+doi,official_url=urls[0],access_urls=urls,
           identity_verified=True,identity_basis='IEEE 官方题录/摘要与 Crossref 登记核对；SDCIM-05 另与 SSCS/作者主页核对；未访问主文。',
           metadata_file=f'{P}/metadata/{sid}_crossref.json',verified_on='2026-09-08',discovered_in='R1_V3_DCIM_search',
           evidence_level='局部 SRAM DCIM macro 候选；流片与细节按官方公开摘要预判',process_class='直接 28 nm 工艺候选，完整时序/测试条件待全文',
           roles=['数字求值与控制','精度与必要步骤','局部操作粒度','独立结构交叉核查'],
           priority='P1' if sid=='SDCIM-04' else 'P2',purpose=why,
           target_path=f'{P}/literature/02_sram_dcim/{sid}_{year}_{short}.pdf',main_file=None,supplements=[],related_versions=[],copy_provenance=None,
           shared_with=['00_cmos_periphery'],package_id=sid,request_batch='V3',
           access_status='user_download_required',access_status_zh='仅题录/官方摘要核验；未下载、未审主文',review_status='awaiting_main_fulltext',
           fulltext_suitability='候选，尚未由主文确认具体周期/并行条件',version='优先所列期刊版本；完整合法作者稿亦可',
           confirmed_content='官方题录/摘要确认数字 SRAM、28 nm 和研究主题；具体完整周期、精度模式、write 路径均待主文。',
           supplement_status='未确认另有独立技术 SI；主文下载页面若确列相关附件，一并保存。',
           manual_request_reason=why,
           manual_request_contents='完整期刊主文 '+j.get('page','')+'；若出版社确有技术 SI，一并获取。')
    if sid=='SDCIM-04':
        s['publication_note']='IEEE 首发 2024-07-03；TVLSI 32(11), 2164–2168，卷期 2024-11。'
        s['independence_note']='Xin Si 等团队与现有 Oh/Seok、Zhang/Kim、Yan 等三篇作者组合不同；注意 Xin Si 与 Xin Zhang 是不同作者。'
        s['state_mode']='有符号整数 MAC；adder 精度可调，不能先把全部模式称为全精度'
    else:
        s['publication_note']='Crossref 当前卷期为 JSSC 61(9), 5098–5110（2026-09）。SSCS 2026-04-08 已刊 Early Access 介绍，证明此前已公开；不把该介绍日或 DOI 创建日充作论文精确首发日，待 PDF 确认。'
        s['independence_note']='Yuan/Zhang 等研究组合与现有三篇 DCIM 不同；和本研究其他介质/外围来源可能有合作者重叠，不声称完全无关联。'
        s['state_mode']='数字 transpose SRAM，accurate/approximate、FP/INT 模式分开，具体支持格式待主文'
        s['related_versions']=[dict(title='14.5 A 28nm 192.3TFLOPS/W Accurate/Approximate Dual-Mode-Transpose Digital 6T-SRAM CIM Macro for Floating-Point Edge Training and Inference',year=2025,
          doi='10.1109/ISSCC49661.2025.10904659',url='https://ieeexplore.ieee.org/document/10904659/',file=None,
          relation='同团队同主题会议前作，与期刊按一个演进工作包管理；不另请下载会议版，收到期刊后核实扩展声明/数据继承范围。')]
    ss[sid]=s

for g in m['groups']:
    if g['directory']=='02_sram_dcim':g['introduction']='现有三篇主文已经覆盖 D6CIM、65 nm 位重构与 28 nm 动态逻辑。V3 新增两篇 28 nm 数字 SRAM 候选，分别补有符号 MAC/精度可调加法树，以及数字转置/精确近似双模式；现在共五篇专属候选，仍只三篇全文在本地。'
    elif g['directory']=='00_cmos_periphery':
        g['introduction']='共同外围分别由实测 SAR、实际 CIM 输入/ADC 共享、SRAM 局部服务与数字宏支持。SACIM-05 的 V2 正文确认四组 2-bit 输入及 GBL-comb，补充共同服务桥接；CMOS-07 的 eFlash 工艺、RF DAC 的负载条件与仿真证据仍分别标注。'
    elif g['directory']=='05_rram':g['introduction']='NeuRRAM/28 nm CIM、产业 raw/P&V 与产品提交周期互补。新到 RRAM-06 确认 hidden-RESET 与局部控制步骤，但其时序图/结果归一化，不能据此得出绝对 page 周期；器件单脉冲与完整更新仍分开。'
    elif g['directory']=='06_mram':g['introduction']='Jung 的电阻求和、Chiu 的 near-memory 数字引擎与新到 Li 等 bitcell 内数字 CIM 是不同机制。MRAM-06 的主文和 SI 已齐，明确输入位串行、互补写两步和 row 读验；数字无损算术不等于任意电压下存储读无误。'
    elif g['directory']=='07_pcm':g['introduction']='IBM 两类 tile/芯片、TSMC SLC/MLC 与独立材料/器件测量互补。V2 的 PCM-06 已补逐行 CLT 和 FPGA 调度；PCM-04 的 SI 已确认亚纳秒脉冲及 2 ms 测量间隔，只作材料对照。'
m['sources']=sorted(ss.values(),key=lambda s:(s['group'],s['source_id']))
m['counts_history_v2']=m.get('counts_history_v2',m['counts'])
reviewed={sid:s['review'] for sid,s in ss.items() if s.get('review')}
m['counts']=dict(candidate_records=len(ss),source_packages=len({s['package_id'] for s in ss.values()}),local_main=60,
  local_pdf_count=69,local_supplements=6,local_related_documents=3,fulltext_reviewed=60,
  decisions=dict(Counter(v['decision'] for v in reviewed.values())),v2_received_packages=5,v2_missing_packages=0,
  latest_user_main=4,latest_user_supplements=1,latest_renamed_files=5,latest_automatically_downloaded_files=0,
  sram_dcim_candidates=5,sram_dcim_local_main=3,manual_pending_packages=2,new_wholly_irrelevant_removed=0)
m['schema_version']='1.2-r1-v3';m['status']='V2 五包已验收；SRAM DCIM 补选完成，等待 V3 两篇主文'
m['download_requests_version']=3;m['pending_downloads']=[]
for sid in ['SDCIM-04','SDCIM-05']:
    s=ss[sid];m['pending_downloads'].append(dict(request_id=sid,source_id=sid,kind='main',batch='V3',priority=s['priority'],status='user_download_required',target_path=s['target_path'],doi=s['doi'],official_urls=s['access_urls'],contents=s['manual_request_contents'],reason=s['purpose']))
m['completed_download_rounds']=dict(V1='55 主文记录齐',V2='5/5 包验收，4 主文+1 SI；2026-09-08')
m['download_policy']='用户负责全部文献下载。本次仅查网页题录/摘要及 Crossref 元数据，新增 PDF 下载为 0。'
dump(B/'source_manifest.json',m);dump(B/'metadata/fulltext_reviews_r1.json',reviewed)

# 通用目录，以当前 manifest 为唯一计数/路径来源。
cat=['# 文献目录（R1 / V3）','','2026-09-08。V1/A/B 与 V2 已全部到齐；**62 条来源记录、61 个资料包，60 条本地主文，69 份 PDF**。SRAM DCIM 共 5 条专属候选，其中新增 2 条待主文。',
 '', '[当前下载清单 V3](DOWNLOAD_REQUESTS_V1.md) · [本轮到件/正文/去留](V2_INTAKE_AND_DCIM_REVIEW.md) · [全部逐篇判断](FULLTEXT_REVIEW_R1.md) · [覆盖矩阵](COVERAGE.md)','',
 '核心是用途优先级，不是性能排名；器件、macro、系统以及仿真/测量分别记录。P1 优先，P2 补充，P3 版本/对照。页码以本地 PDF 第 1 页起计。','']
for g in m['groups']:
    cat+=['## '+g['title'],'',g['introduction'],'']
    if g['shared_sources']:cat+=['共享来源：'+'、'.join(sl(x) for x in g['shared_sources'])+'；不重复保存或计数。','']
    for s in [s for s in m['sources'] if s['group']==g['directory']]:
        sid=s['source_id'];v=s.get('review');decision=v['decision'] if v else '待主文的候选'
        cat += [f'<a id="{sid}"></a>',f'### {sid} — {s["title"]}','',
          '- 身份：'+str(s['year'] or '未署日期')+'；'+s['venue']+'；'+'、'.join(s['authors'][:3])+(' 等。' if len(s['authors'])>3 else '。'),
          '- 链接：'+(f'[DOI](https://doi.org/{s["doi"]}) · ' if s.get('doi') else '')+f'[官方页面]({s["official_url"]})。',
          f'- 判断：**{decision} / {s["priority"]}**；证据层级：{s["evidence_level"]}。',
          '- 用途标签：'+'；'.join(s['roles'])+'。',
          '- 工艺/状态：'+(s.get('process_class') or '介质专用条件；不自动认定 28 nm')+'；'+(s.get('state_mode') or '按正文精度/模式限定')+'。',
          '- 已确认/预判：'+s['confirmed_content'],
          '- 限制：'+(v['limits'] if v else '主文尚未读取，不能预设绝对完整周期、精度模式或写入服务。'),
          '- 访问：'+s['access_status_zh']+'；'+(link(s['target_path']) if s['main_file'] else '待用户下载')+'。',
          f'- 保存路径：`{s["target_path"]}`。']
        if v:cat+=['- 正文定位：'+v['anchors']+'。']
        for key,label in [('publication_note','日期'),('identity_note','版本核验'),('independence_note','独立性')]:
            if s.get(key):cat+=['- '+label+'：'+s[key]]
        cp=s.get('copy_provenance')
        if cp:cat+=['- 复制来源：`'+cp.get('original_path',cp.get('previous_task_path',''))+'`；原文件保留，哈希关系见 manifest。']
        if s.get('intake_path'):cat+=['- 用户原名：`'+s['intake_path']+'`。']
        if s.get('original_archive_path'):cat+=['- 原归档路径：`'+s['original_archive_path']+'`。']
        for f in s['supplements']:cat+=['- 附件：'+link(f['path'],'Supplementary Information')+f'（{f["pages"]} 页）。']
        for vrs in s['related_versions']:
            if vrs.get('file'):cat+=['- 相关版本：'+link(vrs['file']['path'],vrs['title'])+'；'+vrs.get('relation','')]
            elif vrs.get('doi'):cat+=['- 相关前作：[DOI](https://doi.org/'+vrs['doi']+')；'+vrs.get('relation','')]
        cat+=['- 附件情况：'+s['supplement_status'],'']
(B/'LITERATURE_CATALOG.md').write_text('\n'.join(cat)+'\n')

report=['# V2 验收与 SRAM DCIM 补选（R1 / V3）','','2026-09-08。**V2 的 5/5 包到齐、已重命名，主文/附件身份匹配；本轮下载 PDF 0 份。** 四篇主文和一份 SI 均已检查正文及关键图表，未进入正式参数分析。','',
 '## 到件','', '| ID | 内容 | 页数 | 当前文件 |','|---|---|---:|---|']
for f in json.loads((B/'metadata/intake_v2_completed.json').read_text()):report += [f'| {f["request_id"]} | '+('主文' if f['kind']=='main' else '技术 SI')+f' | {f["pages"]} | {link(f["to_path"],Path(f["to_path"]).name)} |']
report+=['','MRAM-06 是 24 页主文+Methods/Extended Data，另有已归档的 15 页 SI，二者不重复。PCM-04 的 18 页 SI 包含所需方法和 Figs.S1–S11。原名与哈希见 [到件记录](metadata/intake_v2_completed.json)。','', '## 新正文改变的判断','']
for sid,v in updates.items():
    report += [f'### {sid} — {v["decision"]}','',v['findings'],'',v['limits'],'','定位：'+v['anchors']+'。 '+sl(sid),'']
report += ['## SRAM DCIM 为什么补这两篇','',
 '| ID | 互补作用 | 已核验程度 |','|---|---|---|',
 '| '+sl('SDCIM-04')+' | 有符号整数 MAC、符号扩展以及精度可调加法树；补现有 bit-serial/dynamic logic 之外的数字服务 | IEEE 官方摘要及出版记录；主文待审 |',
 '| '+sl('SDCIM-05')+' | 28 nm 数字 transpose SRAM，FF/BP 的局部方向/计算复用，精确与近似模式 | IEEE SSCS/作者网页/Crossref；主文待审；同主题 ISSCC 2025 不重复请求 |','',
 '现有 SDCIM-01/02/03 保留，新增后专属来源由 3 增至 5。两篇新候选的作者组合与原三篇不同；不是把同一芯片会议版/期刊版凑成两份。SDCIM-05 的确切扩展声明和测试继承关系留待期刊正文确认。','',
 '## 仍缺什么、哪些不用','',
 '- **当前明确的待下载文件只有 SDCIM-04/05 两篇主文。** 旧 V2 请求全部关闭，未发现新的必需附件。',
 '- **没有新发现需要整篇删除的无关主文。** RRAM-06 虽只给归一化时间，仍补实际写入控制与 hidden-RESET 方法；保留并限制用途。PCM-04 的 SI 到件后改为材料补充，不能用亚纳秒值支撑连续阵列写入。',
 '- **原来的归并/对照处理继续有效**：FENOR-03/04 同包；FENOR-05 是 FeNAND，仅作拓扑对照；旧 Everspin brief、SRAM 会议前作/slides 留版本目录，不占独立核心。',
 '- **技术依据仍有边界缺口**：RRAM-06 的绝对 page 时间；3D NAND SLC 完整 program/erase 与 plane 约束；通用 28 nm compiler 完整时序库。现有材料已提供操作步骤、单器件响应和外围服务依据，不能因此判为不可估算。待确定具体参考模式后再决定是否需要补资料，本轮不继续泛化索取。',
 '- **不追加以下 DCIM 候选**：hybrid-domain/current/TDC 论文不能仅因题名含 digital 就归为 DCIM；同主题 2025 ISSCC 转置稿不和 2026 JSSC 一起索取；两周期 Winograd 整处理器仍是有价值候补，但当前两篇更直接补局部 signed MAC/transpose，暂不扩大阅读负担。','',
 '本次已修正 11 个分类 README 中旧的“PDF 被 .gitignore 排除”说明；PDF 开放 Git 的用户设置保持。只更新 rebuild，未暂存/提交/推送，未改主论文或 Table II。','']
(B/'V2_INTAKE_AND_DCIM_REVIEW.md').write_text('\n'.join(report))

rv=['# R1 正文适用性审阅（V3 更新）','','截至 2026-09-08，**60 条本地主文已完成用途筛选**；43 核心、14 补充、1 条件保留、1 版本归并、1 结构对照。新增 SDCIM-04/05 仅核验题录/摘要，尚不计入全文审阅。',
 '', '最新 V2 五包的正文发现、去留及 SRAM DCIM 补选理由见 [本轮报告](V2_INTAKE_AND_DCIM_REVIEW.md)。页码为本地 PDF 页序；本轮不做最终参数/吞吐范围。','']
for g in m['groups']:
    rv+=['## '+g['title'],'']
    for s in [x for x in m['sources'] if x['group']==g['directory'] and x.get('review')]:
        v=s['review'];rv += [f'**{sl(s["source_id"])} — {v["decision"]}** · '+link(s['target_path']),'','正文定位：'+v['anchors']+'。','','保留用途：'+v['findings'],'','不能据此声称：'+v['limits'],'','本轮/此前处理：'+v['change_from_r0'],'']
(B/'FULLTEXT_REVIEW_R1.md').write_text('\n'.join(rv))

dl=['# 人工下载清单 V3 — SRAM DCIM 补充','','2026-09-08。继续使用用户指定路径 `DOWNLOAD_REQUESTS_V1.md`，**内容已更新为 V3**；[V2 备份](history/r1_v2/DOWNLOAD_REQUESTS_V1.md)。',
 '', '**V2 五包全部到齐并验收，旧请求缺件为 0。本次只请下载下列 2 篇 SRAM DCIM 主文。** 全部论文下载由用户负责；本轮代理没有下载 PDF。',
 '', '本地已有 60 条主文记录、69 份 PDF；SRAM DCIM 现在有 5 条候选，其中 3 篇已有、2 篇待下载。完整目录与文件身份见 [LITERATURE_CATALOG.md](LITERATURE_CATALOG.md)，本轮正文判断见 [V2_INTAKE_AND_DCIM_REVIEW.md](V2_INTAKE_AND_DCIM_REVIEW.md)。','',
 '## 请下载','']
for sid in ['SDCIM-04','SDCIM-05']:
    s=ss[sid];dl += [f'- [ ] **{sid} — {s["title"]}**；{s["year"]}；{s["venue"]}',
      f'  - DOI：[https://doi.org/{s["doi"]}](https://doi.org/{s["doi"]})。',
      '  - 官方/合法入口：'+'；'.join(f'[入口 {i+1}]({u})' for i,u in enumerate(s['access_urls']))+'。',
      f'  - 建议保存路径：`{s["target_path"]}`',
      '  - 为何需要：'+s['purpose'],
      '  - 下载内容：'+s['manual_request_contents'],
      '  - 日期/版本：'+s['publication_note'],
      '  - 当前情况：仅题录与官方摘要已核验，尚未读取全文；完整精度、周期、阵列/写口边界仍待检查。']
    if sid=='SDCIM-04':dl+=['  - 核查重点：signed INT8 的完整 MAC 服务；精度可调模式下的输出/时序差异；不要先视为所有配置都 lossless。']
    else:dl+=['  - 避免重复：只要 2026 JSSC 期刊版（13 页，5098–5110；完整 Early Access 版也可），**不用再下同主题 ISSCC 2025 14.5**。转置/反向传播不自动证明普通权重写周期更快。']
    dl+=['']
dl+=['## 已关闭的 V2 请求','',
 '| 包 | 状态 |','|---|---|',
 '| SACIM-05 | 5 页主文已核验，四组 2-bit DAC/GBL combining 有用 |',
 '| RRAM-06 | 2 页主文已核验，保留写入方法；时间归一化，不当绝对 page 延时 |',
 '| PCM-06 | 8 页主文已核验，逐行闭环及 FPGA 控制明确 |',
 '| MRAM-06 | 24 页主文/Extended Data 与 15 页 SI 均齐 |',
 '| PCM-04-SI | 18 页方法与 Figs.S1–S11 已齐 |','',
 '其他技术缺口暂没有经核实、明确需要用户再取的文件；不再列泛泛候补。原因见本轮报告。收到这两篇后先核对正文，不自动进入正式参数计算。','']
(B/'DOWNLOAD_REQUESTS_V1.md').write_text('\n'.join(dl))

for g in m['groups']:
    (B/'literature'/g['directory']/'README.md').write_text('# '+g['title']+'\n\n身份、用途、当前状态与规范文件名见 [文献目录](../../LITERATURE_CATALOG.md)。\n\n当前下载任务见 [V3 清单](../../DOWNLOAD_REQUESTS_V1.md)；全文下载由用户负责。PDF 已按用户设置允许纳入 Git；versions/comparisons 的资料不重复计为独立核心证据。\n')
print(json.dumps(m['counts'],ensure_ascii=False))

"""Build R0 navigation from reviewed selections and preserved identity records.

No extraction of timing values and no estimation. Writes only inside rebuild/.
"""
from pathlib import Path
import collections
import hashlib
import html
import json
import logging
import re
import shutil

import pdfplumber
from catalog_data import GROUPS, SHARED, SOURCES, FIRST_BATCH_ORDER

logging.getLogger('pdfminer').setLevel(logging.ERROR)
BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
REL = BASE.relative_to(REPO).as_posix()
OLD_BASE = BASE.parent
OLD = {x['source_id']: x for x in json.loads((OLD_BASE / 'sources/manifest.json').read_text())}
DATE = '2026-09-08'


def clean(value):
    for _ in range(2):
        value = html.unescape(value)
    value = re.sub(r'<sup>(.*?)</sup>', r'^\1', value, flags=re.S)
    value = re.sub(r'<[^>]+>', '', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return re.sub(r'\s+\^', '^', value)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def pdf_check(path):
    assert path.is_relative_to(BASE), path
    assert path.read_bytes().startswith(b'%PDF-'), path
    with pdfplumber.open(path) as p:
        n = len(p.pages)
        assert n > 0
        # Parse all page dictionaries; identity text is checked on first two pages.
        for page in p.pages:
            assert page.width > 0 and page.height > 0
        identity_text = '\n'.join((p.pages[i].extract_text() or '') for i in range(min(2, n)))
    return dict(path=path.relative_to(REPO).as_posix(), pages=n,
                bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                validation='PDF signature, all page dimensions, first-two-page text; title manually screened',
                first_page_text_present=bool(identity_text.strip()))


def stamp_link(publisher_url):
    match = re.search(r'ieeexplore.ieee.org/document/(\d+)', publisher_url)
    return 'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=' + match[1] if match else None


guc = BASE / 'literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf'
if not guc.exists():
    shutil.copy2(BASE / 'tmp/GUC_IGADACT01C.pdf', guc)

related_files = {
    'SACIM-03': dict(temp='SACIM-03_ISCAS2022.pdf', filename='SACIM-03_2022_Hierarchical_Attenuator_ISCAS.pdf',
                     title='A Computing-in-Memory SRAM Macro Based on Fully-Capacitive-Coupling With Hierarchical Capacity Attenuator for 4-b MAC Operation',
                     year=2022, venue='IEEE ISCAS 2022，会议公开稿',
                     url='https://confcats-event-sessions.s3.amazonaws.com/iscas22/papers/1140.pdf',
                     relation='相关会议前作，明确为仿真且已有 input-sparsity ADC；同团队／相近结构不另计独立来源，2023 扩展的内容差异仍需核查。'),
    'SDCIM-03': dict(temp='SDCIM-03_AuthorSlides.pdf', filename='SDCIM-03_2022_DynamicLogic_INT8_AuthorSlides.pdf',
                     title='A 1.041Mb/mm2 27.38TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-Less SRAM Compute-In-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications',
                     year=2022, venue='作者公开报告，ISSCC 2022 paper 11.7，ICAC 2022 托管',
                     url='https://www.icacworkshop.cn/2022/slides/ICAC_2022_14.3_Yan_Bonan.pdf',
                     relation='同篇论文的 35 页作者报告；提供原作者图和实现说明，不冒充正式主文；可先审阅，正式版暂缓。'),
}

records = []
for selected in SOURCES:
    s = dict(selected)
    sid = s['source_id']
    old = OLD.get(s.get('old'))
    if old:
        for key in ['title', 'authors', 'venue', 'doi', 'official_url', 'version']:
            if old.get(key) is not None:
                s.setdefault(key, old[key])
        s.setdefault('access_urls', [])
        if old.get('access_url') and old['access_url'] not in s['access_urls']:
            s['access_urls'].append(old['access_url'])

    cf = BASE / 'metadata' / f'{sid}_crossref.json'
    query = BASE / 'metadata' / f'{sid}_crossref_query.json'
    m = None
    if cf.exists():
        m = json.loads(cf.read_text())['message']
    elif 'crossref_query_index' in s:
        cf = query
        m = json.loads(cf.read_text())['message']['items'][s['crossref_query_index']]
    if m:
        # Preserve manually checked PDF titles for Zhou's math / metadata corruption.
        if not sid.startswith('FENOR-0') or sid not in ['FENOR-01', 'FENOR-02']:
            s.setdefault('title', clean(m['title'][0]))
        s.setdefault('authors', [clean(' '.join(filter(None, [a.get('given'), a.get('family')]))) or a.get('name', '')
                                 for a in m.get('author', [])])
        s['doi'] = m['DOI']
        s.setdefault('venue', clean(m.get('container-title', [''])[0]))
        s['publication_dates'] = {k: v['date-parts'] for k, v in m.items()
                                  if k in ['published', 'published-print', 'published-online', 'issued'] and 'date-parts' in v}
        dp = m.get('published', m.get('issued', {})).get('date-parts', [[]])[0]
        s.setdefault('publication_date', '-'.join(str(x).zfill(2) for x in dp))
        s['publisher_url'] = m.get('resource', {}).get('primary', {}).get('URL', m.get('URL')).replace('http://ieeexplore.', 'https://ieeexplore.')
        s['metadata_file'] = cf.relative_to(REPO).as_posix()
        s['identity_basis'] = '出版机构向 Crossref 登记的 DOI、题名、作者、卷期／会议日期；有本地 PDF 时另核题名与版本。'
        s['affiliations'] = list(dict.fromkeys(clean(x.get('name', '')) for a in m.get('author', []) for x in a.get('affiliation', [])))
    else:
        s['identity_basis'] = '原厂／机构文档或前轮已核验出版记录与本次 PDF／官方页面核验。'
    if sid == 'GC-02':
        s['title'] = 'An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications'
        s['identity_note'] = 'Crossref 题名的内联 LaTeX 格式规范为 VT；未改变题意。'
    if sid == 'CMOS-05':
        s['identity_note'] = '出版登记题名写作 16-GS/（缺 s）；此处保留登记形式，待正式 PDF 核对排印。'
    if sid == 'NOR-01':
        s['official_url'] = s['access_urls'][0]
    s.setdefault('doi', None)
    if s['doi']:
        s['doi_url'] = 'https://doi.org/' + s['doi']
        s.setdefault('official_url', s['doi_url'])
        s.setdefault('publisher_url', s['official_url'])
    s.setdefault('access_urls', [])
    s.setdefault('publication_date', str(s['year']) if s['year'] else None)
    s.setdefault('version', '本地正式 PDF（已核验身份）' if not old else old.get('version', ''))
    s['identity_verified'] = True
    s['verified_on'] = DATE
    s['fulltext_suitability'] = 'R0 初筛；有全文不等于已完成参数适用性审阅'
    s['package_id'] = s.get('duplicate_package', sid)
    s['shared_with'] = [g for g, ids in SHARED.items() if sid in ids]
    year_name = str(s['year']) if s['year'] else 'undated'
    path = BASE / 'literature' / s['group'] / f"{sid}_{year_name}_{s['short_title']}.pdf"
    s['target_path'] = path.relative_to(REPO).as_posix()
    s['copy_provenance'] = None
    if old and old.get('local_file'):
        origin = REPO / old['original_path'] if old.get('original_path') else OLD_BASE / old['local_file']
        if not path.exists():
            shutil.copy2(origin, path)
        sha = hashlib.sha256(origin.read_bytes()).hexdigest()
        assert sha == hashlib.sha256(path.read_bytes()).hexdigest()
        if old.get('sha256'):
            assert sha == old['sha256']
        s['copy_provenance'] = dict(original_path=origin.relative_to(REPO).as_posix(),
                                     previous_task_path=(OLD_BASE / old['local_file']).relative_to(REPO).as_posix(),
                                     previous_source_id=old['source_id'], sha256=sha, byte_identical=True)
    s['main_file'] = pdf_check(path) if path.exists() else None
    s['access_status'] = ('existing_verified' if s['copy_provenance'] else 'downloaded_verified') if path.exists() else 'metadata_or_abstract_only'
    s['access_status_zh'] = ('已有全文，已复制并核验' if s['copy_provenance'] else '本轮公开取得全文，已核验') if path.exists() else '题录／摘要可读，主文未取得'
    if sid in ['NOR-01', 'NAND-01', 'MRAM-05'] and not path.exists():
        s['access_status'] = 'public_web_pdf_no_local'
        s['access_status_zh'] = '官方 PDF 网页内容可读；本地文件未取得'
    if not path.exists():
        s['version'] = '拟获取正式主文；机构／作者接受稿内容完整也可'
    s['supplements'] = []
    supp_path = path.with_name(path.stem + '_Supplement.pdf')
    if supp_path.exists():
        supp = pdf_check(supp_path)
        supp['identity'] = '与主文题名／DOI 对应的 Supplementary Information，首页已核验'
        supp['access_status'] = 'downloaded_verified'
        article_keys = {'FERAM-05': ('s41467-024-47194-8', '41467_2024_47194'),
                        'FERAM-06': ('s41928-025-01454-7', '41928_2025_1454'),
                        'FENOR-05': ('s41467-023-36270-0', '41467_2023_36270')}
        ak, mk = article_keys[sid]
        supp['url'] = f'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2F{ak}/MediaObjects/{mk}_MOESM1_ESM.pdf'
        s['supplements'].append(supp)
        s['supplement_status'] = '已取得官方 Supplementary Information；数据／视频附件未作批量下载。'
    elif sid in ['RRAM-01', 'MRAM-01', 'PCM-02']:
        s['supplement_status'] = '主文含 Methods／Extended Data；独立补充包尚未完整核验，R1 如依赖其中信息再定向补，不重复请求主文。'
    elif not path.exists():
        s['supplement_status'] = '未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。'
    else:
        s['supplement_status'] = 'R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。'
    s['related_versions'] = []
    if sid in related_files:
        related = dict(related_files[sid])
        rpath = path.parent / related['filename']
        if not rpath.exists():
            shutil.copy2(BASE / 'tmp' / related['temp'], rpath)
        related['file'] = pdf_check(rpath)
        related['access_status'] = 'downloaded_verified'
        related.pop('temp')
        s['related_versions'].append(related)
        if not path.exists():
            s['access_status'] = 'related_fulltext_only' if sid == 'SACIM-03' else 'author_slides_only'
            s['access_status_zh'] = '相关 2022 会议前作已取得；2023 主文未取得' if sid == 'SACIM-03' else '同篇作者报告已取得；正式主文暂缺'
            s['confirmed_content'] = '已核验 2022 会议 PDF 的题名、作者和 28 nm 电荷域结构；第 III 节为 Simulation Results，已有 input-sparsity 方案；2023 扩展内容和证据类型待正式主文。' if sid == 'SACIM-03' else '已核验同篇作者 35 页报告的题名、作者与 macro 框图；正式主文的完整时序定义未审阅。'
    if sid == 'CMOS-01':
        s['related_versions'].append(dict(title='The Best Data Converter Total Solution Provider', year=2022,
            venue='GUC 2022Q3 Data Converter Portfolio', url='https://www.guc-asic.com/upload/media/2022_event/Data_Converter.pdf',
            relation='官方总览的网页索引确认 2022Q3 与 N28 IP 表；直接下载返回 HTML。具体 v002 简表已足够初筛，不再请求较粗总览。',
            access_status='web_index_only', file=None))
    if sid == 'SDCIM-01':
        version = OLD['t1_d6cim2026']
        s['related_versions'].append(dict(title=version['title'], year=2026, venue=version['venue'],
            doi=version['doi'], url='https://doi.org/' + version['doi'],
            relation='期刊扩展版题录线索；会议稿已足够 R0，暂不重复请求或另计独立证据。', file=None,
            access_status='metadata_only'))
    if sid in ['GC-02', 'GC-04', 'GC-05']:
        items = json.loads(query.read_text())['message']['items']
        related_index = 1 if sid == 'GC-02' else 0
        x = items[related_index]
        s['related_versions'].append(dict(title=clean(x['title'][0]), year=x['published']['date-parts'][0][0],
            doi=x['DOI'], url='https://doi.org/' + x['DOI'], venue=clean(x.get('container-title', [''])[0]),
            relation='相关会议版；优先本条期刊文，不同时索取，不增加独立证据数。', file=None, access_status='metadata_only'))
    if sid in ['FENOR-03', 'FENOR-04']:
        s['version_relation'] = 'FENOR-03／04 同团队直接相关系列，保守合为一个资料包；实验复用关系须全文核验。优先 FENOR-04。'
    if sid == 'NAND-04':
        s['older_reason'] = '直接连接 NAND 物理组织与 CIM 外围的 codesign 方法；虽略超五年仍提供缺少的估算桥梁。'
    s.setdefault('confirmed_content', '仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。')
    if s.get('family'):
        s['independence_note'] = '相关实验／团队族：' + s['family'] + '；同族条目不自动视作独立交叉验证。'
    s['request_batch'] = 'A' if sid in FIRST_BATCH_ORDER else ('B' if not s['main_file'] and not s.get('duplicate_package') else None)
    s['manual_request_contents'] = ('指定 ' + s['document_id'] + ' PDF；若门户改版，请保留实际修订号。') if s.get('document_id') else '主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。'
    if sid == 'NAND-04':
        s['manual_request_contents'] = '完整主文 PDF，特别是 Table 1 原图；如有补充材料一并获取。'
    if sid == 'SACIM-03':
        s['manual_request_reason'] = '2022 会议前作已自动取得，明确为仿真且已有 input-sparsity 方案，足够 R0 初筛。暂缓 2023 期刊文，R1 仅在前作不能覆盖所需条件时再补，核查扩展差异。'
    elif sid == 'FENOR-04':
        s['manual_request_reason'] = '优先较完整的期刊文；2024 会议版 FENOR-03 先不下载。公开接受稿 URL 已尝试，服务器返回 HTTP 418。'
        s['access_urls'].append('https://ieeexplore.ieee.org/ielam/16/11004132/10957835-aam.pdf')
    else:
        s['manual_request_reason'] = s['purpose']
    records.append(s)

byid = {s['source_id']: s for s in records}
assert len(byid) == len(records)
assert all(byid[sid]['main_file'] is None for sid in FIRST_BATCH_ORDER)
assert 15 <= len(FIRST_BATCH_ORDER) <= 20
assert len({s['doi'].lower() for s in records if s['doi']}) == sum(bool(s['doi']) for s in records)
stats = dict(candidate_records=len(records), source_packages=len({s['package_id'] for s in records}),
             existing_main=sum(s['access_status'] == 'existing_verified' for s in records),
             automatically_obtained_main=sum(s['access_status'] == 'downloaded_verified' for s in records),
             local_main=sum(bool(s['main_file']) for s in records),
             automatically_obtained_supplements=sum(len(s['supplements']) for s in records),
             automatically_obtained_related_documents=sum(bool(v.get('file')) for s in records for v in s['related_versions']),
             first_batch_packages=len(FIRST_BATCH_ORDER), deferred_packages=sum(s['request_batch'] == 'B' for s in records))
manifest = dict(schema_version='1.0-r0', stage='R0', checked_on=DATE,
                status='R0 文献准备完成，等待用户补充第一批全文',
                scope='文献筛选、身份／版本核验、公开文件获取、归档、人工下载组织；未进行参数提取或吞吐计算',
                baseline=json.loads((BASE / 'metadata/baseline.json').read_text()), counts=stats,
                groups=[dict(directory=g, title=title, introduction=intro, shared_sources=SHARED.get(g, [])) for g, title, intro in GROUPS],
                sources=records)
write_json(BASE / 'source_manifest.json', manifest)


def source_link(sid):
    return f'[{sid}](LITERATURE_CATALOG.md#{sid.lower()})'


def link_pdf(p):
    relative = Path(p).relative_to(REL).as_posix()
    return f'[{Path(p).name}]({relative})'


def links(s):
    out = []
    if s.get('doi'):
        out.append(f"[DOI: {s['doi']}]({s['doi_url']})")
    if s.get('publisher_url') and s['publisher_url'] != s.get('doi_url'):
        out.append(f"[出版页面]({s['publisher_url']})")
    if s.get('official_url') and s['official_url'] not in [s.get('doi_url'), s.get('publisher_url')]:
        out.append(f"[官方页面]({s['official_url']})")
    for i, u in enumerate(s['access_urls']):
        if u not in [s.get('doi_url'), s.get('official_url'), s.get('publisher_url')]:
            out.append(f'[机构／作者／原厂入口 {i + 1}]({u})')
    return ' · '.join(out)


def table_row(key, value):
    return f"| {key} | {str(value).replace('|', '／').replace(chr(10), ' ')} |"


cat = ['# R0 文献候选目录', '', f'核验日期：{DATE}。{len(records)} 条候选记录，按明确版本关系保守归并为 {stats["source_packages"]} 个资料包；资料包数量不等于独立实验数量。', '',
       f'现有主文 {stats["local_main"]} 份（仓库复用 {stats["existing_main"]}，本轮公开取得 {stats["automatically_obtained_main"]}）；另归档 {stats["automatically_obtained_supplements"]} 份补充材料、{stats["automatically_obtained_related_documents"]} 份会议前作／作者报告。', '',
       '本目录回答“可支持哪一块后续估算”，不要求单篇闭合两路吞吐。全文可用只表示可进入审阅，不表示已经确认其中参数可直接用于共同参考。P1 为关键依据，P2 为互补／交叉核查，P3 为相关版本或候补；人工顺序另见 [下载清单](DOWNLOAD_REQUESTS_V1.md)。', '',
       '年份采用实际卷期／会议或 datasheet 修订时间，公开稿日期另记。GUC v002 未署日期，保留 undated，未把上传路径日期当发表年。旧文保留理由逐项说明。所有原始 PDF 仅本地使用，由本任务 [.gitignore](.gitignore) 排除。', '', '## 分组入口', '']
for g, title, intro in GROUPS:
    own = [s for s in records if s['group'] == g]
    cat.append(f'- [{title}](#{g})：{len(own)} 条主归属' + (f' + {len(SHARED[g])} 条共享引用' if g in SHARED else ''))
for g, title, intro in GROUPS:
    cat += ['', f'<a id="{g}"></a>', '', f'## {title}', '', intro, '']
    if g in SHARED:
        cat += ['共享：' + '、'.join(source_link(x) for x in SHARED[g]) + '。只保存一份主文件，身份和路径见其主资料卡。', '']
    for s in [x for x in records if x['group'] == g]:
        sid = s['source_id']
        authors = '；'.join(s['authors'][:3]) + (' 等（完整作者见 manifest）' if len(s['authors']) > 3 else '')
        cat += [f'<a id="{sid.lower()}"></a>', '', f'### {sid} — {s["title"]}', '', '| 字段 | 内容 |', '| --- | --- |',
                table_row('身份／日期', f'{authors}；{s["venue"]}；{s["publication_date"] or "发行日期未署"}'),
                table_row('链接', links(s)), table_row('用途标签', '；'.join(s['roles'])),
                table_row('预期支撑', s['purpose']), table_row('层级／优先级', s['evidence_level'] + '；' + s['priority']),
                table_row('工艺／状态边界', '；'.join(filter(None, [s.get('process_class'), s.get('state_mode')])) or '按具体实现核查；未声明统一 28 nm'),
                table_row('访问与判断', s['access_status_zh'] + '。' + s['confirmed_content']),
                table_row('主文位置', link_pdf(s['target_path']) if s['main_file'] else '拟下载：`' + s['target_path'] + '`'),
                table_row('版本／附件', s['version'] + '；' + s['supplement_status'])]
        if s.get('identity_note'):
            cat.append(table_row('身份核验说明', s['identity_note']))
        if s.get('publication_note'):
            cat.append(table_row('日期说明', s['publication_note']))
        if s.get('older_reason'):
            cat.append(table_row('旧资料保留理由', s['older_reason']))
        if s.get('independence_note') or s.get('version_relation'):
            cat.append(table_row('交叉证据边界', ' '.join(filter(None, [s.get('independence_note'), s.get('version_relation')]))))
        if s['copy_provenance']:
            cat.append(table_row('复制来源', '`' + s['copy_provenance']['original_path'] + '`；逐字节 SHA-256 一致，原文件保留；前轮 ID：' + s['old']))
        if s['supplements']:
            cat.append(table_row('本地补充材料', '；'.join(link_pdf(v['path']) for v in s['supplements'])))
        for v in s['related_versions']:
            label = f'{v["year"]} — {v["title"]}；{v["relation"]} [官方／作者入口]({v["url"]})'
            if v.get('file'):
                label += '；本地：' + link_pdf(v['file']['path'])
            cat.append(table_row('相关版本', label))
        cat.append('')
cat += ['## 筛除与未纳入', '',
        '- 前轮 Ambit、Dyamond 和普通 1T1C eDRAM-CIM 不属于本轮 gain-cell 类别；未新增独立 DRAM 类别。',
        '- 传统 PZT 商用 F-RAM datasheet 不用于 HfO₂ FeRAM 核心证据。',
        '- 检索中的 single-finger eDRAM 2024 条目尚未确认符合 gain-cell 结构，未为凑数列入精选；题录搜索记录只供追溯。',
        '- 未经核实的 memory compiler 手册镜像、无时序／结构内容的厂商宣传页和 SSD 总吞吐未用于共同局部服务基线。',
        '- 不把同团队会议／期刊扩展版、作者稿与正式版计算为独立的第三方交叉验证。', '']
(BASE / 'LITERATURE_CATALOG.md').write_text('\n'.join(cat))

req = ['# 第一轮人工下载清单（V1）', '',
       f'已有并核验：**{stats["existing_main"]} 份主文**；本轮自动取得并核验：**{stats["automatically_obtained_main"]} 份主文 + {stats["automatically_obtained_supplements"]} 份补充材料 + {stats["automatically_obtained_related_documents"]} 份会议前作／作者报告**。这些文件均已归档，不需要重复下载。', '',
       f'第一批请协助取得 **{stats["first_batch_packages"]} 个资料包**；其余 **{stats["deferred_packages"]} 个**先暂缓。FENOR-03 与 FENOR-04 合包，先取期刊版；已取得的接受稿不另外请求内容相同正式版。', '',
       f'请放入 `{REL}/literature/` 下对应分类目录，具体文件名逐项给出。所有路径均从仓库根目录开始。补充材料按同名 `_Supplement.pdf` 保存；出版社若提供 ZIP 则用 `_Supplement.zip`。若已下载文件采用不同名字，可在回复中列 ID 与实际文件名，不必修改内容。', '',
       '主文完整、题名和作者匹配的作者接受稿也可；无需绕过权限。若某项没有补充文件，只交主文即可。第一批到件后再由用户启动 R1；当前不进入正式参数提取。', '',
       '优先顺序考虑证据缺口和互补性，不按每类平均分配。共同外围的 ADC 已有两篇全文、DAC IP 已取得；第一批补 DAC 负载机制、SRAM 普通读写及实际 CIM 读出连接，再补各介质关键阵列依据。', '',
       '## A. 第一批优先下载', '']


def request_card(s):
    out = [f'- [ ] **{s["source_id"]} — {s["title"]}**；{s["year"] or "未署日期"}；{s["venue"]}']
    if s.get('doi'):
        out.append(f'  - DOI：[{s["doi"]}]({s["doi_url"]})')
    entry = s.get('publisher_url') or s['official_url']
    out.append(f'  - 官方页面：[出版／原厂入口]({entry})')
    stamp = stamp_link(entry)
    alternatives = [u for u in s['access_urls'] if u not in [entry, s.get('doi_url')]
                    and u != 'https://people.eecs.berkeley.edu/~krste/papers/zimmer-ieeetcasII-2012.pdf']
    if stamp and stamp not in alternatives:
        alternatives.insert(0, stamp)
    if alternatives:
        out.append('  - 备用合法入口：' + '；'.join(f'[入口 {i + 1}]({u})' for i, u in enumerate(alternatives)))
    out += [f'  - 建议保存路径：`{s["target_path"]}`',
            f'  - 为何需要：{s["manual_request_reason"]}',
            f'  - 下载内容：{s["manual_request_contents"]}',
            f'  - 当前情况：{s["access_status_zh"]}。' + (s.get('identity_note') or '已核验出版身份；全文适用性和完整时序尚待审阅。'), '']
    return out


for sid in FIRST_BATCH_ORDER:
    req += request_card(byid[sid])
req += ['## B. 暂缓候补（现在不必下载）', '',
        '以下资料仍有价值，但先用已有全文和第一批内容判断具体缺口。这里列出可点击入口和最终路径，避免以后重新找题名。SDCIM-03 作者报告已取得，正式主文可暂缓；FENOR-03 仅为同包版本线索。', '']
for s in records:
    if s['request_batch'] == 'B':
        req += request_card(s)
req += ['### 同包版本线索：先不发重复任务', '',
        f'- FENOR-03：{links(byid["FENOR-03"])}。优先 FENOR-04；仅当期刊未覆盖所需器件细节时再取会议版。拟保存 `{byid["FENOR-03"]["target_path"]}`。', '',
        '取得文件后，请告知已完成的 ID。无需先提取数字、整理参数或替本轮决定统一外围延时。', '']
(BASE / 'DOWNLOAD_REQUESTS_V1.md').write_text('\n'.join(req))

COVER = [
    ('00_cmos_periphery', 'CMOS-02 ADC 实测；CMOS-06 ADC 后仿真；CMOS-04 感测待全文', 'CMOS-03／04（普通 SRAM）；CMOS-01／05（输入驱动，不代表介质编程）', 'CMOS-03／04；compiler 的公开负载／PVT 库仍缺', 'ADC: CMOS-02／06；DAC: CMOS-01／05；数字: SDCIM-01；CIM 感测设计: SACIM-03', 'ADC 实测与另一团队模型、GUC 与独立 DAC、两类 SRAM 基础；实际负载适配尚未确认'),
    ('01_sram_acim', 'SACIM-01／02；SACIM-03／04 待主文', 'CMOS-03／04 候选；各 CIM macro 写口细节仍缺', 'SACIM-01／02；不同 bit phase／ADC 共享需区分', 'SACIM-03 直接 28 nm（2022 前作已得）；CMOS-01／02／06', 'Princeton、PICO-RAM、PKU、Intel 多种结构；跨节点不直接等同'),
    ('02_sram_dcim', 'SDCIM-01；SDCIM-03 作者报告；SDCIM-02 待主文', 'SDCIM-01 写口；CMOS-03／04 完成周期待补', 'SDCIM-01／02／03；位串行与完整精度分开', 'SDCIM-01／03 直接 28 nm 数字求值；完整精度服务间隔待审', 'D6CIM、动态逻辑、可重构数字 macro；不是一实现配对限制'),
    ('03_nor_2d', 'NOR-02／03；NOR-01 网页 PDF', 'NOR-02／03 普通 program/erase；NOR-05 模拟反馈', 'NOR-01／02／03 字／页／buffer／sector；NOR-05 小阵列', 'NOR-04／05 连接模拟 NOR；共同电压驱动仍需适配', '三家产品；NOR-04／05 同技术族不算独立团队'),
    ('04_nand_3d', 'NAND-01 网页简表；NAND-02／03 待全文；SLC 直接基线缺', 'NAND-01 MLC/TLC；NAND-02／03 QLC；完整循环约束待审', 'NAND-01／02／03 页／块／plane／die 分层', 'NAND-04／05 候选；codesign Table 1 原图缺', 'Micron／KIOXIA／SK hynix 不同厂商；状态模式不能混合'),
    ('05_rram', 'RRAM-01／02；RRAM-04 产品时序；RRAM-05 感测待主文', 'RRAM-01／02 完整编程线索；RRAM-03／04 产业来源', 'RRAM-01／02／04；差分、写 buffer、外部控制分开', 'RRAM-01／02／05；28 nm 专用读出不覆盖全部介质', 'Weebit／CEA-Leti、Fujitsu、多个 CIM 团队；RRAM-03 时间充分性待审'),
    ('06_mram', 'MRAM-01；MRAM-02／03／04 候选', 'MRAM-01；MRAM-03 自终止写；MRAM-05 产品语义', 'MRAM-01／02；1T1MTJ、2T2MTJ、封装接口分层', 'MRAM-01 电阻求和／TDC；MRAM-02 集成 spintronic', 'Samsung、Chiu、Dong、Yang、Everspin；器件／单元机制分开'),
    ('07_pcm', 'PCM-01／02；PCM-03 macro 待全文', 'PCM-01／02 编程组织；PCM-05 SET/RESET；PCM-04 条件器件', 'PCM-01 writehead、PCM-02 tile；PCM-03 SLC/MLC', 'PCM-01／02／03；外围仿真／测量分开', 'PCM-03 TSMC、PCM-05 ST；PCM-01／02 同 IBM 平台相关'),
    ('08_feram_hfo2', 'FERAM-01／06 FeCAP；FERAM-02／03／04 阵列待主文', 'FERAM-05 器件；FERAM-06 阵列；恢复／判读终点待审', 'FERAM-02／03 1T1C、FERAM-04 大阵列、FERAM-06 FeCAP 支路', 'FERAM-01 2T2C 计算桥接；不可把独立 FeCAP 实验说成完整 macro', 'Sony／SK hynix／Micron 候选 + 两组材料／阵列全文；无 PZT 替代'),
    ('09_gain_cell_edram', 'GC-01；GC-02 实测存储、GC-04／05 CIM 待主文', 'GC-02／04 候选；GC-03 设计方法；刷新成本待审', 'GC-01 2T1C；GC-02 4T；GC-04 3T1C；GC-03 oxide 模型', 'GC-01／04／05 CIM；GC-02 28 nm 存储与 GC-03 模型分开', 'gain-cell 存储与多种 CIM／oxide 结构互补；跨结构仅条件核查'),
    ('10_fenor_3d', 'FENOR-01／02 指定原稿；FENOR-05 为 FeNAND，不直接代表 NOR 读出', 'FENOR-01／02；FENOR-03／04／06 候选；FENOR-05 条件性器件编程', 'FENOR-02 AND-type 选择／扰动；FENOR-01 NOR；FENOR-05 串联 FeNAND', 'FENOR-04 直接 FeNOR-CIM 桥接缺全文；共同驱动尚未定', 'FENOR-03／04 同包；FENOR-01／02／06 同团队；FENOR-05 仅独立垂直集成／器件对照'),
]


def ref_ids(text):
    # Turn both the leading ID and abbreviated /NN runs into real source links.
    def repl(m):
        prefix, suffix = m.group(1), m.group(2)
        return '／'.join(source_link(prefix + '-' + n) for n in suffix.split('／'))
    return re.sub(r'\b(CMOS|SACIM|SDCIM|NOR|NAND|RRAM|MRAM|PCM|FERAM|GC|FENOR)-(\d{2}(?:／\d{2})*)', repl, text)


coverage = ['# R0 文献覆盖与真实缺口', '',
            '**本矩阵只表示来源准备程度。候选存在 ≠ 已有全文 ≠ 已确认可用于计算。** 所有格子均是待 R1 核查的支撑路径，没有计算新范围。主文可用数包括共享来源，不能跨行相加。', '',
            '| 类别 | 读侧 | 写侧／更新 | 操作粒度／并行条件 | 外围或求值桥接 | 交叉验证 | 当前全文可用性 |',
            '| --- | --- | --- | --- | --- | --- | --- |']
for g, *cells in COVER:
    ss = [s for s in records if s['group'] == g or s['source_id'] in SHARED.get(g, [])]
    available = [s for s in ss if s['main_file']]
    partial = [s for s in ss if not s['main_file'] and any(v.get('file') for v in s['related_versions'])]
    availability = f'{len(available)}/{len(ss)} 条主文可用：' + ('、'.join(source_link(s['source_id']) for s in available) or '暂无本地主文')
    if partial:
        availability += '；另有相关稿／作者报告：' + '、'.join(source_link(s['source_id']) for s in partial)
    title = next(title for group, title, _ in GROUPS if group == g)
    coverage.append('| ' + ' | '.join([title] + [ref_ids(x) for x in cells] + [availability]) + ' |')
coverage += ['', '## 共同 28 nm 外围：覆盖的边界', '',
             '- ADC：CMOS-02 有实测芯片与 PVT 后仿真，CMOS-06 仅为另一团队的 28 nm 后仿真设计。分辨率、精度与转换机制有全文，但不能将二者都称作实测证据；CIM 输入负载、保持方式及适用模式尚未判定。',
             '- DAC／输入驱动：CMOS-01 为官方 28 nm IP 简表，输出类别与合规范围有依据，但未公开指定 CIM 负载的建立曲线；CMOS-05 原始电路补机制，第一批取全文判断是否适配。',
             '- sensing／mux／普通 SRAM 写入：CMOS-03／04 为 28 nm 基础设计与实际 macro；需要全文补局部负载、PVT、端口和冲突条件。公开 compiler 保证时序仍缺，不能用模糊商业接口替代。',
             '- 数字求值／控制：SDCIM-01 会议全文与 SDCIM-03 作者报告可启动后续审阅；必须明确位串行展开、累加和规定精度输出服务。',
             '- 介质专用驱动：NOR/NAND 擦写高压、RRAM/PCM 编程与 verify、MRAM 自终止写、FeCAP 判读恢复、FeFET 选择／扰动、gain-cell refresh 各自保留。共同 ADC/DAC 资料不抹掉这些物理代价。', '',
             '## 到件后仍须决定的共同条件（本轮不定数值）', '',
             '1. 局部 sub-array／macro 服务边界：输入接收、驻留写入、规定输出完成到哪里；多个 bank 是否为同一逻辑服务。',
             '2. 逻辑行列尺寸、输入／驻留精度、输出精度和状态编码；二值与多级分情景，而非混成一个材料固有数字。',
             '3. ADC／DAC／数字累加的共享与并行服务方式；采样率、latency、稳态 service interval 及填充排空如何区分。',
             '4. 更新模式：字／页／块，直接更新或显式擦除＋编程＋verify；单脉冲与完成目标状态的全部步骤分别记录。',
             '5. PVT、输入摆幅和负载：哪些为统一 28 nm 条件，哪些保留介质专用高压／驱动／感测约束；不先固定精细延时链。',
             '6. refresh、restore、校准、保持与寿命约束的处理边界；内部维护不计成新的 workload payload。', '',
             '## 第一轮之后的实际缺口', '',
             '- NAND 当前没有本地主文；优先 Micron 明确 MLC/TLC 的原厂资料、两家 QLC 芯片和 codesign 完整图表。SLC 专用模式及公开完整器件 datasheet 仍缺，R1 后定向补，不能用 SSD 性能补洞。',
             '- HfO₂ FeRAM 已有器件／CIM 方案，但实际 1T1C 阵列的读、恢复、写入完整边界仍依赖第一批产业论文。',
             '- gain-cell 有 2T1C CIM 与 oxide 设计全文；普通 28 nm gain-cell 实测存储和多级写入完成条件等待 GC-02／04。',
             '- 3D FeNOR 已有两篇指定原稿及独立三维 FeFET 全文。直接 FeNOR-CIM 桥接与另一个 FeNOR 团队的证据仍需 FENOR-04；不因不同结构都叫 FeFET 就合并计时。',
             '- 28 nm DAC 的给定 CIM 负载建立条件与公开 memory compiler 时序是共同缺口；现有资料不足以现在选定唯一统一外围延时。', '',
             '这些缺口不表示该介质不可估算，只表示后续要补全文、选择参考情景或明确条件。无需用户现在先决定数值；当前操作是补第一批文件。', '']
(BASE / 'COVERAGE.md').write_text('\n'.join(coverage))

readme = f'''# Task 1-R0 — 统一 28 nm 外围参考的文献准备

**状态：R0 文献准备完成，等待用户补充第一批全文**

核验日期：{DATE}。本轮以本地实际 HEAD `5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c` 为起点，初始 Git 状态干净。理论检查点 `6817194a3be1ba18ad2c3eb9273bb25a0fa470c2` 只用于理解基线，未回退。

## 现在使用的入口

- [全部精选候选目录](LITERATURE_CATALOG.md)：共同 CMOS 组在前，随后严格十类介质；每项有用途、层级、版本和访问状态。
- [第一轮人工下载清单](DOWNLOAD_REQUESTS_V1.md)：先完成 A 批 {stats['first_batch_packages']} 个资料包，B 批 {stats['deferred_packages']} 个暂缓。
- [覆盖矩阵与真实缺口](COVERAGE.md)：有候选、有全文和可用于计算是三件不同的事。
- [资料根目录](literature/) 与 [机器可读来源登记](source_manifest.json)。
- [核验与访问记录](metadata/VERIFICATION.md)。

## 当前归档量

| 项目 | 数量／说明 |
| --- | --- |
| 精选记录 | {stats['candidate_records']} 条；保守归并 {stats['source_packages']} 个资料包，不代表同数目的独立实验 |
| 从仓库复用并核验的主文 | {stats['existing_main']} 份 |
| 本轮自动取得并核验的主文 | {stats['automatically_obtained_main']} 份 |
| 主文可用合计 | {stats['local_main']} 份 |
| 自动取得的补充材料 | {stats['automatically_obtained_supplements']} 份 |
| 自动取得的相关会议前作／作者报告 | {stats['automatically_obtained_related_documents']} 份；不计新独立来源 |
| 第一批人工下载 | {stats['first_batch_packages']} 个资料包 |
| 暂缓候补 | {stats['deferred_packages']} 个资料包；另列 FENOR-03 同包版本，不重复索取 |

计数按“本目录选定主文”定义：SACIM-03 的 2022 会议前作、SDCIM-03 的作者报告单列，没有冒充所登记正式主文。Zhou 2025／2026 从仓库根目录原文件复制，原路径、前轮路径与 SHA-256 对应关系保存在 manifest；根目录文件不动。

## 本轮采用的研究边界

目标是为共同 28 nm 外围条件下的小型 CIM 参考设计估算准备可互补的依据，不是已制造芯片排名。器件／阵列时间、更新步骤、并行粒度、外围服务与换算方法可以由不同来源支撑；不再沿用“单篇没有完整 streaming／resident 配对就不能估算”的筛选限制。

已阅读根 README、`docs/MODEL_CONVENTIONS.md`、主论文 CIM 定义与计量约定、`CIM_Roofline_Paper/archive/task0_legacy.tex` 的硬件与 workload 定量标定，以及前轮 Task 1 来源清单、SUPPORT.zh.md、AUDIT.md 和有关原文。旧稿的“共同外围→通用方法→介质分析→汇总”用于指引选文献；未经核实的旧数字及精细延时链没有继承。

逻辑 payload、完整服务间隔、完整写入／擦除／verify 和局部边界的约定保留；参考情景的具体尺寸、精度、负载、共享及状态模式仍待决定。本轮未采集完整参数表、未拟合或计算 ρ、τ、RI*，未制作新版 Table I，也未进入 R1／R2。

## 文件放置与版本规则

按下载清单的仓库相对路径存放；主文件 `ID_Year_ShortTitle.pdf`，补充材料在同名后加 `_Supplement`。唯一例外 CMOS-01 未署发行日期，使用 `undated`，不以 URL 上传日期代替出版日期。同一来源跨组只引用一个 ID／主路径，会议／期刊版本关系单列。

原始 PDF／ZIP 由本任务 [.gitignore](.gitignore) 排除；目录、身份记录及自己的说明正常保留。生成器在 [scripts/](scripts/)；用户到件后不要盲目重跑 R0 生成器，以免把新文件未经人工核验就标记可用，应在 R1 更新状态和身份记录。

所有新内容仅位于 `tasks/task1_table_i/rebuild/`。原 Table I、Table II、主论文、共享 docs、全局 README 均未修改；未执行 git add、commit、push、checkout、reset 或 stash。用户负责最终提交。

最终 Git 检查另观察到仓库根目录 `.DS_Store` 与 `tasks/.DS_Store` 的变化，来源未判断；本任务未直接写入或恢复这两项，按要求保留当前状态。其余已跟踪研究文件没有差异，HEAD 未变。

用户现在只需补 A 批文件并告知已完成 ID。没有需要先确认才能继续下载的实质问题。后续由用户启动 R1，审阅到件全文后再决定第二批定向下载；本轮到此停止。
'''
(BASE / 'README.md').write_text(readme)
print(json.dumps(stats, ensure_ascii=False))

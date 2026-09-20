#!/usr/bin/env python3
"""Lightweight, read-only-by-default adapter of the ten native calculators.

--emit writes normalized JSON/CSV, compact result cards and one summary table.
Times are ns, exported rates are decimal MB/s; source results remain Byte/s.
No model formula or shared parameter is changed here.
"""
import argparse,csv,hashlib,io,json,math,re
from pathlib import Path
A=Path(__file__).resolve().parents[1]
META={
'01_sram_acim': dict(technology='SRAM ACIM',mode='二进制9T1C电荷域；128行求和；8位平面并行',update_pattern='同一输入行的16个输出权重，对齐16 Byte；1024事务覆盖整矩阵',resources='128 SAR、16条两拍重构通道、128对真实写驱动；沿用R0求值组织，前端合并预算',main_assumptions='参考20 ns合并前端与20 ns SAR各占读服务39.9%；普通写5 ns完整周期与DCIM同源，不再加控制拍',dominant_contrast='固定外围扫前端10/20/50 ns；64写驱动对照单列',maintenance='无周期维护；普通SRAM需持续供电',main_key='scenarios'),
'02_sram_dcim': dict(technology='SRAM DCIM',mode='二进制6T；D6CIM型16项归约、16活动输出通道',update_pattern='对齐128 bit普通写口，完成16 Byte；1024事务覆盖整矩阵',resources='8个容量分片、总128条/活动16条HCA-BFA；R0的32项改16项；完整MAC槽覆盖静态读/保持',main_assumptions='512个完整MAC槽、64次行组选择；参考5 ns计算槽与5 ns普通写槽独立，静态连接不另付重读',dominant_contrast='32项同钟资源对照；额外握手仅适用于边界改变',maintenance='无周期维护；普通SRAM需持续供电',main_key='scenarios'),
'03_nor_2d': dict(technology='2D NOR Flash',mode='binary本地感测＋精确数字归约；非实测模拟CIM宏',update_pattern='整矩阵16384 Byte任意重写：4次sector擦除、64次256 Byte页编程；非任意小字写吞吐',resources='32读分片、每片128 SA，共4096 SA；每sector容纳8读片；读并行与擦除域分开',main_assumptions='参考120 ns为商品随机读周期桥接的本地读槽；写侧87.5%为擦除；完整P/E终点保留',dominant_contrast='32独占sector对照；固定其余条件读槽±20%',maintenance='无另列周期维护；擦除已含resident服务',main_key='scenarios'),
'04_nand_3d': dict(technology='3D NAND',mode='SGVC SLC c=1；SL电流积分ACIM；持续同地址重写',update_pattern='16384 Byte整矩阵：1024数据页＋256参考页＋128块擦；每数据页仅16 Byte位片段，8页凑128个INT8权重',resources='128路积分前端/SAR、每路新增16 pF、16重构通道＋128校正乘法器；单更新域，保留原生页/块',main_assumptions='固定0.4 V、2 nA得25 μs积分，约95%读占用；参考P=2.5 ms、E=30 ms为完整操作移植预算',dominant_contrast='已有c=108资源/信号对照；预擦除append仅有限窗口',maintenance='参考页重建及三读校准含resident，不增加payload',main_key='main_scenarios'),
'05_rram': dict(technology='RRAM',mode='HRS/LRS二状态32项ACIM；16-lane两相写验',update_pattern='16 Byte为同输出WL、两个列组各8个完整INT8权重；8批×16cell；互补组选通共1024事务覆盖矩阵',resources='128 SAR、16重构通道、16耐压限流写驱动、32窗口比较器；实际写并行度独立于128bit接口',main_assumptions='1 μs脉冲、前后各1 μs HV预留；参考RESET/SET为2/1次，HV余量占写服务约66%',dominant_contrast='固定参考外围单独扫1/1、2/1、4/2尝试；W1资源及前端对照',maintenance='无另列周期维护；完整RESET/SET、窗口读验与恢复已计入',main_key='scenarios'),
'06_mram': dict(technology='MRAM',mode='互补2T2MTJ二状态数字路径；两相写＋双支路终验',update_pattern='8 Byte对齐组＝64互补bit对；2048事务覆盖矩阵；先两MTJ置P，再择一AP并验两支路',resources='4096活动读对；128方向写支路、64单端绝对P/AP验收lane、128bit状态锁存',main_assumptions='一次完整尝试为主点；参考两写槽占60/95 ns；重写对照保留失败尝试时间，非裸脉冲',dominant_contrast='同外围一次额外整组重写，ΔR=180 ns',maintenance='无周期维护；终验/返回包括在事务内',main_key='scenarios'),
'07_pcm': dict(technology='PCM',mode='SLC二状态8行电压式ACIM；32-IDAC对角写入',update_pattern='32 Byte为对角选通，非任意连续32 Byte；d=0…127、s=0…3，512事务无重复覆盖矩阵',resources='128 SAR、16重构通道、32实际IDAC与行/对角选通；8位平面、每向量1024轮',main_assumptions='参考SET/RESET占写时间73%；8行组织增加读轮次使ρ及ridge较低，不能推出普适动态工作负载优势',dominant_contrast='主二态终验与768 ns弱信号前端分开；SET总250/300 ns解释对照',maintenance='无另列周期维护；完整波形、驱动预留与终验在resident内',main_key='paired_scenarios'),
'08_feram_hfo2': dict(technology='HfO₂ FeRAM',mode='HZO 1T1C二状态数字路径；已有读码跨8输入位复用',update_pattern='128bit完整局部行＝16 Byte；1024行事务覆盖矩阵；每次真实破坏读均整行恢复',resources='32片×128 SA/恢复驱动；已有4096bit读码寄存器，新增权重锁存为0；128目标写驱动',main_assumptions='32次真实读恢复＋256数字轮；每极性14/50/100 ns为保守工程预算，14 ns原值是write latency',dominant_contrast='旧256次重读仅为调度对照；不将主动弃码归为介质必需恢复',maintenance='真实破坏读恢复已含raw streaming；无另列周期刷新',main_key='paired'),
'09_gain_cell_edram': dict(technology='Gain-cell eDRAM',mode='3T1C伪差分±700 nA二端点ACIM；固定400 μs刷新',update_pattern='16 Byte对齐组＝128差分pair；1024事务覆盖矩阵；长期整矩阵更新沿用同一刷新预留',resources='128 SAR、16重构通道、128 pair写驱动；64行组、8位平面；双支路200 fF积分负载',main_assumptions='参考刷新266.24 μs/400 μs，禁发185 ns，α=0.3339375；保留65 ns完整两步写和保持统计条件',dominant_contrast='长预算α≈3.93%仅压力点；α≤0不可行；32输出/双倍资源单列',maintenance='raw为无周期维护占用，effective为扣除固定刷新及禁发后的长期平均；同α抵消ridge不抵消能力损失',main_key='scenarios'),
'10_fenor_3d': dict(technology='3D vertical AND FeFET（2026）',mode='2026 vertical AND二状态数字路径；16-cell写条带',update_pattern='16 Byte完整权重，8个16-cell条带分两极性写验；1024事务覆盖矩阵',resources='32横向读通路/4096感测节点；四层仅分装容量；16cell写驱动，128cell对照需8倍资源',main_assumptions='±2 V/20 ns脉冲；100 ns写后观察预算已含最后返回，终态读验另计；观察占参考写时间46.2%',dominant_contrast='固定外围观察预算100/150 ns；128cell驱动资源对照；不由RAWD<100 ns推出零等待',maintenance='无周期维护；写后观察为工程预留，不是已证实必需等待',main_key='main_scenarios'),
}
SUMMARY_LABELS={'01_sram_acim':'SRAM ACIM：二进制电荷域','02_sram_dcim':'SRAM DCIM：16项归约','03_nor_2d':'2D NOR：binary本地感测＋数字归约','04_nand_3d':'3D NAND：c=1积分／持续重写','05_rram':'RRAM：32项ACIM／16-lane写验','06_mram':'MRAM：互补MTJ数字路径','07_pcm':'PCM：8行电压ACIM／对角更新','08_feram_hfo2':'HZO FeRAM：1T1C数字／读码复用','09_gain_cell_edram':'Gain-cell：二端点ACIM／含刷新','10_fenor_3d':'2026 vertical AND FeFET：数字路径'}
CORE=('B_S_Byte','B_R_Byte','delta_S_ns','delta_R_ns','rho_Byte_per_s','tau_Byte_per_s','ridge')
def walk(x,path=()):
 if isinstance(x,dict):
  if all(k in x for k in CORE):
   yield path,x
   return
  for k,v in x.items():yield from walk(v,path+(str(k),))
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,path+(str(i),))
def profile(row,path):
 return row.get('profile',row.get('common_profile',row.get('id',path[-1])))
def classify(c,p,r,main_key):
 if p[0]==main_key:
  if c=='04_nand_3d' and p[-1]=='append':return 'finite_pre_erased_window'
  if c=='09_gain_cell_edram' and profile(r,p)=='long':return 'pressure_near_refresh_saturation'
  return 'recommended_reference' if profile(r,p)=='reference' or 'reference' in r.get('id','') else 'paired_conditional'
 if 'pressure' in p[0] or 'stress' in p[0] or 'feasibility' in p[0]:return 'pressure_infeasible' if r['rho_Byte_per_s'] is None else 'pressure_near_refresh_saturation'
 if c=='08_feram_hfo2' and p[0]=='sensitivity':return 'schedule_comparison'
 if c=='06_mram':return 'finite_retry_sensitivity'
 if 'attempt' in p[0] or 'guard' in p[0] or 'sensitivity' in p[0] or 'sensitivities' in p[0]:
  if 'resource' not in r.get('kind','') and 'same_clock' not in r.get('id',''):return 'independent_sensitivity'
 return 'resource_or_organization_comparison'
def tex(s):
 for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
 return s.replace('μ',r'$\mu$').replace('α',r'$\alpha$').replace('ρ',r'$\rho$').replace('τ',r'$\tau$').replace('Δ',r'$\Delta$').replace('≤',r'$\leq$').replace('±',r'$\pm$').replace('HfO₂',r'HfO$_2$').replace('…','--').replace('≈',r'$\approx$').replace('10^6',r'$10^6$')
def f(v):return '不可行' if v is None else f'{v:.4g}'
def normalized():
 allrows=[];cases=[]
 for c,m in META.items():
  d=A/c;data=json.loads((d/'data/results.json').read_text());inp=(d/'data/inputs.json').read_text()
  sources=sorted(set(re.findall(r'(?:SACIM|SDCIM|CMOS|NOR|NAND|RRAM|MRAM|PCM|FERAM|GC|FENOR)-\d{2}',inp)))
  notes=sorted(str(p.relative_to(A)) for p in (d/'notes').glob('*') if p.suffix in ['.md'])
  primary=data[m['main_key']]
  case={k:v for k,v in m.items() if k!='main_key'};case.update(case_id=c,source_ids=sources,evidence_entries=notes,shared_baseline_id='shared_baseline')
  cases.append(case)
  for path,row in walk(data):
   if path[0] not in [m['main_key']] and not any(s in path[0] for s in ['sensitiv','compar','contrast','pressure','stress']):continue
   # NAND profile is on parent, not the metrics dictionary.
   r=dict(row)
   if c=='04_nand_3d':
    parent=primary[int(path[1])] if path[0]==m['main_key'] else data['organization_comparison']
    r['profile']=parent['profile'];r['id']=parent['id']+'_'+path[-1]
   typ=classify(c,path,r,m['main_key']);raw=r.get('nominal',r)
   feasible=r['rho_Byte_per_s'] is not None and r['tau_Byte_per_s'] is not None
   refresh=r.get('refresh')
   out=dict(case_id=c,technology=m['technology'],mode=m['mode'],scenario_id=r.get('id','/'.join(path)),scenario_type=typ,
    recommended=typ=='recommended_reference',rate_unit='MB/s',payload_unit='Byte',B_S=r['B_S_Byte'],B_R=r['B_R_Byte'],update_pattern=m['update_pattern'],
    raw_service_time=dict(streaming_ns=raw['delta_S_ns'],resident_ns=raw['delta_R_ns']),
    effective_service_interval=(dict(streaming_ns=r['delta_S_ns'],resident_ns=r['delta_R_ns']) if refresh else None),
    rho=(None if r['rho_Byte_per_s'] is None else r['rho_Byte_per_s']/1e6),tau=(None if r['tau_Byte_per_s'] is None else r['tau_Byte_per_s']/1e6),RI_star=r['ridge'],
    rho_raw=(None if raw['rho_Byte_per_s'] is None else raw['rho_Byte_per_s']/1e6),tau_raw=(None if raw['tau_Byte_per_s'] is None else raw['tau_Byte_per_s']/1e6),
    maintenance=refresh or dict(periodic=False,included_in_raw=m['maintenance']),feasibility='conditional_feasible' if feasible else 'infeasible_under_declared_schedule',
    main_assumptions=m['main_assumptions'],key_resources=m['resources'],source_ids=sources,shared_baseline_id='shared_baseline',
    source_result=f'{c}/data/results.json#/'+'/'.join(path),scenario_parameters={k:v for k,v in r.items() if k not in CORE and k not in ['nominal','refresh']})
   if c=='04_nand_3d' and path[-1]=='append':out['update_pattern']='已预擦除数据页、已建立参考页的整矩阵有限append窗口；写后重算校准'
   # Contrasts must identify their own resources and update shape, not inherit a false main-mode identity.
   if c=='01_sram_acim' and r.get('parallel_write_cells')==64:
    out['key_resources']=m['resources'].replace('128对真实写驱动','64对活动写驱动（两个完整写槽）')
   if c=='02_sram_dcim' and 'same_clock' in r.get('id',''):
    out['mode']='二进制SRAM数字路径；32项归约、16输出的同钟资源对照'
    out['key_resources']='归约及读带宽相对16项主点扩展至32项，同完整MAC时钟为条件；256轮'
   if c=='03_nor_2d' and path[0]=='organization_contrast':
    out['update_pattern']=m['update_pattern'].replace('4次sector擦除','32次sector擦除')
    out['key_resources']='32读片各独占4 KiB sector，4096 SA不变，分配128 KiB仅16 KiB有用；单更新域'
   if c=='04_nand_3d' and path[0]=='organization_comparison':
    out['mode']=m['mode'].replace('c=1；','c=108；')
    out['key_resources']=m['resources']+'；每路27.648 μA/1.728 V/μs驱动条件，积分231.481 ns'
   if c=='05_rram' and r.get('write_details',{}).get('parallel_cells')==1:
    out['update_pattern']=m['update_pattern'].replace('8批×16cell','128批×1cell')
    out['key_resources']='仅启用1个写lane；'+('复用SAR终验' if r['write_details']['verify_mode']=='sar' else 'binary窗口终验')+'；16-lane其余不活动'
   if c=='07_pcm' and r.get('verify_mode')=='weak_signal_analog_front':
    out['mode']=m['mode']+'；768 ns弱信号终验对照'
   if c=='08_feram_hfo2' and typ=='schedule_comparison':
    out['mode']='HZO 1T1C二状态数字路径；同硬件逐输入位重读；256次读/恢复'
   if c=='09_gain_cell_edram' and r.get('output_width')==32:
    out['update_pattern']='32 Byte对齐组，512事务覆盖矩阵；按此更宽资源重算刷新及长期占用'
    out['key_resources']='256 SAR、256 pair写驱动、32活动输出；数字重构仍16通道，原始求值64轮'
   if c=='10_fenor_3d' and path[0]=='structural_contrast':
    out['mode']=m['mode'].replace('16-cell写条带','128-cell并行写资源对照')
    out['update_pattern']='16 Byte完整权重，8个位平面条带同时两相写，128节点并行读回、16路8拍比较；1024事务覆盖矩阵'
    out['key_resources']='128个BL/SL列对及8组WL写驱动（约8倍写资源）；读资源不变'
   if c=='04_nand_3d' and path[-1]=='append':out['mode']=out['mode'].replace('持续同地址重写','预擦除有限append窗口')
   allrows.append(out)
  ref=[x for x in allrows if x['case_id']==c and x['recommended']];assert len(ref)==1,(c,len(ref))
  main=[x for x in allrows if x['case_id']==c and x['scenario_type'] in ['recommended_reference','paired_conditional']]
  case['reference_scenario_id']=ref[0]['scenario_id']
  case['conditional_paired_range']={k:[min(x[k] for x in main),max(x[k] for x in main)] for k in ['rho','tau','RI_star']}
  case['range_semantics']='short/reference only; long is refresh stress' if c=='09_gain_cell_edram' else 'extrema of three paired engineering scenarios, not physical uncertainty envelope'
  for x in [x for x in allrows if x['case_id']==c]:
   if x['feasibility']=='conditional_feasible':
    s=x['effective_service_interval'] or x['raw_service_time']
    assert math.isclose(x['rho'],x['B_S']/s['streaming_ns']*1000,rel_tol=1e-11)
    assert math.isclose(x['tau'],x['B_R']/s['resident_ns']*1000,rel_tol=1e-11)
    assert math.isclose(x['RI_star'],x['rho']/x['tau'],rel_tol=1e-11)
 return dict(schema_version='ten-case-review-1',units=dict(payload='Byte',time='ns',rho_tau='decimal MB/s (10^6 Byte/s)',RI_star='dimensionless'),shared_baseline_id='shared_baseline',shared_parameter_sha256=hashlib.sha256((A/'shared_baseline/data/shared_parameters.json').read_bytes()).hexdigest(),cases=cases,results=allrows)
def card(case,rows):
 ref=next(r for r in rows if r['recommended']);main=[r for r in rows if r['scenario_type'] in ['recommended_reference','paired_conditional']]
 raw=ref['raw_service_time'];eff=ref['effective_service_interval'];rng=case['conditional_paired_range']
 pairs=[('技术/模式',case['technology']+'；'+case['mode']),('逻辑粒度/聚合',f"B_S={ref['B_S']:g} Byte；B_R={ref['B_R']:g} Byte。"+case['update_pattern']),('资源/相对R0',case['resources']),('服务口径',case['maintenance']),('主导因素/选择',case['main_assumptions']),('关键对照',case['dominant_contrast'])]
 t=[r'% Generated by analysis/scripts/export_ten_cases.py',r'\subsection*{统一结果卡}',r'\begingroup\small',r'\noindent\begin{tabularx}{\textwidth}{@{}p{24mm}X@{}}\toprule']
 t += [tex(k)+' & '+tex(v)+r'\\' for k,v in pairs]
 t += [r'\bottomrule\end{tabularx}',r'\vspace{3mm}',r'\begin{center}\begin{tabular}{@{}lrrr@{}}\toprule',r'成对条件情景 & $\rho$ (MB/s) & $\tau$ (MB/s) & $\mathrm{RI}^{*}$\\\midrule']
 for i,r in enumerate(main):
  label='参考（推荐）' if r['recommended'] else ('短预算' if i==0 else '长预算')
  t.append(label+' & '+' & '.join(f(r[k]) for k in ['rho','tau','RI_star'])+r'\\')
 t += [r'\bottomrule\end{tabular}\end{center}',r'\noindent '+tex(f"参考原始占用：streaming {f(raw['streaming_ns'])} ns；resident {f(raw['resident_ns'])} ns。")]
 if eff:t.append(tex(f"维护后长期平均间隔：{f(eff['streaming_ns'])}/{f(eff['resident_ns'])} ns；原始ρ/τ={f(ref['rho_raw'])}/{f(ref['tau_raw'])} MB/s。"))
 t.append(r'\par\noindent '+tex('范围为有限成对条件情景极值，不是物理不确定性包络。'+('长预算与不可行压力情景在正文另列。' if case['case_id']=='09_gain_cell_edram' else '')+'1 MB=10^6 Byte；整矩阵16384 Byte=16 KiB。源定位见本例证据笔记；公共基线shared_baseline。'))
 t += [r'\endgroup',r'\clearpage']
 return '\n'.join(t)+'\n'
def outputs(d):
 out={'data/ten_case_results.json':json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n'}
 cols=['case_id','technology','mode','scenario_id','scenario_type','recommended','rate_unit','payload_unit','B_S','B_R','update_pattern','raw_service_time','effective_service_interval','rho','tau','RI_star','rho_raw','tau_raw','maintenance','feasibility','main_assumptions','key_resources','source_ids','shared_baseline_id','source_result','scenario_parameters']
 b=io.StringIO();w=csv.DictWriter(b,fieldnames=cols,lineterminator="\n");w.writeheader()
 for r in d['results']:w.writerow({k:json.dumps(r[k],ensure_ascii=False,separators=(',',':')) if isinstance(r[k],(dict,list)) else r[k] for k in cols})
 out['data/ten_case_results.csv']=b.getvalue()
 summary=['<!-- Generated by scripts/export_ten_cases.py; decimal MB/s. -->','| 案例（PDF，主模式见下文） | 参考ρ | 参考τ | 参考RI* |','|---|---:|---:|---:|'];ranges=['','| 案例 | 条件ρ范围 | 条件τ范围 | 成对RI*范围 |','|---|---:|---:|---:|']
 for c in d['cases']:
  rows=[r for r in d['results'] if r['case_id']==c['case_id']];r=next(r for r in rows if r['recommended']);ran=c['conditional_paired_range']
  pdf=c['case_id']+'/output/'+('pdf/rram' if c['case_id']=='05_rram' else c['case_id'][3:])+'.pdf'
  summary.append('| ['+SUMMARY_LABELS[c['case_id']]+']('+pdf+') | '+' | '.join(f(r[k]) for k in ['rho','tau','RI_star'])+' |')
  ranges.append('| '+c['technology']+' | '+' | '.join('–'.join(f(v) for v in ran[k]) for k in ['rho','tau','RI_star'])+' |')
  out[c['case_id']+'/tex/result_card.tex']=card(c,rows)
 summary_text='\n'.join(summary+ranges)+'\n'
 review=A/'TEN_CASE_REVIEW.zh.md'
 if review.exists():
  before,rest=review.read_text().split('<!-- BEGIN TEN CASE SUMMARY -->',1);_,after=rest.split('<!-- END TEN CASE SUMMARY -->',1)
  out['TEN_CASE_REVIEW.zh.md']=before+'<!-- BEGIN TEN CASE SUMMARY -->\n'+summary_text+'<!-- END TEN CASE SUMMARY -->'+after
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args();d=normalized()
 for name,s in outputs(d).items():
  path=A/name
  if args.emit:
   path.parent.mkdir(parents=True,exist_ok=True)
   if not path.exists() or path.read_text()!=s:path.write_text(s)
  else:assert path.read_text()==s,f'stale {name}'
 print(f"PASS: {len(d['cases'])} cases, {len(d['results'])} normalized scenarios; MB/s and service-time consistency; synchronized cards/exports.")

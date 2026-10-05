#!/usr/bin/env python3
"""Build paired-scenario Table I and rho-tau plots from full-precision data.

Typography, palette, table rules and log-plot geometry are adapted from the
read-only NVM summary-figure scripts. No NVM performance data are read.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
os.environ.setdefault('MPLCONFIGDIR', str(Path.home()/'.cache/cim-roofline/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
REFERENCE = ANALYSIS/'data/ten_case_results.json'
SOURCE = ANALYSIS/'data/paired_scenario_results.json'
PROFILES = ('optimistic','reference','pessimistic')
PROFILE_LABELS = ('Optimistic','Typical','Pessimistic')
OUT, DATA = HERE/'output', HERE/'data'
INK, MUTED, GRID, ACCENT = '#182838', '#657382', '#e5eaf0', '#245b78'
COLORS = ['#2d63ad', '#6e52a2', '#a37622', '#68737d', '#c54e55',
          '#178276', '#ca6b2b', '#338fa5', '#7b8736', '#ad5390']
LABELS = ['SRAM ACIM', 'SRAM DCIM', '2D NOR', '3D NAND', 'RRAM',
          'MRAM', 'PCM', r'HfO$_2$ FeRAM', 'Gain-cell eDRAM', '3D FeFET']
PLAIN_LABELS = ['SRAM ACIM', 'SRAM DCIM', '2D NOR', '3D NAND', 'RRAM',
                'MRAM', 'PCM', 'HfO2 FeRAM', 'Gain-cell eDRAM', '3D FeFET']
CASE_IDS = ['01_sram_acim','02_sram_dcim','03_nor_2d','04_nand_3d','05_rram',
            '06_mram','07_pcm','08_feram_hfo2','09_gain_cell_edram','10_fenor_3d']
METRICS = ('rho','tau','RI_star','U_star')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
    'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,
    'ytick.color':MUTED,'axes.edgecolor':'#afbac5','axes.titleweight':'bold',
    'mathtext.fontset':'dejavusans','pdf.fonttype':42,'ps.fonttype':42,
    'svg.fonttype':'none','savefig.facecolor':'white'})


def fmt(value):
    """The reference template's two-significant-digit display rule."""
    if value == 0: return '0'
    rounded = float(f'{value:.2g}')
    decimals = max(0,1-math.floor(math.log10(abs(rounded))))
    return f'{rounded:,.{decimals}f}'


def normalize_svg(path):
    path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')


def save_figure(fig, stem):
    for ext in ('png','pdf','svg'):
        fig.savefig(OUT/f'{stem}.{ext}',dpi=220,bbox_inches='tight',pad_inches=.16)
        if ext == 'svg': normalize_svg(OUT/f'{stem}.{ext}')


def normalized(row, index):
    r=dict(row,technology=PLAIN_LABELS[index])
    r['rho']=r['rho_Byte_per_s']/1e6
    r['tau']=r['tau_Byte_per_s']/1e6
    assert r['B_S_Byte']==r['K']*r['bytes_per_input']
    assert r['B_R_Byte']==r['K']*r['N']*r['bytes_per_weight']
    a=r['availability'];s=r['effective_delta_S_ns'];t=r['effective_T_R_ns']
    assert r.get('feasible',True) is True, 'Infeasible case cannot enter ordinary scenario plots'
    assert 0<a<=1 and s>0 and t>0
    checks=[(s,r['raw_delta_S_ns']/a),(t,r['raw_T_R_ns']/a),
            (r['rho'],r['B_S_Byte']/s*1e3),(r['tau'],r['B_R_Byte']/t*1e3),
            (r['rho'],r['rho_MBps']),(r['tau'],r['tau_MBps']),
            (r['RI_star'],r['rho']/r['tau']),(r['U_star'],t/s),
            (r['U_star'],r['N']*r['bytes_per_weight']/r['bytes_per_input']*r['RI_star'])]
    assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=0) for x,y in checks),r['case_id']
    return r


def load_and_validate():
    document=json.loads(SOURCE.read_text(encoding='utf-8'))
    reference=json.loads(REFERENCE.read_text(encoding='utf-8'))
    by_reference={r['case_id']:r for r in reference['case_results']}
    assert len(by_reference)==10 and set(by_reference)==set(CASE_IDS)
    assert len(document['case_results'])==30
    assert document['scenario_order']==list(PROFILES)
    groups=[]
    comparable=('case_id','K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight',
                'timing_min_period_ns','actual_period_ns','raw_delta_S_ns','raw_T_R_ns',
                'effective_delta_S_ns','effective_T_R_ns','availability',
                'rho_Byte_per_s','tau_Byte_per_s','rho_MBps','tau_MBps','RI_star','U_star')
    for i,cid in enumerate(CASE_IDS):
        selected=[r for r in document['case_results'] if r['case_id']==cid]
        assert len(selected)==3
        group={r['scenario']:normalized(r,i) for r in selected}
        assert set(group)==set(PROFILES)
        for key in comparable:
            assert group['reference'][key]==by_reference[cid][key], f'Reference changed: {cid}/{key}'
        for profile in PROFILES:
            r=group[profile]
            assert all(r[k]==group['reference'][k] for k in ('K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight'))
            assert isinstance(r['scenario_parameters'],dict) and r['scenario_input_path'] and r['result_path']
        groups.append(group)
    report={'all_passed':True,'cases':10,'paired_scenario_points':30,
        'checks':['Exactly three feasible paired scenarios for each of ten reference configurations',
                  'Typical values exactly equal the current reference authority',
                  'Logical payload unchanged across paired scenarios',
                  'Raw and effective intervals distinguished through availability',
                  'Full-precision rho, tau, RI_star and U_star identities'],
        'sha256':{'data/ten_case_results.json':hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                  'data/paired_scenario_results.json':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
        'display':{'rate_unit':'MB/s = 10^6 Byte/s','significant_digits':2,
                   'scatter_uses_unrounded_values':True,'axis_scales':'equal log10 scales'},
        'scenario_semantics':document.get('scenario_semantics'),
        'range_interpretation':'Finite paired engineering scenarios; not confidence intervals, same-chip PVT guarantees or strict bounds for all implementations.'}
    return document,groups,report


def make_table(groups):
    # Original NVM visual grammar, with U* retained in each scenario group.
    fig=plt.figure(figsize=(19.8,8.5),facecolor='white')
    ax=fig.add_axes([.030,.20,.94,.64]);ax.set(xlim=(0,1),ylim=(0,12));ax.axis('off')
    fig.text(.030,.947,'TABLE I   |   Two service capacities across ten CIM technologies',fontsize=20,weight='bold')
    fig.text(.030,.898,'INT8 logical payloads  ·  Fixed reference organizations  ·  Finite paired engineering scenarios',fontsize=11.8,color=MUTED)
    name_width=.225;cw=(1-name_width)/12
    center=lambda j:name_width+(j+.5)*cw
    gx=[name_width+j*4*cw for j in range(3)]
    for i in range(10):
        if i%2:ax.add_patch(Rectangle((0,9-i),1,1,color='#f6f8fa',lw=0))
    ax.add_patch(Rectangle((gx[1],0),4*cw,12,color='#e9f2f6',lw=0,zorder=1))
    for y,lw in [(12,1.8),(10,1.1),(0,1.4)]:ax.plot([0,1],[y,y],color=INK,lw=lw,clip_on=False)
    ax.text(.014,11.2,'Technology / K × N',ha='left',va='center',fontsize=11.5,weight='bold')
    for i,label in enumerate(PROFILE_LABELS):
        ax.text(gx[i]+2*cw,11.45,label,ha='center',va='center',fontsize=12.2,weight='bold',color=ACCENT if i==1 else INK)
        ax.plot([gx[i]+.008,gx[i]+4*cw-.008],[10.98,10.98],color='#b8c8d3',lw=.8)
        for j,m in enumerate((r'$\rho$',r'$\tau$',r'$\mathrm{RI}^{*}$',r'$U^{*}$')):
            ax.text(center(i*4+j),10.5,m+(' [MB/s]' if j<2 else ' [-]'),ha='center',va='center',fontsize=10.8,color=ACCENT if i==1 else MUTED)
    for i,g in enumerate(groups):
        y=9.5-i;r=g['reference']
        ax.add_patch(Rectangle((.001,y-.27),.0038,.54,color=COLORS[i],lw=0))
        ax.text(.014,y+.14,LABELS[i],ha='left',va='center',fontsize=12,weight='bold')
        ax.text(.014,y-.23,f"{r['K']}×{r['N']}",ha='left',va='center',fontsize=9.4,color=MUTED)
        for j,profile in enumerate(PROFILES):
            for k,metric in enumerate(METRICS):
                ax.text(center(j*4+k),y,fmt(g[profile][metric]),ha='center',va='center',fontsize=11.5,
                        weight='bold' if j==1 else 'normal',color=ACCENT if j==1 else INK)
    notes=[
      (r'$\rho=B_S/\Delta_S$, $\tau=B_R/T_R$, $\mathrm{RI}^{*}=\rho/\tau$, $U^{*}=T_R/\Delta_S=N\mathrm{RI}^{*}$ for the selected one-Byte input and weight payloads.',10.5,INK),
      ('Scenarios are finite paired engineering conditions, not statistical confidence intervals, same-chip PVT guarantees or strict bounds for all implementations.',9.9,MUTED),
      ('Both capacities use complete service boundaries. Gain-cell is volatile and includes refresh; internal planes and maintenance do not increase logical payload.',9.9,MUTED),
      ('Model-limited or unchanged budgets remain explicit; coincident values retain their source coordinates and do not establish zero uncertainty.',9.9,MUTED),
      ('Native resources, sizes and precision conditions differ. 3D FeFET denotes vertical AND FeFET; see METHOD for actual varied inputs and remaining conditions.',9.9,MUTED)]
    for y,(text,fs,c) in zip((.150,.118,.086,.054,.022),notes):fig.text(.030,y,text,fontsize=fs,color=c)
    save_figure(fig,'table_I_three_scenarios')
    return fig


def export_data(document,groups):
    # Preserve complete scenario provenance in JSON; scalar fields plus a JSON
    # column retain the full precision and varying-parameter records in CSV.
    flat=[dict(g[p]) for g in groups for p in PROFILES]
    (DATA/'table_I.json').write_text(json.dumps(flat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    scalar_fields=['case_id','technology','scenario','K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight',
            'actual_period_ns','timing_min_period_ns','raw_delta_S_ns','raw_T_R_ns','effective_delta_S_ns','effective_T_R_ns',
            'availability','rho_Byte_per_s','tau_Byte_per_s','rho_MBps','tau_MBps','RI_star','U_star','feasible',
            'scenario_input_path','result_path']
    with (DATA/'table_I.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=scalar_fields+['scenario_parameters'],lineterminator='\n');w.writeheader()
        for r in flat:w.writerow({**{k:r[k] for k in scalar_fields},'scenario_parameters':json.dumps(r['scenario_parameters'],ensure_ascii=False,sort_keys=True)})
    md=['# Table I：十例成对工程情景','','ρ、τ 为十进制 MB/s；显示约两位有效数字，完整精度保存在 CSV/JSON。','',
        '| 技术 | K×N | 乐观 ρ | 乐观 τ | 乐观 RI* | 乐观 U* | **典型 ρ** | **典型 τ** | **典型 RI*** | **典型 U*** | 悲观 ρ | 悲观 τ | 悲观 RI* | 悲观 U* |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    tex=[r'% Generated by build_figures.py; requires booktabs and graphicx.',r'\begin{table*}[t]',r'\centering\small',
         r'\setlength{\tabcolsep}{3pt}',
         r'\caption{Finite paired engineering scenarios for selected CIM configurations. Capacities use decimal MB/s; $\mathrm{RI}^{*}=\rho/\tau$, $U^{*}=T_R/\Delta_S$.}',
         r'\label{tab:cim-paired-scenarios}',r'\resizebox{\textwidth}{!}{%',r'\begin{tabular}{@{}ll rrrr rrrr rrrr@{}}',r'\toprule',
         r'Technology & $K\!\times\!N$ & \multicolumn{4}{c}{Optimistic} & \multicolumn{4}{c}{Typical} & \multicolumn{4}{c}{Pessimistic} \\',
         r'\cmidrule(lr){3-6}\cmidrule(lr){7-10}\cmidrule(l){11-14}',
         r' & & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $U^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $U^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $U^{*}$ \\\midrule']
    for i,g in enumerate(groups):
        r=g['reference'];values=[];texvalues=[]
        for profile in PROFILES:
            for k in METRICS:
                value=fmt(g[profile][k]);values.append('**'+value+'**' if profile=='reference' else value)
                texvalues.append(r'\textbf{'+value+'}' if profile=='reference' else value)
        md.append('| '+' | '.join([PLAIN_LABELS[i],f"{r['K']}×{r['N']}",*values])+' |')
        tex.append(' & '.join([LABELS[i],f"${r['K']}\\times{r['N']}$",*texvalues])+r'\\')
    note='Finite paired engineering scenarios are not statistical confidence intervals, same-chip PVT guarantees or strict bounds for all implementations. Gain-cell includes refresh. Internal encoding and maintenance do not increase logical payload. Coincident endpoints do not establish zero uncertainty. Native sizes, resources and precision conditions differ; no equal-area or equal-work ranking is implied. 3D FeFET denotes vertical AND FeFET.'
    md+=['','情景是有限的成对工程条件，不是统计置信区间、同一芯片 PVT 保证或所有实现的严格边界。',
         'GC 是易失性存储；两率已计周期刷新。内部编码与维护不增加逻辑 payload。U* 是服务交叉点，不是工作负载实际复用次数。',
         '重合的数值保持原样，不代表未知项为零。3D FeFET 为垂直 AND FeFET。',
         '实际变动参数、保留条件与范围来源见 [方法](../../METHOD.zh.md) 和完整精度数据。']
    tex +=[r'\bottomrule\end{tabular}}',r'\par\smallskip\begin{minipage}{\textwidth}\footnotesize',note,r'\end{minipage}',r'\end{table*}']
    (OUT/'table_I.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    (OUT/'table_I.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=SOURCE,help='Current paired-scenario authority')
    parser.add_argument('--reference',type=Path,default=REFERENCE,help='Current unchanged typical authority')
    parser.add_argument('--output-root',type=Path,default=HERE,help='Directory holding output/ and data/; use a local path for previews.')
    args=parser.parse_args()
    global OUT,DATA
    globals()['SOURCE']=args.source.resolve();globals()['REFERENCE']=args.reference.resolve()
    OUT=args.output_root.resolve()/'output';DATA=args.output_root.resolve()/'data'
    OUT.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    document,groups,report=load_and_validate()
    from build_loglog_circles import circle_for
    specs=[circle_for(g) for g in groups]
    export_data(document,groups);table=make_table(groups)
    from build_loglog import render_plot
    scatter=render_plot(groups,report)
    circles=render_plot(groups,report,circle_specs=specs,output_stem='rho_tau_loglog_circles')
    with PdfPages(OUT/'table_I.pdf',metadata={'Title':'Table I and paired-configuration rho-tau maps'}) as pdf:
        for fig in (table,scatter,circles):pdf.savefig(fig,bbox_inches='tight',pad_inches=.16)
    report['circles']={'count':len(specs),'degenerate_case_ids':[s['case_id'] for s in specs if s['geometry_case']!='distinct_endpoints'],
                       'zero_radius_case_ids':[s['case_id'] for s in specs if s['radius_decades']==0]}
    (DATA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    plt.close('all')
    print(f'PASS: thirty full-precision paired points; typical authority unchanged; figures: {OUT}')


if __name__=='__main__':
    sys.modules['build_figures']=sys.modules[__name__]
    main()

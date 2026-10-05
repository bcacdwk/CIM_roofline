#!/usr/bin/env python3
"""Build Table I and the rho-tau plot from the current full-precision data.

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
SOURCE = ANALYSIS/'data/ten_case_results.json'
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


def load_and_validate():
    document = json.loads(SOURCE.read_text(encoding='utf-8'))
    source_rows = document['case_results']
    assert len(source_rows)==10
    by_id = {r['case_id']:r for r in source_rows}
    assert set(by_id)==set(CASE_IDS), 'Expected the ten reference configurations'
    rows=[]
    for i,cid in enumerate(CASE_IDS):
        r=dict(by_id[cid],technology=PLAIN_LABELS[i])
        r['rho']=r['rho_Byte_per_s']/1e6
        r['tau']=r['tau_Byte_per_s']/1e6
        assert r['B_S_Byte']==r['K']*r['bytes_per_input']
        assert r['B_R_Byte']==r['K']*r['N']*r['bytes_per_weight']
        a=r['availability'];s=r['effective_delta_S_ns'];t=r['effective_T_R_ns']
        assert 0<a<=1 and s>0 and t>0
        checks=[(s,r['raw_delta_S_ns']/a),(t,r['raw_T_R_ns']/a),
                (r['rho'],r['B_S_Byte']/s*1e3),(r['tau'],r['B_R_Byte']/t*1e3),
                (r['rho'],r['rho_MBps']),(r['tau'],r['tau_MBps']),
                (r['RI_star'],r['rho']/r['tau']),(r['U_star'],t/s),
                (r['U_star'],r['N']*r['bytes_per_weight']/r['bytes_per_input']*r['RI_star'])]
        assert all(math.isclose(x,y,rel_tol=1e-12,abs_tol=0) for x,y in checks),cid
        rows.append(r)
    report={'all_passed':True,'cases':10,
        'checks':['Exactly ten reference configurations',
                  'Logical payload identities and Byte/s to decimal MB/s conversion',
                  'Raw and effective intervals distinguished through availability',
                  'Full-precision rho, tau, RI_star and U_star identities'],
        'sha256':{'data/ten_case_results.json':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
        'display':{'rate_unit':'MB/s = 10^6 Byte/s','significant_digits':2,
                   'scatter_uses_unrounded_values':True,'axis_scales':'equal log10 scales'},
        'circle_status':'Not generated: no compatible traceable paired ranges in this reference evaluation.'}
    return document,rows,report


def make_table(rows):
    fig=plt.figure(figsize=(14.9,8.3),facecolor='white')
    ax=fig.add_axes([.035,.20,.93,.64]);ax.set(xlim=(0,1),ylim=(0,12));ax.axis('off')
    fig.text(.035,.947,'TABLE I   |   Two service capacities across ten CIM technologies',fontsize=20,weight='bold')
    fig.text(.035,.898,'INT8 logical payloads  ·  Selected reference configurations  ·  Sustained complete-matrix loading',fontsize=11.8,color=MUTED)
    name_width=.255
    widths=[.115,.125,.125,.125,.13,.125]
    centers=[];x=name_width
    for w in widths:centers.append(x+w/2);x+=w
    for i in range(10):
        if i%2:ax.add_patch(Rectangle((0,9-i),1,1,color='#f6f8fa',lw=0))
    ax.add_patch(Rectangle((name_width+widths[0],0),sum(widths[1:5]),12,color='#e9f2f6',lw=0,zorder=1))
    for y,lw in [(12,1.8),(10,1.1),(0,1.4)]:ax.plot([0,1],[y,y],color=INK,lw=lw,clip_on=False)
    ax.text(.014,11.15,'Technology / K × N',ha='left',va='center',fontsize=11.5,weight='bold')
    headers=[('Clock',r'$P$ [ns]'),('Streaming',r'$\rho$ [MB/s]'),('Resident',r'$\tau$ [MB/s]'),
             ('Service ratio',r'$\mathrm{RI}^{*}$ [-]'),('Crossover',r'$U^{*}$ [-]'),('Availability',r'$a$ [-]')]
    for i,((name,unit),x) in enumerate(zip(headers,centers)):
        ax.text(x,11.45,name,ha='center',va='center',fontsize=11.5,weight='bold',color=ACCENT if 1<=i<=4 else INK)
        ax.text(x,10.5,unit,ha='center',va='center',fontsize=11.3,color=ACCENT if 1<=i<=4 else MUTED)
    for i,r in enumerate(rows):
        y=9.5-i
        ax.add_patch(Rectangle((.001,y-.27),.0044,.54,color=COLORS[i],lw=0))
        ax.text(.014,y+.14,LABELS[i],ha='left',va='center',fontsize=12,weight='bold')
        ax.text(.014,y-.23,f"{r['K']}×{r['N']}",ha='left',va='center',fontsize=9.4,color=MUTED)
        values=[r['actual_period_ns'],r['rho'],r['tau'],r['RI_star'],r['U_star'],r['availability']]
        for j,(x,value) in enumerate(zip(centers,values)):
            ax.text(x,y,fmt(value),ha='center',va='center',fontsize=11.7,weight='bold' if 1<=j<=4 else 'normal',color=ACCENT if 1<=j<=4 else INK)
    notes=[
      (r'$\rho=B_S/\Delta_S$, $\tau=B_R/T_R$, $\mathrm{RI}^{*}=\rho/\tau$; $U^{*}=T_R/\Delta_S=N\mathrm{RI}^{*}$ for the selected one-Byte input and weight payloads.',10.3,INK),
      ('Both capacities use complete service boundaries. Gain-cell is volatile; its rates and effective intervals include periodic refresh.',9.7,MUTED),
      ('Internal planes, reference pages, verification and refresh consume resources and time without increasing logical payload.',9.7,MUTED),
      ('Native sizes, precision conditions and resources differ; these capacities do not rank equal-area or equal-work implementations.',9.7,MUTED),
      ('Device services combine literature estimates with NeuroSim peripheral models. 3D FeFET denotes vertical AND FeFET; see METHOD for scope.',9.5,MUTED)]
    for y,(text,fs,c) in zip((.150,.118,.086,.054,.022),notes):fig.text(.035,y,text,fontsize=fs,color=c)
    save_figure(fig,'table_I_typical')
    return fig


def export_data(document,rows):
    fields=['case_id','technology','K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight',
            'actual_period_ns','timing_min_period_ns','raw_delta_S_ns','raw_T_R_ns','effective_delta_S_ns','effective_T_R_ns',
            'availability','rho_Byte_per_s','tau_Byte_per_s','rho_MBps','tau_MBps','RI_star','U_star','result_path','input_path']
    flat=[{k:r[k] for k in fields} for r in rows]
    with (DATA/'table_I.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(flat)
    (DATA/'table_I.json').write_text(json.dumps(flat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md=['# Table I：十例参考配置','','ρ、τ 为十进制 MB/s；显示约两位有效数字，完整精度保存在 CSV/JSON。','',
        '| 技术 | K×N | 周期 ns | ρ MB/s | τ MB/s | RI* | U* | 可用率 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    tex=[r'% Generated by build_figures.py; requires booktabs.',r'\begin{table*}[t]',r'\centering\small',
         r'\caption{Table I. Selected CIM reference configurations. Capacities use decimal MB/s; $\mathrm{RI}^{*}=\rho/\tau$, $U^{*}=T_R/\Delta_S$.}',
         r'\label{tab:cim-reference}',r'\begin{tabular}{@{}lrrrrrrr@{}}',r'\toprule',
         r'Technology & $K\!\times\!N$ & $P$ [ns] & $\rho$ [MB/s] & $\tau$ [MB/s] & $\mathrm{RI}^{*}$ & $U^{*}$ & $a$ \\ \midrule']
    for i,r in enumerate(rows):
        values=[fmt(r[k]) for k in ('actual_period_ns','rho','tau','RI_star','U_star','availability')]
        md.append('| '+' | '.join([PLAIN_LABELS[i],f"{r['K']}×{r['N']}",*values])+' |')
        tex.append(' & '.join([LABELS[i],f"${r['K']}\\times{r['N']}$",*values])+r'\\')
    note='Gain-cell includes periodic refresh. Internal encoding and maintenance do not increase logical payload. Native sizes, resources and precision conditions differ; no equal-area or equal-work ranking is implied. 3D FeFET denotes vertical AND FeFET.'
    md+=['','GC 是易失性存储；两率已计周期刷新。内部编码与维护不增加逻辑 payload。U* 是服务交叉点，不是工作负载实际复用次数。',
         '3D FeFET 为垂直 AND FeFET。不同规模、资源和精度条件下的配置不构成等面积或等工作量材料排名。',
         '完整服务与来源范围见 [方法](../../METHOD.zh.md)。']
    tex +=[r'\bottomrule\end{tabular}',r'\par\smallskip\begin{minipage}{\textwidth}\footnotesize',note,r'\end{minipage}',r'\end{table*}']
    (OUT/'table_I.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    (OUT/'table_I.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output-root',type=Path,default=HERE,help='Directory holding output/ and data/; use a local path for preview runs.')
    args=parser.parse_args()
    global OUT,DATA
    globals()['SOURCE']=args.source.resolve()
    OUT=args.output_root.resolve()/'output';DATA=args.output_root.resolve()/'data'
    OUT.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
    document,rows,report=load_and_validate()
    export_data(document,rows);table=make_table(rows)
    # Import after arguments establish destination paths.
    from build_loglog import render_plot
    scatter=render_plot(rows,report)
    with PdfPages(OUT/'table_I.pdf',metadata={'Title':'Table I and reference-configuration rho-tau map'}) as pdf:
        for fig in (table,scatter):pdf.savefig(fig,bbox_inches='tight',pad_inches=.16)
    (DATA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    plt.close('all')
    print(f'PASS: ten full-precision reference configurations; figures: {OUT}')


if __name__=='__main__':
    # Ensure build_loglog imports this executing module, including CLI paths.
    sys.modules['build_figures']=sys.modules[__name__]
    main()

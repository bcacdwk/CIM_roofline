#!/usr/bin/env python3
"""Compact paper Fig.4; preserve the accepted six workload SI lines and hardware ranges.

The accepted Task III Qwen design supplies read-only inputs and plotting helpers.
This paper entry point replaces the historical U* plot. It never writes Task data.
Use --output-dir to keep previews and validation outside the synchronized tree.
"""
from __future__ import annotations
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE_RELATIVE = Path('tasks/task3_matching_figures/06_final/fig4_qwen36')


def load_readonly_data(source):
    checks = {}
    for name, expected in source.EXPECTED.items():
        raw = (source.ROOT/'data'/name).read_bytes()
        git_sha = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert git_sha == expected, f'Accepted input changed: {name}'
        checks[name] = {'git_blob_sha':git_sha, 'sha256':hashlib.sha256(raw).hexdigest()}
    with (source.ROOT/'data/plotted_thresholds.csv').open(newline='') as f:
        hw = list(csv.DictReader(f))
    with (source.ROOT/'data/rho_tau_loglog_circles_points.csv').open(encoding='utf-8-sig',newline='') as f:
        fig3 = {(r['case_id'],r['profile']):r for r in csv.DictReader(f)}
    assert len(hw) == len(fig3) == 30
    for row in hw:
        assert row['RI_star'] == fig3[row['case_id'],row['profile']]['RI_star']
        row['RI_star'] = float(row['RI_star'])
    ref = {r['case_id']:r for r in hw if r['profile']=='reference'}
    order = sorted(ref,key=lambda cid:ref[cid]['RI_star'])
    assert len(order) == 10
    with (source.ROOT/'data/selected_workloads.csv').open(newline='') as f:
        lookup = {r['case_id']:r for r in csv.DictReader(f)}
    loads = []
    for workload,label,var,n in source.CHOICES:
        cid=f'{source.MODEL}/{workload}/{n}'
        row=lookup[cid]
        si=Fraction(int(row['RI_numerator']),int(row['RI_denominator']))
        assert si == Fraction(int(row['Q_S']),int(row['Q_R']))
        loads.append({'case_id':cid,'label':label,
                      'condition_label':f'{var}={source.fmt_condition(n)}',
                      'SI':float(si),'SI_exact':str(si)})
    qa={'baseline':source.BASELINE,'source_checks':checks,'six_points':loads,
        'all_30_hardware_SI_values_unchanged':True,'plot_checks':{}}
    return hw,ref,order,loads,qa


def one_dimensional(hw, ref, order, loads, out, qa):
    # Preserve the supplied ten-row / six-guide design at actual column width.
    # Space comes from the short title and tighter outer margins, not point shifts.
    w,h = 3.5,2.75
    left,right,bottom,top = .735,.075,.40,.31
    fig=plt.figure(figsize=(w,h))
    ax=fig.add_axes([left/w,bottom/h,(w-left-right)/w,(h-bottom-top)/h])
    x_axis(ax)
    ax.set_ylim(9.72,-.62)
    ax.set_yticks(range(10), [TECH[c][0] for c in order], fontsize=7.4)
    ax.tick_params(axis='y',length=0,pad=3)
    for t,c in zip(ax.get_yticklabels(),order):
        t.set_color(TECH[c][1])
    for side in ['left','top','right']:
        ax.spines[side].set_visible(False)
    headers,guide_positions=workload_guides(ax,loads,fontsize=7.4)
    title=ax.text(.985,.985,MODEL_NAME,transform=ax.transAxes,fontsize=6.2,
                  fontstyle='italic',color='#444444',ha='right',va='top',zorder=8,
                  bbox={'facecolor':'white','edgecolor':'none','pad':.5})
    value_labels=[]
    hardware_geometry=[]
    plotted_ranges=[]
    for y,cid in enumerate(order):
        color=TECH[cid][1]
        vals=[r['RI_star'] for r in hw if r['case_id']==cid]
        lo,hi=min(vals),max(vals)
        ax.axhline(y,color='#ededed',lw=.4,zorder=0)
        segment=ax.plot([lo,hi],[y,y],color=color,lw=1.25,zorder=2)[0]
        dot=ax.scatter(ref[cid]['RI_star'],y,s=17,c=color,edgecolors='white',linewidths=.45,zorder=4)
        assert float(dot.get_offsets()[0,0])==ref[cid]['RI_star']
        assert np.array_equal(segment.get_xdata(),[lo,hi])
        hardware_geometry.append((lo,hi,ref[cid]['RI_star'],y))
        plotted_ranges.append({'case_id':cid,'reference_SI_star':ref[cid]['RI_star'],
                              'scenario_min':lo,'scenario_max':hi,'color':color,'row':y})
        value=f'{ref[cid]["RI_star"]:.3g}'
        pos,off,ha=(lo,(-4,0),'right') if cid=='03_nor_2d' else (hi,(4,0),'left')
        value_labels.append(ax.annotate(value,(pos,y),xytext=off,textcoords='offset points',ha=ha,va='center',
                    fontsize=7.15,color=color,zorder=6,
                    bbox={'facecolor':'white','edgecolor':'none','pad':.4}))
    note=direction_note(ax,y=.032,fontsize=7.0)
    xlabel=ax.set_xlabel(r'Streaming intensity SI, SI$^{*}$ [B/B]',fontsize=7.7,labelpad=2.8)

    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    annotations=[title,*headers,*value_labels,note,xlabel]
    boxes=[a.get_window_extent(renderer).padded(.6) for a in annotations]
    collisions=[]
    for i,b in enumerate(boxes):
        for j in range(i+1,len(boxes)):
            if b.overlaps(boxes[j]):
                collisions.append([annotations[i].get_text(),annotations[j].get_text()])
    assert not collisions,collisions
    # Labels may mask a short piece of a guide, but never a native point/range.
    # Point/guide near-coincidence is retained exactly (notably NAND/Prefill).
    for b in boxes:
        for lo,hi,x,y in hardware_geometry:
            px,py=ax.transData.transform((x,y))
            radius=(math.sqrt(17)+.45)*fig.dpi/72/2
            distance=math.hypot(px-np.clip(px,b.x0,b.x1),py-np.clip(py,b.y0,b.y1))
            assert distance>radius,'Annotation covers a reference point'
            x0,y0=ax.transData.transform((lo,y));x1,_=ax.transData.transform((hi,y))
            assert not (b.y0-.8<=y0<=b.y1+.8 and b.x0<=x1 and b.x1>=x0),'Annotation covers a native scenario range'
    save_figure(fig,'critical_reuse_single',out,qa,headers,
                {'reference_points':10,'scenario_range_includes_all_30_values':True,
                 'workload_guide_positions':guide_positions,'hardware_ranges':plotted_ranges,
                 'annotation_overlaps':collisions,'no_point_or_range_masking':True,
                 'two_line_workload_labels':True,
                 'scope':'Raw native SI* versus model logical SI; no deployment correction.'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE)
    parser.add_argument('--repo-root',type=Path,default=HERE.parents[1],
                        help='Repository containing the accepted Task III inputs.')
    args=parser.parse_args()
    source_path=args.repo_root.resolve()/SOURCE_RELATIVE/'plot_qwen36.py'
    spec=importlib.util.spec_from_file_location('accepted_fig4_style',source_path)
    source=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    # Reuse layout helpers only: load_data()/main() would write the Task directory.
    for name in ['TECH','MODEL_NAME','x_axis','workload_guides','direction_note','save_figure']:
        globals()[name]=getattr(source,name)
    hw,ref,order,loads,qa=load_readonly_data(source)
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    source.configure()
    one_dimensional(hw,ref,order,loads,out,qa)
    (out/'critical_reuse_layout_validation.json').write_text(json.dumps(qa,indent=2)+'\n')
    print('Fig.4: 3.50 x 2.75 in; all ten ranges and six workload SI lines retained.')


if __name__=='__main__':
    main()

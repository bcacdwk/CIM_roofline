#!/usr/bin/env python3
"""Qwen3.6-35B-A3B workload-line Fig.4 variants, pinned to f98cb74d936f58d1b8eda33bc1a7384e02d00abb.

Reproduce offline: python plot_qwen36.py [--output-dir figures]
All inputs are read-only CSV snapshots. No remote write, interpolation, tile
conversion, workload recounting, or prediction of realized performance.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.ticker import NullLocator
import numpy as np

ROOT = Path(__file__).resolve().parent
BASELINE = 'f98cb74d936f58d1b8eda33bc1a7384e02d00abb'
MODEL = 'qwen36_35b_a3b'
MODEL_NAME = 'Qwen3.6-35B-A3B'
EXPECTED = {
    'plotted_thresholds.csv': '8bdaef9fdf1b68dd77745229ae926c543fd2ba59',
    'selected_workloads.csv': '401b5b19fed92f674c06424930dc631924966984',
    'rho_tau_loglog_circles_points.csv': '5d074af7d7becca5bbc2c407a71bc4433ad29b79',
}
TECH = {
 '01_sram_acim': ('SRAM ACIM', '#2d63ad'),
 '02_sram_dcim': ('SRAM DCIM', '#6e52a2'),
 '03_nor_2d': ('2D NOR', '#a37622'),
 '04_nand_3d': ('3D NAND', '#68737d'),
 '05_rram': ('RRAM', '#c54e55'),
 '06_mram': ('STT-MRAM', '#178276'),
 '07_pcm': ('PCM', '#ca6b2b'),
 '08_feram_hfo2': ('FeRAM', '#338fa5'),
 '09_gain_cell_edram': ('eDRAM', '#7b8736'),
 '10_fenor_3d': ('3D FeNOR', '#ad5390'),
}
# Chosen only from existing Table II cells. They cover roughly five SI decades.
# Actual U/L values are never adjusted to make the SI spacing more regular.
CHOICES = [
 ('ffn_or_moe', 'MoE', 'U', 16),
 ('qkv_projection', 'QKV', 'U', 1024),
 ('ffn_or_moe', 'MoE', 'U', 1024),
 ('attention_prefill', 'Prefill', 'L', 1024),
 ('qkv_projection', 'QKV', 'U', 1048576),
 ('attention_decode', 'Decode', 'L', 65536),
]
XLIM = (.0075, 4000.)
XTICKS = [.01, .1, 1., 10., 100., 1000.]
XLABELS = [rf'$10^{{{p}}}$' for p in range(-2, 4)]


def fmt_condition(n: int) -> str:
    if n == 1048576:
        return '1M'
    return f'{n // 1024}K' if n >= 1024 and n % 1024 == 0 else str(n)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f'No rows for {path}')
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_data():
    checks = {}
    for name, expected in EXPECTED.items():
        data = (ROOT / 'data' / name).read_bytes()
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if git_sha != expected:
            raise ValueError(f'Pinned source differs: {name}')
        checks[name] = {'git_blob_sha': git_sha, 'matches_baseline': True,
                        'sha256': hashlib.sha256(data).hexdigest()}
    with (ROOT / 'data' / 'plotted_thresholds.csv').open(newline='') as f:
        hw = list(csv.DictReader(f))
    with (ROOT / 'data' / 'rho_tau_loglog_circles_points.csv').open(encoding='utf-8-sig', newline='') as f:
        original_fig3 = {(r['case_id'], r['profile']): r for r in csv.DictReader(f)}
    if len(hw) != 30 or len(original_fig3) != 30:
        raise ValueError('Expected all 30 paired native scenarios')
    for r in hw:
        orig = original_fig3[r['case_id'], r['profile']]
        for a, b in [('RI_star','RI_star'), ('rho_MB_per_s','rho'),
                     ('tau_MB_per_s','tau'), ('U_star','U_star'), ('K','K'), ('N','N')]:
            if r[a] != orig[b]:
                raise ValueError(f'Fig.3a / Fig.4 mismatch: {r["case_id"]}, {a}')
        for k in ['RI_star','rho_MB_per_s','tau_MB_per_s','U_star']:
            r[k] = float(r[k])
        assert math.isclose(r['RI_star'], r['rho_MB_per_s']/r['tau_MB_per_s'], rel_tol=2e-14)
    ref = {r['case_id']: r for r in hw if r['profile'] == 'reference'}
    assert len(ref) == 10
    order = sorted(ref, key=lambda cid: ref[cid]['RI_star'])
    with (ROOT / 'data' / 'selected_workloads.csv').open(newline='') as f:
        all_workloads = list(csv.DictReader(f))
    lookup = {r['case_id']: r for r in all_workloads}
    loads = []
    for workload, label, var, n in CHOICES:
        cid = f'{MODEL}/{workload}/{n}'
        row = lookup[cid]
        si = Fraction(int(row['RI_numerator']), int(row['RI_denominator']))
        assert si == Fraction(int(row['Q_S']), int(row['Q_R']))
        loads.append({'case_id': cid, 'model': MODEL_NAME, 'workload': workload,
                      'label': label, 'variable': var, 'condition': n,
                      'condition_label': f'{var}={fmt_condition(n)}',
                      'SI_exact': str(si), 'SI': float(si),
                      'Q_S': int(row['Q_S']), 'Q_R': int(row['Q_R'])})
    assert all(a['SI'] < b['SI'] for a, b in zip(loads, loads[1:]))
    selected = {x['case_id'] for x in loads}
    available = []
    for r in all_workloads:
        if r['case_id'].startswith(MODEL + '/'):
            si = Fraction(int(r['RI_numerator']), int(r['RI_denominator']))
            available.append({'case_id': r['case_id'], 'SI_exact': str(si),
                              'SI': float(si), 'selected': r['case_id'] in selected})
    comparisons = []
    for load in loads:
        for cid in order:
            for r in [r for r in hw if r['case_id'] == cid]:
                ratio = load['SI'] / r['RI_star']
                comparisons.append({'workload_case_id': load['case_id'],
                    'workload_SI': load['SI'], 'technology': TECH[cid][0],
                    'profile': r['profile'], 'SI_star': r['RI_star'],
                    'rho_MB_s': r['rho_MB_per_s'], 'SI_over_SI_star': ratio,
                    'reference_side': 'streaming' if ratio > 1 else 'resident' if ratio < 1 else 'balance'})
    write_csv(ROOT / 'data' / 'selected_six_points.csv', loads)
    write_csv(ROOT / 'data' / 'qwen36_all_table_II_points.csv', available)
    write_csv(ROOT / 'data' / 'six_point_comparisons.csv', comparisons)
    qa = {'baseline': BASELINE, 'source_checks': checks,
          'fig3a_nvm_all_30_rows_match': True,
          'workloads_are_existing_table_II_cells': True,
          'workload_x_not_jittered_or_remapped': True,
          'six_points': loads, 'log10_spacing': [math.log10(b['SI']/a['SI']) for a,b in zip(loads,loads[1:])],
          'rho_unit': 'decimal MB/s', 'MoE_scope': 'one routed expert',
          'reference_streaming_counts': [sum(l['SI'] > r['RI_star'] for r in ref.values()) for l in loads],
          'plot_checks': {}}
    return hw, ref, order, loads, qa


def configure():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 7.5,
        'mathtext.fontset': 'dejavusans', 'text.color': 'black',
        'axes.edgecolor': 'black', 'axes.labelcolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black', 'axes.linewidth': .6,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
        'figure.facecolor': 'white', 'savefig.facecolor': 'white',
        'lines.solid_capstyle': 'round',
    })


def x_axis(ax):
    ax.set_xscale('log')
    ax.set_xlim(*XLIM)
    ax.set_xticks(XTICKS, XLABELS)
    ax.xaxis.set_minor_locator(NullLocator())
    ax.tick_params(axis='x', length=3, labelsize=7.5, pad=2, colors='black')
    for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(.6)


def workload_guides(ax, loads, fontsize=7.6):
    """All x positions are actual SI. Only header label heights may be staggered."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = []
    lines = []
    guide_positions = []
    # Heights are in axes fraction, derived from physical sizes for portability.
    ax_height_in = ax.get_position().height * fig.get_figheight()
    base = 1 + .055 / ax_height_in
    tier_step = .255 / ax_height_in
    for load in loads:
        x = load['SI']
        line = ax.axvline(x, color='#646464', lw=.65, ls=(0, (3, 3)), zorder=.7)
        assert np.array_equal(line.get_xdata(), [x, x])
        txt = ax.text(x, base, load['label']+'\n'+load['condition_label'],
                      transform=ax.get_xaxis_transform(), ha='center', va='bottom',
                      fontsize=fontsize, linespacing=1.10, clip_on=False, zorder=7)
        for tier in [0, 1]:
            txt.set_y(base + tier*tier_step)
            box = txt.get_window_extent(renderer).padded(1.0)
            if not any(box.overlaps(t.get_window_extent(renderer).padded(1.0)) for t in texts):
                break
        else:
            raise RuntimeError('Workload headers require more than two tiers')
        texts.append(txt)
        connector = ax.plot([x,x], [1, txt.get_position()[1]-.016/ax_height_in],
                            transform=ax.get_xaxis_transform(), clip_on=False,
                            color='#646464', lw=.65, zorder=.7)[0]
        lines += [line, connector]
        guide_positions.append({'case_id':load['case_id'], 'x':x, 'label_tier':tier})
    return texts, guide_positions


def direction_note(ax, y=.05, fontsize=6.8):
    return ax.text(.024, y, 'Hardware relative to each line:\n' + '← streaming  |  resident →',
            transform=ax.transAxes, ha='left', va='bottom', fontsize=fontsize,
            linespacing=1.2, color='black', zorder=8,
            bbox={'facecolor':'white','edgecolor':'none','alpha':.97,'pad':1.0})


def save_figure(fig, name, out, qa, headers, extra=None):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fw, fh = fig.canvas.get_width_height()
    outside = []
    for text in fig.findobj(match=Text):
        if not text.get_visible() or not text.get_text():
            continue
        b = text.get_window_extent(renderer)
        # Out-of-range tick label artists can exist but will not be rendered.
        if b.x0 < -1 or b.x1 > fw+1 or b.y0 < -1 or b.y1 > fh+1:
            outside.append(text.get_text())
    header_overlaps = []
    for i,a in enumerate(headers):
        for b in headers[i+1:]:
            if a.get_window_extent(renderer).padded(.5).overlaps(b.get_window_extent(renderer).padded(.5)):
                header_overlaps.append([a.get_text(), b.get_text()])
    if outside or header_overlaps:
        raise RuntimeError(f'{name}: off-canvas={outside}; overlaps={header_overlaps}')
    check = {'figure_inches': fig.get_size_inches().tolist(), 'outside_text': outside,
             'workload_header_overlaps': header_overlaps, 'png_dpi': 360,
             'font_sizes_pt': sorted({float(t.get_fontsize()) for t in fig.findobj(match=Text)
                                      if t.get_visible() and t.get_text()})}
    check.update(extra or {})
    qa['plot_checks'][name] = check
    for ext in ['png', 'svg', 'pdf']:
        kwargs = {'metadata': {'Title': f'Qwen3.6-35B-A3B — {name}',
                               'Creator': 'Matplotlib; read-only Fig.4 design study'}} if ext == 'pdf' else {}
        fig.savefig(out / f'{name}.{ext}', dpi=360, **kwargs)
    plt.close(fig)


def two_dimensional(hw, ref, order, loads, out, qa):
    w,h = 7.16,3.15
    left,right,bottom,top = .53,.105,.44,.63
    fig = plt.figure(figsize=(w,h))
    ax = fig.add_axes([left/w, bottom/h, (w-left-right)/w, (h-bottom-top)/h])
    x_axis(ax)
    ax.set_yscale('log')
    ax.set_ylim(.75,1150)
    ax.set_yticks([1,10,100,1000], [r'$10^{0}$',r'$10^{1}$',r'$10^{2}$',r'$10^{3}$'])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.tick_params(axis='y', length=3, labelsize=7.5, pad=2, colors='black')
    ax.grid(axis='y', color='#e8e8e8', lw=.45, zorder=0)
    ax.set_xlabel(r'Streaming intensity [B/B]: workload SI; hardware SI$^{*}=\rho/\tau$', fontsize=8, labelpad=4)
    ax.set_ylabel(r'Native streaming ceiling $\rho$ [MB/s]', fontsize=8, labelpad=4)
    headers, guide_positions = workload_guides(ax, loads, fontsize=8)
    fig.text(.04/w, (h-.135)/h, MODEL_NAME + ' · selected operating points', fontsize=9.1,
             weight='bold', ha='left', va='center')
    points = []
    for cid in order:
        color = TECH[cid][1]
        reference = ref[cid]
        for row in [r for r in hw if r['case_id']==cid]:
            x,y = row['RI_star'], row['rho_MB_per_s']
            if row['profile'] != 'reference':
                ax.plot([reference['RI_star'],x], [reference['rho_MB_per_s'],y],
                        color=color, alpha=.66, lw=.7, zorder=2)
                dot = ax.scatter(x,y, s=10, marker='o', facecolors='white',
                                 edgecolors=color, linewidths=.75, zorder=4)
            else:
                dot = ax.scatter(x,y, s=33, marker='o', c=color,
                                 edgecolors='white', linewidths=.45, zorder=5)
            assert np.array_equal(dot.get_offsets()[0].data, [x,y])
            points.append((cid,row['profile'],x,y))
    # Label offsets only; no point movements. Use a deterministic fallback search.
    pref = {
        '01_sram_acim':(8,-10,'left','top'),
        '02_sram_dcim':(8,2,'left','center'),
        '09_gain_cell_edram':(-8,0,'right','center'),
        '08_feram_hfo2':(7,-8,'left','top'),
        '07_pcm':(8,0,'left','center'),
        '10_fenor_3d':(9,0,'left','center'),
        '06_mram':(9,0,'left','center'),
        '05_rram':(9,0,'left','center'),
        '04_nand_3d':(0,-9,'center','top'),
        '03_nor_2d':(0,-10,'center','top'),
    }
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = ax.get_window_extent()
    occupied = []
    pix = [ax.transData.transform((x,y)) for _,_,x,y in points]
    placements = {}
    for cid in order:
        row = ref[cid]
        a = ax.annotate(TECH[cid][0], (row['RI_star'], row['rho_MB_per_s']),
                        xytext=(0,0), textcoords='offset points', fontsize=7.8,
                        color=TECH[cid][1], zorder=7,
                        bbox={'facecolor':'white','edgecolor':'none','alpha':.96,'pad':.45})
        candidates = [pref[cid]]
        for d in [8,12,18,24,30]:
            candidates += [(d,0,'left','center'),(-d,0,'right','center'),
                           (0,-d,'center','top'),(0,d,'center','bottom')]
        for dx,dy,ha,va in candidates:
            a.set_position((dx,dy));a.set_ha(ha);a.set_va(va)
            b = a.get_window_extent(renderer).padded(1)
            inside = bounds.contains(b.x0,b.y0) and bounds.contains(b.x1,b.y1)
            text_free = not any(b.overlaps(bb) for bb in occupied)
            point_free = all(math.hypot(px-np.clip(px,b.x0,b.x1), py-np.clip(py,b.y0,b.y1))>4.3 for px,py in pix)
            if inside and text_free and point_free:
                occupied.append(b)
                placements[cid] = [dx,dy,ha,va]
                break
        else:
            raise RuntimeError(f'No point-label placement for {cid}')
    note = direction_note(ax, y=.055, fontsize=7.0)
    # Only native hardware uses the rho axis. There are no workload y limits.
    handles = [Line2D([],[],ls='none',marker='o',ms=4.4,mfc='#4c4c4c',mec='white',mew=.4,label='Reference'),
               Line2D([],[],ls='none',marker='o',ms=3,mfc='white',mec='#4c4c4c',mew=.7,label='Paired alternatives')]
    leg = ax.legend(handles=handles, loc='upper right', bbox_to_anchor=(.994,.985),
                     frameon=True, fancybox=False, edgecolor='none', facecolor='white', framealpha=.98,
                     ncol=2, fontsize=7.1, handletextpad=.35, handlelength=.85, columnspacing=1.1, borderpad=.2)
    fig.canvas.draw()
    for obj in [note, leg]:
        bb = obj.get_window_extent(renderer).padded(1)
        assert not any(bb.contains(px,py) for px,py in pix), 'Annotation covers a hardware point'
        assert not any(bb.overlaps(b) for b in occupied), 'Annotation covers a technology label'
    save_figure(fig, 'Qwen36_six_lines_SI_rho_double', out, qa, headers,
                {'hardware_points':points, 'all_30_native_paired_coordinates_exact':True,
                 'workload_guide_positions':guide_positions, 'technology_label_offsets':placements,
                 'no_technology_label_or_dot_collisions':True,
                 'no_workload_throughput_requirement_implied':True})


def one_dimensional(hw, ref, order, loads, out, qa):
    # Preserve the supplied ten-row / six-guide design at actual column width.
    # Space comes from the short title and tighter outer margins, not point shifts.
    w,h = 3.5,3.08
    left,right,bottom,top = .735,.075,.56,.48
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
    title=fig.text(.04/w,(h-.105)/h,MODEL_NAME,fontsize=8.6,
             weight='bold',ha='left',va='center')
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
    legend=fig.text(.045/w,.072/h,'● Reference; segment: three native scenarios.',fontsize=7.0,va='center')

    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    annotations=[title,*headers,*value_labels,note,xlabel,legend]
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
    save_figure(fig,'Qwen36_six_lines_shared_SI_single',out,qa,headers,
                {'reference_points':10,'scenario_range_includes_all_30_values':True,
                 'workload_guide_positions':guide_positions,'hardware_ranges':plotted_ranges,
                 'annotation_overlaps':collisions,'no_point_or_range_masking':True,
                 'two_line_workload_labels':True,
                 'scope':'Raw native SI* versus model logical SI; no deployment correction.'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'figures')
    parser.add_argument('--variant',choices=['single','double','both'],default='single',
                        help='Only the selected single-column Fig.4 is redrawn by default.')
    parser.add_argument('--install-paper',action='store_true',
                        help='Copy the single-column PNG/SVG/PDF to the existing paper figure stem; never edit TeX.')
    args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    (ROOT/'qa').mkdir(exist_ok=True)
    hw,ref,order,loads,qa=load_data()
    configure()
    if args.variant in ('double','both'):
        two_dimensional(hw,ref,order,loads,out,qa)
    if args.variant in ('single','both'):
        one_dimensional(hw,ref,order,loads,out,qa)
    if args.install_paper:
        if args.variant=='double':
            parser.error('--install-paper requires the single-column variant')
        paper_figures=ROOT.parents[3]/'papers'/'figures'
        assert (paper_figures/'critical_reuse.tex').exists()
        for ext in ('png','svg','pdf'):
            shutil.copy2(out/f'Qwen36_six_lines_shared_SI_single.{ext}',
                         paper_figures/f'critical_reuse_single.{ext}')
        qa['paper_install']={'stem':'papers/figures/critical_reuse_single',
                             'figure_label_unchanged':'fig:critical-reuse',
                             'tex_files_edited':False}
    (ROOT/'qa'/'validation.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Created {args.variant} variant in PNG, SVG, and PDF.')
    print('Selected SI:',', '.join(f'{r["SI"]:.9g}' for r in loads))
    print('Reference streaming-side counts:',qa['reference_streaming_counts'])
    print('Output:',out)

if __name__=='__main__':
    main()

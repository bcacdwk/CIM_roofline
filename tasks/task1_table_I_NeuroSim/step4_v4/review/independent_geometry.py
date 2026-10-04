#!/usr/bin/env python3
"""Independent reviewer geometry check, including actual SVG marker coordinates."""
from pathlib import Path
import math,json,sys,xml.etree.ElementTree as ET,hashlib
root=Path(sys.argv[1]).resolve(); figs=root/'figures'
rows=json.loads((root/'summary.json').read_text())['case_results']; byid={r['paired_id']:r for r in rows}
g=json.loads((figs/'geometry.json').read_text());points=json.loads((figs/'plot_points.json').read_text())['case_results']
checks=[]
def near(label,a,b,tol=1e-9):
    passed=abs(a-b)<tol;checks.append({'label':label,'actual':a,'independent_expected':b,'passed':passed})
    if not passed:raise AssertionError((label,a,b))
def logxy(r):return math.log10(r['tau_MB_per_s']),math.log10(r['rho_MB_per_s'])
for p in points: assert p==byid[p['paired_id']]
for c in g['circle_specs']:
    group={r['scenario']:r for r in rows if r['case_id']==c['case_id']}
    a=logxy(group['optimistic']);b=logxy(group['pessimistic']);p=logxy(group['reference'])
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    assert length>1e-12 and c['fallback_reason'] is None
    normal=(-dy/length,dx/length);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
    normal_pos=(p[0]-mid[0])*normal[0]+(p[1]-mid[1])*normal[1]
    center=(mid[0]+normal_pos*normal[0],mid[1]+normal_pos*normal[1]);radius=math.dist(center,a)
    near(c['case_id']+'/cx',c['center_log10'][0],center[0]);near(c['case_id']+'/cy',c['center_log10'][1],center[1]);near(c['case_id']+'/radius',c['radius_decades'],radius)
    assert math.dist(center,p)<=radius+1e-10
    for s in ('optimistic','reference','pessimistic'):
        record=next(x for x in c['paired_points'] if x['scenario']==s)
        assert record['paired_id']==group[s]['paired_id'];xy=logxy(group[s])
        near(record['paired_id']+'/logtau',record['log10_tau'],xy[0]);near(record['paired_id']+'/logrho',record['log10_rho'],xy[1])
for name in ('rho_tau_pairs','rho_tau_circles'):
    a=g['figures'][name];xmin,xmax=a['x_limits_log10'];ymin,ymax=a['y_limits_log10'];bx,by,bw,bh=a['axes_display_bounds_px'];dpi=a['figure_dpi'];fig_h=a['figure_size_inches'][1]*72
    xscale=bw/(xmax-xmin);yscale=bh/(ymax-ymin)
    near(name+'/actual_scale_equality',xscale,yscale,1e-7);near(name+'/45degree',math.degrees(math.atan2(yscale,xscale)),45)
    xml=ET.parse(figs/(name+'.svg'));ns='{http://www.w3.org/2000/svg}'
    collections=[x for x in xml.iter(ns+'g') if x.get('id','').startswith('PathCollection_')]
    assert len(collections)==9
    expected=[]
    for r in rows:
        x,y=logxy(r);sx=(bx+(x-xmin)/(xmax-xmin)*bw)*72/dpi;sy=fig_h-(by+(y-ymin)/(ymax-ymin)*bh)*72/dpi
        expected.append((r,sx,sy))
    colors={'ns_sram_acim':'#3176a7','ns_sram_dcim':'#c46b27','ns_rram_1t1r':'#38866b'}
    for collection in collections:
        marks=list(collection.iter(ns+'use'));assert len(marks)==1
        sx=float(marks[0].get('x'));sy=float(marks[0].get('y'))
        match=min(expected,key=lambda e:math.hypot(sx-e[1],sy-e[2]));r,x,y=match
        assert colors[r['case_id']] in marks[0].get('style','')
        near(name+'/'+r['paired_id']+'/svg_x',sx,x,2e-6);near(name+'/'+r['paired_id']+'/svg_y',sy,y,2e-6)
        expected.remove(match)
    assert not expected
    for c in g['circle_specs']:
        cx,cy=c['center_log10'];radius=c['radius_decades'];assert xmin<cx-radius and cx+radius<xmax and ymin<cy-radius and cy+radius<ymax
out={'run':str(root),'all_passed':all(x['passed'] for x in checks),'method':'Independent normal-vector construction; actual SVG PathCollection marker locations and measured axis box; no production plot import','checks':checks,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(Path(__file__).resolve().parent/'independent_geometry.json').write_text(json.dumps(out,indent=2)+'\n')
print('Independent actual SVG / paired geometry audit passed')

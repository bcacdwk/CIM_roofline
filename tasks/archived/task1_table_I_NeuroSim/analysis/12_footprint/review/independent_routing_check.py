#!/usr/bin/env python3
"""Finite abstract-routing checks, not foundry DRC/LVS or extracted electrical proof."""
import argparse,copy,json,math
from pathlib import Path

def rect(r):return (r['x_um'],r['y_um'],r['x_um']+r['width_um'],r['y_um']+r['height_um'])
def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0])+1e-12 and min(a[3],b[3])>max(a[1],b[1])+1e-12
def route_layer(s):
 if s.startswith('M1'):return 'M1'
 if s in ('M2','M3','M4'):return s
 if s=='RRAM top electrode to M3':return 'M3'
 raise ValueError('Unassigned physical metal layer: '+s)
def net_name(net,i,j,cid):
 if net=='GND':return 'GND'
 if net in ('BL','SL'):return net+':col'+str(i)
 if net in ('WL','PL','TBL'):return net+':row'+str(j)
 return net+':cell'+str(i)+','+str(j)
def segment(a,b,w):
 assert a[0]==b[0] or a[1]==b[1]
 return min(a[0],b[0])-w/2,min(a[1],b[1])-w/2,max(a[0],b[0])+w/2,max(a[1],b[1])+w/2

def run_check(inp,results):
 records={**{k+':main':v for k,v in results['case_results'].items()},**results['sensitivity']};summaries=[]
 for name,m in records.items():
  cid,cond=name.split(':',1);c=copy.deepcopy(inp['cases'][cid]);r=c['rules']
  if cond=='loose_rules_20pct':r={k:v*1.2 for k,v in r.items()};c['rules']=r
  elif cond!='main':
   q=next(x for x in c['single_parameter_checks'] if x['id']==cond);obj=c;keys=q['path'].split('.')
   for k in keys[:-1]:obj=obj[k]
   obj[keys[-1]]=q['value']
  width,height=m['width_um'],m['height_um'];R=m['rectangles']
  for z in R:
   x,y,xx,yy=rect(z);assert min(x,y)>=-1e-12 and xx<=width+1e-12 and yy<=height+1e-12,(name,z['name'])
  for dev,t in m['terminal_placement'].items():
   assert t['same_layer_SD_pad_gap_um']>=r['metal_gap_um']-1e-12,(name,dev,'SD pad spacing')
   assert t['actual_source_contact_to_gate_gap_um']>=r['gate_contact_gap_um']-1e-12
   assert t['actual_drain_contact_to_gate_gap_um']>=r['gate_contact_gap_um']-1e-12
  if cid=='08_feram_hfo2':
   cap=next(z for z in R if z['name']=='MFM electrode envelope')
   wl=next(z for z in R if z['name']=='WL_gate contact landing')
   bl=next(z for z in R if z['name']=='BL_source contact landing')
   assert not overlap(rect(cap),rect(wl)) and not overlap(rect(cap),rect(bl)),name
   assert rect(wl)[1]-rect(cap)[3]>=r['electrode_margin_um']-1e-12
   assert rect(cap)[0]-rect(bl)[2]>=r['electrode_margin_um']-1e-12
   capact=next(z for z in R if z['kind']=='storage_device')
   assert math.isclose(capact['width_um']*capact['height_um'],c['capacitor']['active_area_um2'],rel_tol=1e-12)
  # Repeat a 2x2 tile on fixed pitches. Shared row and column lines retain net identity.
  segments=[]
  for i in range(2):
   for j in range(2):
    for q in m['routes']:
     layer=route_layer(q['layer']);net=net_name(q['net'],i,j,cid)
     pts=[[x+i*width,y+j*height] for x,y in q['points_um']]
     for a,b in zip(pts,pts[1:]):segments.append((layer,net,segment(a,b,q['width_um'])))
  for idx,(la,na,a) in enumerate(segments):
   for lb,nb,b in segments[idx+1:]:
    if la==lb and na!=nb:assert not overlap(a,b),(name,'same-metal route short',la,na,nb,a,b)
  required={'WL':('left','right'),'BL':('bottom','top')}
  if cid=='05_rram':required.update({'SL':('bottom','top'),'TBL':('left','right')})
  else:required['PL']=('left','right')
  for net,ports in required.items():
   q=next(q for q in m['routes'] if q['net']==net and tuple(q['boundary_ports'])==ports)
   pts=q['points_um']
   if ports==('left','right'):assert abs(pts[0][0])<1e-12 and math.isclose(pts[-1][0],width)
   else:assert abs(pts[0][1])<1e-12 and math.isclose(pts[-1][1],height)
  summaries.append({'condition':name,'rectangles':len(R),'routed_segments_2x2':len(segments),'SD_and_gate_contact_clearance':True,'gate_and_source_paths_avoid_MFM':True if cid=='08_feram_hfo2' else None,'different_net_same_metal_no_intersection':True,'shared_row_column_ports_continue_on_tile_pitch':True})
 return {'status':'PASS','scope':'Explicit abstract route/landing boxes and 2x2 repeat; not exhaustive foundry DRC/LVS, body/well parasitics or electrical validation','conditions':summaries}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('routing_review.json'));a=p.parse_args();d=run_check(json.load(open(a.input)),json.load(open(a.results)));a.output.write_text(json.dumps(d,indent=2)+'\n');print('PASS',len(d['conditions']),'abstract placement/routing conditions')

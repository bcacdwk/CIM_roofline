#!/usr/bin/env python3
"""Reviewer formulas: no production model imports; source W/L plus explicit tile allocations."""
import argparse,copy,hashlib,json,math
from pathlib import Path

def close(a,b):return math.isclose(a,b,rel_tol=2e-12,abs_tol=2e-12)
def primitive(F,device,r):
 W,L=device['W_um'],device['L_um']
 # Independently read locked NeuroSim one-finger bulk/no-PMOS expression.
 native=2*(1.0+2.8)*F
 height=max(W+2*(1.0+1.6/2)*F,W+2*r['poly_extension_um']+r['field_poly_gap_um'])
 landing=max(r['metal_width_um'],r['contact_um']+2*r['via_enclosure_um'])
 gap=max(r['gate_contact_gap_um'],(landing+r['metal_gap_um']-L-r['contact_um'])/2)
 actual_contact_span=L+2*(r['contact_um']+gap+r['diff_enclosure_um'])
 corrected=max(native+L-F,actual_contact_span)
 return {'native_width_um':native,'length_correction_um':L-F,'contact_span_um':actual_contact_span,'adapted_width_um':corrected,'height_um':height,'gap_um':gap}

def model(cid,c):
 r=c['rules'];F=c['geometry_scale_um'];p={k:primitive(F,v,r) for k,v in c['devices'].items()}
 land=max(r['metal_width_um'],r['contact_um']+2*r['via_enclosure_um']);lane=land+r['metal_gap_um']
 if cid=='05_rram':
  devside=c['rram_landing_side_um']
  inset=max(0,(p['T1']['adapted_width_um']-p['T1']['contact_span_um'])/2)
  drain_center=inset+r['diff_enclosure_um']+1.5*r['contact_um']+2*p['T1']['gap_um']+c['devices']['T1']['L_um']
  core=max(p['T1']['adapted_width_um'],p['T2']['adapted_width_um'],devside+2*r['metal_gap_um'],drain_center+devside/2)
  w=core+2*lane
  h=max(p['T1']['height_um'],devside+2*r['metal_gap_um'])+p['T2']['height_um']+4*lane
  detail={'lane_um':lane,'core_width_um':core,'RRAM_physical_side_is_assumed':True,'T1_gate_length_um':c['devices']['T1']['L_um']}
 else:
  W=c['devices']['access']['W_um'];cap=c['capacitor'];cw=math.sqrt(cap['active_area_um2']*cap['aspect_ratio']);ch=math.sqrt(cap['active_area_um2']/cap['aspect_ratio'])
  ew=cw+2*r['electrode_margin_um'];eh=ch+2*r['electrode_margin_um']
  gtop=r['gate_contact_to_active_um']+r['contact_um']+2*r['gate_contact_enclosure_um']+r['field_poly_gap_um']/2
  btie=r['active_gap_um']+r['contact_um']+2*r['diff_enclosure_um']+r['active_gap_um']/2
  source=r['diff_enclosure_um']+r['contact_um']+r['gate_contact_gap_um']
  access_height=max(p['access']['height_um'],W+gtop+btie)
  cap_y=btie+max(0,(W-eh)/2)
  wl_center=max(btie+W+r['gate_contact_to_active_um']+r['contact_um']/2,cap_y+eh+r['electrode_margin_um']+land/2)
  access_height=max(access_height,wl_center+land/2+r['metal_gap_um']/2)
  access=(lane,0,p['access']['adapted_width_um'],access_height)
  inset=max(0,(p['access']['adapted_width_um']-p['access']['contact_span_um'])/2)
  source_contact_center=inset+r['diff_enclosure_um']+r['contact_um']/2
  cap_x=max(lane+source,lane+source_contact_center+land/2+r['electrode_margin_um'])
  electrode=(cap_x,btie+max(0,(W-eh)/2),ew,eh)
  # Bounding rectangle of independently positioned lower access and upper cap.
  w=max(access[0]+access[2],electrode[0]+electrode[2])+r['metal_gap_um']/2
  h=max(access[3],electrode[1]+electrode[3]+r['metal_gap_um']/2)
  overlap_x=max(0,min(access[0]+access[2],electrode[0]+electrode[2])-max(access[0],electrode[0]))
  overlap_y=max(0,min(access[1]+access[3],electrode[1]+electrode[3])-max(access[1],electrode[1]))
  assert close(cw*ch,cap['active_area_um2'])
  assert overlap_x*overlap_y>0
  detail={'lane_um':lane,'access_rectangle':access,'electrode_rectangle':electrode,'overlap_area_um2':overlap_x*overlap_y,'capacitor_active_area_um2':cw*ch,'capacitor_double_counted':False}
 a=w*h;b=1;f=c['F_mem_nm']/1000
 assert close((a/f**2)*f**2,a) and close((1/a)*a,1)
 return {'width_um':w,'height_um':h,'area_xy_um2':a,'independent_bits':b,'a_bit_um2':a,'density_Mbit_mm2':1/a,'alpha_F2_per_bit':a/f**2,'primitives':p,'details':detail}

def variants(cid,c):
 yield cid+':main',copy.deepcopy(c)
 lo=copy.deepcopy(c);lo['rules']={k:v*1.2 for k,v in lo['rules'].items()};yield cid+':loose_rules_20pct',lo
 for v in c['single_parameter_checks']:
  d=copy.deepcopy(c);path=v['path'].split('.');obj=d
  for k in path[:-1]:obj=obj[k]
  obj[path[-1]]=v['value'];yield cid+':'+v['id'],d

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--primitive-record',type=Path,required=True);ap.add_argument('--producer-results',type=Path,required=True);ap.add_argument('--output',type=Path,default=Path('independent_model_results.json'));arg=ap.parse_args()
 inp=json.load(open(arg.input));rec=json.load(open(arg.primitive_record));producer=json.load(open(arg.producer_results));out={}
 assert inp['cases']['05_rram']['devices']=={'T1':{'W_um':.5,'L_um':.15},'T2':{'W_um':.1,'L_um':.03}}
 assert inp['cases']['08_feram_hfo2']['capacitor']['active_area_um2']==1
 for cid,c in inp['cases'].items():
  for name,setting in variants(cid,c):
   own=model(cid,setting);ref=producer['case_results'][cid] if name.endswith(':main') else producer['sensitivity'][name]
   for k in ['width_um','height_um','area_xy_um2','independent_bits','a_bit_um2','density_Mbit_mm2','alpha_F2_per_bit']:assert close(own[k],ref[k]),(name,k,own[k],ref[k])
   for mid,p in own['primitives'].items():
    got=rec['primitives'][name+':'+mid]
    for k in ['native_width_um','length_correction_um','contact_span_um','adapted_width_um']:assert close(p[k],got[k]),(name,mid,k)
    assert got['fingers']==1
   altered=copy.deepcopy(setting);altered['F_mem_nm']*=2;f2=model(cid,altered)
   assert own['area_xy_um2']==f2['area_xy_um2'] and own['density_Mbit_mm2']==f2['density_Mbit_mm2']
   assert close(own['alpha_F2_per_bit']/4,f2['alpha_F2_per_bit'])
   out[name]=own
 for cid in inp['cases']:
  a=out[cid+':main']['area_xy_um2']
  for name,r in out.items():
   if name.startswith(cid+':'):r['relative_area_change']=r['area_xy_um2']/a-1
 assert out['05_rram:T1_L_180nm']['area_xy_um2']>out['05_rram:main']['area_xy_um2']
 assert out['05_rram:rram_pad_200nm']['area_xy_um2']>out['05_rram:main']['area_xy_um2']
 assert out['05_rram:rram_pad_400nm']['area_xy_um2']>out['05_rram:main']['area_xy_um2']
 assert out['08_feram_hfo2:access_L_0p7um']['primitives']['access']['adapted_width_um']>out['08_feram_hfo2:main']['primitives']['access']['adapted_width_um']
 result={'status':'PASS','method':'Independent formulas from source W/L, locked no-PMOS primitive and declared coordinate allocations; no production imports, no CSV as evidence','cases_and_finite_checks':out,'normalization_only_invariance':True,'input_file_sha256':hashlib.sha256(arg.input.read_bytes()).hexdigest(),'reviewer_fresh_primitive_record_sha256':hashlib.sha256(arg.primitive_record.read_bytes()).hexdigest()}
 arg.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:{'A':v['area_xy_um2'],'response':v['relative_area_change']} for k,v in out.items()},indent=2))
if __name__=='__main__':main()

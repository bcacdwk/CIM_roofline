#!/usr/bin/env python3
"""Separate polarization and current/sampling native component builds. No shared cell model."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
from native_probe import dump,sha,execute
SPEC={
 'gc_current':{'branch':'2DTrainingV2.1','core':'Training_pytorch/NeuroSIM','driver':'src/gc_current_probe.cpp','cpp':['SarADC.cpp','Mux.cpp','RowDecoder.cpp','DFF.cpp','Technology.cpp','FunctionUnit.cpp','formula.cpp','Param.cpp'],'integer':{'technology_nm','temperature_K','adc_lanes','adc_bits','physical_rows','physical_arrays','bank_choices','row_driver_fanout'}},
 'current_sampling':{'branch':'2DTrainingV2.1','core':'Training_pytorch/NeuroSIM','driver':'src/current_sampling_probe.cpp','cpp':['SarADC.cpp','Mux.cpp','SwitchMatrix.cpp','DFF.cpp','Technology.cpp','FunctionUnit.cpp','formula.cpp','Param.cpp'],'integer':{'technology_nm','temperature_K','adc_lanes','adc_bits','active_rows','physical_rows'}},
 'polarization':{'branch':'MLPInferenceV3.0','core':'NeuroSim','driver':'src/polarization_port_probe.cpp','cpp':['SenseAmp.cpp','RowDecoder.cpp','DFF.cpp','Technology.cpp','FunctionUnit.cpp','formula.cpp'],'integer':{'technology_nm','temperature_K','rows','read_columns','destructive_domain_bits','restore_lanes','case_charge_ports','destructive_read'}}}
SPEC['voltage_sense']=dict(SPEC['polarization'])

def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--run-id',required=True)
 p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','/opt/homebrew/bin/g++-16'));a=p.parse_args()
 request=json.loads(a.request.read_text());kind=request['kind'];spec=SPEC[kind];v=request['parameters'];root=a.root.expanduser().absolute();out=root/'runs/step4-v5/components'/(kind+'-'+a.run_id)
 if kind in ('polarization','voltage_sense'):
  if request.get('front_end')=='case_charge_ports':
   if not request.get('source_ids') or not request.get('applicability'):p.error('Case charge ports require source/domain record')
   v['case_charge_ports']=1
   mapping={'BL_external_cap_F':v['BL_wire_extra_cap_F'],'external_access_drain_F':v['HV_access_drain_cap_F_each']*v['rows'],'external_access_R_ohm':v['HV_access_R_ohm'],'decoder_LV_load_F':v['LV_decoder_output_load_F']}
   for key,value in mapping.items():
    if key in v and v[key]!=value:p.error('Conflicting derived charge port '+key)
    v[key]=value
   for key,value in {'access_width_F':1.,'FE_dielectric_cap_F':0.,'plate_read_voltage_V':2.5,'polarization_switch_charge_C':0.,'reference_voltage_V':0.,'settle_error_fraction':.01,'plate_line_cap_F':0.,'plate_current_limit_A':1.,'WL_load_F':v['decoder_LV_load_F'],'WL_high_voltage_V':5.,'switch_min_FE_voltage_V':0.}.items():v.setdefault(key,value)
  for key,value in {'destructive_read':int(kind!='voltage_sense'),'case_charge_ports':0,'external_access_drain_F':0.,'external_access_R_ohm':0.,'decoder_LV_load_F':v.get('WL_load_F',0.)}.items():v.setdefault(key,value)
  if v['case_charge_ports'] and (v['external_access_drain_F']<0 or v['external_access_R_ohm']<=0 or v['decoder_LV_load_F']<=0):p.error('Explicit positive HV access/decoder ports required')
 if kind=='gc_current':
  for key,value in {'external_hold_cap_F':0.,'wwl_gate_load_F':5e-14,'wwl_wire_ohm':10.56,'wwl_driver_target_ohm':50.,'wwl_active_voltage_V':1.0}.items():v.setdefault(key,value)
 if request.get('point_eligibility')!='component_only' or not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Explicit component-only request/run ID required')
 if any(q.is_symlink() for q in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe runtime path')
 for k,x in v.items():
  if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):p.error('Invalid numeric input '+k)
  if k in spec['integer'] and (not isinstance(x,int) or x<0):p.error('Invalid integer '+k)
 if v['technology_nm'] not in (130,90,65,45,32,22) or not 300<=v['temperature_K']<=400:p.error('Unsupported native operating point')
 out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();src=out/'src';src.mkdir();(src/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
 for f in (Path(__file__),own/'native_probe.py',own/spec['driver'],own/'provenance/dependencies.lock.json'):shutil.copy2(f,canon/f.name)
 if kind in ('polarization','voltage_sense'):shutil.copy2(own/'patches/mlp_decoder_consistency.patch',canon/'mlp_decoder_consistency.patch')
 dump(out/'input.json',request);trees=json.loads((root/'worktrees.json').read_text());tree=Path(trees[spec['branch']]);lock=json.loads((own/'provenance/dependencies.lock.json').read_text());dep=next(d for d in lock['branches'] if d['branch']==spec['branch'])
 head=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
 if head!=dep['sha']:raise ValueError('SHA mismatch')
 names=subprocess.check_output(['git','-C',str(tree),'ls-tree','-r','--name-only',head,spec['core']],text=True).splitlines();upstream={}
 for name in names:
  f=Path(name)
  if str(f.parent)!=spec['core'] or f.suffix not in ('.cpp','.h'):continue
  if f.suffix=='.cpp' and f.name not in spec['cpp']:continue
  data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name])
  if (tree/f).read_bytes()!=data:raise ValueError('Modified upstream '+name)
  (src/f.name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
 if kind in ('polarization','voltage_sense'):
  for name in ('Param.h','Param.cpp'):
   data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name]);(out/name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
  execute(['patch','-p1','--batch','-i',own/'patches/mlp_decoder_consistency.patch'],src,out/'patch.log')
 declarations=['#pragma once','namespace request {']
 for key in sorted(v):
  if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key):raise ValueError('Invalid parameter identifier')
  declarations.append('inline constexpr '+('int' if key in spec['integer'] else 'double')+' '+key+' = '+format(v[key],'.17g')+';')
 (src/'request.h').write_text('\n'.join(declarations)+'\n}\n');shutil.copy2(canon/Path(spec['driver']).name,src/'probe.cpp')
 exe=out/'component';cpp=list(sorted(src.glob('*.cpp')))+([out/'Param.cpp'] if kind in ('polarization','voltage_sense') else [])
 argv=[a.cxx,'-std=c++17','-O2','-fopenmp','-I',src,*cpp,'-o',exe];execute(argv,out,out/'build.log');text=execute([exe],out,out/'probe.log')
 if re.search(r'\b(?:Error|ERROR|V5_INVALID)\b',text):raise ValueError('Native model error')
 raw={k:float(x) for k,x in (line.split('=',1) for line in text.splitlines() if '=' in line)}
 if not raw or any(not math.isfinite(x) for x in raw.values()):raise ValueError('Nonfinite/missing native output')
 dump(out/'resolved.json',raw);dump(out/'source_manifest.json',{'kind':kind,'backend':dep,'upstream':upstream,'canonical':{f.name:sha(f) for f in canon.iterdir()},'patched_sources':{f.name:sha(f) for f in src.iterdir() if f.suffix in ('.cpp','.h')},'binary_sha256':sha(exe),'argv':list(map(str,argv))})
 print(json.dumps({'status':'component_only','kind':kind,'formal_point':False,'run_directory':str(out),'eligibility_fields':{k:x for k,x in raw.items() if any(t in k for t in ('valid','compatible','feasible'))}}))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Fresh standalone native digital operators; no SubArray or memory-device simulation."""
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
FIELDS={'technology_nm','temperature_K','logical_K','logical_N','mac_lanes','accumulator_bits','weight_hold_rows','weight_hold_outputs','weight_capture_bits','input_port_bits','resident_port_bits','program_lanes','clock_Hz','operand_route_cap_F','program_control_cap_F'}
INTS=FIELDS-{'clock_Hz','operand_route_cap_F','program_control_cap_F'}

def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--request',type=Path,default=own/'probes/digital_service_request.json');p.add_argument('--run-id',required=True)
 p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','/opt/homebrew/bin/g++-16'))
 a=p.parse_args();root=a.root.expanduser().absolute();out=root/'runs/step4-v5/components'/('digital-'+a.run_id)
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id) or any(q.is_symlink() for q in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe run path')
 request=json.loads(a.request.read_text());v=request['parameters']
 if request.get('point_eligibility')!='component_only' or set(v)!=FIELDS:p.error('Explicit component-only parameter set required')
 for k,x in v.items():
  if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 or (k not in ('operand_route_cap_F','program_control_cap_F') and x==0):p.error('Invalid parameter '+k)
  if k in INTS and not isinstance(x,int):p.error('Integer required '+k)
 if v['technology_nm'] not in (130,90,65,45,32,22) or not 300<=v['temperature_K']<=400:p.error('Unsupported technology/temperature')
 if v['logical_N']%v['mac_lanes'] or v['weight_hold_outputs']%v['mac_lanes'] or v['weight_hold_outputs']>v['logical_N'] or v['weight_hold_rows']>v['logical_K']:p.error('Unsupported lane/held-tile organization')
 for bits,port in ((v['logical_K']*8,v['input_port_bits']),(v['logical_N']*8,v['resident_port_bits']),(v['weight_hold_rows']*v['weight_hold_outputs']*8,v['weight_capture_bits']),(v['logical_N']*8,v['program_lanes'])):
  if bits%port:p.error('Whole transfer groups required by current component contract')
 out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();src=out/'src';src.mkdir();(src/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
 for f in (Path(__file__),own/'native_probe.py',own/'src/digital_service_probe.cpp',own/'patches/mlp_decoder_consistency.patch',own/'provenance/dependencies.lock.json'):shutil.copy2(f,canon/f.name)
 dump(out/'input.json',request)
 trees=json.loads((root/'worktrees.json').read_text());tree=Path(trees['MLPInferenceV3.0']);lock=json.loads((own/'provenance/dependencies.lock.json').read_text());dep=next(d for d in lock['branches'] if d['branch']=='MLPInferenceV3.0')
 head=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
 if head!=dep['sha']:raise ValueError('SHA mismatch')
 names=subprocess.check_output(['git','-C',str(tree),'ls-tree','-r','--name-only',head,'NeuroSim'],text=True).splitlines();hashes={}
 for name in names+['Param.h','Param.cpp']:
  f=Path(name)
  if f.suffix not in ('.cpp','.h'):continue
  data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name])
  if (tree/f).read_bytes()!=data:raise ValueError('Modified upstream '+name)
  target=(src/f.name) if f.parent==Path('NeuroSim') else out/f.name;target.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
 patch=own/'patches/mlp_decoder_consistency.patch';execute(['patch','-p1','--batch','-i',patch],src,out/'patch.log')
 declaration=['#pragma once','namespace request {']
 for key in sorted(v):declaration.append('inline constexpr '+('int' if key in INTS else 'double')+' '+key+' = '+format(v[key],'.17g')+';')
 (src/'request.h').write_text('\n'.join(declaration)+'\n}\n');shutil.copy2(own/'src/digital_service_probe.cpp',src/'probe.cpp')
 exe=out/'digital_probe';argv=[a.cxx,'-std=c++17','-O2','-fopenmp','-I',src,*sorted(src.glob('*.cpp')),out/'Param.cpp','-o',exe]
 execute(argv,out,out/'build.log');text=execute([exe],out,out/'probe.log')
 if re.search(r'\b(?:Error|ERROR|V5_INVALID)\b',text):raise ValueError('Native error')
 raw={k:float(x) for k,x in (line.split('=',1) for line in text.splitlines() if '=' in line)}
 if not raw or any(not math.isfinite(x) for x in raw.values()) or raw.get('native_digital_area_m2',0)<=0:raise ValueError('Invalid native outputs')
 dump(out/'resolved.json',raw);dump(out/'source_manifest.json',{'backend':dep,'upstream':hashes,'canonical':{f.name:sha(f) for f in canon.iterdir()},'patched_sources':{f.name:sha(f) for f in src.iterdir() if f.suffix in ('.cpp','.h')},'binary_sha256':sha(exe),'argv':list(map(str,argv))})
 result={'status':'component_only','formal_point':False,'run_directory':str(out),'clock_budget_satisfied':bool(raw['digital_clock_budget_satisfied']),'minimum_period_s':raw['digital_halfcycle_min_period_s'],'held_weight_bits':raw['weight_hold_bits'],'native_area_m2':raw['native_digital_area_m2']}
 dump(out/'component_result.json',result);print(json.dumps(result))
if __name__=='__main__':main()

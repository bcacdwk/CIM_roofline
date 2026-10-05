#!/usr/bin/env python3
"""Fresh locked native array/periphery build; diagnostic outputs only, never Roofline rates."""
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

FIELDS=('technology_nm','device_node_nm','temperature_K','rows','cols','read_mux','write_mux',
        'resistance_on_ohm','resistance_off_ohm','access_resistance_ohm','cell_pitch_x_m',
        'cell_pitch_y_m','read_voltage_V','access_voltage_V','write_port_voltage_V',
        'wire_ohm_per_m','clock_Hz','extra_column_cap_F','sense_threshold_V','precharge_width_F','precharge_error_fraction','input_port_bits','resident_port_bits','read_mux_IR_fraction','write_mux_target_ohm','write_current_A')
INTS=set(FIELDS[:7])|{'input_port_bits','resident_port_bits'}

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def execute(argv,cwd,log):
    r=subprocess.run(list(map(str,argv)),cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     env=dict(os.environ,TMPDIR=str(cwd/'tmp'),PYTHONDONTWRITEBYTECODE='1'))
    log.write_text(r.stdout)
    if r.returncode:raise RuntimeError(str(log)+': exit '+str(r.returncode))
    return r.stdout

def main():
    own=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,default=own/'probes/binary_port_request.json')
    p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))))
    p.add_argument('--run-id',required=True)
    p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','/opt/homebrew/bin/g++-16'))
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Invalid run ID')
    root=a.root.expanduser().absolute();out=root/'runs/step4-v5/p1'/('integrator-'+a.run_id)
    for target in (out,*out.parents):
        if target.is_symlink():p.error('Symlink in runtime path: '+str(target))
    out=out.resolve();root=root.resolve()
    if root not in out.parents or any(x in str(out) for x in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe local runtime root')
    request=json.loads(a.request.read_text());v=request['parameters']
    if request.get('point_eligibility')!='probe_only':p.error('This entry is diagnostic only')
    if set(v)!=set(FIELDS):p.error('Probe requires exact authoritative field set')
    for k,x in v.items():
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 or (k!='extra_column_cap_F' and x==0):p.error('Invalid '+k)
        if k in INTS and (not isinstance(x,int)):p.error('Integer required '+k)
    if v['technology_nm'] not in (130,90,65,45,32,22):p.error('Unsupported CMOS process')
    if not 300<=v['temperature_K']<=400:p.error('Unsupported temperature')
    if v['rows']<2 or v['read_mux']<2 or v['write_mux']<2 or v['cols']%(8*v['read_mux']) or v['cols']%v['write_mux']:p.error('Native probe shape/mux unsupported')
    if not 0<v['read_mux_IR_fraction']<=1:p.error('Read MUX fraction must be in (0,1]')
    if not 0<v['precharge_error_fraction']<1:p.error('Precharge error fraction must be in (0,1)')
    if (v['rows']*8)%v['input_port_bits'] or v['cols']%v['resident_port_bits']:p.error('Whole input/target port groups required in API v1')
    if v['resistance_on_ohm']>=v['resistance_off_ohm']:p.error('Binary states must be distinct and ordered')
    out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();src=out/'src';src.mkdir();(src/'tmp').mkdir();canonical=out/'canonical';canonical.mkdir()
    for f in (Path(__file__),own/'src/native_binary_probe.cpp',own/'provenance/dependencies.lock.json',own/'patches/mlp_binary_column_load.patch',own/'patches/mlp_decoder_consistency.patch',own/'patches/mlp_single_row_mux_and_write_target.patch'):
        shutil.copy2(f,canonical/f.name)
    dump(out/'input.json',request)
    lock=json.loads((own/'provenance/dependencies.lock.json').read_text())
    dep=next(x for x in lock['branches'] if x['branch']=='MLPInferenceV3.0')
    trees=json.loads((root/'worktrees.json').read_text());tree=Path(trees[dep['branch']])
    head=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
    if head!=dep['sha']:raise ValueError('Dependency SHA mismatch')
    names=subprocess.check_output(['git','-C',str(tree),'ls-tree','-r','--name-only',head,'NeuroSim'],text=True).splitlines()
    upstream={}
    for name in names:
        rel=Path(name)
        if rel.parent!=Path('NeuroSim') or rel.suffix not in ('.cpp','.h'):continue
        data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name])
        if (tree/name).read_bytes()!=data:raise ValueError('Original upstream modified: '+name)
        (src/rel.name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
    for name in ('Param.h','Param.cpp'):
        data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name])
        if (tree/name).read_bytes()!=data:raise ValueError('Original upstream modified: '+name)
        (out/name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
    patches=[own/'patches/mlp_binary_column_load.patch',own/'patches/mlp_decoder_consistency.patch',own/'patches/mlp_single_row_mux_and_write_target.patch']
    for patch in patches:
        execute(['patch','-p1','--batch','-i',patch],src,out/(patch.stem+'.log'))
    declarations=['#pragma once','namespace request {']
    for k in FIELDS:
        declarations.append('inline constexpr '+('int' if k in INTS else 'double')+' '+k+' = '+format(v[k],'.17g')+';')
    (src/'request.h').write_text('\n'.join(declarations)+'\n}\n')
    shutil.copy2(own/'src/native_binary_probe.cpp',src/'probe.cpp')
    exe=out/'native_probe';argv=[a.cxx,'-std=c++17','-O2','-fopenmp','-I',src,*sorted(src.glob('*.cpp')),out/'Param.cpp','-o',exe]
    execute(argv,out,out/'build.log');raw=execute([exe],out,out/'probe.log')
    if re.search(r'\b(?:Error|ERROR|V5_INVALID)\b',raw):raise RuntimeError('Native model reported an error')
    values={}
    for line in raw.splitlines():
        if '=' not in line:continue
        k,x=line.split('=',1)
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',k):
            values[k]=float(x)
            if not math.isfinite(values[k]):raise ValueError('Nonfinite native field '+k)
    for k in ('native_area_m2','array_BL_cap_F','native_SA_s','actual_access_width_m','port_delta_I_A','adapted_read_aggregate_s'):
        if values.get(k,0)<=0:raise ValueError('Missing/invalid native field '+k)
    bindings={'rows':'input_rows','cols':'input_cols','temperature_K':'input_temperature_K','technology_nm':'input_technology_nm','device_node_nm':'input_device_node_nm','read_voltage_V':'input_read_voltage_V','resistance_on_ohm':'input_Ron_ohm','resistance_off_ohm':'input_Roff_ohm','access_resistance_ohm':'input_access_ohm','cell_pitch_x_m':'input_pitch_x_m','cell_pitch_y_m':'input_pitch_y_m','wire_ohm_per_m':'input_wire_ohm_per_m','read_mux':'input_read_mux','write_mux':'input_write_mux','clock_Hz':'input_clock_Hz','access_voltage_V':'input_access_voltage_V','write_port_voltage_V':'input_write_port_voltage_V','extra_column_cap_F':'input_extra_column_cap_F','sense_threshold_V':'sense_threshold_V','precharge_width_F':'input_precharge_width_F','precharge_error_fraction':'input_precharge_error_fraction','input_port_bits':'input_port_bits','resident_port_bits':'resident_port_bits','read_mux_IR_fraction':'input_read_mux_IR_fraction','write_mux_target_ohm':'input_write_mux_target_ohm','write_current_A':'input_write_current_A'}
    checks={k:{'requested':v[k],'actual':values[field],'matches':math.isclose(v[k],values[field],rel_tol=1e-12,abs_tol=0)} for k,field in bindings.items()}
    if not all(x['matches'] for x in checks.values()):raise ValueError('Input-consumption mismatch')
    dump(out/'resolved.json',values);dump(out/'consumption.json',checks)
    dump(out/'source_manifest.json',{'backend':dep,'upstream_hashes':upstream,'canonical_hashes':{f.name:sha(f) for f in canonical.iterdir()},'input_sha256':sha(out/'input.json'),'request_header_sha256':sha(src/'request.h'),'executable_sha256':sha(exe),'argv':list(map(str,argv)),'patched_source_hashes':{f.name:sha(f) for f in src.iterdir() if f.suffix in ('.cpp','.h')},'patches':[{'path':patch.name,'sha256':sha(patch)} for patch in patches]})
    result={'status':'probe_only','formal_point':False,'run_directory':str(out),'native_read_aggregate_s':values['native_read_aggregate_s'],'adapted_read_aggregate_s':values['adapted_read_aggregate_s'],'passive_threshold_reachable':bool(values['passive_threshold_reachable']),'sense_qualification':('passive peak clears threshold; noise/offset/reference unqualified' if values['passive_threshold_reachable'] else 'INFEASIBLE for passive unregulated port at native threshold; regulated port not modeled'),'remaining':['reference/clamp electrical implementation','complete signed schedule and control','write current capability and waveform','independent physical review']}
    dump(out/'probe_result.json',result);print(json.dumps(result))
if __name__=='__main__':main()

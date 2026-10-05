#!/usr/bin/env python3
"""P2 threshold-FET network -> native terminal periphery, isolated from frozen P1."""
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


def network(p):
    vt=.025852*p['temperature_K']/300
    def ids(vg,vd,vs,vth):
        vds=max(0.,vd-vs);over=vg-vs-vth
        if over<=0:return p['leakage_I0_A']*math.exp(over/(p['subthreshold_factor']*vt))*(-math.expm1(-vds/vt))
        return p['beta_A_per_V2']*(over*vds-.5*vds*vds) if vds<over else .5*p['beta_A_per_V2']*over*over
    length=p['rows']*p['row_pitch_m']+p['layers']*p['layer_pitch_m']
    rbl=length*p['wire_res_ohm_per_m']+p['mux_target_ohm']
    def column(state,vs):
        lo,hi=0.,p['drain_rail_V']
        for _ in range(70):
            vd=(lo+hi)/2
            selected=ids(p['selected_gate_V'],vd,vs,p['threshold_low_V'] if state==0 else p['threshold_high_V'])
            off=(p['rows']*p['layers']-1)*ids(p['unselected_gate_V'],vd,vs,p['threshold_low_V'])
            if vd+rbl*(selected+off)>p['drain_rail_V']:hi=vd
            else:lo=vd
        return selected,off,vd
    result={}
    for state in (0,1):
        lo,hi=p['source_rail_V'],p['drain_rail_V']
        for _ in range(70):
            vs=(lo+hi)/2;i,off,vd=column(state,vs)
            predicted=p['source_rail_V']+p['shared_source_ohm']*p['cols']*(i+off)
            if vs>predicted:hi=vs
            else:lo=vs
        result[str(state)]={'selected_current_A':i,'unselected_current_A':off,'total_current_A':i+off,'actual_drain_V':vd,'actual_source_V':vs,'actual_Vds_V':vd-vs,'actual_Vgs_V':p['selected_gate_V']-vs}
    gate=p['cols']*(p['cell_gate_cap_F']+p['column_pitch_m']*p['wire_cap_F_per_m'])
    bl=p['rows']*p['layers']*p['cell_drain_cap_F']+length*p['wire_cap_F_per_m']
    sl=p['rows']*p['layers']*p['cols']*p['cell_source_cap_F']+p['cols']*p['column_pitch_m']*p['wire_cap_F_per_m']
    return result,{'actual_gate_load_F':gate,'actual_BL_load_F':bl,'actual_SL_load_F':sl,
                   'sense_current_high_A':result['0']['total_current_A'],'sense_current_low_A':result['1']['total_current_A']}

def main():
    own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,default=own/'probes/threshold_port_request.json');p.add_argument('--run-id',required=True)
    p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','/opt/homebrew/bin/g++-16'))
    a=p.parse_args();root=a.root.expanduser().absolute();out=root/'runs/step4-v5/p2'/('integrator-'+a.run_id)
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Invalid run ID')
    if any(x.is_symlink() for x in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe run root')
    request=json.loads(a.request.read_text());parameters=request['parameters']
    defaults={'gate_driver_width_F':32.,'precharge_width_F':16.,'reference_switch_target_ohm':1000.,'precharge_voltage_V':parameters.get('drain_rail_V',0.1),'precharge_error_fraction':.002}
    for key,value in defaults.items():parameters.setdefault(key,value)
    if request.get('point_eligibility')!='probe_only':p.error('Only synthetic/diagnostic probe supported')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in parameters.values()):p.error('Finite numeric parameters required')
    for key in ('technology_nm','temperature_K','rows','cols','layers','read_mux'):
        if not isinstance(parameters[key],int) or isinstance(parameters[key],bool):p.error('Integer required: '+key)
    if parameters['technology_nm'] not in (130,90,65,45,32,22) or not 300<=parameters['temperature_K']<=400:p.error('Unsupported native technology/temperature')
    common_positive=('mux_target_ohm','sense_threshold_V','clock_Hz','gate_driver_width_F','precharge_width_F','reference_switch_target_ohm','precharge_voltage_V','precharge_error_fraction')
    for key in common_positive:
        if parameters[key]<=0:p.error('Positive common port required: '+key)
    if not 0<parameters['precharge_error_fraction']<1:p.error('Precharge error must be in (0,1)')
    if request.get('front_end')!='case_terminal_ports':
        if parameters['drain_rail_V']<=parameters['source_rail_V'] or parameters['threshold_low_V']>=parameters['threshold_high_V']:p.error('Invalid threshold/drain domain')
        for key in ('beta_A_per_V2','leakage_I0_A','subthreshold_factor','cell_gate_cap_F','cell_drain_cap_F','cell_source_cap_F','row_pitch_m','column_pitch_m','layer_pitch_m','wire_cap_F_per_m','wire_res_ohm_per_m','shared_source_ohm'):
            if parameters[key]<=0:p.error('Positive synthetic-model parameter required: '+key)
    if parameters['rows']<1 or parameters['rows']*parameters['layers']<2 or parameters['layers']<1 or parameters['read_mux']<2 or parameters['cols']%parameters['read_mux']:p.error('Unsupported organization')
    out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();src=out/'src';src.mkdir();(src/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
    for f in (Path(__file__),own/'native_probe.py',own/'src/threshold_port_probe.cpp',own/'patches/mlp_decoder_consistency.patch',own/'provenance/dependencies.lock.json'):shutil.copy2(f,canon/f.name)
    dump(out/'input.json',request)
    if request.get('front_end')=='case_terminal_ports':
        if not request.get('frontend_identity') or not request.get('source_ids') or not request.get('applicability'):raise ValueError('Case terminal ports require source identity/domain')
        derived=request['terminal_ports'];ports=request['operating_states']
        required={'actual_gate_load_F','actual_BL_load_F','actual_SL_load_F','sense_current_high_A','sense_current_low_A'}
        if set(derived)!=required or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in derived.values()):raise ValueError('Invalid actual terminal port set')
        model='case-supplied state/terminal compact model; inspected separately from native periphery'
    else:
        ports,derived=network(parameters);model='synthetic level-1/subthreshold shared-source and per-column KCL, not a literature device fit'
    dump(out/'compact_ports.json',{'operating_states':ports,'derived':derived,'model':model})
    if derived['sense_current_high_A']<=derived['sense_current_low_A']:raise ValueError('Invalid sensed state ordering')
    trees=json.loads((root/'worktrees.json').read_text());tree=Path(trees['MLPInferenceV3.0']);lock=json.loads((own/'provenance/dependencies.lock.json').read_text());dep=next(d for d in lock['branches'] if d['branch']=='MLPInferenceV3.0')
    head=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
    if head!=dep['sha']:raise ValueError('SHA mismatch')
    names=subprocess.check_output(['git','-C',str(tree),'ls-tree','-r','--name-only',head,'NeuroSim'],text=True).splitlines();hashes={}
    for name in names+['Param.h','Param.cpp']:
        f=Path(name)
        if f.suffix not in ('.cpp','.h'):continue
        data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name]);target=(src/f.name) if f.parent==Path('NeuroSim') else out/f.name
        if (tree/f).read_bytes()!=data:raise ValueError('Modified upstream '+name)
        target.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    patch=own/'patches/mlp_decoder_consistency.patch';execute(['patch','-p1','--batch','-i',patch],src,out/'patch.log')
    values=dict(parameters,**derived);decl=['#pragma once','namespace request {']
    integers={'technology_nm','temperature_K','rows','cols','layers','read_mux'}
    for key,value in values.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key):raise ValueError('Invalid key')
        decl.append('inline constexpr '+('int' if key in integers else 'double')+' '+key+' = '+format(value,'.17g')+';')
    (src/'request.h').write_text('\n'.join(decl)+'\n}\n');shutil.copy2(own/'src/threshold_port_probe.cpp',src/'probe.cpp')
    exe=out/'threshold_probe';argv=[a.cxx,'-std=c++17','-O2','-fopenmp','-I',src,*sorted(src.glob('*.cpp')),out/'Param.cpp','-o',exe]
    execute(argv,out,out/'build.log');text=execute([exe],out,out/'probe.log')
    if re.search(r'\b(?:Error|ERROR|V5_INVALID)\b',text):raise ValueError('Native model error')
    raw={k:float(v) for k,v in (line.split('=',1) for line in text.splitlines() if '=' in line)}
    if not raw or not all(math.isfinite(v) for v in raw.values()) or raw.get('native_periphery_area_m2',0)<=0:raise ValueError('Invalid native output')
    dump(out/'resolved.json',raw);dump(out/'source_manifest.json',{'backend':dep,'upstream':hashes,'canonical':{f.name:sha(f) for f in canon.iterdir()},'patched_sources':{f.name:sha(f) for f in src.iterdir() if f.suffix in ('.cpp','.h')},'binary_sha256':sha(exe),'argv':list(map(str,argv))})
    result={'status':'probe_only','run_directory':str(out),'formal_point':False,'active_layers':1,'native_gate_driver_compatible':bool(raw['native_gate_driver_compatible']),'state_currents_A':[derived['sense_current_high_A'],derived['sense_current_low_A']],'limitations':[('case terminal physics requires independent review' if request.get('front_end')=='case_terminal_ports' else 'synthetic FET model, no measured calibration'),'compact lower-rail gate/precharge and reference TG require case transient qualification; HV/program service separate','VSA current carrier is local operator only, never string/FET transient resistance']}
    dump(out/'probe_result.json',result);print(json.dumps(result))
if __name__=='__main__':main()

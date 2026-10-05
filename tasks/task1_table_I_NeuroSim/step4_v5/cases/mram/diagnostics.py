#!/usr/bin/env python3
"""Local electrical/encoding diagnostics. Independent review is a different role."""
import json, argparse, importlib.util, hashlib
from pathlib import Path
sp=importlib.util.spec_from_file_location('mram_adapter',Path(__file__).with_name('case_adapter.py'))
a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def run(case_run,out):
 res=json.loads((case_run/'input.json').read_text());n=json.loads((case_run/'resolved.json').read_text());p=res['resolved_parameters'];m=a.model(p)
 r=a.transient_reference(p,n,m);half=dict(p,read_integrator_step_s=p['read_integrator_step_s']/2);r2=a.transient_reference(half,n,m)
 doubled=dict(n,sa_effective_node_cap_F=2*n['sa_effective_node_cap_F']);rload=a.transient_reference(p,doubled,m)
 c=r['capture'];bit_p=int(c['V_P_V']<c['V_ref_V']);bit_ap=int(c['V_AP_V']<c['V_ref_V']);mismatch=0
 for w in range(-128,128):
  word=w%256
  decoded=sum((bit_p if (word>>b)&1 else bit_ap)*(1<<b) for b in range(8));signed=decoded-(256 if decoded&128 else 0)
  for x in range(-128,128):
   got=sum((((x%256)>>b)&1)*signed*((1<<b) if b<7 else -128) for b in range(8))
   mismatch+=got!=x*w
 mos={'vdd':n['actual_tech_vdd_V'],'vth':n['actual_tech_vth_V'],'rwire':n['array_col_res_ohm']+n['write_column_TG_ohm']+a.local_return(p),'shared_return_ohm':a.strap(p,n),'active_lanes':int(p['write_lanes'])}
 pulse_results=[]
 for target in [-1,1]:
  for dt in [1e-10,5e-11]:
   q=a.u.pulse(-target,-target*p['write_port_voltage_V'],500e-9,p['access_resistance_ohm'],dt,1e-9,False,m,mos);q.pop('trace');q['dt_s']=dt;q['target']=target;pulse_results.append(q)
 failed=a.u.pulse(-1,-p['write_port_voltage_V'],160e-9,p['access_resistance_ohm'],1e-10,1e-9,False,m,mos);failed.pop('trace')
 stress=[]
 # Deliberately longer constant positive read than a single developed request;
 # deterministic state stability only, no simulated probability or measured read-disturb claim.
 read_mos=dict(mos,rwire=n['array_col_res_ohm']+n['actual_mux_res_ohm']+a.local_return(p),active_lanes=int(p['cols']),shared_background_wire_ohm=n['array_col_res_ohm']+a.local_return(p))
 for init in [-1,1]:
  q=a.u.pulse(init,p['read_voltage_V'],1e-6,p['access_resistance_ohm'],2e-10,0,False,m,read_mos);q.pop('trace');stress.append(q)
 result={'status':'author_diagnostics_not_independent_review','case_snapshot':str(case_run),'bit_decisions':{'P':bit_p,'AP':bit_ap},'signed_scalar_pairs':65536,'mismatches':mismatch,'read_step_refinement':{'step_s':p['read_integrator_step_s'],'base_develop_s':r['develop_s'],'half_step_develop_s':r2['develop_s'],'base_margin_V':r['max_worst_margin_V'],'half_step_margin_V':r2['max_worst_margin_V']},'physical_C_counterfactual':{'base_F':n['sa_effective_node_cap_F'],'double_F':doubled['sa_effective_node_cap_F'],'base_develop_s':r['develop_s'],'doubled_develop_s':rload['develop_s']},'write_convergence':pulse_results,'failed_short_source_degenerated_pulse':failed,'read_stress_model_only':stress,'limitations':['Original UMEM soft clipping can allow rawstate slightly outside±1;no manual truth clipping used.','Readstress is no-thermal deterministic stability;not physical BER.','Source-degeneratedMOS adapter lacksbodyeffect calibration;bankterminalis0..0.6V gate1.1V.'],'source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Path(__file__).with_name('case_adapter.py'),Path(__file__).with_name('umem_port.py')]}}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'out':str(out),'mismatches':mismatch,'read_develop_ns':r['develop_s']*1e9,'doubleC_develop_ns':rload['develop_s']*1e9,'negative160ns_final':failed['final_state']}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--case-run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 if 'CloudStorage' in str(args.out.resolve()):raise SystemExit('diagnosticoutputmuststaylocal')
 run(args.case_run,args.out)

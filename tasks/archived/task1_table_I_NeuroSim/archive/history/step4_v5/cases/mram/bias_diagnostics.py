#!/usr/bin/env python3
"""Author electrical crosschecks; never an independent-review substitute."""
import json,math,argparse,importlib.util,hashlib
from pathlib import Path
sp=importlib.util.spec_from_file_location('mram_case',Path(__file__).with_name('case_adapter.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def run(run_dir,out):
 r=json.loads((run_dir/'input.json').read_text());p=r['resolved_parameters'];n=json.loads((run_dir/'resolved.json').read_text());m=a.model(p);q=a.native_mos(n);port=a.bias_port(p,n,m,True)
 sat=port.mos(q['vdd'],q['vdd'],q['beta_access']);anchors={'native_Ion_A':n['actual_access_Ion_at_native_bias_A'],'compact_Ion_A':sat,'effective_R_ohm':n['input_access_ohm'],'compact_smallVDS_R_ohm':1/(q['beta_access']*(q['vdd']-q['vth'])),'CACTI_multiplier':q['native_effective_R_multiplier']}
 tg=[]
 for cm in [0.,.1,.3,.5,.55,.6]:
  lo=max(0.,cm-5e-7);hi=lo+1e-6;i=port.tg(hi,lo);tg.append({'common_mode_V':cm,'differential_R_ohm':1e-6/i,'source_native_effective_R_ohm':n['write_column_TG_ohm']})
 dc=[]
 for v in [-.6,.6]:
  for s in [-1.,1.]:
   i,vm,_=port(v,s);mag=abs(i);drop=port.cache[v]
   if v>0:
    va=port.inv_mos(mag,q['vdd']-drop,q['beta_access']);node=drop+va+abs(vm)+mag*port.wire;vtg=v-node;available=port.tg(v,node)
   else:
    vtg=port.low_tg_drop(mag);node=vtg+mag*port.wire+abs(vm);va=abs(v)-drop-node;available=port.mos(va,q['vdd']-node,q['beta_access'])
   dc.append({'port_V':v,'state':s,'current_A':i,'MTJ_V':vm,'access_VDS_V':va,'TG_drop_V':vtg,'wire_drop_V':mag*port.wire,'shared_drop_V':drop,'KVL_error_V':abs(v)-(abs(vm)+va+vtg+mag*port.wire+drop),'KCL_error_A':mag-available})
 pulses=[]
 for target in [-1,1]:
  for dt in [1e-10,5e-11]:
   z=a.u.pulse(-target,-target*.6,500e-9,p['access_resistance_ohm'],dt,0,False,m,port);z.pop('trace');z.update(dt_s=dt,target=target,effective_final_state=a.u.state_clamp(z['final_state']));pulses.append(z)
 short=[]
 for target in [-1,1]:
  z=a.u.pulse(-target,-target*.6,40e-9,p['access_resistance_ohm'],1e-10,0,False,m,port);z.pop('trace');z.update(target=target,accepted=z['final_state']*target>=p['accepted_state_magnitude']);short.append(z)
 read=a.transient_reference(p,n,m);rd2=a.transient_reference(dict(p,read_integrator_step_s=p['read_integrator_step_s']/2),n,m)
 ramp={'native_data_ref_enable_edge_s':[n['WL_enable_edge_only_s'],n['reference_isolation_edge_s']],'qualified_step_skew_s':p['reference_enable_skew_bound_s'],'scope':'nominalmatchedstep-port and finiteoffset,not fullfinitegatewaveform/STA validation'}
 res={'status':'author_bias_diagnostics','calibration':anchors,'TG_common_mode':tg,'DC_KCL_KVL':dc,'pulse_step_refinement':pulses,'short_failed_pulses':short,'read_step_refinement':{'base_develop_s':read['develop_s'],'half_step_develop_s':rd2['develop_s'],'base_margin_V':read['max_worst_margin_V'],'half_margin_V':rd2['max_worst_margin_V']},'enable_model_scope':ramp,'limits':['Saturation-anchor square-law extension has no foundry/BSIM/body-effect validation.','Native effective Ron is a delay proxy; oldR-matched adapter is a different sensitivity model,not anerrorbound.','No stochastic switching or real read-disturb BER claimed.'],'source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Path(__file__).with_name('umem_port.py'),Path(__file__).with_name('case_adapter.py')]}}
 out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({'out':str(out),'anchors':anchors,'max_KVL_error':max(abs(x['KVL_error_V']) for x in dc),'max_KCL_error':max(abs(x['KCL_error_A']) for x in dc),'read_margin':read['max_worst_margin_V'],'short40ns_success':[z['accepted'] for z in short]}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);p=ap.parse_args()
 if 'CloudStorage' in str(p.out.resolve()):raise SystemExit('Localoutputs only')
 run(p.run,p.out)

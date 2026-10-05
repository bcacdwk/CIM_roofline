"""Finite-ramp NOR data/reference network; no static V/I transient proxy.
Electrical driver dictionary must be filled from an actual native port snapshot.
Gate-current and TG beta are explicit Ion/W/Vth compact adaptations, not STA.
"""
import math
from threshold_model import fit,ids,geometry,operating_point

def mos(vds,vgs,beta,vth):
 over=max(0.,vgs-vth);v=min(max(0.,vds),over)
 return beta*(over*v-v*v/2)

def tg(hi,lo,gn,gp,bn,bp,vt):
 if hi<=lo:return 0.
 return mos(hi-lo,gn-lo,bn,vt)+mos(hi-lo,hi-gp,bp,vt)

def beta(Ion_per_m,W,vdd,vth):return 2*Ion_per_m*W/(vdd-vth)**2

def integrate(p,table,e,step_s=20e-12):
 """e defines true terminal/load/drive values; no invented defaults accepted.
 Data use exact two-cap constant-current segments in the valid saturation domain.
 Reference uses conservative backward-Euler charge balance with nonlinear TG.
 Its temporal convergence must be checked byhalving stepbeforeformalacceptance.
 """
 required=('vdd_V','vth_V','ion_N_A_per_m','ion_P_A_per_m','mux_N_width_m','mux_P_width_m',
  'reference_N_width_m','reference_P_width_m','reference_gate_N_cap_F','reference_gate_P_cap_F','reference_main_cap_F','reference_internal_cap_F',
  'reference_N_control_tau_s','reference_P_control_tau_s','reference_control_delay_s','reference_N_additional_delay_s','reference_internal_initial_upper_V',
  'gate_P_width_m','gate_total_load_F','gate_control_delay_s','data_BL_cap_F','data_SA_cap_F',
  'precharge_P_width_m','precharge_output_cap_F','precharge_control_delay_s')
 missing=[k for k in required if k not in e]
 if missing:raise ValueError('Actualnativeelectricalportmissing:'+','.join(missing))
 f=fit(table);g=geometry(p);op=operating_point(p,table);vt=e['vth_V'];vdd=e['vdd_V'];rail=p['read_drain_V'];gate=p['read_gate_V']
 bn=beta(e['ion_N_A_per_m'],e['mux_N_width_m'],vdd,vt);bp=beta(e['ion_P_A_per_m'],e['mux_P_width_m'],vdd,vt)
 rn=beta(e['ion_N_A_per_m'],e['reference_N_width_m'],vdd,vt);rp=beta(e['ion_P_A_per_m'],e['reference_P_width_m'],vdd,vt)
 gatebeta=beta(e['ion_P_A_per_m'],e['gate_P_width_m'],vdd,vt)
 Cb=e['data_BL_cap_F'];Cs=e['data_SA_cap_F'];Cm=e['reference_main_cap_F'];Cx=e['reference_internal_cap_F'];Ct=Cb+Cs
 Rr=p['reference_resistance_ohm']+g['source_column_R_ohm']+p['cols']/p['read_mux']*g['source_common_R_ohm']
 gateC=e['gate_total_load_F'];gdC=3.9*8.8541878128e-12/p['equivalent_gate_oxide_m']*p['cell_gate_width_m']*p['gate_overlap_length_m']
 eps=p['precharge_error_fraction'];skew=p['enable_skew_bound_s'];need=p['sense_threshold_V']+p['sense_error_budget_V']
 h=step_s;t=0.;vg=0.;states={}
 for k,offset in enumerate([-skew,0.,skew]):
  for pol in ('P','OFF'):
   ini=rail*(1+eps if pol=='P' else 1-eps)
   states[(k,pol)]={'BL':ini,'SA':ini,'ref':rail*(1-eps if pol=='P' else 1+eps),'x':0. if pol=='P' else e['reference_internal_initial_upper_V'],'offset':offset,'kind':pol,'previous_gate_N':0.,'previous_gate_P':vdd}
 def ref_advance(s,tm):
  dt=tm-e['reference_control_delay_s']-s['offset']
  # Earlyenable prehistory is explicitly integrated fromt<0 below.
  dtn=dt-e['reference_N_additional_delay_s']
  gn=0. if dtn<0 else vdd*(-math.expm1(-dtn/e['reference_N_control_tau_s']))
  gp=vdd if dt<0 else vdd*math.exp(-dt/e['reference_P_control_tau_s'])
  # Conservativegate-injectionenvelope: allunfavourable totalgatecharge
  # mayreachmainnode; favourablecomplementaryinjectionignored. Thisdoesnot
  # claimunknownoverlapC=totalgateC, butboundsitwithoutideal cancellation.
  injection=e['reference_gate_P_cap_F']*(gp-s['previous_gate_P']) if s['kind']=='P' else e['reference_gate_N_cap_F']*(gn-s['previous_gate_N'])
  s['ref']+=injection/Cm;s['previous_gate_N']=gn;s['previous_gate_P']=gp
  decay=1+h/(Cx*Rr);limit=max(0.,(s['ref']-s['x']/decay)/(h/Cm+(h/Cx)/decay))
  lo=0.;hi=limit
  for _ in range(35):
   cur=(lo+hi)/2;vr=s['ref']-h*cur/Cm;vx=(s['x']+h*cur/Cx)/decay
   actual=tg(vr,vx,gn,gp,rn,rp,vt)
   if cur>actual:hi=cur
   else:lo=cur
  cur=(lo+hi)/2;s['ref']-=h*cur/Cm;s['x']=(s['x']+h*cur/Cx)/decay
 # Begin beforeanypermittedreferenceenable; dataWL remainsfullyoff.
 t=-max(skew,0.)
 while t<0:
  for s in states.values():ref_advance(s,t+h/2)
  t+=h
 captures=None;best=(-math.inf,None);worst_early=math.inf;trace=[];domain=True;steps=0
 while t<300e-9:
  oldg=vg
  if t+h/2>=e['gate_control_delay_s']:
   # Gatebuffer pull-up explicitrailVGS, not a generic nativeVdddelay.
   def fg(v):return mos(gate-v,gate,gatebeta,vt)/gateC
   a=fg(vg);b=fg(vg+h*a/2);c=fg(vg+h*b/2);d=fg(vg+h*c);vg=min(gate,vg+h*(a+2*b+2*c+d)/6)
  for key,s in states.items():
   pol=key[1];source=op['source_upper_V'] if pol=='P' else 0.
   current=ids((oldg+vg)/2,s['BL'],source,'erased' if pol=='P' else 'programmed',f,table)
   if pol=='P' and (oldg+vg)/2-source<.25:current=0. # slowONboundbelowfirstmeasuredgate
   if pol=='OFF':current+=op['all_unselected_column_leak_upper_A']
   # Exact localRCsegment withIconstant; dataMUXconductanceusesactualcommonmode.
   center=(s['BL']+s['SA'])/2
   conduct=bn*max(vdd-center-vt,0)+bp*max(center-vt,0)
   if conduct<=0:raise ValueError('ReadTGhasnobiasconductance')
   rm=1/conduct;tau=rm*Cb*Cs/Ct
   diff=s['SA']-s['BL'];mean=(Cb*s['BL']+Cs*s['SA'])/Ct
   mean-=current*h/Ct
   # Conservative ON-side gatefeedthrough raisesBL; OFF omitsbeneficialpositivekick.
   injection=gdC*(vg-oldg) if pol=='P' else 0.
   mean+=injection/Ct;diff-=injection/Cb
   diff=diff*math.exp(-h/tau)+(current/Cb)*tau*(-math.expm1(-h/tau))
   s['BL']=mean-Cs/Ct*diff;s['SA']=mean+Cb/Ct*diff
   ref_advance(s,t+h/2)
   actual_drain=s['BL']-current*g['BL_R_ohm']
   # The gate transitionusessourcecurve; theaccepteddecisionmustlieintheVDsaturationdomain.
   s['Vds']=actual_drain-source;s['Vgs']=vg-source;s['current']=current
  t+=h;steps+=1
  margins=[(s['ref']-s['SA'] if key[1]=='P' else s['SA']-s['ref']) for key,s in states.items()]
  minmargin=min(margins);worst_early=min(worst_early,minmargin) if captures is None else worst_early;in_domain=all(s['Vds']>=.8 and s['BL']<=rail*(1+eps)+.001 for s in states.values())
  if minmargin>best[0]:best=(minmargin,t)
  if captures is None and minmargin>=need and in_domain:
   captures={'time_s':t,'margin_V':minmargin,'gate_V':vg,'contexts':[dict(s,context=str(key)) for key,s in states.items()]}
  if steps%50==0:trace.append([t,vg,minmargin,min(s['Vds'] for s in states.values())])
  if captures and (not in_domain or t>captures['time_s']*2):break
  if not in_domain and t>max(e['gate_control_delay_s'],e['reference_control_delay_s'])+10e-9:break
 return {'feasible':captures is not None and worst_early>-(p['sense_threshold_V']-p['sense_error_budget_V']),'capture':captures,'wrong_polarity_extreme_V':worst_early,'unfavourable_gate_injection_bound_C':{'P':e['reference_gate_P_cap_F']*vdd,'OFF':e['reference_gate_N_cap_F']*vdd},'false_early_latch_excluded':worst_early>-(p['sense_threshold_V']-p['sense_error_budget_V']),'best_margin_V':best[0],'best_time_s':best[1],'required_V':need,'step_s':h,'trace':trace,'data_total_C_F':Ct,'reference_main_C_F':Cm,'reference_internal_C_F':Cx,'reference_R_including_returns_ohm':Rr,'source_upper_V':op['source_upper_V'],'gate_feedthrough_charge_upper_C':gdC*gate,'model':'two-capsaturationdataRC+finiteWLPMOSramp+nonlinearcomplementaryreferenceTGandinternalnode;independentprecharge±error,enable±skew; nooldaccess'}

def precharge_bound(p,table,e):
 """Current-limited PMOS plusworstreadMUX resistance chargesactualtwo-nodeC.
 Conservative lumped totalC andseriesR; allWLoff, referenceisolated. Maximum
 source-figureleakage is retained andequilibrium mustmeetchosenerror beforetiming.
 """
 vdd=e['vdd_V'];vt=e['vth_V'];rail=p['read_drain_V'];eps=p['precharge_error_fraction']
 bn=beta(e['ion_N_A_per_m'],e['mux_N_width_m'],vdd,vt);bp=beta(e['ion_P_A_per_m'],e['mux_P_width_m'],vdd,vt)
 bpre=beta(e['ion_P_A_per_m'],e['precharge_P_width_m'],vdd,vt)
 Rmux=max(1/(bn*max(vdd-v-vt,0)+bp*max(v-vt,0)) for v in [rail*j/1000 for j in range(1001)])
 leak=p['rows']*table['samples'][0]['erased_current_A']
 C=e['data_BL_cap_F']+e['data_SA_cap_F'] # precharge drain alreadyinactualdataSAport; donotaddtwice
 def available(v):
  lo=0.;hi=max(0,(rail-v)/Rmux)
  for _ in range(35):
   i=(lo+hi)/2;pred=mos(rail-v-i*Rmux,rail,bpre,vt)
   if i>pred:hi=i
   else:lo=i
  return (lo+hi)/2
 target=rail*(1-eps);at_target=available(target)
 if at_target<=leak:return {'feasible':False,'target_drive_A':at_target,'unselected_leak_A':leak,'target_V':target}
 count=5000;dv=target/count;t=0.
 for j in range(count):
  v=(j+.5)*dv;t+=C*dv/(available(v)-leak)
 return {'feasible':True,'charge_after_control_valid_s':t,'complete_precharge_s':e['precharge_control_delay_s']+t,'worst_mux_bias_R_ohm':Rmux,'actual_lumped_C_F':C,'target_V':target,'target_drive_A':at_target,'all256rowleak_upper_A':leak,'each_branch_initial_peak_A':available(0),'branches':2*p['cols']//p['read_mux'],'source_current_upper_A':2*p['cols']//p['read_mux']*available(0),'scope':'PMOSsourcerail1V,gate0/1.3;nativeIon/W/Vthcompact;allWL/refOFF;sourcefiguremonotoneleakbound;notNMOSpass1V'}

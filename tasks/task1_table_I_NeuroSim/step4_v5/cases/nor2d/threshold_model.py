"""ESF1 binary threshold-state local model; no legacy access or write time.
Measured transfer points calibrate two fit parameters; C/geometries are explicit
engineering inputs, not values reverse-fitted from old access latency.
"""
import math

def fit(table):
 lo=next(q for q in table['samples'] if q['gate_V']==1.1)
 hi=next(q for q in table['samples'] if q['gate_V']==1.3)
 slope=(math.sqrt(hi['erased_current_A'])-math.sqrt(lo['erased_current_A']))/.2
 threshold=1.1-math.sqrt(lo['erased_current_A'])/slope
 mid=next(q for q in table['samples'] if q['gate_V']==1.2)
 pred=slope*slope*(1.2-threshold)**2
 return {'beta_A_V2':2*slope*slope,'threshold_V':threshold,'fit_gate_V':[1.1,1.3],
  'heldout_gate_V':1.2,'heldout_measured_line_A':mid['erased_current_A'],'heldout_prediction_A':pred,
  'heldout_relative_difference':pred/mid['erased_current_A']-1,
  'qualification':'Fit to measured-figure line centers atVD1V; heldoutpoint is another measured gate, not separate chip or statistical sample.'}

def ids(vg,vd,vs,state,f,table):
 vgs=vg-vs;vds=max(0.,vd-vs)
 if state=='programmed':return table['floor_A']*(-math.expm1(-vds/.026))
 # Native control transition includes subthreshold region; source low-gate
 # transfer supplies this branch rather than an invented threshold cutoff.
 samples=[q for q in table['samples'] if q['gate_V']<=1.1]
 if vgs<1.1:
  if vgs<=samples[0]['gate_V']:
   # Monotone constant upper envelope below measured0.25V, conservative leakage.
   value=samples[0]['erased_current_A']
  else:
   a,b=next((a,b) for a,b in zip(samples,samples[1:]) if a['gate_V']<=vgs<=b['gate_V'])
   q=(vgs-a['gate_V'])/(b['gate_V']-a['gate_V']);value=math.exp(math.log(a['erased_current_A'])*(1-q)+math.log(b['erased_current_A'])*q)
  return value*(-math.expm1(-vds/.026))
 if vgs>1.3+1e-12:raise ValueError('Unsupported read gate')
 over=vgs-f['threshold_V'];vdlin=min(vds,max(0,over))
 return f['beta_A_V2']*(over*vdlin-.5*vdlin*vdlin)

def geometry(p):
 eps0=8.8541878128e-12;epsSi=11.7*eps0;epsOx=3.9*eps0;q=1.602176634e-19
 W=p['cell_gate_width_m'];L=p['cell_gate_length_m'];overlap=p['gate_overlap_length_m'];diff=p['diffusion_length_m']
 cox=epsOx/p['equivalent_gate_oxide_m'];cg=cox*W*(L+2*overlap)
 # Zero bias junction depletion gives conservative upper capacitance for reverse drain/source.
 depletion=math.sqrt(2*epsSi*p['junction_built_in_V']/(q*p['junction_doping_m3']))
 area=W*diff;perimeter=2*(W+diff)
 cd=epsSi*area/depletion+p['junction_sidewall_F_per_m']*perimeter+cox*W*overlap
 lengthBL=p['rows']*p['pitch_y_m'];lengthWL=p['cols']*p['pitch_x_m']
 rbl=lengthBL*p['wire_res_ohm_per_m']
 returnR=p['metal_resistivity_ohm_m']*lengthWL/(p['source_strap_width_m']*p['source_strap_thickness_m'])
 localR=p['metal_resistivity_ohm_m']*lengthBL/(p['source_column_width_m']*p['source_column_thickness_m'])
 coupled=epsOx*p['source_column_width_m']*lengthBL/p['source_BL_spacing_m']
 cbl=p['rows']*cd+lengthBL*p['wire_cap_F_per_m']+coupled+p['other_BL_cap_F']
 return {'cell_gate_C_F':cg,'cell_drain_C_F':cd,'cell_source_C_F':cd,'junction_depletion_m':depletion,
  'gate_load_F':p['cols']*cg+lengthWL*p['wire_cap_F_per_m'],
  'BL_load_F':cbl,'SL_load_F':p['cols']*p['rows']*cd+lengthWL*p['wire_cap_F_per_m'],
  'BL_R_ohm':rbl,'source_common_R_ohm':returnR,'source_column_R_ohm':localR,
  'source_BL_coupling_F':coupled,'array_width_m':lengthWL,'array_height_m':lengthBL,'array_area_m2':lengthWL*lengthBL,
  'area_gate_plus_two_diffusion_m2':W*(L+2*diff),'cell_pitch_area_m2':p['pitch_x_m']*p['pitch_y_m'],
  'C_qualification':'Engineering parallel-plate/depletion/overlap/sidewall compact geometry. EOT/doping/pitch are not ESF1 extracted values or measured capacitances.'}

def operating_point(p,table):
 f=fit(table);g=geometry(p);N=p['cols'];unselected=p['rows']-1
 leakage_bound=table['samples'][0]['erased_current_A']
 # Bounding all physical columns ON uses source atupperreadrail andomitsreadMUX.
 lo=0.;hi=p['read_drain_V']
 for _ in range(70):
  vs=(lo+hi)/2
  current=ids(p['read_gate_V'],p['read_drain_V'],vs,'erased',f,table)+unselected*leakage_bound
  actual=N*current*g['source_common_R_ohm']+current*g['source_column_R_ohm']
  if vs>actual:hi=vs
  else:lo=vs
 source_upper=(lo+hi)/2
 def drain(state,source):
  a=source;b=p['read_drain_V']
  for _ in range(70):
   vd=(a+b)/2;current=ids(p['read_gate_V'],vd,source,state,f,table)
   if state=='programmed':current+=unselected*leakage_bound
   if vd+current*(g['BL_R_ohm']+p['mux_target_ohm'])>p['read_drain_V']:b=vd
   else:a=vd
  return {'I_A':current,'drain_V':vd,'source_V':source,'Vds_V':vd-source,'Vgs_V':p['read_gate_V']-source}
 on=drain('erased',source_upper);off=drain('programmed',0.)
 return {'fit':f,'geometry':g,'erased_slowest':on,'programmed_fastest':off,
  'source_upper_V':source_upper,'unselected_branch_leak_upper_A':leakage_bound,'all_unselected_column_leak_upper_A':unselected*leakage_bound,
  'scope':'ON usesmaximumallcolumnsourceIR;OFF useszeroreturnlowerboundandmaximumunselectedleak; measuredstateatVD1V, saturation-domain extension checked separately.'}

"""PCM-specific all-HV array and bounded port service; no legacy timing inputs."""
import json,math
from pathlib import Path
from hv_port_probe import Port,level_shift_probe,interp
from hv_array_probe import integrate_current_time

def source_data():
 root=Path(__file__).parent
 return json.loads((root/'hv_data.json').read_text()),json.loads((root/'hv_access_data.json').read_text())

def hardware(p):
 data,ad=source_data();port=Port(data);small=Port(dict(data,raw_measured_N_curves=ad['curves']))
 ac=small.caps(ad['W_m'],ad['L_m'],1);big=port.caps(20e-6,.5e-6);pc=port.caps(7e-6,.5e-6)
 rows=p['rows'];cols=p['cols'];L=rows*p['pitch_y_m'];W=cols*p['pitch_x_m'];rho=p['metal_resistivity_ohm_m']
 Rbl=rho*L/(p['BL_width_m']*p['BL_thickness_m']);Rloc=rho*L/(p['source_width_m']*p['source_thickness_m']);Rs=rho*(W*p['source_bus_length_factor'])/(p['source_bus_width_m']*p['source_bus_thickness_m'])
 coupling=3.9*8.8541878128e-12*p['source_width_m']*L/p['source_BL_spacing_m']
 Cwire=L*p['wire_cap_F_per_m']+coupling
 Cbase=rows*ac['drain_upper_F']+Cwire
 # Hot node: readisolation+returnclampdrains andtwoPprogramoutputs.
 Chot=Cbase+2*ac['drain_upper_F']+2*pc['drain_upper_F']
 # Low SA node: other sideofisolation,prechargeN,groundparkingN.
 Clow=3*ac['drain_upper_F']
 Cwl=cols*ac['gate_upper_F']+W*p['wire_cap_F_per_m']
 Clv=16*big['gate_upper_F']
 baseLS=level_shift_probe(port)
 bufferCg=big['gate_upper_F']+4*pc['gate_upper_F'];WLload=Cwl+big['drain_upper_F']+4*pc['drain_upper_F']
 loadedLS=baseLS['switch_after_valid_complementary_inputs_s']*(baseLS['control_node_upper_C_F']+bufferCg)/baseLS['control_node_upper_C_F']
 rise=integrate_current_time(WLload,0,4.95,lambda v:4*port.current('P',5,5-v))
 fall=integrate_current_time(WLload,5,.05,lambda v:port.current('N',5,v))
 rr=.05/small.current('N',4,.05,-2.5)
 peak=small.current('N',5,p['hot_BL_upper_V']);ground=peak*(p['write_lanes']*Rs+Rloc)
 returntime=integrate_current_time(Chot,p['hot_BL_upper_V'],p['read_voltage_V'],lambda v:small.current('N',4,v-ground,-2.5))
 cv=next(r for r in ad['curves'] if r['gate']==4 and r['body']==-2.5);lo=0.;hi=5.
 for _ in range(60):
  v=(lo+hi)/2
  if interp(cv['V'],cv['I'],v)<p['reset_current_A']:lo=v
  else:hi=v
 access_drop=(lo+hi)/2
 compliance=p['hot_BL_upper_V']-access_drop-p['reset_current_A']*(Rbl+Rloc+p['write_lanes']*Rs)
 outcap=2*port.current('P',5,5-p['hot_BL_upper_V'])
 return {'access_W_m':ad['W_m'],'access_L_m':ad['L_m'],'access_C':ac,'Poutput_C':pc,'HV_read_access_R_bound_ohm':rr,'BL_R_ohm':Rbl,'local_source_R_ohm':Rloc,'shared_source_R_ohm':Rs,'wire_and_source_C_F':Cwire,'BL_hot_total_C_F':Chot,'BL_low_extra_C_F':Clow,'BL_wire_extra_for_native_F':Cwire+5*ac['drain_upper_F']+2*pc['drain_upper_F'],'WL_C_F':Cwl,'LV_decoder_load_F':Clv,'levelshift_loaded_s':loadedLS,'levelshift_unloaded':baseLS,'HV_WL_rise_s':rise,'HV_WL_fall_s':fall,'reference_enable_matching_dummy_C_F':W*p['wire_cap_F_per_m'],'HV_return_after_gate_s':returntime,'HV_return_ground_upper_V':ground,'HV_return_peak_group_A':p['write_lanes']*peak,'program_access_drop_V':access_drop,'material_terminal_compliance_V':compliance,'Poutput_current_capacity_A_each':outcap,'off_current_absolute_instrument_bound_A':ad['off_absolute_instrument_bound_A'],'array_area_m2':rows*cols*p['pitch_x_m']*p['pitch_y_m'],'raw_geometry_is_measured':True,'scope':'NewfullHV3umaccessarray;actualmeasuredI-V+separateTTcap;notTiSbTe40nmoriginalmacroorPDKcorners'}

def read_network(p,h,C,dt_factor=300):
 """Three coupled physical source nodes: victim,other127 cells,128references.
 Conditionalacceptedresistancewindowsandfinite±enable/prechargebounds.
 All128columnsareactuallysensed;nohiddenunsensedcolumn deletion.
 """
 S=p['cols'];common=2*h['HV_read_access_R_bound_ohm']+h['BL_R_ohm']+h['local_source_R_ohm'];Rref=p['reference_R_ohm']+common;Rs=h['shared_source_R_ohm'];V=p['read_voltage_V'];err=p['read_initial_error_V'];skew=p['enable_skew_s'];leak=(p['rows']-1)*h['off_current_absolute_instrument_bound_A'];contexts=[]
 for label,R in [('on',p['on_accept_max_ohm']),('off',p['off_accept_min_ohm'])]:
  for others in [p['on_accept_min_ohm'],p['off_accept_max_ohm']]:
   for age in [-skew,0.,skew]:
    initial=[V+err if label=='on' else V-err,V,V-err if label=='on' else V+err]
    x={'label':label,'R':[R+common,others+common,Rref],'counts':[1,S-1,S],'v':initial,'age':age,'leak':[0. if label=='on' else leak,0.,h['off_current_absolute_instrument_bound_A'] if label=='on' else 0.]};contexts.append(x)
 dt=min(min(x['R']) for x in contexts)*C/dt_factor
 def deriv(x,v,ref_active=True,data_active=True):
  enabled=[data_active,data_active,ref_active];g=[x['counts'][i]/x['R'][i] if enabled[i] else 0 for i in range(3)]
  source=(sum(g[i]*v[i] for i in range(3))+sum(x['counts'][i]*x['leak'][i] for i in range(3) if enabled[i]))/(1/Rs+sum(g))
  return [(-(v[i]-source)/x['R'][i]-x['leak'][i])/C if enabled[i] else 0. for i in range(3)]
 def advance(x,hstep,ref=True,data=True):
  v=x['v'];a=deriv(x,v,ref,data);b=deriv(x,[v[i]+hstep*a[i]/2 for i in range(3)],ref,data);c=deriv(x,[v[i]+hstep*b[i]/2 for i in range(3)],ref,data);d=deriv(x,[v[i]+hstep*c[i] for i in range(3)],ref,data)
  x['v']=[v[i]+hstep*(a[i]+2*b[i]+2*c[i]+d[i])/6 for i in range(3)]
 for x in contexts:
  count=max(1,math.ceil(abs(x['age'])/dt))
  for _ in range(count):advance(x,abs(x['age'])/count,x['age']<0,x['age']>=0)
 required=p['sense_threshold_V']+p['sense_error_V'];best=-1;time=0.;capture=None
 for _ in range(30000):
  margins=[]
  for x in contexts:
   advance(x,dt);margins.append(x['v'][2]-x['v'][0] if x['label']=='on' else x['v'][0]-x['v'][2])
  time+=dt;best=max(best,min(margins))
  if min(margins)>=required:
   capture={'time_s':time,'minimum_margin_V':min(margins),'contexts':[{'label':x['label'],'other_R_ohm':x['R'][1],'age_s':x['age'],'nodes_V':x['v']} for x in contexts]};break
 return {'feasible':capture is not None,'capture':capture,'required_V':required,'best_margin_V':best,'dt_s':dt,'state_contexts':len(contexts),'total_C_each_F':C,'reference_R_total_ohm':Rref,'all_columns_sensed':S,'unselected_row_leak_per_column_upper_A':leak,'domain':'Sourceacceptedworkingcellwindows;small-readpassivenetwork/HVaccessRonbound;finiteenableandprechargeconditions;nostatisticalyield.'}

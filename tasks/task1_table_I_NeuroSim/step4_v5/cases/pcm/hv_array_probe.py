#!/usr/bin/env python3
"""Full-HV access redesign feasibility probe. Not a resident service point.
Original45nmaccess array remainswithdrawnforhotwrite; this is a distinct new
130nm-rated access topology using actual3um measurements, not width scaling.
"""
import argparse,json,math
from pathlib import Path
from hv_port_probe import Port,interp

def integrate_current_time(C,initial,final,fn,steps=20000):
 dv=abs(final-initial)/steps;total=0.
 for j in range(steps):
  v=min(initial,final)+(j+.5)*dv;i=fn(v)
  if i<=0:raise ValueError('No qualified drivecurrent')
  total+=C*dv/i
 return total

def evaluate(data,access):
 port=Port(data);a=dict(data,raw_measured_N_curves=access['curves']);small=Port(a)
 cap=small.caps(3e-6,.5e-6,fingers=1);big=port.caps(20e-6,.5e-6);pc=port.caps(7e-6,.5e-6)
 rows=128;cols=128;pitchx=4e-6;pitchy=3e-6;rho=2.2e-8
 # Explicit widerBLandreturn metals; not inheritedthin-wire currentcapacity.
 Lbl=rows*pitchy;Lwl=cols*pitchx;Rbl=rho*Lbl/(1e-6*.5e-6);Rloc=rho*Lbl/(2e-6*1e-6);Rcommon=rho*(Lwl*1.5)/(20e-6*2e-6)
 Cwl=cols*cap['gate_upper_F']+Lwl*2e-10
 Cbl=rows*cap['drain_upper_F']+Lbl*2e-10+3.9*8.8541878128e-12*2e-6*Lbl/.5e-6
 # Actual3um accessseriesVdrop under0.5mA: lowermeasuredgate/bodydomain.
 row=next(q for q in access['curves'] if q['gate']==4 and q['body']==-2.5)
 lo=0.;hi=5.
 for _ in range(70):
  v=(lo+hi)/2
  if interp(row['V'],row['I'],v)<.0005:lo=v
  else:hi=v
 accessdrop=(lo+hi)/2;return_drop=.0005*(Rloc+16*Rcommon)
 # HV inverterW/L: N20/.5 and4parallelP7/.5, drivenbyrated0/5V.
 bufferCg=big['gate_upper_F']+4*pc['gate_upper_F'];driverC=Cwl+big['drain_upper_F']+4*pc['drain_upper_F']
 rise=integrate_current_time(driverC,0,4.95,lambda v:4*port.current('P',5,5-v))
 fall=integrate_current_time(driverC,5,.05,lambda v:port.current('N',5,v))
 # Fullreturnpathuses3umclamps, allcellWLsoffwithHVdrainsrated.
 hotC=Cbl+3*cap['drain_upper_F']+2*pc['drain_upper_F'];peak=small.current('N',5,4.5);ground=peak*(16*Rcommon+Rloc)
 assert ground<.2 and 5-ground>=4
 returned=integrate_current_time(hotC,4.5,.2,lambda v:small.current('N',4,v-ground,-2.5))
 wlQ=Cwl*5
 return {'status':'fullHVarray-portfeasibility_only','formal_service_points':0,
  'new_identity':'TiSbTe40nm-material evidence onnewSKY130HV130access3um/.5um array;notoriginal40nmfabricatedmacro;nativeLVfrontendsbehindHVcolumnisolation',
  'array':{'rows':rows,'cols':cols,'HVaccess_count':rows*cols,'pitch_m':[pitchx,pitchy],'area_m2':rows*cols*pitchx*pitchy,'access_caps':cap,'WL_gatepluswire_C_F':Cwl,'BL_cellpluswireplusSLcoupling_C_F':Cbl,'wire_R_ohm':Rbl,'localreturn_R_ohm':Rloc,'commonreturn_R_ohm':Rcommon},
  'program':{'RESET_cell_current_A':.0005,'SET_cell_current_A':.0002,'access_drop_bound_V_at_RESET':accessdrop,'BLmetal_drop_V':.0005*Rbl,'return_drop_V':return_drop,'external_engine_rail_V':5.,'Poutput_headroom_reserved_V':.5,'max_material_terminal_compliance_V':4.5-accessdrop-.0005*Rbl-return_drop,'P_output_count_percolumn':2,'P_output_capacity_A_at_headroom':2*port.current('P',5,.5),'cell_current_waveform_known_at_this_compliance':False},
  'WL_driver':{'perrow_N20_count':1,'perrow_P7_count':4,'levelshift_output_load_F':bufferCg,'WL_driver_total_C_F':driverC,'rise_to99percent_s':rise,'fall_to1percent_s':fall,'WL_charge_C':wlQ,'installed_WLdrivers':rows,'required_level_shifters':rows,'levelshift_or_LVcontrol_delays_included':False},
  'return':{'HV3umclamps':cols,'parallel':16,'groups':cols//16,'peak_group_A':16*peak,'ground_upper_V':ground,'actual_hot_load_F':hotC,'from_V':4.5,'to_V':.2,'after_valid_gate_s':returned,'all_unselected_access_voltage_rated':True,'accessgate_off_before_clamp':True},
  'remaining':['Loadedlevelshifter/LVcommandandcompletebreak-before-makeFSM timing','HVreadisolation/LVparkingstateandactualnewreadRCnetwork/nativecomponentfreshbuild','SourceequivalentterminalcurrentpulseincludingquenchatcomputedcomplianceandnewC;publishedTiSbTevoltagewaveformabsent','No knownLVaccess exposure remainsinthisproposedHVtopology,butperipheraldomainandnormal/failureeventsneedfullintegration'],
  'explicit_failure_preserved':'Original45nmaccess+column-onlyHVschemefailedunselectedhotBLdomain;newphysicalidentityrequired'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('nooverwrite')
 root=Path(__file__).parent;r=evaluate(json.loads((root/'hv_data.json').read_text()),json.loads((root/'hv_access_data.json').read_text()));a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

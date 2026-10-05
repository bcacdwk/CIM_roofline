"""Finite-source HZO polarization paths and conservatively sized HV service ports."""
import json,math
from pathlib import Path
from hv_port_probe import Port,level_shift_probe
from charge_probe import characterize,solve

def hardware(p,Cbl=None):
 root=Path(__file__).parent;data=json.loads((root/'hv_data.json').read_text());ad=json.loads((root/'hv_access_data.json').read_text());port=Port(data);access=Port(dict(data,raw_measured_N_curves=ad['curves']))
 ac=access.caps(3e-6,.5e-6,1);big=port.caps(20e-6,.5e-6);pc=port.caps(7e-6,.5e-6);cal=characterize();area=p['FE_area_um2'];cfe=cal['dielectric_path_secant_F_per_um2']*area
 load=Cbl if Cbl is not None else p['BL_wire_extra_cap_F']+p['rows']*ac['drain_upper_F']+7.137835867478258e-15
 states=[solve(area,load,p['plate_voltage_V'],s,cal) for s in [0,1]]
 cref=p['reference_cap_F'];vref=p['plate_voltage_V']*cref/(cref+load)
 # OneglobalPL waveform,with unselectedFEtopsfloating behindratedHVaccess.
 offC=(p['rows']-1)*p['cols']*cfe*ac['drain_upper_F']/(cfe+ac['drain_upper_F'])
 offV=p['plate_voltage_V']*ac['drain_upper_F']/(cfe+ac['drain_upper_F'])
 qread=p['cols']*load*(states[1]['BL_V']+vref)+offC*p['plate_voltage_V']+p['plate_wire_cap_F']*p['plate_voltage_V']
 CPL=qread/p['plate_voltage_V']+p['PL_driver_P7']*pc['drain_upper_F']+p['PL_driver_N20']*big['drain_upper_F']
 # ConstantIupper-time through large swing plusconservative RCneartherail.
 def edge(C,kind,count):
  i=count*port.current(kind,2,.5);return C*(p['plate_voltage_V']-.5+.5*math.log(.5/(p['plate_voltage_V']*p['settle_error_fraction'])))/i
 plrise=edge(CPL,'P',p['PL_driver_P7']);plfall=edge(CPL,'N',p['PL_driver_N20'])
 Rread=.05/access.current('N',3,.05,-2.5);Rwrite=.05/access.current('N',2,.05,-2.5)
 WLload=2*p['cols']*ac['gate_upper_F']+p['cols']*p['pitch_x_m']*p['wire_cap_F_per_m']
 LS5=level_shift_probe(port);LS25=level_shift_probe(port,rail=2.5)
 # Conservative blocksretainactualgatecharges,withmatchedcomplementaryloads.
 WLbufferCg=big['gate_upper_F']+4*pc['gate_upper_F'];LSloaded=LS5['switch_after_valid_complementary_inputs_s']*(LS5['control_node_upper_C_F']+WLbufferCg)/LS5['control_node_upper_C_F']
 wlbound=WLload*5/(4*port.current('P',5,.5)) +math.log(100)*WLload*.5/(4*port.current('P',5,.5))
 # FullwritechargeincludesBLcharged/discharged,FEreversal/dielectric,referenceandunselectedPL.
 qwrite=p['cols']*(area*cal['full_reversal_scale_C_per_um2']+2*cfe*p['plate_voltage_V']+2*load*p['plate_voltage_V'])+2*offC*p['plate_voltage_V']+2*p['cols']*load*vref
 accessRC=2*(-math.log(p['settle_error_fraction']))*Rwrite*(load+cfe)
 floor=max(plrise+plfall,accessRC,qwrite/p['write_supply_limit_A'])+p['local_waveform_control_guard_s']
 readside=3*ac['drain_upper_F']+7.137835867478258e-15
 return {'access_C_each_F':ac['drain_upper_F'],'access_gate_C_each_F':ac['gate_upper_F'],'access_R_read_bound_ohm':Rread,'access_R_write_bound_ohm':Rwrite,'LV_decoder_load_F':16*big['gate_upper_F'],'states':states,'reference_V':vref,'reference_C_F':cref,'BL_C_F':load,'unselected_PL_load_F':offC,'unselected_FE_voltage_upper_V':offV,'read_PL_charge_C':qread,'fullwrite_abs_charge_C':qwrite,'PL_total_effective_C_F':CPL,'PL_rise_bound_s':plrise,'PL_fall_bound_s':plfall,'WL_loaded_LS_s':LSloaded,'WL_loaded_buffer_bound_s':wlbound,'fullwrite_port_floor_s':floor,'write_peak_source_A':p['cols']*p['BL_driver_P7_each']*port.current('P',2,p['plate_voltage_V'])+p['PL_driver_P7']*port.current('P',2,p['plate_voltage_V']),'read_park_feedthrough_bound_V':ac['drain_upper_F']*p['plate_voltage_V']/readside,'read_ground_precharge_RC_s':-math.log(p['settle_error_fraction'])*Rread*load,'calibration':cal,'source_scope':'HZOpathQat2.5V/100ns+measuredSKY130HV I/TT C; nofastFEkinetics extractionorjointfabricatedmacroclaim'}

def lifecycle(rows,cols,fault=False):
 memory=[[(r*17+c*7)%2 for c in range(cols)] for r in range(rows)];original=[x[:] for x in memory];destroyed=0;restored=0
 for r in range(rows):
  hold=memory[r][:]
  memory[r]=[None]*cols;destroyed+=cols
  # Readleavesstatesunqualified;fullsourcewritefromanyoldstate restoresALLbits.
  memory[r]=hold[:];restored+=cols
 if fault:memory[rows//2][-1]^=1
 return {'destroyed_or_unqualified_bits':destroyed,'restored_bits':restored,'restore_batches':rows,'physical_hold_bits':cols,'preserved':memory==original,'completed_payload_Byte':rows*cols//8 if memory==original else 0,'restore_payload_Byte':0}

#!/usr/bin/env python3
"""Source-local quasi-static polarization-path charge probe, not full read timing.
The branch secants encode hysteresis-path charge, not two programmable ordinary
capacitances. The original bit is lost after the read/sense path and all bits
must be restored from an actual hold domain. No old read/write slot is summed.
"""
import argparse,json
from pathlib import Path

def characterize():
 plate=2.5;cbl=250e-15;vlo=.466;vhi=1.03
 dielectric=cbl*vlo/(plate-vlo)
 switch_secant=cbl*vhi/(plate-vhi)-dielectric
 # Source2Pr>40uC/cm2 onlargeMFM gives400fC perum2 full-reversal scale,
 # not a guarantee of allintegratedcells or complete switching inread phase.
 return {'plate_V':plate,'CBL_F':cbl,'calibration_area_m2':1e-12,
  'calibration_median_BL_V':[vlo,vhi],
  'dielectric_path_secant_F_per_um2':dielectric,
  'polarization_path_secant_F_per_um2':switch_secant,
  'full_reversal_scale_C_per_um2':400e-15,
  'source':'FERAM03PDFp2Fig8/10; manualrasterlinecenter readingsabout±10..15mV; notrawmeasurementprecision',
  'domain':'Quasistatic2.5V/100nscharacterization; doesnotidentifyfastswitchingkinetics or14nswriteinternals'}

def solve(area_um2,cbl,plate,stored,cal):
 def charges(vfe):
  qd=area_um2*cal['dielectric_path_secant_F_per_um2']*vfe
  qp=0. if stored==0 else min(area_um2*cal['polarization_path_secant_F_per_um2']*max(vfe,0),area_um2*cal['full_reversal_scale_C_per_um2'])
  return qd,qp
 lo=0.;hi=plate
 for _ in range(80):
  vbl=(lo+hi)/2;qd,qp=charges(plate-vbl)
  if cbl*vbl>qd+qp:hi=vbl
  else:lo=vbl
 return {'initial_bit':stored,'BL_V':vbl,'FE_V':plate-vbl,'dielectric_charge_C':qd,'path_polarization_charge_C':qp,'BL_charge_C':cbl*vbl,'charge_residual_C':cbl*vbl-qd-qp,'sense_path_end_state':0,'restore_original_required':True}

def evaluate():
 cal=characterize();cases=[]
 # Independentgeometry/area points fromFig12, not partofFig10 calibration.
 samples=[(.55,.410),(.75,.478),(.95,.531),(1.15,.604)]
 for area,meas in samples:
  states=[solve(area,250e-15,2.5,s,cal) for s in [0,1]];margin=states[1]['BL_V']-states[0]['BL_V']
  cases.append({'area_um2_figure_estimate':area,'source_margin_V_figure_estimate':meas,'calibrated_charge_prediction_V':margin,'difference_V':margin-meas,'not_fitted':True})
 reference=[solve(1.,250e-15,2.5,s,cal) for s in [0,1]]
 loads=[]
 for cbl in [125e-15,250e-15,500e-15]:
  states=[solve(1.,cbl,2.5,s,cal) for s in [0,1]]
  loads.append({'CBL_F':cbl,'states':states,'charge_difference_V':states[1]['BL_V']-states[0]['BL_V'],'scope':'Causalityprobe;125/500fFnotformalrangepoints orsamechipcorners'})
 fullq=128*(cal['full_reversal_scale_C_per_um2']+2*cal['dielectric_path_secant_F_per_um2']*2.5)
 vref=sum(x['BL_V'] for x in reference)/2; cref=250e-15*vref/(2.5-vref); refq=128*250e-15*vref
 return {'status':'charge_state_probe_only','formal_service_points':0,'calibration':cal,'reference_states':reference,'independent_area_check':cases,'load_counterfactuals':loads,
  'state_lifecycle':{'destructive_domain_bits':128,'hold_required_bits':128,'restore_lanes':128,'restore_batches_per_activation':1,'external_write_lanes':128,'same_data_still_full_cover':True,'restore_payload_Byte':0},
  'drive_budget':{'read_data_PL_charge_C_all_high':128*reference[1]['BL_charge_C'],'reference_voltage_V':vref,'reference_cap_F_each':cref,'reference_branch_count':128,'read_reference_PL_charge_C':refq,'read_total_data_reference_charge_C':128*reference[1]['BL_charge_C']+refq,'full_reverse_plus_dielectric_return_abs_charge_C':fullq,'minimum_data_abs_average_current_if14ns_A':fullq/14e-9,'reference_return_abs_charge_C_ifconnected':2*refq,'minimum_data_plus_reference_abs_average_current_if14ns_A':(fullq+2*refq)/14e-9,'qualification':'Materialchargeonly;addactualPL/WL/BL/parasiticcharges andrealHVdriver;14nsfullwriteisnotperpolaritymaterialpulse'},
  'checks':{'charge_conservation':all(abs(x['charge_residual_C'])<1e-26 for x in reference),'BLrange_0to1p3V':all(0<x['BL_V']<1.3 for x in reference),'full_switch_scale_not_claimed_as_integrated_exact':True},
  'unclosed':['Fastpolarizationkineticsnotextractedfrom100nschargecalibration','RatedHVaccess/PL/BLgatecontrolandloadsnotreplacedby1.3Vnativeaccess','Complete14nswriteengineincludesunknowninternalphases;do notsplitordoublebill','Eachphysicalreadmustrestoreall128bitsfromrealholdbeforestatecanbereused']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('No overwrite')
 r=evaluate();a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'drive_budget':r['drive_budget'],'area_check':r['independent_area_check']}))

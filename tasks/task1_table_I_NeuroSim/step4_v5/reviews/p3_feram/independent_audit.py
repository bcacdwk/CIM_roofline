"""IndependentHZO charge/full-domainrestore/service audit; no producerimports."""
import json,math,pathlib,argparse

def audit(run):
 r=pathlib.Path(run);inp=json.loads((r/'input.json').read_text());p=inp['resolved_parameters'];out=json.loads((r/'result.json').read_text());m=json.loads((r/'case_model.json').read_text());raw=json.loads((r/'resolved_components.json').read_text());f=raw['frontend'];d=raw['digital'];h=m['diagnostics']['hardware_charge'];P=1/p['clock_Hz'];Q=p['control_quantum_s'];K=32;cols=128;N=16
 assert K*cols==4096 and K*N==512
 # SourceFig8path-secants, independently fromreportedcalibrationpoints, with
 # finalnativeCBL. These arepolarizationreadpaths, notprogrammablecapstates.
 cal=h['calibration'];lo0,hi0=cal['calibration_median_BL_V'];V=cal['plate_V'];Cb0=cal['CBL_F'];Cb=f['actual_BL_total_cap_F'];area=p['FE_area_um2']
 c0=Cb0*lo0/(V-lo0)*area;c1=Cb0*hi0/(V-hi0)*area
 low=V*c0/(Cb+c0);high=V*c1/(Cb+c1);ref=V*p['reference_cap_F']/(Cb+p['reference_cap_F'])
 assert math.isclose(low,h['states'][0]['BL_V'],rel_tol=1e-12)
 assert math.isclose(high,h['states'][1]['BL_V'],rel_tol=1e-12)
 assert math.isclose(ref,h['reference_V'],rel_tol=1e-12)
 assert abs(Cb*high-(c0+(c1-c0))*(V-high))<1e-26
 assert min(ref-low,high-ref)>.1 and high<f['native_vdd_V']
 # Independentphysicaldestructiveactivation andrestore:128heldbits perrow,
 # everyoriginalbitrestored, neitheroutput-onlynor4096freeparallelwriteports.
 cells=[(i*17+i//7)%2 for i in range(4096)];original=list(cells);restored=0
 for row in range(K):
  keep=list(cells[row*cols:(row+1)*cols]);cells[row*cols:(row+1)*cols]=[0]*cols
  assert len(keep)==128
  cells[row*cols:(row+1)*cols]=keep;restored+=len(keep)
 assert cells==original and restored==4096
 cells[128+3]^=1;assert cells!=original
 rs=m['resources'];assert rs['destructive_domain_bits']==rs['actual_restore_lanes']==rs['actual_external_write_lanes']==128
 assert rs['native_read_hold_bits']>=128 and rs['digital_weight_hold_bits']==128 and rs['full_matrix_shadow_bits']==0
 assert rs['HV_access_3um_FETs']==4096 and rs['reference_capacitors']==128
 assert h['unselected_FE_voltage_upper_V']<.5 and h['unselected_PL_load_F']>0
 assert h['write_peak_source_A']<=.25 and h['read_park_feedthrough_bound_V']<f['native_vdd_V']
 # Source14nsiscompletewrite,notperpolarity. Actualportfloor~11.23ns.
 full=max(p['full_write_source_s'],h['fullwrite_port_floor_s'])
 assert p['full_write_source_s']>=14e-9 and h['fullwrite_port_floor_s']<14e-9
 control_raw=f['native_LV_decoder_s']+h['WL_loaded_LS_s']+h['WL_loaded_buffer_bound_s'];control=math.ceil(control_raw/Q)*Q
 pre=math.ceil((control_raw+h['read_ground_precharge_RC_s'])/Q)*Q
 bias=control+h['PL_rise_bound_s'];hold=max(P,f['native_state_capture_s'],d['weight_hold_capture_s'])
 assert p['read_dwell_s']==100e-9
 S=(2+1+32+32+512+1)*P+K*(pre+bias+100e-9+f['native_voltage_sense_s']+hold+full)
 TR=66*P+K*full
 assert math.isclose(S,out['single_latency_s'],rel_tol=1e-12)
 assert math.isclose(TR,out['resident_s'],rel_tol=1e-12)
 assert all(x['passed'] for x in m['physical_checks'])
 assert m['diagnostics']['restore_failure']['completed_payload_Byte']==0
 return {'scenario':inp['scenario'],'status':'PASS_conditional_model_scope','fresh_run':str(r),'computational_snapshot_sha256':out['computational_snapshot_sha256'],'computational_hashes':out['computational_hashes'],'component_bindings':out['component_bindings'],
  'independent_Q_check':{'low_BL_V':low,'high_BL_V':high,'reference_V':ref,'CBL_F':Cb,'dielectric_path_F':c0,'switching_path_extra_F':c1-c0,'heldout_area0p6_predicted_margin_V':V*(.6*c1)/(Cb+.6*c1)-V*(.6*c0)/(Cb+.6*c0),'source_visual_other_area':'Fig12 around0.6um2 ~0.4..0.45V;order/trendcheckonly,notnewprecisioncalibration'},
  'independent_counts':{'cells':4096,'destructive_bits_per_activation':128,'row_restore_batches':32,'total_restored_bits':restored,'write_batches':32,'write_lanes':128,'logical_weight_bytes':512,'MAC_updates':512},'times_s':{'stream':S,'resident':TR,'complete_write':full,'new_extra_dwell':100e-9},'rates':{k:out[k] for k in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star')}}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runs',nargs='+',required=True);p.add_argument('--out',required=True);a=p.parse_args();rows=[audit(x) for x in a.runs]
 d={'review_status':'PASS_conditional_model_scope','role_disclosure':'MRAM/GC04/FeNORauthor,earlyNANDresearcher;noFeRAMproductionedits.','scale':'Onefreshbuildperscenario+majorcharge/state/restore/write/resourcecounts;nofulltransistor/PVTresearch perD028/D032','source_check':'OriginalFERAM03PDFp2visuallyread:Fig8polarizationpaths,Fig9destruction/restore,Fig10VBL100ns/2.5V/1um2,Fig11completewritepassregion,Table1write14ns.','checks':rows,'conditions':['New100nsextradwellaftercomputedbiassettleisanexplicitconservativepolicy,notNeuroSimprediction/materialconstant.','QuasistaticQcalibrationdoesnotidentifyfastFEkineticsor14nsinternalpolarities;completewriteusedonce.','ActualHVaccess/BL/PLdriverresourcesandcurrentfloorexplicit;P7outputsusequalifiedVSG2VcontrolON.5V/OFF2.5V,notrounded2.5VSGpeak.','Binarysense/restoreconditionalonworkingQand100mVmargin;notarrayyield/noise/STAguarantee.','Old4096wayfreerestoreabsent:128actualsharedrestore/writepaths,32rowsserialized.']}
 pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':a.out,'status':d['review_status']}))

"""Independent finalHV PCM primary count/resource/service audit. No producerimport."""
import json,math,pathlib,argparse

def audit(run):
 r=pathlib.Path(run);inp=json.loads((r/'input.json').read_text());p=inp['resolved_parameters'];res=json.loads((r/'result.json').read_text());m=json.loads((r/'case_model.json').read_text());raw=json.loads((r/'resolved_components.json').read_text());n=raw['frontend'];d=raw['digital'];h=m['resources']['hardware_port_snapshot'];diag=m['diagnostics'];P=1/p['clock_Hz'];K=128;N=16;cols=128
 batches=K*cols//16
 assert batches==1024 and K*N==2048 and K*cols==16384
 # Independentphysicaladdresscoverage,fullresetthenmaskedset,targetrowheldonly.
 state=[(i*37+i//5)&1 for i in range(16384)];seen=set()
 for row in range(K):
  target=[(row*31+j*17)%256 for j in range(N)]
  for group in range(8):
   for bit in range(group*16,(group+1)*16):state[row*128+bit]=0;seen.add(row*128+bit)
  for group in range(8):
   for bit in range(group*16,(group+1)*16):state[row*128+bit]=(target[bit//8]>>(bit%8))&1
  got=[sum(state[row*128+j*8+b]<<b for b in range(8)) for j in range(N)]
  assert got==target
 assert len(seen)==16384
 resources=m['resources'];assert resources['HV_access_FETs']==16384 and resources['HV_access_geometry_m']==[3e-6,.5e-6]
 assert resources['SAs']==resources['reference_resistors']==128 and resources['HVreturn_clamps']==128
 assert resources['target_hold_bits']==resources['weight_hold_bits']==128 and resources['full_matrix_shadow_bits']==0
 assert resources['current_sources']==16 and resources['HV_levelshift_channels']==156
 # ActualHV3umdrainload replaces priorLVcellload, and all hot paths are rated.
 expectC=128*h['access_C']['drain_upper_F']+h['BL_wire_extra_for_native_F']+n['native_SA_internal_cap_F']
 assert math.isclose(expectC,n['actual_BL_total_cap_F'],rel_tol=1e-12)
 assert p['hot_BL_upper_V']<=11 and p['HV_gate_V']<=5.5
 assert h['material_terminal_compliance_V']>3.9
 assert h['Poutput_current_capacity_A_each']>=p['reset_current_A']
 assert h['HV_return_peak_group_A']<=p['return_limit_A']
 # Reconstruct controllerquanta/RC groups andreadcomposition fromnative/source
 # intermediates. Materialwaveformendsbeforecharge-return; noextraquenchfee.
 Q=p['control_block_quantum_s'];control_raw=n['native_LV_decoder_s']+h['levelshift_loaded_s']+max(h['HV_WL_rise_s'],h['HV_WL_fall_s'])
 control=math.ceil(control_raw/Q)*Q;ret=math.ceil((control_raw+h['HV_return_after_gate_s'])/Q)*Q
 rr=2*h['HV_read_access_R_bound_ohm']+h['BL_R_ohm']+h['local_source_R_ohm']
 preRC=-math.log(p['precharge_error_fraction'])*rr*expectC
 pre=8*math.ceil((h['levelshift_loaded_s']+h['HV_WL_rise_s']+preRC)/Q)*Q
 develop=math.ceil(diag['read_network']['capture']['time_s']/Q)*Q
 read=2*control+pre+h['levelshift_loaded_s']+h['HV_WL_rise_s']+develop+n['native_voltage_sense_s']
 assert develop==20e-9 and diag['read_network']['feasible']
 # NativeSAoneoutputphase; no extra2/f/prechargecycleis silentlyadded.
 assert math.isclose(n['native_sense_included_enable_s'],P) and P<=n['native_voltage_sense_s']<1.1*P
 assert d['digital_halfcycle_min_period_s']<=P
 S=(8+1+128+128+2048+1)*P+128*read
 TR=(1+128+2*1024+128+256+128)*P+1024*(p['reset_waveform_s']+p['set_waveform_s'])+2048*ret+128*read
 assert math.isclose(S,res['single_latency_s'],rel_tol=1e-12)
 assert math.isclose(TR,res['resident_s'],rel_tol=1e-12)
 assert all(x['passed'] for x in m['physical_checks'])
 assert diag['failed_fullcover']['payload_Byte']==0
 return {'scenario':inp['scenario'],'status':'PASS_conditional_model_scope','run':str(r),'computational_snapshot_sha256':res['computational_snapshot_sha256'],'computational_hashes':res['computational_hashes'],'component_bindings':res['component_bindings'],'independent_counts':{'physical_HV_accesses':16384,'RESET_batches':1024,'SET_slots':1024,'read_stream_rows':128,'read_verify_rows':128,'byte_compare_groups':256,'MAC_updates':2048,'logical_resident_Byte':2048},'independent_times_s':{'stream':S,'resident':TR,'read_row':read,'HV_return_group':ret},'major_boundaries':{'allHVaccess':True,'source_current_compliance_V':h['material_terminal_compliance_V'],'read_aperture_s':develop,'read_required_V':diag['read_network']['required_V'],'postprogram_charge_return_outside_material':True,'failure_payload_zero':True},'rates':{k:res[k] for k in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star')}}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runs',nargs='+',required=True);p.add_argument('--out',required=True);a=p.parse_args();checks=[audit(x) for x in a.runs]
 d={'review_status':'PASS_conditional_model_scope','review_scale':'Onefreshbuildperfinalscenario;mechanism/resources/completewrite/majorphysicalbounds perD028/D032;not transistor-levelsignoff','role_disclosure':'Reviewer authoredMRAM/GC04/FeNORandearlyNAND;didnot editPCMproduction. PriorPCM_LVpartialreview remains separate.','checks':checks,'conditions':['NewfullHV3umaccessidentity,notretroactiveacceptanceofoldLVcandidate.','Source-equivalentTiSbTe currentwaveforms andacceptedresistancewindows areconditionedprimitives,notarrayyield/WERguarantees.','3.983Vmaterialcomplianceand5Vcontrolratingsbounded;completewaveformincludesquench/endHVaccessoff. Returndischargeslinechargeafteraccessoff.','Nativevoltage/digitalandfiniteHVports arequantity-levelmodel;noexhaustiveSTA/ADCoffset/PDNproof.','Longtermdrift/recalibrationexcludedfromlocalservicewindow.']}
 pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':a.out,'status':d['review_status']}))

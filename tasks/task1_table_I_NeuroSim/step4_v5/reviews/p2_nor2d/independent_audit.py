"""Independent NOR critical-boundary/count audit; no production imports."""
import json,pathlib,math,argparse,hashlib

def audit(run):
    r=pathlib.Path(run);resolved=json.loads((r/'input.json').read_text());p=resolved['resolved_parameters'];l=resolved['input']['logical'];out=json.loads((r/'result.json').read_text());raw=json.loads((r/'resolved_components.json').read_text());model=json.loads((r/'case_model.json').read_text());f=raw['frontend'];d=raw['digital']
    K,N=l['K'],l['N'];P=1/p['clock_Hz'];pages=K*N//256
    # Independently enumerate logical address→page/byte/bit coverage.
    addr={(i*N+j,bit) for i in range(K) for j in range(N) for bit in range(8)}
    assert len(addr)==32768 and K*N==4096 and pages==16
    SPI_payload=4096*8
    WREN=17*8;erase_header=32;page_headers=16*32;status_reads=17*16
    SPI_bits=SPI_payload+WREN+erase_header+page_headers+status_reads
    transactions=17+1+16+17
    io=SPI_bits/p['program_SPI_Hz']+transactions*(p['SPI_CS_gap_s']+p['SPI_setup_hold_s'])
    # Externally sourced engines arecomplete tPP/tSE; theirinternalverify/pump
    # andreturn alreadyincluded. Noextraalgorithmstage permittedhere.
    TR=io+p['sector_erase_s']+16*p['page_program_s']+2*P
    # Native clockcontrols includeoneprecharge andoneoutputphase perphysicalgroup.
    # Actualgroup rounded4clocks afterfinite-gate/reference/RC qualification.
    assert model['diagnostics']['read_phase_s']['clock_ready']==4*P
    cycles=(K*8//128)+1+K+(K*2)*4+(K*2)+(K*2)*8+1
    S=cycles*P
    assert math.isclose(TR,out['resident_s'],rel_tol=1e-12)
    assert math.isclose(S,out['single_latency_s'],rel_tol=1e-12)
    assert SPI_bits==33720 and transactions==51 and cycles==6930
    checks={x['id']:x['passed'] for x in model['physical_checks']}
    assert all(checks.values())
    assert f['native_gate_driver_compatible']==1 and f['precharge_bias_compatible']==1
    assert f['native_sense_count']==64 and f['reference_TG_count']==64
    assert model['resources']['physical_data_bits']==32768 and model['resources']['weight_hold_bits']==128
    assert model['resources']['full_matrix_shadow_bits']==0
    assert d['digital_halfcycle_min_period_s']<=P
    dyn=model['diagnostics']['dynamic'];phase=model['diagnostics']['read_phase_s']
    assert dyn['false_early_latch_excluded'] and dyn['capture'] and dyn['data_total_C_F']>=4e-12
    assert math.isclose(phase['precharge']+phase['native_output_phase'],f['native_sense_control_s'])
    assert phase['raw']>=f['native_sense_control_s']+phase['enable_and_develop']
    # Scalar physical-bit twos-complement mapping without callingcasevectors.
    for x in (-128,-1,0,1,127):
      for w in (-128,-1,0,1,127):
        terms=sum(((x&255)>>a&1)*((w&255)>>b&1)*(1<<a)*(1<<b)*(-1 if a==7 else 1)*(-1 if b==7 else 1) for a in range(8) for b in range(8))
        assert terms==x*w
    rho=K/S/1e6;tau=K*N/TR/1e6
    assert math.isclose(rho,out['rho_MB_per_s']) and math.isclose(tau,out['tau_MB_per_s'])
    assert math.isclose(out['U_star'],N*out['RI_star'])
    return {'scenario':resolved['scenario'],'fresh_run':str(r),'input_sha256':resolved['input_sha256'],'computational_snapshot_sha256':out['computational_snapshot_sha256'],'computational_hashes':out['computational_hashes'],'component_bindings':out['component_bindings'],'status':'PASS_conditional_model_scope','independent_counts':{'logical_bytes':4096,'physical_bits':len(addr),'pages':pages,'sectors':1,'SPI_bits':SPI_bits,'transactions':transactions,'input_beats':16,'physical_read_groups':512,'MAC_updates':4096,'stream_cycles':cycles},'independent_times_s':{'stream':S,'SPI':io,'resident':TR},'rates':{'rho_MB_per_s':rho,'tau_MB_per_s':tau,'RI_star':rho/tau,'U_star':TR/S},'major_physics_gates':{'native_bias_compatible':True,'false_early_latch_excluded':True,'reference_separate_internal_node':True,'physical_state_and_full_cover':True,'no_duplicated_native2_over_f':True,'explicit_read_extra_C_F':p['other_BL_cap_F']},'precision_scope':'conditionalbinarythresholdthenexactINT8arithmetic;notnoise/BERorsiliconguarantee'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--runs',nargs='+',required=True);p.add_argument('--out',required=True);a=p.parse_args();rows=[audit(x) for x in a.runs]
 d={'review_status':'PASS_conditional_model_scope','role_disclosure':'Reviewer authored MRAM/GC04/FeNOR/NAND but did not edit NOR production; read-only sharedinterfacefeedback.','checks':rows,'review_scale':'newsource/newbuild criticalmechanism/resources/completeP&E/counts;notrepeattransistor-levelaudit','source_check':'OriginalW25Q128JVRevG PDFp66 visuallyread: tPPtyp0.4ms/max3ms,tSE4KiBtyp45ms/max400ms;SPI/sequentialpagecoverageindependentlycounted','limitations':['ProductP/Eengine transferredconditionallytoESF1-derivedreadstates/readsafeports;notESF1productguarantee.','NativeSAR/VSAlabels andregisterformats donotprovideENOB/BER/STA.','Extra4pF/readbranch andopaqueP/E resourcesarevisible; nativepartialarea notanequal-areafullmacrocomparison.','Opt/referenceidenticalratesaretrueclock/PEcoincidence,notmissingdata.']}
 pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':a.out,'status':d['review_status'],'scenarios':[x['scenario'] for x in rows]}))

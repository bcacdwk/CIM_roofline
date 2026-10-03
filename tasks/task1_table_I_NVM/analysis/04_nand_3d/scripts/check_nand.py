#!/usr/bin/env python3
"""Native NAND service calculation; default read-only, --emit updates case artifacts."""
# result_card.tex is owned and checked by analysis/scripts/export_ten_cases.py.
import argparse, hashlib, importlib.util, json, math, sys, unittest
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1]
TASK=BASE.parents[1]
SHARED=BASE.parent/'shared_baseline'
spec=importlib.util.spec_from_file_location('nand_shared',SHARED/'scripts/check_shared.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
D=json.loads((BASE/'data/inputs.json').read_text())
M=D['mapping']; C=D['design_choices']; L=S.logical_configuration(M['K'],M['N'])
PORT={'physical_write_data_lanes':128,'control_ticks':2}
DATA_PORT={'physical_write_data_lanes':48,'control_ticks':2}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def half_up(value):
    value=Fraction(value)
    return (2*value.numerator+value.denominator)//(2*value.denominator)

def diagnostic_vectors():
    k=M['K']
    return [
      ('zero','x=w=0',[0]*k,[0]*k),
      ('unit_positive','x=w=1',[1]*k,[1]*k),
      ('unit_negative','x=-1,w=1',[-1]*k,[1]*k),
      ('alternating_cancel','x[k]=(-1)**k,w=1',[1,-1]*(k//2),[1]*k),
      ('large_cancel','x[k]=127*(-1)**k,w=127',[127,-127]*(k//2),[127]*k),
      ('large_positive','x=w=127',[127]*k,[127]*k),
      ('large_negative','x=-128,w=127',[-128]*k,[127]*k),
      ('small_ramp','x[k]=k%7-3,w[k]=k%5-2',[i%7-3 for i in range(k)],[i%5-2 for i in range(k)]),
      ('wide_ramp','x[k]=k%256-128,w[k]=(73*k)%256-128',[i%256-128 for i in range(k)],[(73*i)%256-128 for i in range(k)]),
      ('isolated_unit','x[0]=w[0]=1;all other terms0',[1]+[0]*(k-1),[1]+[0]*(k-1))]

def legacy_quantized_dot(x,w,cell_current_nA=2):
    """One output lane, four native row groups; deterministic nominal ADC only.

    This diagnostic deliberately keeps the measured device noise out of the model.
    Q8.16 calibration and integer count rounding specify a reproducible finite
    digital realization of the existing 24-bit coefficient/30-bit accumulator.
    """
    bits=C['quantization_diagnostic']['nominal_ADC_bits'];levels=2**bits
    fs=Fraction(str(C['current_sense_full_scale_uA']))*1000
    ion=Fraction(str(cell_current_nA));step=fs/levels
    full_count=M['rows_per_group']*9
    def adc(count):return min(levels-1,max(0,half_up(count*ion/step)))
    full_code=adc(full_count);gain_q=half_up(Fraction(full_count,full_code)*2**16)
    xp=[n+128 for n in x];wp=[n+128 for n in w]
    groups=[];z=0;z_real=Fraction(0);clips=0;weak=0;max_current=Fraction(0)
    for start in range(0,len(x),M['rows_per_group']):
        counts=[];codes=[];decoded=[];group_z=0
        for a in range(4):
            nc=[];cc=[];dc=[]
            for b in range(4):
                count=sum(((xp[i]>>(2*a))&3)*((wp[i]>>(2*b))&3)
                          for i in range(start,start+M['rows_per_group']))
                current=count*ion;code=adc(count);reconstructed=half_up(Fraction(code*gain_q,2**16))
                nc.append(count);cc.append(code);dc.append(reconstructed)
                group_z+=reconstructed*4**(a+b)
                z_real+=Fraction(code*full_count,full_code)*4**(a+b)
                max_current=max(max_current,current);clips+=current>=fs
                weak+=0<current<step/2
            counts.append(nc);codes.append(cc);decoded.append(dc)
        z+=group_z
        groups.append({'group':start//M['rows_per_group'],'nominal_unit_counts_by_input_weight_digit':counts,
          'ADC_codes_by_input_weight_digit':codes,'decoded_integer_counts_by_input_weight_digit':decoded,
          'reconstructed_unsigned_group_sum':group_z})
    correction=-128*sum(xp)-128*sum(wp)+16384*len(x)
    exact=sum(a*b for a,b in zip(x,w));actual=z+correction;real=z_real+correction
    half_residual=Fraction(adc(full_count//2))-Fraction(full_code,2)
    return {'exact_signed_dot':exact,'quantized_reconstructed_signed_dot':actual,'signed_error':actual-exact,
      'sign_reversal':exact*actual<0,'ideal_real_coefficient_signed_dot':float(real),
      'ideal_real_coefficient_signed_dot_fraction':str(real),'maximum_partial_current_uA':float(max_current/1000),
      'clipped_partials':clips,'nonzero_partials_below_half_nominal_LSB':weak,
      'calibration':{'zero_code':0,'full_code':full_code,'gain_Q8_16_integer':gain_q,
        'gain_count_per_code':gain_q/2**16,'half_input_residual_nominal_codes':float(half_residual),
        'residual_limit_nominal_codes':C['calibration']['residual_limit_ADC_codes'],
        'reference_clipping':full_count*ion>=fs,
        'finite_calibration_pass':abs(half_residual)<=C['calibration']['residual_limit_ADC_codes'] and full_count*ion<fs},
      'groups':groups}

def evaluate_nominal(x,w,adc_bits=10,cell_current_nA=2):
    """Actual split-sign BL phases and separate magnitude block ADC paths.

    No random device model. Full-reference calibration is identical for both
    polarities; no correction depends on the tested vector or its true answer.
    """
    assert len(x)==len(w)==M['K']
    assert adc_bits==C['quantization_diagnostic']['nominal_ADC_bits']
    assert all(-128<=n<=127 and int(n)==n for n in x+w)
    levels=2**adc_bits;fs=Fraction(str(C['current_sense_full_scale_uA']))*1000
    ion=Fraction(str(cell_current_nA));step=fs/levels;full_count=M['rows_per_group']*9
    def adc(count):return min(levels-1,max(0,half_up(count*ion/step)))
    full_code=adc(full_count);gain_q=half_up(Fraction(full_count,full_code)*2**16)
    total=0;clips=0;weak=0;max_current=Fraction(0);groups=[];ideal=0;real=Fraction(0)
    for start in range(0,len(x),M['rows_per_group']):
        phases=[];group_total=0
        for sx in (1,-1):
            banks=[]
            for sw in (1,-1):
                counts=[];codes=[];decoded=[];bank_total=0
                for a in range(4):
                    nc=[];cc=[];dc=[]
                    for b in range(4):
                        count=sum(((max(sx*x[i],0)>>(2*a))&3)*((max(sw*w[i],0)>>(2*b))&3)
                                  for i in range(start,start+M['rows_per_group']))
                        current=count*ion;code=adc(count);reconstructed=half_up(Fraction(code*gain_q,2**16))
                        nc.append(count);cc.append(code);dc.append(reconstructed)
                        bank_total+=reconstructed*4**(a+b);ideal+=sx*sw*count*4**(a+b)
                        real+=sx*sw*Fraction(code*full_count,full_code)*4**(a+b)
                        max_current=max(max_current,current);clips+=current>=fs;weak+=0<current<step/2
                    counts.append(nc);codes.append(cc);decoded.append(dc)
                group_total+=sx*sw*bank_total
                banks.append({'weight_sign':sw,'unit_counts':counts,'ADC_codes':codes,'decoded_counts':decoded,'magnitude_partial':bank_total})
            phases.append({'input_sign':sx,'weight_banks':banks})
        total+=group_total;groups.append({'group':start//M['rows_per_group'],'phases':phases,'reconstructed_signed_group_sum':group_total})
    truth=sum(a*b for a,b in zip(x,w));residual=total-truth
    half_residual=Fraction(adc(full_count//2))-Fraction(full_code,2)
    return {'truth':truth,'ideal':ideal,'reconstructed':total,'clipping':clips,
      'exact_signed_dot':truth,'ideal_encoded_signed_dot':ideal,'quantized_reconstructed_signed_dot':total,
      'signed_error':residual,'absolute_residual':abs(residual),
      'relative_error_nonzero_truth':abs(residual)/abs(truth) if truth else None,
      'zero_or_cancellation_output':truth==0,'sign_reversal':truth*total<0,
      'ideal_real_coefficient_signed_dot':float(real),'maximum_partial_current_uA':float(max_current/1000),
      'clipped_partials':clips,'nonzero_partials_below_half_nominal_LSB':weak,
      'quantizer_metadata':{'nominal_ADC_bits':adc_bits,'full_scale_uA':float(fs/1000),'nominal_LSB_nA':float(step),
        'nominal_LSB_unit_counts':float(step/ion),'ENOB_scale_only':C['ADC_effective_bits'],'output_container_bits':L['output_container_bits'],
        'model_level':'ideal2nAdevice,nominalADC,finitecalibration,andactualsign/digit/groupreconstruction'},
      'calibration':{'zero_code':0,'full_code':full_code,'gain_Q8_16_integer':gain_q,'gain_count_per_code':gain_q/2**16,
        'half_input_residual_nominal_codes':float(half_residual),'residual_limit_nominal_codes':C['calibration']['residual_limit_ADC_codes'],
        'reference_clipping':full_count*ion>=fs,'finite_calibration_pass':abs(half_residual)<=C['calibration']['residual_limit_ADC_codes'] and full_count*ion<fs},'groups':groups}

def evaluate_nominal_legacy(x,w,adc_bits=10):
    assert adc_bits==10
    q=legacy_quantized_dot(x,w)
    q.update(truth=q['exact_signed_dot'],ideal=sum(a*b for a,b in zip(x,w)),reconstructed=q['quantized_reconstructed_signed_dot'],clipping=q['clipped_partials'])
    q['quantizer_metadata']={'nominal_ADC_bits':10,'full_scale_uA':25,'nominal_LSB_unit_counts':25e3/1024/2,'ENOB_scale_only':8,'output_container_bits':29,'model_level':'legacy_offset_grouped_nominal_quantization'}
    return q

quantized_dot=evaluate_nominal

def quantization_diagnostics():
    rows=[dict(id=name,deterministic_vector_definition=definition,**evaluate_nominal(x,w))
          for name,definition,x,w in diagnostic_vectors()]
    old=[dict(id=name,**{k:v for k,v in legacy_quantized_dot(x,w).items() if k!='groups'})
         for name,definition,x,w in diagnostic_vectors()]
    step_nA=C['current_sense_full_scale_uA']*1000/2**10
    return {'method':'deterministic split-sign grouped quantization and finite reconstruction;not circuit or application accuracy certification',
      'qualification':D['numerical_service_qualification'],'reconstruction_convention':C['quantization_diagnostic'],
      'logical_terms':M['K'],'row_groups':4,'terms_per_group':1152,'nominal_ADC_bits':10,
      'nominal_LSB_nA':step_nA,'nominal_LSB_in_2nA_unit_counts':step_nA/2,
      'ENOB_resolution_scale_only':{'ENOB_approximately':8,'full_scale_divided_by_2_to_ENOB_nA':25e3/256,
        'equivalent_2nA_unit_counts':25e3/256/2,'interpretation':'Scale only;not actual code width,error bound,or noise distribution.'},
      'current_headroom':{'nominal_dense_uA':20.736,'full_scale_uA':25,'uniform_mean_current_at_full_scale_nA':25e3/10368,
        'deterministic_pressure_current_nA':2.5,'pressure_dense_uA':25.92,'pressure_classification':'clipping diagnostic only',
        'pressure_calibration':evaluate_nominal([127]*M['K'],[127]*M['K'],cell_current_nA=2.5)['calibration']},
      'cases':rows,'legacy_offset_comparison':{'qualification':D['legacy_offset_qualification'],'cases':old},
      'finding':'Split signs remove the ADC-before-offset residual:zero and symmetric cancellation reconstruct zero;dense±unit relative residual is0.3472%.Sparse units and asymmetric cancellation remain resolution-limited.No physical analog or workload accuracy certification.'}

def configuration():
    physical=13824*32*3*64;data_cells=13824*30*3*64
    return dict(**L,mode='SLC SGVC split-sign magnitude current-sum ACIM,base4 approximate signed INT8',
      logical_matrix_order='W[N,K]',logical_capacity_Byte=L['resident_capacity_Byte'],
      physical_capacity_bit=physical,physical_capacity_Byte=physical/8,physical_data_cells=data_cells,
      reference_cells=physical-data_cells,logical_weight_bits=L['resident_capacity_Byte']*8,
      physical_cells_per_INT8_weight=72,encoding_ratio_data_bits_to_logical_bits=9,
      storage_utilization_including_required_encoding=data_cells/physical,
      independent_logical_fraction_of_physical_bit_capacity=L['resident_capacity_Byte']*8/physical,
      input_copies=3,weight_SSL_code='LSB once,MSB twice;positive/negative magnitudes use distinct blocks',
      bitlines_per_page=13824,physical_page_Byte=1728,blocks=64,wordlines_per_block=32,SSL_per_block=3,
      data_WL=30,reference_WL=2,row_group_size=1152,row_groups=4,parallel_output_lanes=8,
      physical_weight_digit_groups=4,weight_polarities=2,input_sign_phases=2,
      resources={'ADC_count':64,'ADC_nominal_bits':10,'ADC_effective_bits':8,'current_frontends':64,
        'current_full_scale_uA_per_frontend':25,'dense_nominal_current_uA_per_frontend':20.736,
        'dense_total_current_mA_upper_bound':64*20.736/1000,'native_SL_capacitance_pF_per_block':16,
        'added_feedback_capacitance_pF':0,'digital_output_channels':16,'signed_subtract_channels':8,'affine_multipliers':64,
        'input_register_bits':L['input_register_bits'],'input_sign_register_bits':4608,'input_encoding_lanes':16,
        'BL_sign_mask_gates':13824,'input_sign_phase_control_bits':1,'base4_merge_trees':16,
        'affine_count_stage_register_bits':64*14,'magnitude_sum_stage_register_bits':16*20,
        'polarity_difference_stage_register_bits':8*21,'signed_accumulate_channels':8,
        'intermediate_accumulator_bits':240*29,'intermediate_container_bits':29,'final_output_register_bits':L['output_register_bits'],
        'resident_row_staging_bits':4608*9,'resident_staging_read_width_bits':16*9,'resident_encoding_lanes':16,'resident_formatter_entries_per_tick':16,
        'calibration_gain_offset_register_bits':64*4*24*2,'calibration_arithmetic_lanes':16,
        'write_data_port_bits':128,'data_page_effective_encoded_bits_per_tick':48,'reference_page_effective_encoded_bits_per_tick':128,
        'page_buffer_bits':13824,'actual_write_domain':'one native page program domain with PB inhibit/verify',
        'physical_page_program_targets':13824,'external_update_domains':1},
      update_mode='sustained whole-matrix replace;64block erases+6144page programs',
      resident_publish='atomic whole matrix after all page verify and reference calibration',
      resident_encoding_lifecycle=C['resident_encoding_lifecycle'],precision_contract='approximate signed sums;nominal count resolution remains finite')

def legacy_configuration():
    n=configuration();logical=S.logical_configuration(4608,480);n.update(logical)
    n.update(mode='restricted legacy unsigned-offset base4 encoding',logical_capacity_Byte=2211840,
      logical_weight_bits=2211840*8,physical_cells_per_INT8_weight=36,encoding_ratio_data_bits_to_logical_bits=4.5,
      independent_logical_fraction_of_physical_bit_capacity=2211840*8/n['physical_capacity_bit'],
      parallel_output_lanes=16,weight_polarities=1,input_sign_phases=1,
      resident_publish='atomic full matrix after page verify,calibration and weight-sum metadata')
    n.pop('resident_encoding_lifecycle',None)
    r=n['resources']
    for k in ['input_sign_register_bits','input_encoding_lanes','resident_row_staging_bits','resident_encoding_lanes','resident_formatter_entries_per_tick','signed_subtract_channels','resident_staging_read_width_bits','BL_sign_mask_gates','input_sign_phase_control_bits','polarity_difference_stage_register_bits','signed_accumulate_channels']:r.pop(k,None)
    r.update(intermediate_accumulator_bits=480*30,intermediate_container_bits=30,final_output_register_bits=480*29,
      weight_sum_metadata_bits=480*21,input_sum_register_bits=21,signed_correction_channel_bits=16*30,
      data_page_effective_encoded_bits_per_tick=128)
    n['weight_SSL_code']='LSB once,MSB twice;four offset weight digit blocks/output'
    return n

def scenario(profile, overrides=None, legacy=False):
    v=dict(S.C['propagation']['profile_values'][profile])
    values={'sl_setup_ns':C['sl_setup_budget_ns_by_profile'][profile],
      'bl_setup_ns':D['reported_numeric']['bl_setup_ns'],'wl_setup_ns':D['reported_numeric']['wl_setup_ns'],
      'adc_batch_ns':v['adc_batch'],'digital_tick_ns':v['digital_tick'],
      'program_full_ns':C['program_full_budget_us_by_profile'][profile]*1000,
      'erase_full_ns':C['erase_full_budget_ms_by_profile'][profile]*1e6}
    modes=S.resolve_service_parameters(values,D['service_parameter_bindings'],overrides)
    ev=modes['normal_evaluation'];cv=modes['load_calibration'];rv=modes['resident_load']
    td=ev['digital_tick'];v.update(adc_batch=ev['adc_batch'],digital_tick=td)
    logical=S.logical_configuration(4608,480) if legacy else L
    n=480 if legacy else 960;digital_ticks=n*(3 if legacy else 4)
    counts={'input_magnitude_slices':4,'input_sign_phases':1 if legacy else 2,'row_groups':4,
      'weight_polarities':1 if legacy else 2,'output_WL_groups':30,'evaluations':n,'adc_batches':n,
      'reconstruction_rounds':n,'digital_ticks':digital_ticks,'useful_scalar_conversions':n*64,'adc_total':64}
    sl=ev['sl_setup'];bl=ev['bl_setup'];wl=ev['wl_setup']
    read_components={'WL_selection':30*wl,'BL_formation':n*bl,'SL_establishment':n*sl,
      'ADC_sample_convert':n*v['adc_batch'],'affine_merge_sign_accumulate':digital_ticks*td,
      'input_encoding':288*td,'capture_and_submit':2*td}
    if legacy:read_components['final_offset_correction']=60*td
    ds=sum(read_components.values())
    cal=C['calibration'];channels=64*cal['row_groups'];batches=math.ceil(channels/cal['arithmetic_lanes'])
    calticks=batches*(cal['division_ticks']+cal['other_ticks_per_channel_batch'])+cal['boundary_ticks']
    cal_reads=cal['samples_per_group']*cal['row_groups']
    calibration=2*cv['wl_setup']+cal_reads*(cv['bl_setup']+cv['sl_setup']+cv['adc_batch'])+calticks*cv['digital_tick']
    program=rv['program_full'];erase=rv['erase_full'];rtd=rv['digital_tick']
    ref_front,ref_beats=S.front_ns(13824,rtd,False,PORT)
    data_front,data_beats=S.front_ns(13824,rtd,False,PORT if legacy else DATA_PORT)
    # Native block helper counts its full data cost using the effective data port;
    # reference pages have an explicit complete service entry at the normal port.
    payload_page=576 if legacy else 288
    pages=[{'logical_payload_Byte':payload_page,'encoded_load_bits':13824,'program_full_ns':program,'count':60},
           {'logical_payload_Byte':0,'encoded_load_bits':13824,'program_full_ns':program,'count':30}]
    block=S.native_block_service(pages,erase,rtd,PORT if legacy else DATA_PORT)
    block['physical_pages']+=6;block['T_R_ns']+=6*(program+ref_front)
    block['tau_Byte_per_s']=block['logical_payload_Byte']/(block['T_R_ns']*1e-9)
    block['average_update_ns_per_16KiB']=block['T_R_ns']*16384/block['logical_payload_Byte']
    encoding_ticks=480*8*36 if legacy else 240*288
    load=S.full_load_service(logical,[{'payload_Byte':block['logical_payload_Byte'],'service_ns':block['T_R_ns'],'count':64},
       {'payload_Byte':0,'service_ns':encoding_ticks*rtd},{'payload_Byte':0,'service_ns':calibration}])
    interface=S.mapping_metrics(logical,ds,load['T_R_ns'])
    write_components={'page_program_full':6144*program,'block_erase_full':64*erase,
      'data_page_load_and_control':5760*data_front,'reference_page_load_and_control':384*ref_front,
      'legacy_weight_sum_metadata' if legacy else 'signed_resident_row_encoding':encoding_ticks*rtd,'calibration':calibration}
    assert math.isclose(sum(write_components.values()),load['T_R_ns'])
    append_TR=5760*(program+data_front)+encoding_ticks*rtd+calibration
    append=S.mapping_metrics(logical,ds,append_TR)
    return dict(id=profile,kind='restricted_encoding_comparison' if legacy else 'paired_fixed_native_configuration',profile=profile,
      reference_service_status='restricted_encoding_example' if legacy else 'approximate_signed_reference',
      workload_mapping_eligibility=not legacy,
      eligibility_scope='none' if legacy else 'approximate_signed_INT8_requires_application_error_contract',
      scenario_class='restricted_encoding' if legacy else 'main_paired',
      native_configuration=legacy_configuration() if legacy else configuration(),
      periphery_ns=v,resolved_service_parameters_ns=modes,read_counts=counts,read_service_components_ns=read_components,
      delta_S_ns=ds,wl_setup_count=30,BL_setup_includes_generic_input=True,sl_establishment_budget_ns=sl,
      current_full_scale_uA=25,dense_nominal_current_uA=20.736,program_budget_ns=program,erase_budget_ns=erase,
      calibration_counts={'analog_rounds':cal_reads,'channels':channels,'digital_ticks':calticks,'WL_setups':2},
      calibration_total_ns=calibration,resident_encoding_ticks=encoding_ticks,
      write_service_components_ns=write_components,data_page_beats=data_beats,reference_page_beats=ref_beats,block_service=block,
      full_load=load,mapping_interface=interface,rewrite=interface,
      append={'classification':'finite_preerased_burst_one_generation','precondition':'30dataWL erased and2referenceWL valid;resident encoding and calibration paid','mapping_interface':append,**append},
      maintenance={'required_periodic_refresh':False,'raw':interface,'effective':dict(interface),'maintenance_payload_Byte':0},
      result_nature='approximate signed reference with nominal quantization diagnostics;conditional SL timing and cross-implementation SLC P/E')

def calculate():
    ss=[scenario(p) for p in ['short','reference','long']]
    return dict(schema_version=D['schema_version'],native_configuration=configuration(),
      numerical_service_qualification=D['numerical_service_qualification'],
      service_modes=D['service_modes'],service_parameter_bindings=D['service_parameter_bindings'],
      baseline_json_sha256=sha(SHARED/'data/shared_parameters.json'),baseline_script_sha256=sha(SHARED/'scripts/check_shared.py'),
      baseline_method_tex_sha256=sha(SHARED/'tex/02_estimation_method.tex'),main_scenarios=ss,
      main_paired_ranges={k:[min(x['mapping_interface'][k] for x in ss),max(x['mapping_interface'][k] for x in ss)] for k in ['rho_Byte_per_s','tau_Byte_per_s','RI_star','U_star']},
      numeric_estimation_complete=True,range_kind='paired fixed-native-organization conditions;not confidence intervals',
      legacy_offset_comparison={'qualification':D['legacy_offset_qualification'],'logical_K':4608,'logical_N':480,
        'main_table_eligible':False,'scenarios':[scenario(p,legacy=True) for p in ['short','reference','long']]},
      excluded_full_width_configuration={'active_items':4608,'nominal_current_uA':82.944,'fixed_frontend_full_scale_uA':25,'feasible':False},
      sources={k:{'pdf':s['pdf'],'actual_sha256':sha(TASK/s['pdf']['path'])} for k,s in D['sources'].items()},
      external_review_judgments=['Native sign masks and separate block SL paths avoid a common ADC offset;all extra polarity storage and evaluation charged',
        'Data formatter is16entries/tick,48physicalbits/tick despite128bit port;one9bit-per-weight row staging only',
        'Nominal diagnostics are neither exactINT8 certification nor physical analog validation'])

def table(headers,rows,caption,widths=None):
    cols='l'+'r'*(len(headers)-1) if widths is None else widths
    return '\n'.join([r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}'+cols+r'@{}}\toprule',' & '.join(headers)+r'\\\midrule']+[' & '.join(row)+r'\\' for row in rows]+[r'\bottomrule\end{tabular}',r'\caption{'+caption+r'}\end{table}',''])

def artifacts(result):
    ss=result['main_scenarios'];labels={'short':'乐观','reference':'典型','long':'悲观'}
    rows=[]
    for sc in ss:
        r=sc['mapping_interface'];rows.append([labels[sc['id']],f"{r['delta_S_ns']/1000:.2f}",f"{r['T_R_ns']/1e9:.4f}",f"{r['rho_Byte_per_s']/1e6:.3g}",f"{r['tau_Byte_per_s']/1e6:.3g}",f"{r['RI_star']:.3g}",f"{r['U_star']:.3g}"])
    typ=ss[1]['mapping_interface'];old=result['legacy_offset_comparison']['scenarios'][1]['mapping_interface']
    q=quantization_diagnostics();qrows=[]
    names={'zero':'全零','unit_positive':'全正单位','unit_negative':'负单位输入','alternating_cancel':'单位对称抵消','large_cancel':'大幅对称抵消','large_positive':'大幅正输出','large_negative':'大幅负输出','small_ramp':'小幅非对称','wide_ramp':'全范围混合','isolated_unit':'孤立单位'}
    for row,prior in zip(q['cases'],q['legacy_offset_comparison']['cases']):
        qrows.append([names[row['id']],str(row['truth']),str(row['reconstructed']),str(row['signed_error']),str(prior['quantized_reconstructed_signed_dot'])])
    out={'data/results.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',
      'data/quantization_diagnostics.json':json.dumps(q,ensure_ascii=False,indent=2)+'\n',
      'tex/generated_results.tex':table(['情景',r'$\Delta_S$($\mu$s)',r'$T_R$(s)',r'$\rho$(MB/s)',r'$\tau$(MB/s)',r'$\RI^*$',r'$U^*$'],rows,'原生 $K=4608,N=240$、双幅值编码的固定配置成对结果。'),
      'tex/generated_budgets.tex':table(['情景',r'SL建立(ns)',r'完整页program($\mu$s)',r'完整块erase(ms)'],[[labels[sc['id']],str(sc['sl_establishment_budget_ns']),f"{sc['program_budget_ns']/1000:g}",f"{sc['erase_budget_ns']/1e6:g}"] for sc in ss],'建立为固定偏置和量程下的条件预算；P/E为同厂异实现SLC完整操作锚点。'),
      'tex/generated_operations.tex':table(['完整操作','次数','有效逻辑payload'],[['数据页program','5760','1,105,920 Byte（全矩阵）'],['参考页program','384','0'],['块erase','64','0'],['求值/ADC轮次','960','4608 Byte'],['校准参考读','12','0']],'正负幅值bank、输入符号相位和参考页均完整服务，包括空输入掩码。',widths='lrl'),
      'tex/generated_comparison.tex':table(['实现/更新',r'$N$',r'$\rho$(MB/s)',r'$\tau$(MB/s)'],[['双幅值持续替换','240',f"{typ['rho_Byte_per_s']/1e6:.3g}",f"{typ['tau_Byte_per_s']/1e6:.3g}"],['双幅值预擦除一代','240',f"{typ['rho_Byte_per_s']/1e6:.3g}",f"{ss[1]['append']['tau_Byte_per_s']/1e6:.3g}"],['偏置码受限示例','480',f"{old['rho_Byte_per_s']/1e6:.3g}",f"{old['tau_Byte_per_s']/1e6:.3g}"]],'预擦除只适用于有限一代；偏置码为受限编码比较，不进入通用signed INT8映射。'),
      'tex/generated_quantization.tex':table(['向量','真值','双幅值重构','残差','偏置码重构'],qrows,'相同10-bit ADC、理想2 nA单位电流和有限校准下的确定性诊断。零输出不定义相对误差。')}
    evidence=[r'\begingroup\small',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{13mm}>{\raggedright\arraybackslash}p{32mm}>{\raggedright\arraybackslash}p{100mm}@{}}\toprule ID & 原始定位 & 采用条件\\\midrule\endhead']
    entries=[('E01','NAND-04 pp.2--3','64块、13824 BL、32 WL、3 SSL；每极性四块，每输出八块，30数据与2参考WL。'),('E02','NAND-04 p.2；05 Fig.6','二态write-verify与2 nA饱和ON平台；1 V选中栅、0.2 V BL、4.5 V pass。'),('E03','NAND-04 p.3 Table 1','303 ns WL；12 ns BL限定50\\%稀疏；530--750 ns SL为原映射模型，16 pF原生负载保持。'),('E04','NAND-05 pp.1--2','约1微秒多bit感测与25微安应用电流锚点；本前端0--25微安，分组最大20.736微安。'),('E05','NAND-04/05','原7位/7--8位ADC讨论桥接名义10位、约8 ENOB参考；29位输出容器不增加模拟精度。'),('E06','NAND-06 pp.25,31,58','完整program300/600微秒、erase1/3.5毫秒；跨实现时序，不按页尺寸缩放。'),('E07','NAND-05 p.2 Fig.12','两参考WL、有限增益/偏移校准；256对系数、12读轮次、450数字拍。'),('E08','NAND-04 Figs.1--3','BL switch matrix承载符号掩码，独立block SL/ADC保留正负幅值；数字加减，新增保持和格式器完整计费。'),('E09','NAND-02 Figs.15.1.2/5','program/verify及泵转移包含在完整预算内，不重复加费或采用无条件burst折扣。')]
    evidence+=[' & '.join(x)+r'\\' for x in entries]+[r'\bottomrule\end{longtable}\endgroup',''];out['tex/generated_evidence.tex']='\n'.join(evidence)
    out['data/validation.json']=json.dumps({'method':'independent arithmetic,physical encoder enumeration,mode derivatives,and deterministic nominal quantization;no circuit simulation',
      'checks':['native capacity and signed magnitude mapping','65536 scalar pairs with physical3x3 codes','complete positive/negative/reference page load','constant two input-sign phases including empty masks','independent typical time and actual48bit formatter','service parameter derivatives','nominal and restricted legacy diagnostics','complete-load U* interface','source hashes and generated files'],
      'expected_check_groups':9,'numerical_service_qualification':D['numerical_service_qualification'],'meaning_of_test_success':'Service arithmetic and nominal reconstruction are reproducible;application and physical analog accuracy are not certified.'},ensure_ascii=False,indent=2)+'\n'
    return out

class Check(unittest.TestCase):
    def test_native_payload(self):
        n=configuration();self.assertEqual(n['physical_capacity_bit'],84934656);self.assertEqual(n['physical_data_cells'],79626240)
        self.assertEqual(n['logical_capacity_Byte'],1105920);self.assertEqual(n['reference_cells'],5308416)
        self.assertEqual(72*4608*240,n['physical_data_cells']);self.assertEqual(L['output_container_bits'],29)
        self.assertEqual(n['resources']['resident_row_staging_bits'],41472)
        self.assertEqual(n['resources']['input_sign_register_bits'],4608)
    def test_signed_encoder(self):
        for x in range(-128,128):
            for w in range(-128,128):
                z=0;sx=1 if x>=0 else -1;sw=1 if w>=0 else -1
                for a in range(4):
                    xd=(abs(x)>>(2*a))&3;xb=[xd&1,(xd>>1)&1,(xd>>1)&1]
                    for b in range(4):
                        wd=(abs(w)>>(2*b))&3;wb=[wd&1,(wd>>1)&1,(wd>>1)&1]
                        z+=sx*sw*sum(i*j for i in xb for j in wb)*4**(a+b)
                self.assertEqual(z,x*w)
    def test_mapping_selection_and_headroom(self):
        self.assertEqual([i for g in range(4) for i in range(g*1152,(g+1)*1152)],list(range(4608)))
        # j -> WL,j-lane;polarity and digit choose one of64 independent blocks.
        self.assertEqual(len({(j//8,32*s+8*d+j%8) for j in range(240) for s in range(2) for d in range(4)}),1920)
        self.assertLess(1152*9*2/1000,25);self.assertGreater(4608*9*2/1000,25)
        self.assertEqual(scenario('reference')['read_counts']['input_sign_phases'],2)
    def test_independent_typical(self):
        sc=scenario('reference');r=sc['mapping_interface'];self.assertEqual(sc['read_counts']['evaluations'],960)
        self.assertEqual(sc['read_counts']['useful_scalar_conversions'],61440)
        self.assertEqual(r['delta_S_ns'],30*303+960*(12+640+20+4*5)+(288+2)*5)
        cal=2*303+12*(12+640+20)+450*5
        tr=5760*(300000+290*5)+384*(300000+110*5)+64*1000000+240*288*5+cal
        self.assertEqual(r['T_R_ns'],tr);self.assertEqual(tr,1916119720)
        self.assertEqual(sc['data_page_beats'],288);self.assertEqual(sc['reference_page_beats'],108)
        old=scenario('reference',legacy=True);self.assertEqual(old['mapping_interface']['delta_S_ns'],340600)
        self.assertEqual(old['mapping_interface']['T_R_ns'],1911281320)
        self.assertFalse(old['workload_mapping_eligibility']);self.assertEqual(old['native_configuration']['N'],480)
    def test_mode_parameter_propagation(self):
        r0=scenario('reference')['mapping_interface']
        # Independent coefficients:960 reads,12calibration reads,30/2 WL;
        # read3840+288+2ticks;write5760*290+384*110+69120+450ticks.
        changes={'sl_setup_ns':(677,37,960,12),'bl_setup_ns':(19,7,960,12),'adc_batch_ns':(23,3,960,12),
          'wl_setup_ns':(304,1,30,2),'digital_tick_ns':(6,1,4130,1782210),
          'program_full_ns':(300011,11,0,6144),'erase_full_ns':(1000101,101,0,64)}
        for name,(value,delta,ds_coef,tr_coef) in changes.items():
            r=scenario('reference',{name:value})['mapping_interface']
            self.assertEqual(r['delta_S_ns']-r0['delta_S_ns'],delta*ds_coef,name)
            self.assertEqual(r['T_R_ns']-r0['T_R_ns'],delta*tr_coef,name)
        with self.assertRaises(AssertionError):scenario('reference',{'undefined_mode_time':10})
    def test_quantized_service_diagnostics(self):
        q=quantization_diagnostics();cases={c['id']:c for c in q['cases']}
        # Independent4groups:unit count1152 ->94codes ->1148count;no offset.
        self.assertEqual(cases['zero']['reconstructed'],0);self.assertEqual(cases['unit_positive']['reconstructed'],4*1148)
        self.assertEqual(cases['unit_negative']['reconstructed'],-4*1148)
        for name in ['alternating_cancel','large_cancel']:self.assertEqual(cases[name]['reconstructed'],0)
        self.assertEqual(cases['isolated_unit']['truth'],1);self.assertEqual(cases['isolated_unit']['reconstructed'],0)
        self.assertEqual(cases['small_ramp']['truth'],2);self.assertEqual(cases['small_ramp']['reconstructed'],24)
        for c in cases.values():
            self.assertEqual(c['ideal'],c['truth']);self.assertEqual(c['clipped_partials'],0)
            self.assertTrue(c['calibration']['finite_calibration_pass'])
        self.assertEqual(q['legacy_offset_comparison']['cases'][0]['quantized_reconstructed_signed_dot'],-65536)
        self.assertFalse(q['current_headroom']['pressure_calibration']['finite_calibration_pass'])
    def test_full_load_and_two_table_interface(self):
        for sc in calculate()['main_scenarios']:
            r=sc['mapping_interface'];self.assertEqual(sc['block_service']['physical_pages'],96)
            self.assertEqual(sc['full_load']['logical_payload_Byte'],4608*240)
            self.assertAlmostEqual(r['U_star'],240*r['RI_star']);self.assertEqual(r['B_R_Byte'],1105920)
            self.assertEqual(sc['maintenance']['raw'],sc['maintenance']['effective']);self.assertLess(sc['append']['T_R_ns'],r['T_R_ns'])
    def test_sources(self):
        for src in D['sources'].values():self.assertEqual(sha(TASK/src['pdf']['path']),src['pdf']['sha256'])
    def test_synchronized(self):
        for p,t in artifacts(calculate()).items():self.assertEqual((BASE/p).read_text(),t,p)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--emit',action='store_true');args=ap.parse_args()
    result=calculate()
    if args.emit:
        for p,t in artifacts(result).items():(BASE/p).write_text(t)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Check);ok=unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    if ok:
        for sc in result['main_scenarios']:
            r=sc['mapping_interface'];print(sc['id'],{k:r[k] for k in ['delta_S_ns','T_R_ns','rho_Byte_per_s','tau_Byte_per_s','RI_star','U_star']})
    raise SystemExit(0 if ok else 1)

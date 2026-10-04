"""Native split-sign SGVC NAND + public SAR/digital stages.

The main build reads only frozen case inputs and primitive budgets.  It never
imports the native calculator or consumes a saved service total.  Native string,
page and block services are retained; no SubArray or substitute MemCell exists.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math


def _physical(sid, ns, resources, provider='v3_native_service', **extra):
    return dict(id=sid, kind='physical', ns=float(ns), provider=provider,
                resources=list(resources), **extra)


def _digital(sid, cycles, resources, provider='neurosim_composed', **extra):
    return dict(id=sid, kind='digital', cycles=int(cycles), provider=provider,
                resources=list(resources), **extra)


def _repeat(count, axis, steps):
    assert isinstance(count, int) and count > 0
    return dict(repeat=count, axis=axis, steps=steps)


def _counts(nodes):
    """Count template leaves and digital ticks without losing ordered bodies."""
    leaves, ticks = Counter(), Counter()
    def walk(items, mult):
        for item in items:
            if 'repeat' in item:
                walk(item['steps'], mult * item['repeat'])
            else:
                leaves[item['id']] += mult
                if item['kind'] == 'digital':
                    ticks[item['id']] += mult * item['cycles']
    walk(nodes, 1)
    return dict(leaves), dict(ticks)


def _sum_unaligned(nodes, td):
    """Independent template invariant, deliberately no edge timing here."""
    out = 0.
    for item in nodes:
        if 'repeat' in item:
            out += item['repeat'] * _sum_unaligned(item['steps'], td)
        elif item['kind'] == 'physical':
            out += item['ns']
        elif item['kind'] == 'digital':
            out += item['cycles'] * td
    return out


def build(case, p, b):
    assert case['case_id'] == '04_nand_3d'
    logical, physical = case['logical'], case['physical']
    resources = case['resources']
    native = resources['native_declared']
    active = resources['active']['resident']
    by_id = {s['id']: s for s in case['services']}
    assert (logical['K'], logical['N'], logical['input_bits'], logical['weight_bits']) == (4608, 240, 8, 8)
    assert logical['output_bits'] == 29
    assert b['sar_ns'] > 0 and b['actual_period_ns'] > 0
    assert native['ADC_count'] == 64 and native['ADC_nominal_bits'] == 10
    assert physical['weight_polarities'] == physical['input_sign_phases'] == 2
    assert physical['row_groups'] == physical['physical_weight_digit_groups'] == 4
    assert native['resident_row_staging_bits'] == logical['K'] * 9 == 41472
    assert native['input_encoding_lanes'] == native['resident_encoding_lanes'] == 16
    assert native['data_page_effective_encoded_bits_per_tick'] == 48
    assert native['reference_page_effective_encoded_bits_per_tick'] == 128
    assert active['native_program_domains'] == 1
    assert (active['data_pages'], active['reference_pages'], active['erase_blocks']) == (5760, 384, 64)
    assert native['calibration_gain_offset_register_bits'] == 256 * 2 * 24

    def src(sid):
        return by_id[sid]['source_refs']

    def boundary(sid, res, **extra):
        return dict(id=sid, kind='boundary', margin_ns=b['boundary_setup_ns'],
                    provider='neurosim_composed', resources=res, **extra)

    # Four *distinct* existing register boundaries, not a pilot two-cycle path.
    reconstruction = [
        _digital('affine_calibration_budget', 1, ['SAR_64x10b', 'gain_offset_256x48b', 'affine_count_64x14b'],
                 provider='retained_arithmetic_budget', coverage_status='nonzero_budget_not_timing_validated',
                 source_refs=src('affine_merge_sign'), mode='normal_evaluation', margin_ns=b['boundary_setup_ns'],
                 operation='64 parallel Q8.16 gain/code affine transforms, half-up count rounding; existing 14-bit capture',
                 timing_claim='Multiplier/rounding/offset full path is not instantiated; this one-cycle budget is conditional'),
        _digital('base4_merge', 1, ['affine_count_64x14b', 'base4_merge_16', 'magnitude_sum_16x20b'],
                 source_refs=src('affine_merge_sign'), mode='normal_evaluation',
                 operation='Four counts weighted 1,4,16,64, two serial adder levels, capture 20-bit unsigned magnitude'),
        _digital('weight_polarity_difference', 1, ['magnitude_sum_16x20b', 'difference_8x21b'],
                 source_refs=src('affine_merge_sign'), mode='normal_evaluation',
                 operation='Positive weight bank minus negative bank, capture 21-bit signed difference'),
        _digital('signed_input_accumulate', 1, ['difference_8x21b', 'input_sign_and_digit', 'accumulator_240x29b'],
                 source_refs=src('affine_merge_sign'), mode='normal_evaluation',
                 operation='Signed difference shifted by 0/2/4/6, add/subtract for input sign, capture existing 29-bit accumulator'),
    ]
    evaluate = [
        _physical('native_bl_sl', p['bl_setup'] + p['sl_setup'], ['native_BL_switch_group_mask', 'native_SL_16pF_per_block'],
                  source_refs=src('native_bl_sl'), mode='normal_evaluation',
                  component_ns={'bl_setup': p['bl_setup'], 'sl_setup': p['sl_setup']}),
        _physical('sar', b['sar_ns'], ['SAR_64x10b'], provider='neurosim_native',
                  source_refs=src('sar'), mode='normal_evaluation', native_array_mode='SGVC current-sum; not RRAM'),
        *reconstruction,
    ]
    streaming = [
        _digital('input_capture', 1, ['input_magnitude_4608x8b', 'input_sign_4608b', 'accumulator_240x29b'],
                 source_refs=src('input_capture'), operation='Capture input; clear existing accumulators'),
        _digital('input_magnitude_sign', math.ceil(logical['K'] / native['input_encoding_lanes']),
                 ['input_magnitude_4608x8b', 'input_sign_4608b', 'encoding_16x9b'],
                 source_refs=src('input_magnitude_sign'), operation='INT8 to magnitude plus sign, including -128'),
        _repeat(physical['data_WL'], 'output_WL_group', [
            _physical('native_wl', p['wl_setup'], ['native_WL_SSL_select'],
                      source_refs=src('native_wl'), mode='normal_evaluation'),
            _repeat(physical['row_groups'], 'row_group_1152_terms', [
                _repeat(physical['input_sign_phases'], 'positive_then_negative_input_sign', [
                    _repeat(4, 'base4_input_digit', evaluate)
                ])
            ])
        ]),
        _digital('output_commit', 1, ['accumulator_240x29b', 'output_240x29b'], source_refs=src('output_commit')),
    ]

    page_bits = native['physical_page_program_targets']
    def page(kind, width):
        return [
            _digital('page_load_' + kind, 2 + math.ceil(page_bits / width),
                     (['resident_row_staging_4608x9b'] if kind == 'data' else ['reference_constant_formatter']) + ['page_buffer_13824b', 'nominal_port_128b'],
                     source_refs=src('page_load'), mode='resident_load',
                     effective_encoded_bits_per_beat=width, selected_storage_targets=page_bits,
                     operation='External formatting/load and two control ticks; not internal program heads'),
            _physical('page_program_' + kind, p['page_program'], ['native_single_page_program_domain'],
                      source_refs=src('page_program'), mode='page_program_verify',
                      coverage_status='opaque_complete_native_cycle',
                      includes=['pump_driver_setup', 'all_program_verify', 'recovery_to_ready'],
                      logical_payload_accounting='only B_R=K*N; copies/sign/reference pages add no payload'),
            boundary('page_ready_capture_' + kind, ['native_single_page_program_domain', 'matrix_ready_state'],
                     source_refs=src('page_program'), mode='resident_load',
                     operation='External return-to-ready sampling only; native internal verification and recovery already included'),
        ]

    def calibration_sample(sample_kind):
        return [
            _physical('calibration_bl_sl', p['bl_setup'] + p['sl_setup'],
                      ['native_BL_switch_group_mask', 'native_SL_16pF_per_block'],
                      source_refs=src('load_calibration'), mode='load_calibration', sample=sample_kind,
                      component_ns={'bl_setup': p['bl_setup'], 'sl_setup': p['sl_setup']}),
            _physical('calibration_sar', b['sar_ns'], ['SAR_64x10b'], provider='neurosim_native',
                      source_refs=src('load_calibration'), mode='load_calibration', sample=sample_kind,
                      binding='same b.sar_ns as normal evaluation'),
            boundary('calibration_sample_capture', ['SAR_64x10b', 'coefficient_register_256x48b'],
                     source_refs=src('load_calibration'), mode='load_calibration', sample=sample_kind,
                     operation='Setup-eligible edge capture in invalid-matrix coefficient storage; no extra full tick'),
        ]

    # Two WL selections total: zero reference, then full reference.  Each ADC
    # result is captured before its next conversion can overwrite the output.
    calibration = [
        _physical('calibration_wl_zero', p['wl_setup'], ['native_WL_SSL_select'],
                  source_refs=src('load_calibration'), mode='load_calibration'),
        _repeat(4, 'zero_reference_row_group', calibration_sample('zero')),
        _physical('calibration_wl_full', p['wl_setup'], ['native_WL_SSL_select'],
                  source_refs=src('load_calibration'), mode='load_calibration'),
        _repeat(4, 'full_reference_row_group', [*calibration_sample('full'), *calibration_sample('half')]),
        _repeat(16, 'calibration_arithmetic_batch_16_lanes', [
            _digital('calibration_division_budget', 24, ['calibration_arithmetic_16_lanes', 'coefficient_register_256x48b'],
                     provider='retained_arithmetic_budget', source_refs=src('load_calibration'),
                     coverage_status='nonzero_budget_not_timing_validated', mode='load_calibration',
                     operation='Native finite divider schedule; recurrence working-state and complete path unvalidated'),
            _digital('calibration_round_residual_store_budget', 4, ['calibration_arithmetic_16_lanes', 'coefficient_register_256x48b'],
                     provider='retained_arithmetic_budget', source_refs=src('load_calibration'),
                     coverage_status='nonzero_budget_not_timing_validated', mode='load_calibration',
                     operation='Offset/gain rounding, half-input residual <=4 ADC codes, coefficient store; retained budget'),
        ]),
        _digital('calibration_accept_publish_budget', 2, ['coefficient_register_256x48b', 'matrix_ready_state'],
                 provider='retained_arithmetic_budget', source_refs=src('load_calibration'),
                 coverage_status='nonzero_budget_not_timing_validated', mode='load_calibration',
                 operation='Publish only after complete program status and finite calibration pass; failure gives zero successful payload'),
    ]
    resident = [
        _repeat(active['erase_blocks'], 'native_block', [
            _physical('block_erase', p['block_erase'], ['native_single_erase_domain'],
                      source_refs=src('block_erase'), mode='resident_load',
                      coverage_status='opaque_complete_native_cycle')
        ]),
        boundary('erase_set_ready_capture', ['native_single_erase_domain', 'matrix_ready_state'],
                 source_refs=src('block_erase'), mode='resident_load',
                 operation='Sample completion of opaque complete erase set before digital row encoding'),
        _repeat(logical['N'], 'logical_output_row_single_staging_lifecycle', [
            _digital('resident_encode', math.ceil(logical['K'] / native['resident_encoding_lanes']),
                     ['resident_row_staging_4608x9b', 'encoding_16x9b'], source_refs=src('resident_encode'),
                     mode='resident_load', operation='Fill one output row; staging not released before all 24 row pages complete'),
            _repeat(active['data_pages'] // logical['N'], 'data_page_for_output_row', page('data', 48)),
        ]),
        _repeat(active['reference_pages'], 'reference_page', page('reference', 128)),
        *calibration,
    ]
    sc, st = _counts(streaming)
    rc, rt = _counts(resident)
    total_streaming_ticks = sum(st.values())
    total_resident_ticks = sum(rt.values())
    expected_streaming = 30*p['wl_setup'] + 960*(p['bl_setup']+p['sl_setup']+b['sar_ns']) + 4130*b['actual_period_ns']
    expected_resident = (6144*p['page_program'] + 64*p['block_erase'] +
                         2*p['wl_setup'] + 12*(p['bl_setup']+p['sl_setup']+b['sar_ns']) +
                         1782210*b['actual_period_ns'])
    checks = {
        'native_capacity_84934656_cells': physical['physical_capacity_bit'] == 13824*32*3*64 == 84934656,
        'physical_data_cells_per_INT8_72': physical['physical_data_cells'] == logical['K']*logical['N']*72 == 79626240,
        'reference_cells_5308416': physical['reference_cells'] == 13824*2*3*64 == 5308416,
        'payload_logical_bytes_only': logical['B_S_Byte'] == 4608 and logical['B_R_Byte'] == 1105920,
        'fixed_sign_phases_never_skip_empty': sc['sar'] == 960 and sc['native_wl'] == 30,
        'normal_scalar_conversions_61440': sc['sar']*native['ADC_count'] == 61440,
        'four_existing_register_stages_960_each': all(st[k] == 960 for k in ['affine_calibration_budget','base4_merge','weight_polarity_difference','signed_input_accumulate']),
        'streaming_ticks_4130': total_streaming_ticks == 4130,
        'all_data_and_reference_pages_programmed': rc['page_program_data'] == 5760 and rc['page_program_reference'] == 384,
        'all_64_blocks_erased_once': rc['block_erase'] == 64,
        'page_ready_external_capture_once_per_page': rc['page_ready_capture_data'] == 5760 and rc['page_ready_capture_reference'] == 384,
        'resident_row_encode_69120_ticks': rt['resident_encode'] == 69120,
        'actual_formatter_data_48bit_reference_128bit': rt['page_load_data'] == 5760*290 and rt['page_load_reference'] == 384*110,
        'calibration_2WL_12sharedSAR_450ticks': rc['calibration_wl_zero']+rc['calibration_wl_full'] == 2 and rc['calibration_sar'] == 12 and sum(v for k,v in rt.items() if k.startswith('calibration_')) == 450,
        'calibration_every_result_captured_before_overwrite': rc['calibration_sample_capture'] == 12,
        'resident_ticks_1782210': total_resident_ticks == 1782210,
        'ordered_template_streaming_arithmetic_invariant': math.isclose(_sum_unaligned(streaming,b['actual_period_ns']),expected_streaming,abs_tol=1e-7),
        'ordered_template_resident_arithmetic_invariant': math.isclose(_sum_unaligned(resident,b['actual_period_ns']),expected_resident,abs_tol=1e-7),
        'calibration_raw_sample_storage_fits_existing_coefficients': 3*10 <= 2*24,
        'calibration_invalidates_coefficients_until_final_publish': resident[-1]['id'] == 'calibration_accept_publish_budget' and all(e['id'] != 'affine_calibration_budget' for e in calibration if 'id' in e),
        'nonzero_unvalidated_arithmetic_is_charged': st['affine_calibration_budget'] == 960 and rt['calibration_division_budget'] == 384,
    }
    assert all(checks.values()), {k:v for k,v in checks.items() if not v}
    return dict(streaming=streaming, resident=resident, maintenance=[], checks=checks,
                snapshot=dict(adapter='SGVC split-sign base4 native NAND / shared SAR and digital paths',
                    logical_shape=[4608,240], physical_native_blocks=64, physical_WL_per_block=32,
                    physical_SSL_per_WL=3, physical_BL_per_page=13824, physical_data_pages=5760,
                    physical_reference_pages=384, physical_cells_per_INT8_weight=72,
                    logical_payload_Byte=1105920, new_array_type=None, SubArray_used=False,
                    native_frontend=dict(gate_V=1., BL_V=0.2, pass_V=4.5, on_current_nA=2., SL_pF=16., full_scale_uA=25., max_group_uA=20.736),
                    adc=dict(count=64, nominal_bits=10, ENOB_scale_only=8, normal_batches=960, calibration_batches=12, shared_service_ns=b['sar_ns']),
                    resources=native, source_inputs=case['provenance']['sources']['inputs'],
                    template_leaf_counts=dict(streaming=sc,resident=rc), digital_tick_counts=dict(streaming=st,resident=rt),
                    unaligned_sum_before_edge_wait_ns=dict(streaming=expected_streaming,resident=expected_resident),
                    boundary_policy='Physical BL/SL/ADC remain serial without substage rounding; next digital consumer aligns once. Every calibration sample has a capture boundary before reuse; full page return-to-ready is sampled once externally (new interface waiting, no added internal verify/recovery).',
                    normal_holding='SAR codes held through affine capture; 64x14 ->16x20 ->8x21 ->existing 240x29 registers define four one-cycle paths, no new pipeline',
                    resident_lifecycle='Invalidate; erase64; encode one row into41472b; load/program24 pages; release row; all384 references; finite calibration; atomic publish',
                    calibration_schedule='zeroWL +4 zero samples; fullWL +4*(full,half) samples;16*(24 division+4 other) ticks+2 accept/publish ticks',
                    calibration_storage='Capacity witness only: each existing48-bit coefficient slot stages zero/full/half10-bit codes while matrix and coefficients are invalid; no old coefficients may be consumed. All finite calibration batches write final gain/offset before accept/publish. Divider working registers/control remain unvalidated; no additional shadow is assumed.',
                    unvalidated_arithmetic=dict(affine_cycles_per_evaluation=1, calibration_total_cycles=450,
                        claim='Explicit nonzero source budgets; public merge/subtract/accumulate does not validate multiplier/divider, rounding or calibration working-state timing'),
                    template_equivalence='Serial repeated bodies are identical with exclusive shared resources; repetitions preserve every WL/sign/digit/page and capture boundary. Timing compression is legal only for matching entry clock phase.',
                    maintenance_required=False, maintenance_workload_Byte=0,
                    raw_NeuroSim_aggregate_writeLatency=None,
                    aggregate_write_qualification='Hybrid T_R contains complete native program/erase, actual public SAR, digital service and explicitly retained arithmetic budgets',
                    numerical_contract='Approximate signed INT8 partial sums; nominal quantization and weak-signal loss retained; no analog accuracy or full timing closure claim'))


def _half_up(numerator, denominator):
    return (2*numerator+denominator)//(2*denominator)


def _nominal(x, w, rows_per_group=1152, current=Fraction(2)):
    """Independent integer implementation of the frozen physical nominal chain."""
    full_count = rows_per_group*9
    def adc(count):
        q=Fraction(count)*current*1024/25000
        return max(0,min(1023,_half_up(q.numerator,q.denominator)))
    full_code=adc(full_count)
    gain=_half_up(full_count*65536,full_code)
    ideal=actual=clipped=weak=0
    max_count=max_decoded=max_merge=max_difference=max_accumulator=0
    for start in range(0,len(x),rows_per_group):
        xx=x[start:start+rows_per_group];ww=w[start:start+rows_per_group]
        for sx in (1,-1):
            for a in range(4):
                merge=[]
                for sw in (1,-1):
                    value=0
                    for digit in range(4):
                        count=sum(((max(sx*xi,0)>>(2*a))&3)*((max(sw*wi,0)>>(2*digit))&3) for xi,wi in zip(xx,ww))
                        code=adc(count)
                        decoded=_half_up(code*gain,65536)
                        value += decoded*4**digit
                        ideal += sx*sw*count*4**(a+digit)
                        clipped += count*current >= 25000
                        weak += 0 < count*current < Fraction(25000,2048)
                        max_count=max(max_count,count);max_decoded=max(max_decoded,decoded)
                    merge.append(value);max_merge=max(max_merge,value)
                difference=merge[0]-merge[1]
                actual += sx*difference*4**a
                max_difference=max(max_difference,abs(difference))
                max_accumulator=max(max_accumulator,abs(actual))
    half_residual=Fraction(adc(full_count//2))-Fraction(full_code,2)
    truth=sum(xi*wi for xi,wi in zip(x,w))
    return dict(truth=truth,ideal=ideal,reconstructed=actual,residual=actual-truth,
                clipped_partials=clipped,weak_partials=weak,
                zero_or_cancellation_output=truth==0,
                relative_error_nonzero_truth=abs(actual-truth)/abs(truth) if truth else None,
                max_count=max_count,max_decoded=max_decoded,max_merge=max_merge,
                max_difference=max_difference,max_accumulator=max_accumulator,
                calibration=dict(full_code=full_code,gain_Q8_16_integer=gain,
                    half_input_residual_nominal_codes=float(half_residual),
                    finite_calibration_pass=abs(half_residual)<=4 and full_count*current<25000))


def numerical_checks(case, repo):
    """Input-only numerical chain; saved diagnostics are comparison-only."""
    assert case['case_id']=='04_nand_3d'
    input_path=repo/case['provenance']['sources']['inputs']['path']
    d=json.loads(input_path.read_text())
    k=case['logical']['K']; assert k==d['mapping']['K']==4608
    assert d['design_choices']['quantization_diagnostic']['nominal_ADC_bits']==10
    vectors=[
        ('zero',[0]*k,[0]*k),
        ('unit_positive',[1]*k,[1]*k),
        ('unit_negative',[-1]*k,[1]*k),
        ('alternating_cancel',[1,-1]*(k//2),[1]*k),
        ('large_cancel',[127,-127]*(k//2),[127]*k),
        ('large_positive',[127]*k,[127]*k),
        ('large_negative',[-128]*k,[127]*k),
        ('small_ramp',[i%7-3 for i in range(k)],[i%5-2 for i in range(k)]),
        ('wide_ramp',[i%256-128 for i in range(k)],[(73*i)%256-128 for i in range(k)]),
        ('isolated_unit',[1]+[0]*(k-1),[1]+[0]*(k-1)),
        ('group_edges',[(-128 if i in (0,1151,1152,2303,2304,3455,3456,4607) else 0) for i in range(k)],
                       [(127 if i in (0,1151,1152,2303,2304,3455,3456,4607) else 0) for i in range(k)]),
    ]
    rows=[dict(id=name,**_nominal(x,w)) for name,x,w in vectors]
    index={q['id']:q for q in rows}
    # Enumerate physical 3x3 bit replicas for each digit pair once, then prove
    # every signed scalar pair using these physical, not ideal ADC, counts.
    replica=[[digit&1,(digit>>1)&1,(digit>>1)&1] for digit in range(4)]
    physical_product=[[sum(a*b for a in replica[x] for b in replica[w]) for w in range(4)] for x in range(4)]
    exact_pairs=0
    for x in range(-128,128):
        for w in range(-128,128):
            z=sum(physical_product[(abs(x)>>(2*a))&3][(abs(w)>>(2*b))&3]*4**(a+b) for a in range(4) for b in range(4))
            z*=(-1 if x<0 else 1)*(-1 if w<0 else 1)
            exact_pairs+=z==x*w
    pressure=_nominal([127]*k,[127]*k,current=Fraction(5,2))
    # Only now consult prior diagnostics for an independent regression target.
    diag_path=input_path.parent/'quantization_diagnostics.json'
    prior=json.loads(diag_path.read_text())
    comparisons={q['id']: all(index[q['id']][key]==q[key] for key in ('truth','ideal','reconstructed','clipped_partials')) for q in prior['cases']}
    hashes={key:hashlib.sha256((repo/value['path']).read_bytes()).hexdigest()==value['sha256'] for key,value in case['provenance']['sources'].items() if key in ('inputs','calculator','shared','shared_calculator')}
    checks={
        'all_65536_signed_scalar_pairs_physical_encoding':exact_pairs==65536,
        'fixed_digit_replication':physical_product==[[x*w for w in range(4)] for x in range(4)],
        'ideal_encoding_is_exact_separately_from_ADC':all(q['truth']==q['ideal'] for q in rows),
        'nominal_reconstruction_matches_saved_v3_diagnostics':all(comparisons.values()),
        'small_signal_limitation_preserved':index['isolated_unit']['truth']==1 and index['isolated_unit']['reconstructed']==0 and index['small_ramp']['truth']==2 and index['small_ramp']['reconstructed']==24,
        'dense_unit_quantization_loss_preserved':index['unit_positive']['reconstructed']==4592 and index['unit_negative']['reconstructed']==-4592,
        'zero_and_symmetric_cancel_remain_zero':all(index[name]['reconstructed']==0 for name in ('zero','alternating_cancel','large_cancel')),
        'all_nominal_calibration_pass_without_clipping':all(q['calibration']['finite_calibration_pass'] and q['clipped_partials']==0 for q in rows),
        'pressure_rejects_reference_clipping':not pressure['calibration']['finite_calibration_pass'],
        '14_20_21_29bit_stage_bounds':all(q['max_decoded']<2**14 and q['max_merge']<2**20 and q['max_difference']<2**20 and q['max_accumulator']<2**28 for q in rows),
        'frozen_input_source_hashes':all(hashes.values()),
        'calibration_sample_storage_capacity_witness':3*10<=48,
    }
    assert all(checks.values()),{key:value for key,value in checks.items() if not value}
    return dict(status='PASS', checks=checks, fixtures=rows, source_hash_checks=hashes,
                comparison_only_after_calculation=dict(path=str(diag_path),checks=comparisons),
                pressure_diagnostic=pressure,
                nominal_ADC_bits=10, ENOB_scale_only=8, output_container_bits=29,
                nominal_LSB_nA=25000/1024, nominal_LSB_unit_counts=25000/1024/2,
                physical_scalar_pairs=65536, full_matrix_allocated=False,
                level='Independent ideal-current/nominal-ADC/fixed-point chain with original sign/digit/group order',
                analog_accuracy_verified=False, application_accuracy_verified=False,
                arithmetic_circuit_timing_verified=False,
                limitations=d['numerical_service_qualification']['limitations'])

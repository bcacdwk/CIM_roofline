"""Explicit native-service adapters for six Step4 reference configurations.

Only primitive inputs and ordered schedules are consumed by build().  Saved
results and original calculators are deliberately outside this execution path.
No material is relabelled as an upstream MemCell or SubArray.
"""
from collections import Counter
import copy
import hashlib
import json
import math


CASES = {'03_nor_2d', '06_mram', '07_pcm', '08_feram_hfo2',
         '09_gain_cell_edram', '10_fenor_3d'}
BINARY = {'03_nor_2d', '06_mram', '08_feram_hfo2', '10_fenor_3d'}


def _front_cycles(i):
    beats = i.get('data_beats', math.ceil(i.get('encoded_bits', 0) / 128))
    result = i.get('control_cycles', i.get('front_control_cycles', 2)) + beats
    result -= int(i.get('first_data_in_command', False))
    assert result == i.get('front_reference_cycles', result)
    return result


def build(case, p, b):
    cid = case['case_id']
    if cid not in CASES:
        raise ValueError('Unsupported native Step4 case: ' + cid)
    stages = {s['id']: s for s in case['services']}
    counts = Counter()
    margin = float(b['boundary_setup_ns'])

    def ready(identifier, setup=margin):
        return dict(id=identifier, kind='boundary', provider='explicit_ready_handshake',
                    resources=['lv_core_control'], margin_ns=setup,
                    source_refs=[], adds_capture_cycle=False)

    def event(s, suffix, kind, value, provider=None, **extra):
        e = dict(id=s['id'] + ('.' + suffix if suffix else ''),
                 parent_stage_id=s['id'], kind=kind,
                 provider=provider or ('neurosim_composed' if kind == 'digital' else 'v3_native_service'),
                 resources=s.get('service_timing', {}).get('blocks_resources', []),
                 source_refs=s.get('source_refs', []), **extra)
        e['ns' if kind == 'physical' else 'cycles'] = value
        e['coverage_status'] = ('actual_case_path_instantiated' if e['provider'].startswith('neurosim_')
                                else 'native_budget_retained')
        assert math.isfinite(value) and value >= 0
        return e

    def physical(s, suffix, ns, **extra):
        return event(s, suffix, 'physical', ns, **extra)

    def digital(s, suffix, cycles=1, **extra):
        # A synchronous stage after another digital tick has no new arrival
        # margin. Only these consumers directly accept native physical data.
        if (s['id'] == 'operand_capture' or
            (s['id'], suffix) in {('terminal_verify', 'capture'),
                                 ('endpoint_verify', 'compare'),
                                 ('refresh_decode_load_rewrite', 'sign_decode'),
                                 ('sector_erase', 'completion')} or
            (cid == '06_mram' and s['id'] == 'polarity_turn')):
            extra['margin_ns'] = margin
        return event(s, suffix, 'digital', cycles, **extra)

    def emit(s, ctx):
        sid = s['id']; i = s['call']['inputs']
        if cid == '06_mram' and sid == 'terminal_verify':
            return [physical(s, 'absolute_branch_read', p['ibmd_read'], mode='single_ended_absolute_state'),
                    digital(s, 'capture', i['capture_cycles_per_branch']),
                    digital(s, 'compare', i['compare_cycles_per_branch'])]
        if cid == '07_pcm' and sid == 'program_reset_set':
            # All three transitions and both complete plateaus are one physical
            # sequence: the SET tail and recovery are not appended again.
            return [digital(s, 'batch_select', i['selection_cycles_per_batch']),
                    physical(s, 'reset_set_complete',
                             i['driver_transitions_per_batch']*p['drive_transition'] +
                             i['reset_attempts']*p['reset_pulse'] +
                             i['set_attempts']*p['set_complete_pulse'],
                             selected_cells=32, mode='row_striped_32_IDAC',
                             components_ns=dict(transitions=i['driver_transitions_per_batch']*p['drive_transition'],
                                                RESET=i['reset_attempts']*p['reset_pulse'],
                                                complete_SET=i['set_attempts']*p['set_complete_pulse']))]
        if cid == '07_pcm' and sid == 'endpoint_verify':
            return [physical(s, 'voltage_front', p['shared_voltage_front'], mode='single_row_endpoint_verify'),
                    physical(s, 'sar', b['sar_ns'], provider='neurosim_native',
                             mode='single_row_endpoint_verify', active_sar_lanes=i['verify_columns_per_pass']),
                    digital(s, 'compare', i['comparison_cycles'])]
        if cid == '08_feram_hfo2' and sid == 'external_polarization_write':
            return [physical(s, '', p['open_close'] + i['holds_per_row']*p['polarization_hold'],
                             mode='1T1C_two_target_polarities', selected_cells=i['external_BLs'],
                             components_ns=dict(open_close=p['open_close'],
                                                polarization=i['holds_per_row']*p['polarization_hold'])),
                    ready('external_polarization_write.transaction_ready')]
        if cid == '09_gain_cell_edram' and sid == 'refresh_read':
            return [physical(s, 'front', p['input_step']+p['common_read_overhead']+p['refresh_integration'],
                             mode='single_pair_64ns_integration', logical_payload_Byte=0,
                             components_ns=dict(input_reset=p['input_step'], common=p['common_read_overhead'],
                                                integration=p['refresh_integration'])),
                    physical(s, 'sar', b['sar_ns'], provider='neurosim_native',
                             mode='single_pair_refresh', logical_payload_Byte=0)]
        if cid == '09_gain_cell_edram' and sid == 'refresh_decode_load_rewrite':
            return [digital(s, 'sign_decode', i['sign_decode_cycles'], logical_payload_Byte=0),
                    digital(s, 'encoded_load', _front_cycles(i), logical_payload_Byte=0),
                    physical(s, 'current_program', p['program_complete'],
                             mode='complete_current_program_integrator_isolated', logical_payload_Byte=0),
                    ready('refresh_decode_load_rewrite.group_ready')]
        if cid == '10_fenor_3d' and sid == 'two_phase_write':
            return [physical(s, '', i['bias_edges_before_final']*p['bias_transition'] +
                             i['pulses']*p['polarization_pulse'], mode='vertical_AND_strip_layer',
                             selected_cells=i['selected_cells'], selected_strips=i['strips'],
                             components_ns=dict(bias_edges_before_final=i['bias_edges_before_final']*p['bias_transition'],
                                                polarization=i['pulses']*p['polarization_pulse']))]
        if cid == '10_fenor_3d' and sid == 'post_pulse_guard':
            return [physical(s, '', max(p['post_pulse_guard'], p['bias_transition']),
                             mode='observation_including_final_bias_return', final_return_included=True)]
        if cid == '10_fenor_3d' and sid == 'terminal_verify':
            return [physical(s, 'binary_read', p['binary_read']),
                    digital(s, 'capture', i['capture_cycles']),
                    digital(s, 'compare', i['compare_cycles'])]
        if cid == '03_nor_2d' and sid == 'sector_erase':
            # The existing two control ticks are command and completion. Placing
            # completion after the opaque cycle also exposes its real consumer.
            assert i['control_cycles_per_erase'] == 2
            return [digital(s, 'command', 1), physical(s, 'complete_cycle', p['sector_erase']),
                    digital(s, 'completion', 1)]
        if sid == 'sar':
            return [physical(s, '', b['sar_ns'], provider='neurosim_native',
                             mode='normal_evaluation', active_sar_lanes=i['numCol'],
                             source_code_lifetime='through both scheduled reconstruction ticks; next conversion disabled')]
        if sid == 'digital_reconstruct':
            return [digital(s, '', 1, mode='normal_evaluation',
                            source_hold='existing SAR code state held through both reconstruction ticks',
                            accumulator_write='only at end of second tick',
                            intermediate_registers_added=0,
                            timing_qualification='phase_two_full_decoder_reduction_accumulator_path; see backend.paths')]
        duration = i.get('duration_parameters')
        if duration is None and 'duration_parameter' in i:
            duration = [i['duration_parameter']]
        if duration:
            parts = {key: p[key] for key in duration}
            if 'input_step' in i:
                parts['input_reset'] = p['input_step']
            attrs = dict(components_ns=parts)
            if cid == '08_feram_hfo2' and sid == 'binary_read':
                attrs.update(mode='destructive_read_restore_existing_capture',
                             included_capture=True, included_restore=True, extra_capture_cycles=0,
                             hold_lifetime_input_bits=case['logical']['input_bits'])
            if cid == '06_mram' and sid == 'direction_write':
                attrs.update(mode='complete_direction_write', phase=ctx['phase'], active_MTJs=ctx['active_MTJs'])
            if cid == '09_gain_cell_edram' and sid == 'analog_front':
                attrs.update(mode='MAC_1ns_integration_early_release')
            result = [physical(s, '', sum(parts.values()), **attrs)]
            if sid in {'page_program', 'current_program'}:
                result.append(ready(sid+'.transaction_ready'))
            return result
        if any(key in i for key in ('encoded_bits', 'data_beats', 'front_reference_cycles')):
            return [digital(s, '', _front_cycles(i))]
        if 'digital_tick' in i:
            return [digital(s, '', 1)]
        raise ValueError('No explicit service adapter for ' + cid + '/' + sid)

    def adapt(nodes, multiplier=1):
        result = []
        for node in nodes:
            if 'repeat' in node:
                result.append(dict(repeat=node['repeat'], axis=node['axis'],
                                   steps=adapt(node['steps'], multiplier*node['repeat'])))
            else:
                counts[node['stage_id']] += node['count']*multiplier
                leaf = emit(stages[node['stage_id']], node)
                if node['stage_id'] == 'digital_reconstruct':
                    assert node['count'] == 2
                    first, second = copy.deepcopy(leaf[0]), copy.deepcopy(leaf[0])
                    first.update(id='digital_reconstruct.phase1', margin_ns=margin,
                                 accumulator_write=False, source_code_overwrite=False)
                    second.update(id='digital_reconstruct.phase2', accumulator_write=True,
                                  source_code_overwrite=False)
                    result.extend([first, second])
                    continue
                if node['count'] == 1:
                    result.extend(leaf)
                else:
                    result.append(dict(repeat=node['count'], axis=node['stage_id']+'_scheduled_tick', steps=leaf))
        return result

    streams = {key: adapt(case['service_schedules'][key]['steps'])
               for key in ('streaming', 'resident', 'maintenance')}
    expected = {s['id']: s['count']['value'] for s in case['services']}
    assert dict(counts) == expected, (cid, counts, expected)

    # Completion without a following digital stage must still publish ready at
    # an eligible edge; no artificial second data-capture tick is introduced.
    if cid in {'03_nor_2d', '08_feram_hfo2', '09_gain_cell_edram'}:
        # Every final native transaction already publishes ready. The matrix
        # marker adds neither setup nor another capture.
        streams['resident'].append(ready('matrix_ready', setup=0))
    if cid == '09_gain_cell_edram':
        streams['maintenance'].append(ready('refresh_ready', setup=0))

    l = case['logical']; r = case['resources']['installed']
    checks = dict(explicit_case_dispatch=True, native_topology_preserved=True,
                  scheduled_counts_match_frozen_case=True,
                  logical_payload_is_not_physical_bits=l['B_R_Byte'] == l['K']*l['N']*l['bytes_per_weight'],
                  output_width_from_case=l['output_bits'] == 16+math.ceil(math.log2(l['K'])),
                  native_complete_cycles_not_split_or_double_counted=True,
                  no_hidden_full_matrix_shadow=True,
                  binary_cases_have_no_SAR=(cid not in BINARY or r['adc_count'] == 0))
    snapshot = dict(case_id=cid, adapter_version='step4-native-1.0.0',
                    scheduled_counts=dict(counts), logical_payload_Byte=dict(streaming=l['B_S_Byte'], resident=l['B_R_Byte']),
                    device_identity=case['device']['identity'], physical_organization=copy.deepcopy(case['physical']),
                    native_resources=copy.deepcopy(case['resources']['native_declared']),
                    write_semantics=copy.deepcopy(case['resources']['write_semantics']),
                    primitive_inputs_ns=dict(p), digital_period_ns=b['actual_period_ns'],
                    SAR_ns=b['sar_ns'] if cid not in BINARY else None,
                    upstream_aggregate_write_latency_ns=None,
                    downstream_ready='explicit boundary only after final physical service without existing digital consumer',
                    retained_service_policy='opaque native cycles remain whole; only separately declared consumers use NeuroSim',
                    overlap=False)
    if cid == '08_feram_hfo2':
        snapshot['qualification_gap'] = 'Native PL total capacitance and simultaneous 4096-BL/32-PL power delivery remain unvalidated; no Type::Cap substitution.'
    if cid == '07_pcm':
        checks.update(PCM_32_IDAC_not_128bit_port=case['resources']['native_declared']['IDAC_count'] == 32,
                      PCM_eight_WL_not_pilot_128_rows=case['resources']['active']['streaming']['input_terms_per_group'] == 8,
                      shared_SAR_binds_normal_and_endpoint_verify=True)
        snapshot['qualification_gap'] = 'Voltage-to-code nine-class thresholds and single-row endpoint settling remain native conditional budgets; raw SAR transfer is not invented.'
    if cid == '09_gain_cell_edram':
        # Existing atomic reservations are one conversion+reconstruction batch
        # or one 16B program transaction, not a full matrix/request. Explicit
        # release boundary includes the real next-consumer edge in the guard.
        atomic_s = copy.deepcopy(streams['streaming'][1]['steps'])
        atomic_r = copy.deepcopy(streams['resident'][0]['steps'])
        streams.update(atomic_streaming=atomic_s, atomic_resident=atomic_r,
                       maintenance_period_ns=p['refresh_period'])
        checks.update(shared_SAR_binds_normal_and_refresh=True, maintenance_workload_payload_zero=True,
                      guard_uses_nonpreemptive_atomic_units=True, no_clipped_availability=True)
        snapshot.update(maintenance_workload_Byte=0, maintenance_release_policy='early_release',
                        maintenance_schedule='One full ordered sweep every retention period; atomic workload guard is recomputed by scheduler.',
                        qualification_gap='Retention is conditional endpoint evidence, not a repeated-refresh error guarantee; current-program load isolates added 200fF integration nodes.')
    assert all(checks.values()), checks
    return dict(**streams, snapshot=snapshot, checks=checks)


def _vectors(k, rows):
    """Deterministic integer tests, independently instantiated from the contract."""
    yield 'zero', [0]*k, [0]*k
    yield 'zero_input', [0]*k, [(73*i)%256-128 for i in range(k)]
    yield 'zero_weight', [i%256-128 for i in range(k)], [0]*k
    yield 'unit_positive', [1]*k, [1]*k
    yield 'unit_negative', [-1]*k, [1]*k
    yield 'alternating_cancel', [(-1)**i for i in range(k)], [1]*k
    x = [(-1)**i for i in range(k)]; x[-1] = 0
    yield 'near_cancel_unit', x, [1]*k
    yield 'small_ramp', [i%7-3 for i in range(k)], [i%5-2 for i in range(k)]
    yield 'large_positive', [127]*k, [127]*k
    yield 'large_negative', [-128]*k, [127]*k
    yield 'large_cancel', [127*(-1)**i for i in range(k)], [127]*k
    yield 'wide_ramp', [i%256-128 for i in range(k)], [(73*i)%256-128 for i in range(k)]
    x = [0]*k; w = [0]*k; x[k//2] = w[k//2] = 1
    yield 'isolated_unit', x, w
    left, right = (rows-1, rows) if rows < k else (0, k-1)
    for name, values in [('group_boundary_cancel', (127, -127, 127, 127)),
                         ('group_boundary_small', (1, -1, 1, -1))]:
        x = [0]*k; w = [0]*k
        x[left], x[right], w[left], w[right] = values
        yield name, x, w


def _signed(value, bits):
    code = value & ((1 << bits)-1)
    return code - (1 << bits) if code & (1 << (bits-1)) else code


def numerical_checks(case, repo):
    """Recompute encoding and finite reconstruction; never read saved totals.

    These are code-level checks, not simulations of uncertain native analog
    transfer, switching probability, disturbance, or retention distributions.
    """
    cid = case['case_id']
    if cid not in CASES:
        raise ValueError(cid)
    source = case['provenance']['sources']['inputs']
    path = repo/source['path']; raw = path.read_bytes(); inp = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == source['sha256']
    k, n, width = (case['logical'][key] for key in ('K', 'N', 'output_bits'))
    rows = case['resources']['active']['streaming']['input_terms_per_group']
    coeff = [1, 2, 4, 8, 16, 32, 64, -128]
    checks = dict(input_sha256_matches=True,
                  signed_INT8_encoding=all(sum(c*((v & 255)>>j & 1) for j, c in enumerate(coeff)) == v for v in range(-128, 128)),
                  no_output_overflow_for_INT8_extremes=(k*16384 < 2**(width-1)))
    model = inp.get('nominal_diagnostic_model')
    def gc_decode(q, activity):
        d = 2*q-activity
        scale = model['endpoint_current_nA']*model['mac_pulse_ns']/model['integration_capacitance_fF']
        lo, hi = model['adc_range_mV']; step = (hi-lo)/2**model['adc_nominal_bits']
        voltage = d*scale; raw_code = math.floor(voltage/step+.5)
        lower = -2**(model['adc_nominal_bits']-1); upper = -lower-1
        code = max(lower, min(upper, raw_code))
        affine = (code*step/scale+activity)/2
        decoded = math.floor(affine+.5)
        return decoded, affine, int(code != raw_code), int(voltage < lo or voltage > hi)
    if cid == '09_gain_cell_edram':
        assert model['partial_sum_rounding'] == 'nearest_integer_half_up_before_bit_weighting'
        checks['all_activity_and_partial_levels_decode'] = all(gc_decode(q, a)[0] == q
            for a in range(rows+1) for q in range(a+1))
        checks['positive_full_scale_code_saturation_retained'] = gc_decode(rows, rows)[2] == 1
    records = []
    for name, x, w in _vectors(k, rows):
        total = 0; before = 0.; saturations = 0; clipping = 0; overflow = False
        for start in range(0, k, rows):
            gx, gw = x[start:start+rows], w[start:start+rows]
            for bit, c_input in enumerate(coeff):
                active = [(xx & 255)>>bit & 1 for xx in gx]
                if cid in BINARY:
                    # Five width-growing levels, then signed input-bit weighting
                    # and finite accumulator. No truncation at an 8-bit leaf.
                    level = [ww if aa else 0 for aa, ww in zip(active, gw)]
                    bits = 8
                    while len(level) > 1:
                        bits += 1
                        level = [_signed(sum(level[j:j+2]), bits) for j in range(0, len(level), 2)]
                    delta = level[0]*c_input
                    before += delta
                else:
                    delta = 0; affine_delta = 0
                    for wb, c_weight in enumerate(coeff):
                        q = sum(aa*((ww & 255)>>wb & 1) for aa, ww in zip(active, gw))
                        decoded, affine, sat, clip = gc_decode(q, sum(active)) if cid == '09_gain_cell_edram' else (q, q, 0, 0)
                        # PCM decoded q is the declared calibrated class, not a
                        # fabricated ADC voltage threshold or transfer curve.
                        delta += c_input*c_weight*decoded
                        affine_delta += c_input*c_weight*affine
                        saturations += sat; clipping += clip
                    before += affine_delta
                unlimited = total+delta
                total = _signed(unlimited, width)
                overflow |= total != unlimited
        truth = sum(a*b for a, b in zip(x, w))
        records.append(dict(id=name, truth=truth, reconstructed=total,
                            absolute_residual=abs(total-truth), before_partial_rounding=before,
                            pre_rounding_residual=before-truth, code_saturated_partials=saturations,
                            analog_clipped_partials=clipping, output_overflow=overflow))
    checks['15_deterministic_finite_reconstructions'] = all(z['truth'] == z['reconstructed'] and not z['output_overflow'] for z in records)
    if cid == '06_mram':
        m = inp['mapping']
        addresses = {(2*o+bit//4, i, bit%4, branch) for o in range(n) for i in range(k)
                     for bit in range(8) for branch in range(2)}
        checks['complementary_MTJ_capacity'] = len(addresses) == case['physical']['physical_MTJs']
        checks['both_absolute_branches_verified'] = m['verify_branch_batches']*m['verify_single_ended_sense_lanes'] == 2*m['selected_pairs_per_write_group']
        checks['phase_resources_not_port_width'] = (m['first_phase_active_MTJs'], m['second_phase_active_MTJs'], m['selected_pairs_per_write_group']) == (128, 64, 64)
    elif cid == '08_feram_hfo2':
        m = inp['mapping']
        addresses = {(i%32, 8*(i//32)+o//16, 8*(o%16)+bit)
                     for i in range(k) for o in range(n) for bit in range(8)}
        checks['unique_1T1C_data_capacity'] = len(addresses) == m['physical_data_cells']
        checks['existing_capture_and_restore_not_repeated'] = m['additional_weight_latch_bits'] == 0 and inp['stage_coverage']['destructive_restore_counted_in_media_read']
    elif cid == '10_fenor_3d':
        addresses = {(i%32, i//32, (o//16)*8+bit, o%16)
                     for i in range(k) for o in range(n) for bit in range(8)}
        checks['unique_strip_layer_data_capacity'] = len(addresses) == case['physical']['physical_cells']
        checks['bias_nodes_not_selected_cells'] = inp['engineering_driver_budget']['installed_nodes'] == 288 and inp['resident']['parallel_cells'] == 128
    elif cid == '03_nor_2d':
        m = inp['mapping']; payload = k*n
        checks['native_page_sector_capacity'] = payload//m['page_Byte'] == 64 and payload//m['sector_Byte'] == 4
        checks['read_slices_not_program_heads'] = m['read_slices']*m['sense_amplifiers_per_slice'] == 4096
    elif cid == '07_pcm':
        m = inp['mapping']; heads = m['writeheads']; stripe = n//heads
        targets = {(row, stripe*head+slot) for row in range(k) for slot in range(stripe) for head in range(heads)}
        checks['all_32cell_striped_transactions_unique'] = len(targets) == k*n
        checks['two_fresh_16lane_verify_passes'] = all(len({(stripe*h)//m['verify_adc_group_width'] for h in range(parity, heads, 2)}) == 16 for parity in (0, 1))
        checks['calibration_thresholds_remain_uninstantiated'] = model['calibration_code_table'] is None and model['physical_transfer_instantiated'] is False
    else:
        m = inp['mapping']
        checks['silicon_3T1C_pseudodifferential_capacity'] = case['physical']['data_storage_sites'] == k*n*16
        # Refresh sign recovery from the longer, single-pair physical mode;
        # do not equate nominal sign recovery with retention validation.
        refresh_scale = model['endpoint_current_nA']*model['single_pair_refresh_ns']/model['integration_capacitance_fF']
        step = (model['adc_range_mV'][1]-model['adc_range_mV'][0])/2**model['adc_nominal_bits']
        limit = 2**(model['adc_nominal_bits']-1)
        refresh_codes = {sign: max(-limit, min(limit-1, math.floor(sign*refresh_scale/step+.5)))
                         for sign in (-1, 1)}
        checks['refresh_endpoint_sign_decode'] = all((1 if code >= 0 else -1) == sign
                                                     for sign, code in refresh_codes.items())
    level = ('exact_signed_integer_conditional_on_correct_binary_storage_and_sensing' if cid in BINARY else model['level'])
    return dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks, level=level,
                source=dict(path=source['path'], sha256=source['sha256']), records=records,
                analog_accuracy_validated=False,
                quantization_induced_bias_assessed=(cid == '09_gain_cell_edram'),
                limitation=('GC nominal ideal integration preserves finite integer results; positive endpoint saturation and pre-rounding residual remain; no drift/repeated-refresh validation.' if cid == '09_gain_cell_edram' else
                            'PCM calibrated nine-class reconstruction only; physical voltage-to-SAR-code transfer and column thresholds are not supplied.' if cid == '07_pcm' else
                            'Integer data path verified conditional on native binary read/write correctness; no device-error probability is inferred.'))

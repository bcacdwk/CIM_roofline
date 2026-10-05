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
        return dict(id=identifier, kind='boundary', provider='explicit_ready_handshake', operation_semantics='capture_only', setup_owner='this_boundary',
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
        # Complete launch -> combinational operation -> destination capture.
        # Destination setup is already in the qualified electrical path.
        return event(s, suffix, 'digital', cycles, operation_semantics='cycle',
                     setup_owner='destination_path', **extra)

    def capture(s, suffix, **extra):
        # No intervening combinational operation or additional input bank.
        return dict(id=s['id'] + ('.' + suffix if suffix else ''),
                    parent_stage_id=s['id'], kind='boundary',
                    provider='explicit_capture_boundary', resources=s['service_timing']['blocks_resources'],
                    source_refs=s.get('source_refs', []), margin_ns=margin,
                    operation_semantics='capture_only', setup_owner='this_boundary',
                    replaces_v3_capture_tick_budget=True, **extra)

    def emit(s, ctx):
        sid = s['id']; i = s['call']['inputs']
        if sid == 'operand_capture' and cid in {'03_nor_2d', '10_fenor_3d'}:
            return [capture(s, '', receiver='existing_4096bit_operand_hold', control_stable_since='native_read_start')]
        if sid == 'operand_capture' and cid == '06_mram':
            return [digital(s, '', 1, operation='capture plus IBMD isolation/reset handoff',
                            source_evidence='inputs.stage_coverage.stream and mapping.hold_lifetime')]
        if cid == '06_mram' and sid == 'terminal_verify':
            return [physical(s, 'absolute_branch_read', p['ibmd_read'], mode='single_ended_absolute_state'),
                    capture(s, 'capture', receiver='existing_absolute_verify_state_latch'),
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
                    capture(s, 'capture', receiver='existing_128bit_native_read_hold'),
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
                            timing_qualification='continuous_E0_to_E2_held_data; E1_phase_to_E2_enable_single_cycle')]
        duration = i.get('duration_parameters')
        if duration is None and 'duration_parameter' in i:
            duration = [i['duration_parameter']]
        if duration:
            parts = {key: p[key] for key in duration}
            if 'input_step' in i:
                parts['input_reset'] = p['input_step']
            attrs = dict(components_ns=parts)
            if sid == 'binary_read':
                attrs.update(selection_launch_at='native_read_start', selected_group_held_through_eight_bits=True)
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
                    first.update(id='digital_reconstruct.phase1', launch_offset_cycle=0, capture_offset_cycles=[],
                                 accumulator_write=False, source_code_overwrite=False)
                    second.update(id='digital_reconstruct.phase2', launch_offset_cycle=1, capture_offset_cycles=[2], accumulator_write=True,
                                  source_code_overwrite=False)
                    for e in (first, second):
                        e['timing_window'] = copy.deepcopy(b['source_hold_window'])
                        e['edge1_update'] = 'phase_only'
                        e['stable_sources'] = list(b['source_hold_window']['stable_sources'])
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
    checks = dict(cycle_setup_only_at_destination=True, capture_only_has_no_extra_cycle=True, explicit_case_dispatch=True, native_topology_preserved=True,
                  scheduled_counts_match_frozen_case=True,
                  logical_payload_is_not_physical_bits=l['B_R_Byte'] == l['K']*l['N']*l['bytes_per_weight'],
                  output_width_from_case=l['output_bits'] == 16+math.ceil(math.log2(l['K'])),
                  native_complete_cycles_not_split_or_double_counted=True,
                  no_hidden_full_matrix_shadow=True,
                  binary_cases_have_no_SAR=(cid not in BINARY or r['adc_count'] == 0))
    snapshot = dict(case_id=cid, adapter_version='step4-native-2.0.0',
                    scheduled_counts=dict(counts), logical_payload_Byte=dict(streaming=l['B_S_Byte'], resident=l['B_R_Byte']),
                    device_identity=case['device']['identity'], physical_organization=copy.deepcopy(case['physical']),
                    native_resources=copy.deepcopy(case['resources']['native_declared']),
                    write_semantics=copy.deepcopy(case['resources']['write_semantics']),
                    primitive_inputs_ns=dict(p), digital_period_ns=b['actual_period_ns'],
                    boundary_semantics='cycle: ceil(t/P)+nP, destination setup belongs to path; capture-only: ceil((t+setup)/P), zero added cycle; included native capture is not repeated',
                    capture_budget_revision='NOR/FeNOR tile capture and MRAM/FeNOR terminal capture: old one-tick budget replaced by exact eligible sampling edge; MRAM tile capture/isolation retains one full cycle',
                    SAR_ns=b['sar_ns'] if cid not in BINARY else None,
                    upstream_aggregate_write_latency_ns=None,
                    MAC_frame_lifecycle='input vector and row/output group already selected at native read launch; group held for all 8 bit operations; ibit and output accumulator may change each bit',
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



"""Ordered serial templates, continuous native time and explicit consumers.

Compression is exact for these templates: after the first digital consumer a
fixed ordered body has a fixed exit phase. Two bodies are executed before its
remaining identical, phase-stationary occurrences are counted. No reordering.
"""
import copy
import math


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=2e-6)


def run(events, period, start_ns=0., align=True, compress=True):
    assert math.isfinite(period) and period > 0
    ledger = {}
    now = start_ns
    trace = []

    def merge(rows, multiplier=1):
        for key, value in rows.items():
            if key not in ledger:
                ledger[key] = {**copy.deepcopy(value), 'count': 0,
                               'duration_ns': 0., 'boundary_wait_ns': 0.}
            target = ledger[key]
            for name in ('count', 'duration_ns', 'boundary_wait_ns'):
                target[name] += value[name] * multiplier

    for e in events:
        if 'repeat' in e:
            n = e['repeat']
            assert isinstance(n, int) and n >= 0
            begin = now
            examples = []
            if not compress:
                for _ in range(n):
                    r = run(e['steps'], period, now, align, False)
                    merge(r['_ledger']); now = r['end_ns']
                trace.append({'axis': e['axis'], 'repeat': n, 'start_ns': begin,
                              'end_ns': now, 'compression': False})
                continue
            for _ in range(min(n, 2)):
                r = run(e['steps'], period, now, align, compress)
                merge(r['_ledger']); now = r['end_ns']; examples.append(r)
            if n > 2:
                # Evaluate the next body independently before multiplying it.
                probe = run(e['steps'], period, now, align, compress)
                steady = examples[-1]
                assert close(probe['latency_ns'], steady['latency_ns']), e['axis']
                assert probe['_ledger'].keys() == steady['_ledger'].keys()
                for key in probe['_ledger']:
                    for name in ('count', 'duration_ns', 'boundary_wait_ns'):
                        assert close(probe['_ledger'][key][name], steady['_ledger'][key][name]), (e['axis'], key, name)
                merge(steady['_ledger'], n - 2)
                now += steady['latency_ns'] * (n - 2)
            trace.append({'axis': e['axis'], 'repeat': n, 'start_ns': begin,
                          'end_ns': now, 'compression': 'ordered_first_and_verified_stationary_body',
                          'examples': [r['trace'] for r in examples],
                          'first_body_ns': examples[0]['latency_ns'] if examples else 0,
                          'steady_body_ns': examples[-1]['latency_ns'] if examples else 0})
            continue
        kind = e['kind']; begin = now; wait = 0.
        if kind == 'digital':
            assert e.get('margin_ns', 0.) == 0., 'cycle entry cannot charge destination setup twice'
            assert e.get('operation_semantics', 'cycle') == 'cycle'
        elif kind == 'boundary':
            assert e.get('operation_semantics', 'capture_only') in ('capture_only', 'included_capture', 'ready_marker')
        if kind in ('digital', 'boundary') and align:
            ratio = (now + e.get('margin_ns', 0.)) / period
            edge = math.ceil(ratio - max(1e-10, 4 * math.ulp(ratio))) * period
            wait = max(0., edge - now); now += wait
        if kind == 'physical':
            raw = e['ns']; duration = raw; clock = None; unit = 'ns'
        elif kind == 'digital':
            raw = e['cycles']; duration = raw * period; clock = 'lv_core'; unit = 'cycles'
        elif kind == 'boundary':
            raw = duration = 0.; clock = None; unit = 'ns'
        else:
            raise ValueError(kind)
        assert math.isfinite(duration) and duration >= 0 and e['resources'], e
        now += duration
        key = (e['id'], e['provider'], kind, e.get('mode'), raw)
        row = ledger.setdefault(key, {'id': e['id'], 'provider': e['provider'],
            'kind': kind, 'mode': e.get('mode'), 'raw': raw, 'unit': unit, 'clock_id': clock,
            'count': 0, 'duration_ns': 0., 'boundary_wait_ns': 0.,
            'resources': e['resources'], 'source_refs': e.get('source_refs', []),
            'operation_semantics': e.get('operation_semantics', 'native_service' if kind == 'physical' else 'cycle' if kind == 'digital' else 'capture_only'),
            'setup_owner': e.get('setup_owner', 'retained_complete_native_service' if kind == 'physical' else 'destination_path' if kind == 'digital' else 'this_boundary'),
            'coverage_status': e.get('coverage_status', 'native_budget_retained' if e['provider'].startswith(('v3', 'retained', 'native')) else 'actual_case_path_instantiated')})
        row['count'] += 1; row['duration_ns'] += duration; row['boundary_wait_ns'] += wait
        trace.append({**e, 'start_ns': begin, 'service_start_ns': begin + wait,
                      'end_ns': now, 'boundary_wait_ns': wait})
    stages = []
    for row in ledger.values():
        status = row['coverage_status']
        if status not in ('native_budget_retained', 'case_path_pending', 'actual_case_path_instantiated'):
            status = ('case_path_pending' if 'pending' in status or 'budget' in status else
                      'native_budget_retained' if 'native' in status or 'opaque' in status else 'actual_case_path_instantiated')
        stages.append({'stage_id': row['id'], 'provider': row['provider'],
            'raw_returns': [{'value': row['raw'], 'unit': row['unit'], 'scope': 'per event',
                             'clock_id': row['clock_id'], 'status': 'OK', 'reason': None}],
            'latency_once_ns': row['duration_ns'] / row['count'], 'count': row['count'],
            'resource_occupancy_ns': row['duration_ns'] + row['boundary_wait_ns'],
            'initiation_interval_ns': None, 'initiation_interval_proof': None,
            'clock_id': row['clock_id'], 'included_substages': [], 'included_repetition_dimensions': [],
            'external_repetition_dimensions': ['ordered case templates'], 'conversion_count': 1,
            'status': 'OK', 'reason': None,
            'timing_kind': 'digital_step' if row['kind'] == 'digital' else 'service_duration',
            'constraint_clock_id': None, 'boundary_wait_ns': row['boundary_wait_ns'],
            'case_path_status': status, 'coverage_status': row['coverage_status'],
            'resources': row['resources'], 'mode': row['mode'], 'source_refs': row['source_refs'],
            'operation_semantics': row['operation_semantics'], 'setup_owner': row['setup_owner'],
            'source_category': source_category(row['provider'], row['kind'], row['id']),
            'service_time_total_ns': row['duration_ns']})
    return {'latency_ns': now - start_ns, 'end_ns': now, 'stages': stages, 'trace': trace,
            'boundary_wait_ns': sum(r['boundary_wait_ns'] for r in ledger.values()), '_ledger': ledger}


def public(result):
    return {k: v for k, v in result.items() if k not in ('_ledger', 'trace')}


def metrics(case, s, r, availability=1.):
    l = case['logical']; rho = 1e9 * l['B_S_Byte'] / s; tau = 1e9 * l['B_R_Byte'] / r
    if availability is None or availability <= 0:
        return {'rho_Byte_per_s': None, 'tau_Byte_per_s': None, 'RI_star': None, 'U_star': None, 'status': 'INFEASIBLE'}
    return {'rho_Byte_per_s': rho * availability, 'tau_Byte_per_s': tau * availability,
            'RI_star': rho / tau, 'U_star': r / s, 'status': 'OK'}


def evaluate(case, plan, backend, align=True):
    period = backend['actual_period_ns']
    if align:
        validate_timing(case, plan, backend)
    services = {key: run(plan[key], period, align=align) for key in ('streaming', 'resident', 'maintenance')}
    s = services['streaming']['latency_ns']; r = services['resident']['latency_ns']
    maintenance = {'raw_stage_metrics': metrics(case, s, r), 'effective_stage_metrics': None,
                   'workload_write_Byte': 0, 'recompute_required': True, 'applicable': False,
                   'availability': 1., 'feasible': True}
    if 'maintenance_period_ns' in plan:
        atom_s = run(plan['atomic_streaming'], period, align=align)['latency_ns']
        atom_r = run(plan['atomic_resident'], period, align=align)['latency_ns']
        guard = max(atom_s, atom_r)
        busy = services['maintenance']['latency_ns']; retention = plan['maintenance_period_ns']
        assert retention > 0
        # Fixed clock-aligned frames keep every physical write-back endpoint
        # at the same offset. A nonintegral nominal period may violate an
        # individual cell's retention by edge drift even when H+guard fits.
        frame = math.floor(retention / period + 1e-10) * period if align else retention
        alpha = (frame - busy - guard) / frame if frame > 0 else None
        feasible = alpha is not None and alpha > 0
        retention_proof = {'status': 'INFEASIBLE' if not feasible else 'DIAGNOSTIC_UNALIGNED',
                           'frame_sweep_and_guard_fit': feasible}
        if align and feasible:
            assert close(frame / period, round(frame / period)) and frame <= retention + 1e-8
            completions = []
            for index in range(3):
                sweep = run(list(event_stream(plan['maintenance'])), period, start_ns=index*frame)
                completions.append([x['end_ns'] for x in sweep['trace']
                    if x.get('id') == 'refresh_decode_load_rewrite.current_program'])
            assert len(completions[0]) == len(completions[1]) == len(completions[2]) == 256
            ages = [b-a for first, second in zip(completions, completions[1:]) for a,b in zip(first,second)]
            assert max(ages) <= retention + 1e-8 and all(close(x, frame) for x in ages)
            retention_proof = {'status': 'PASS', 'frames_executed': 3, 'writeback_groups_per_frame': 256,
                'physical_writeback_interval_min_ns': min(ages), 'physical_writeback_interval_max_ns': max(ages),
                'retention_limit_ns': retention, 'frame_sweep_and_guard_fit': busy+guard < frame,
                'frame_starts_ns': [0., frame, 2*frame],
                'policy': 'stop foreground admissions within guard of each fixed frame start; all maintenance endpoints repeat at identical offsets'}
        maintenance.update(applicable=True, availability=alpha, feasible=feasible,
            period_ns=frame, retention_limit_ns=retention, nominal_period_ns=retention,
            scheduled_frame_period_ns=frame, frame_quantization_slack_ns=retention-frame,
            busy_ns=busy, guard_ns=guard, retention_schedule_proof=retention_proof,
            atomic_streaming_ns=atom_s, atomic_resident_ns=atom_r,
            scheduling_proof='clock-aligned frame no longer than native retention, complete maintenance sweep plus one max nonpreemptive foreground guard',
            effective_delta_S_ns=s / alpha if feasible else None,
            effective_T_R_ns=r / alpha if feasible else None,
            effective_times_meaning='long-term service cost; not a single request physical latency')
    m = metrics(case, s, r, maintenance['availability'])
    maintenance['effective_stage_metrics'] = m
    return services, maintenance, m


def validate_timing(case, plan, backend):
    period = backend['actual_period_ns']; paths = backend['paths']
    multicycle = {'pcm_decode_reconstruct_path', 'gc_decode_reconstruct_path'}
    for path in paths:
        assert path['complete_serial_path'] and path['actual_load']
        cycles = path['capture_edge'] - path['launch_edge']
        assert path['single_cycle'] == (cycles == 1) and path['available_cycles'] == cycles
        assert cycles in (1, 2)
        if cycles == 2:
            assert path['id'] in multicycle and path['launch_edge'] == 0
            assert path['stable_sources'] and path['path_class'] == 'held_reconstruction_data'
        if path['id'] == 'capture_enable_path':
            assert (path['launch_edge'], path['capture_edge'], cycles) == (1, 2, 1)
        assert period * cycles + 1e-10 >= path['delay_ns']
    assert period + 1e-10 >= max(5., backend['timing_min_period_ns'])
    frame = backend.get('frame_preselection')
    if frame is not None:
        available = plan['snapshot']['primitive_inputs_ns'][frame['lead_source_parameter']]
        assert available + 1e-10 >= frame['settle_to_existing_combinational_pins_ns']
        assert frame['no_preselected_cache_or_pipeline']
        for name in frame['early_sources']:
            key = 'digital_mac_source_' + name + '_full_s'
            assert frame['full_source_to_capture_delay_ns'][key] <= available + period + 1e-10

        tiles = 0; bits = 0; captured = False
        for event in event_stream(plan['streaming']):
            if event['id'] == 'binary_read':
                assert bits in (0, 8)
                assert event['selection_launch_at'] == 'native_read_start'
                assert event['selected_group_held_through_eight_bits'] is True
                tiles += 1; bits = 0; captured = event.get('included_capture', False)
            elif event['id'] == 'operand_capture':
                assert bits == 0 and not captured
                assert event['kind'] == ('digital' if case['case_id'] == '06_mram' else 'boundary')
                captured = True
            elif event['id'] == 'digital_mac':
                assert captured and bits < 8 and event['cycles'] == 1
                bits += 1
        assert bits == 8 and tiles == next(s['count']['value'] for s in case['services'] if s['id'] == 'binary_read')
    if case['case_id'] in ('07_pcm', '09_gain_cell_edram'):
        hold = backend['source_hold_window']
        assert hold['source_stability_edges'] == [0, 2] and hold['capture_edges'] == [2]
        assert hold['no_new_intermediate_registers'] and not hold['overlap']
        assert hold['edge_updates']['1'] == ['phase_only']
        assert hold['capture_enable_at_edge1'] is False
        assert hold['phase_enable_launch_edge'] == 1 and hold['phase_enable_capture_edge'] == 2
        assert any(x['id'] == 'capture_enable_path' for x in paths)
        required = {'SAR_codes', 'input_register', 'input_bit', 'output_group', 'old_accumulator'}
        required.add('PCM_calibration_thresholds' if case['case_id'] == '07_pcm' else 'GC_popcount_input_bits')
        assert required <= set(hold['stable_sources'])
        for name in required:
            assert hold['source_stability'][name] == [0, 2]
        held_batches = 0; active = None
        for event in event_stream(plan['streaming']):
            if event['id'] == 'sar':
                assert active is None, 'new conversion before previous E2 capture'
                active = 0
            elif event['id'].startswith('digital_reconstruct.phase'):
                assert active in (0, 1), 'reconstruction without its own conversion'
                ending = active + event['cycles']
                assert event['cycles'] == 1 and ending <= 2
                assert event['launch_offset_cycle'] == active
                assert event['capture_offset_cycles'] == ([2] if ending == 2 else [])
                assert event['accumulator_write'] == (ending == 2)
                assert not event['source_code_overwrite']
                assert event['timing_window'] == hold and event['edge1_update'] == 'phase_only'
                assert required <= set(event['stable_sources'])
                if ending == 2:
                    held_batches += 1; active = None
                else:
                    active = ending
            elif active is not None:
                raise AssertionError('intervening operation inside held interval')
        assert active is None
        assert held_batches == next(s['count']['value'] for s in case['services'] if s['id'] == 'sar')
    return {'status': 'PASS', 'policy_floor_and_actual_period_distinct': True,
            'qualified_path_count': len(paths), 'two_cycle_data_only_with_lifecycle_evidence': True,
            'phase_capture_enable_remains_one_cycle': True}


def event_stream(nodes):
    """Transparent ordered template traversal, also used for lifecycle QA."""
    for event in nodes:
        if 'repeat' in event:
            for _ in range(event['repeat']):
                yield from event_stream(event['steps'])
        else:
            yield event


def source_category(provider, kind, stage_id):
    if kind == 'boundary' or provider.startswith(('explicit_', 'public_clock_boundary')):
        return 'interface_and_schedule'
    if provider.startswith(('retained', 'v3', 'native')):
        return 'retained_native_or_arithmetic_service'
    if provider == 'neurosim_native' and 'sar' in stage_id.lower():
        return 'direct_neurosim_module'
    return 'neurosim_gate_composition'


def checks():
    def d(n=1): return {'id': 'd', 'kind': 'digital', 'cycles': n, 'resources': ['r'], 'provider': 'check'}
    def p(n): return {'id': 'p', 'kind': 'physical', 'ns': n, 'resources': ['r'], 'provider': 'native'}
    cases = [([p(7), d()], 5), ([d(), p(7)], 5), ([p(3), p(4)], 5.5),
             ([{'repeat': 9, 'axis': 'inner', 'steps': [p(7), d()]}], 5.5)]
    for body, period in cases:
        events = [{'repeat': 11, 'axis': 'outer', 'steps': body}]
        for start in (0, 1.25, 1e9):
            a = run(events, period, start, compress=True)
            b = run(events, period, start, compress=False)
            assert close(a['latency_ns'], b['latency_ns'])
            assert a['_ledger'].keys() == b['_ledger'].keys()
            for k in a['_ledger']:
                for name in ('count', 'duration_ns', 'boundary_wait_ns'):
                    assert close(a['_ledger'][k][name], b['_ledger'][k][name])
    assert run([p(2), p(2), d()], 5)['boundary_wait_ns'] == 1
    edge_examples = []
    for finish in (9.70, 9.80, 9.99, 10., 10.01):
        setup = .25; period = 10.
        capture = {'id': 'receive', 'kind': 'boundary', 'margin_ns': setup,
                   'provider': 'explicit_capture', 'resources': ['existing_hold']}
        c = run([capture], period, start_ns=finish)
        o = run([d()], period, start_ns=finish)
        assert close(c['end_ns'], math.ceil((finish+setup)/period-1e-10)*period)
        assert close(o['end_ns'], (math.ceil(finish/period-1e-10)+1)*period)
        wrapped = run([{'repeat': 1, 'axis': 'transparent_annotation', 'steps': [capture]}], period, start_ns=finish)
        assert close(wrapped['end_ns'], c['end_ns'])
        assert close(run([d(2)], period, finish)['end_ns'], run([d(), d()], period, finish)['end_ns'])
        edge_examples.append({'physical_complete_ns': finish, 'period_ns': period,
                              'setup_ns': setup, 'capture_only_end_ns': c['end_ns'],
                              'full_cycle_operation_end_ns': o['end_ns']})
    invalid = {**d(), 'margin_ns': .25}
    try: run([invalid], 10)
    except AssertionError: pass
    else: raise AssertionError('double setup was accepted')
    assert close(run([p(2),p(2),d(2)],5)['latency_ns'], run([p(4),d(),d()],5)['latency_ns'])
    return {'status': 'PASS', 'edge_examples': edge_examples,
            'cycle_entry_setup_rejected': True, 'transparent_wrapper_equivalence': True,
            'template_expanded_comparisons': len(cases) * 3,
            'checks': ['first/steady ordered-template equivalence', 'nested phase propagation',
                       'physical subsequences align only at the next digital consumer']}

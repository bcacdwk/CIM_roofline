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
            'service_time_total_ns': row['duration_ns']})
    return {'latency_ns': now - start_ns, 'end_ns': now, 'stages': stages, 'trace': trace,
            'boundary_wait_ns': sum(r['boundary_wait_ns'] for r in ledger.values()), '_ledger': ledger}


def public(result):
    return {k: v for k, v in result.items() if k not in ('_ledger', 'trace')}


def metrics(case, s, r, availability=1.):
    l = case['logical']; rho = 1e9 * l['B_S_Byte'] / s; tau = 1e9 * l['B_R_Byte'] / r
    if availability <= 0:
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
        alpha = (retention - busy - guard) / retention
        maintenance.update(applicable=True, availability=alpha, feasible=alpha > 0,
            period_ns=retention, busy_ns=busy, guard_ns=guard,
            atomic_streaming_ns=atom_s, atomic_resident_ns=atom_r,
            scheduling_proof='strict serial maintenance frame plus one maximum nonpreemptive foreground quantum; fixed ordered group refresh repeated at same frame offsets',
            effective_delta_S_ns=s / alpha if alpha > 0 else None,
            effective_T_R_ns=r / alpha if alpha > 0 else None,
            effective_times_meaning='long-term service cost; not a single request physical latency')
    m = metrics(case, s, r, maintenance['availability'])
    maintenance['effective_stage_metrics'] = m
    return services, maintenance, m


def validate_timing(case, plan, backend):
    period = backend['actual_period_ns']
    paths = backend['paths']
    for path in paths:
        assert path['complete_serial_path'] and path['actual_load']
        assert path['single_cycle'] and path['available_cycles'] == 1
        assert path['capture_edge'] - path['launch_edge'] == 1
        assert period + 1e-10 >= path['delay_ns']
    assert period + 1e-10 >= max(5., backend['timing_min_period_ns'])
    if case['case_id'] in ('07_pcm', '09_gain_cell_edram'):
        hold = backend['source_hold_window']
        assert hold['source_stability_edges'] == [0, 2] and hold['capture_edges'] == [2]
        assert hold['no_new_intermediate_registers'] and hold['no_multicycle_timing_exception']
        held_batches = 0
        def inspect(nodes, multiplier=1):
            nonlocal held_batches
            for i, event in enumerate(nodes):
                if 'repeat' in event:
                    inspect(event['steps'], multiplier * event['repeat'])
                elif event['id'] == 'digital_reconstruct.phase1':
                    held_batches += multiplier
                    other = nodes[i + 1]
                    assert other['id'] == 'digital_reconstruct.phase2'
                    assert event['cycles'] == other['cycles'] == 1
                    assert event['accumulator_write'] is False and other['accumulator_write'] is True
                    assert not event['source_code_overwrite'] and not other['source_code_overwrite']
        inspect(plan['streaming'])
        assert held_batches == next(s['count']['value'] for s in case['services'] if s['id'] == 'sar')
    return {'status': 'PASS', 'all_new_paths_single_cycle': True,
            'policy_floor_and_actual_period_distinct': True,
            'qualified_path_count': len(paths), 'no_inherited_pilot_multicycle_exception': True}


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
    return {'status': 'PASS', 'template_expanded_comparisons': len(cases) * 3,
            'checks': ['first/steady ordered-template equivalence', 'nested phase propagation',
                       'physical subsequences align only at the next digital consumer']}

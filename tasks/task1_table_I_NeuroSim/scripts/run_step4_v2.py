#!/usr/bin/env python3
"""Ten reference configurations; fresh builds, serial service, bounded diagnostics.

From any cwd: python3 <task>/scripts/run_step4_v2.py --run-id <new> [--case ID]
--mode replay replays the original v3 times only, without new backend labels.
"""
import argparse
import copy
import csv
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True

CASES = ['01_sram_acim', '02_sram_dcim', '03_nor_2d', '04_nand_3d', '05_rram',
         '06_mram', '07_pcm', '08_feram_hfo2', '09_gain_cell_edram', '10_fenor_3d']
PILOTS = {'01_sram_acim', '02_sram_dcim', '05_rram'}
BASELINE = '0fac5278fe6477144f6ad74a7747d950b3fc3517'
SHA = '8a88abf85844c0e1ba17cc771ea535fff6040456'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, x):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec); sys.modules[name] = obj
    spec.loader.exec_module(obj); return obj


def snapshot(own, out, cases):
    repo = own.parents[1]; snap = out / 'snapshot'; task = snap / 'tasks/task1_table_I_NeuroSim'
    files = set()
    for directory in ('step4', 'step4_v2', 'pilots', 'contracts'):
        files.update(p for p in (own / directory).rglob('*') if p.is_file() and p.suffix in ('.py', '.cpp', '.h', '.json', '.md', '.csv'))
    files.update(own / rel for rel in ('scripts/run_step4_v2.py', 'scripts/run_step3.py', 'scripts/check_step2.py',
        'probes/interface_revision/legacy_replay.py', 'provenance/neurosim.lock.json'))
    for cid in cases:
        f = own / 'configs/cases' / (cid + '.json'); files.add(f)
        c = json.loads(f.read_text())
        for source in c['provenance']['sources'].values():
            if isinstance(source, dict) and 'path' in source:
                src = repo / source['path']; assert sha(src) == source['sha256'], src; files.add(src)
        for name in ('result.json', 'resolved.json'):
            files.add(own / 'results/step4/reference-final-20261004' / cid / name)
        if cid in PILOTS:
            for dirname in ('results/step3/integration-final-20261004', 'results/step3_v2/integration-audited-v2'):
                for name in ('result.json', 'resolved.json', 'sensitivity.json'):
                    files.add(own / dirname / cid / name)
    shared = repo / 'tasks/task1_table_I_NVM/analysis/shared_baseline'
    for rel in ('scripts/check_nominal_services.py', 'data/nominal_service_diagnostics.json'):
        files.add(shared / rel)
    if '04_nand_3d' in cases:
        files.add(repo / 'tasks/task1_table_I_NVM/analysis/04_nand_3d/data/quantization_diagnostics.json')
    for f in sorted(files):
        dest = snap / f.relative_to(repo); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, dest)
    dump(out / 'snapshot_manifest.json', {str(f.relative_to(repo)): sha(f) for f in sorted(files)})
    return task


def comparison(case, p, b, adapter, engine, replay):
    # All variants are diagnostic decomposition, not additional valid clock points.
    at5 = copy.deepcopy(b); at5['actual_period_ns'] = 5.
    old = copy.deepcopy(at5)
    if old.get('sar_ns') is not None: old['sar_ns'] = p['adc_batch']
    x0, _, _ = engine.evaluate(case, adapter.build(case, p, old), old, align=False)
    x1, _, _ = engine.evaluate(case, adapter.build(case, p, at5), at5, align=False)
    x2, _, _ = engine.evaluate(case, adapter.build(case, p, b), b, align=False)
    x3, _, _ = engine.evaluate(case, adapter.build(case, p, b), b)
    out = {}
    for name, key in [('streaming', 'raw_delta_S_ns'), ('resident', 'raw_T_R_ns'), ('maintenance', 'maintenance_busy_ns')]:
        values = [x[name]['latency_ns'] for x in (x0, x1, x2, x3)]
        out[name] = {'v3_ns': replay[key], 'current_ns': values[-1],
            'difference_ns': values[-1] - replay[key],
            'cause_ledger_ns': {'explicit_stage_or_interface_changes': values[0] - replay[key],
                'SAR_replacement': values[1] - values[0], 'digital_period_change': values[2] - values[1],
                'consumer_boundary_wait': values[3] - values[2]}}
        assert engine.close(sum(out[name]['cause_ledger_ns'].values()), out[name]['difference_ns'])
    out['decomposition_policy'] = 'non-operating diagnostic variants at old clock/no edges; no rho/tau mixing'
    return out


def diagnostics(case, p, b, adapter, engine, baseline):
    cid = case['case_id']; base_services, base_m, _ = baseline; rows = []
    def record(label, pp, bb):
        services, maintenance, metrics = engine.evaluate(case, adapter.build(case, pp, bb), bb)
        row = {'id': label, 'actual_period_ns': bb['actual_period_ns'],
               **{k + '_ns': v['latency_ns'] for k, v in services.items()},
               'availability': maintenance['availability'], 'maintenance_feasible': maintenance['feasible'],
               'guard_ns': maintenance.get('guard_ns'), 'metrics': metrics}
        rows.append(row); return services, maintenance
    if b.get('sar_ns') is not None:
        bb = copy.deepcopy(b); bb['sar_ns'] += 8.
        services, maintenance = record('shared_SAR_duration_plus8ns', p, bb)
        consumers = ['streaming'] + (['resident'] if cid in ('04_nand_3d', '07_pcm') else ['maintenance'])
        for kind in consumers:
            before = [x for x in base_services[kind]['stages'] if 'sar' in x['stage_id'].lower() and x['provider'] == 'neurosim_native']
            after = [x for x in services[kind]['stages'] if 'sar' in x['stage_id'].lower() and x['provider'] == 'neurosim_native']
            count = sum(x['count'] for x in before)
            delta = sum(x['service_time_total_ns'] for x in after) - sum(x['service_time_total_ns'] for x in before)
            assert count > 0 and engine.close(delta, 8 * count)
            assert services[kind]['latency_ns'] + 1e-6 >= base_services[kind]['latency_ns']
            rows[-1].setdefault('actual_SAR_consumers', {})[kind] = {'count': count, 'physical_duration_increase_ns': delta,
                'total_latency_increase_ns': services[kind]['latency_ns'] - base_services[kind]['latency_ns'],
                'policy': 'new physical time may consume previous boundary slack without increasing total latency'}
        if cid == '09_gain_cell_edram':
            assert engine.close(services['resident']['latency_ns'], base_services['resident']['latency_ns'])
            assert maintenance['availability'] <= base_m['availability'] + 1e-12
    key = {'03_nor_2d': 'page_program', '04_nand_3d': 'page_program', '06_mram': 'direction_write_slot',
           '07_pcm': 'reset_pulse', '08_feram_hfo2': 'polarization_hold',
           '09_gain_cell_edram': 'program_complete', '10_fenor_3d': 'polarization_pulse'}[cid]
    assert key in p, (cid, key, list(p))
    pp = copy.deepcopy(p); pp[key] += 11.
    services, _ = record('shared_polarization_hold_plus11ns' if cid == '08_feram_hfo2' else 'native_write_only_plus11ns', pp, b)
    if cid == '08_feram_hfo2':
        assert services['streaming']['latency_ns'] > base_services['streaming']['latency_ns']
    else:
        assert engine.close(services['streaming']['latency_ns'], base_services['streaming']['latency_ns'])
    assert services['resident']['latency_ns'] + 1e-6 >= base_services['resident']['latency_ns']
    physical = lambda service: sum(x['service_time_total_ns'] for x in service['stages'] if x['timing_kind'] == 'service_duration')
    assert physical(services['resident']) > physical(base_services['resident'])
    rows[-1]['resident_native_physical_increase_ns'] = physical(services['resident']) - physical(base_services['resident'])
    if cid == '09_gain_cell_edram':
        pp = copy.deepcopy(p); pp['refresh_period'] = base_services['maintenance']['latency_ns'] / 2
        _, m = record('infeasible_retention_negative_control', pp, b)
        assert not m['feasible'] and m['effective_stage_metrics']['rho_Byte_per_s'] is None
    return {'status': 'PASS', 'scope': 'few synthetic service-dependency controls; not new device scenarios', 'rows': rows}


def budget_sensitivity(case, p, b, adapter, engine):
    if case['case_id'] != '04_nand_3d':
        return {'status': 'NOT_APPLICABLE', 'reason': 'no retained unclosed NAND affine/calibration budget in this case'}
    _, base_m, base = engine.evaluate(case, adapter.build(case, p, b), b)
    rows = []
    for factor in (1, 2, 4):
        bb = copy.deepcopy(b)
        bb['retained_affine_budget_scale'] = factor
        bb['retained_calibration_budget_scale'] = factor
        plan = adapter.build(case, p, bb)
        services, maintenance, metrics = engine.evaluate(case, plan, bb)
        rows.append({'factor': factor, 'actual_period_ns': bb['actual_period_ns'],
            'affine_cycles_per_round': factor, 'calibration_cycles': 448*factor+2,
            'delta_S_ns': services['streaming']['latency_ns'], 'T_R_ns': services['resident']['latency_ns'],
            'rho_Byte_per_s': metrics['rho_Byte_per_s'], 'tau_Byte_per_s': metrics['tau_Byte_per_s'],
            'RI_star': metrics['RI_star'], 'U_star': metrics['U_star']})
    for row in rows:
        row['streaming_time_change_percent'] = (row['delta_S_ns']/rows[0]['delta_S_ns']-1)*100
        row['resident_time_change_percent'] = (row['T_R_ns']/rows[0]['T_R_ns']-1)*100
    return {'status': 'PASS', 'scope': 'few conditional-budget controls, not modeled multiplier/divider designs',
            'fixed': ['native P/E/frontend', 'ADC', 'encoding', 'resources', 'working period'],
            'changed': 'normal affine/round budget and 448 calibration arithmetic cycles; two publish cycles unchanged',
            'rows': rows, 'conclusion': 'these bounded controls preserve order of magnitude; unclosed arithmetic remains an explicit condition, not a certification'}


def worker(a, own, out, cases):
    repo = own.parents[1]
    sys.path[:0] = [str(own / 'pilots'), str(own / 'scripts'), str(own / 'probes/interface_revision')]
    import legacy_replay
    from check_step2 import schema_check, output_contract_tests
    engine = module('step4_engine', own / 'step4_v2/engine.py')
    dump(out / 'interface_checks.json', {'scheduler': engine.checks(), 'base_output': output_contract_tests(own)})
    configs = {cid: json.loads((own / 'configs/cases' / (cid + '.json')).read_text()) for cid in cases}
    replays = {}
    for cid, case in configs.items():
        schema_check(case, json.loads((own / 'contracts/case.schema.json').read_text()))
        p = legacy_replay.parameters(case, repo); replay = legacy_replay.aggregate(case, p)
        expected, source = legacy_replay.expected_reference(case, repo)
        assert all(math.isclose(replay[k], v, rel_tol=1e-12, abs_tol=1e-7) for k, v in expected.items())
        replay['comparison_source'] = source; replays[cid] = replay
    if a.mode == 'replay':
        rows = []
        for cid, replay in replays.items():
            dump(out / cid / 'replay.json', replay)
            rows.append({'case_id': cid, 'delta_S_ns': replay['raw_delta_S_ns'], 'T_R_ns': replay['raw_T_R_ns']})
        dump(out / 'summary.json', {'status': 'PASS', 'mode': 'v3_original_time_replay', 'case_results': rows})
        return
    pilots = [cid for cid in cases if cid in PILOTS]
    pilot_regression = {}
    if pilots:
        pilot_out = out / 'pilot_execution'; pilot_out.mkdir()
        choice = 'all' if len(pilots) == 3 else pilots[0]
        argv = [sys.executable, '-B', str(own / 'scripts/run_step3.py'), '--root', a.root, '--cxx', a.cxx,
                '--case', choice, '--worker', str(pilot_out), '--revision', 'v2', '--wire-um', str(a.wire_um)]
        if a.period_ns is not None: argv += ['--period-ns', str(a.period_ns)]
        run = subprocess.run(argv, cwd=out, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / 'pilots.log').write_text(run.stdout)
        if run.returncode: raise RuntimeError(str(out / 'pilots.log'))
        for cid in pilots:
            shutil.move(str(pilot_out / cid), str(out / cid))
            current = json.loads((out / cid / 'result.json').read_text())
            accepted = json.loads((own / 'results/step3_v2/integration-audited-v2' / cid / 'result.json').read_text())
            match = current == accepted
            if a.period_ns is None and a.wire_um == 10.: assert match, cid
            pilot_resolved = json.loads((out / cid / 'resolved.json').read_text())
            pilot_adapter = module('v2_pilot_adapter_'+cid, own / 'pilots/adapters' / ({'01_sram_acim':'acim.py','02_sram_dcim':'dcim.py','05_rram':'rram.py'}[cid]))
            pilot_plan = pilot_adapter.build(configs[cid], legacy_replay.parameters(configs[cid], repo), pilot_resolved['backend'])
            common_s = engine.run(pilot_plan['streaming'], pilot_resolved['backend']['actual_period_ns'])
            common_r = engine.run(pilot_plan['resident'], pilot_resolved['backend']['actual_period_ns'])
            assert engine.close(common_s['latency_ns'], current['streaming']['delta_S_ns'])
            assert engine.close(common_r['latency_ns'], current['resident_load']['T_R_ns'])
            pilot_regression[cid] = {'status': 'PASS' if match else 'NAMED_OPERATING_POINT',
                'entire_result_identical_to_accepted_V2': match,
                'pilot_implementation_changed': False, 'V2_common_boundary_engine_agrees': True}
    dump(out / 'pilot_regression.json', pilot_regression)
    backend = module('step4_backend', own / 'step4_v2/backend.py') if any(cid not in PILOTS for cid in cases) else None
    for cid in cases:
        if cid in PILOTS: continue
        case = configs[cid]; p = legacy_replay.parameters(case, repo)
        work = out / cid; work.mkdir()
        adapter = module('step4_' + cid, own / 'step4_v2/adapters' / ('nand.py' if cid == '04_nand_3d' else 'native.py'))
        execute = backend.build(case, Path(a.root), work / 'backend', a.cxx, own / 'step4_v2')
        b = execute('reference', wire_um=a.wire_um, operating_period_ns=a.period_ns)
        plan = adapter.build(case, p, b)
        assert all(plan['checks'].values()), (cid, plan['checks'])
        services, maintenance, metrics = engine.evaluate(case, plan, b)
        timing_check = engine.validate_timing(case, plan, b)
        wrapped_plan = copy.deepcopy(plan)
        for key in ('streaming', 'resident', 'maintenance'):
            wrapped_plan[key] = [{'repeat': 1, 'axis': 'transparent_adapter_container', 'steps': plan[key]}]
        wrapped_services, wrapped_m, wrapped_metrics = engine.evaluate(case, wrapped_plan, b)
        assert all(engine.close(wrapped_services[key]['latency_ns'], services[key]['latency_ns']) for key in services)
        assert wrapped_metrics == metrics
        timing_check['actual_case_transparent_wrapper_invariance'] = True

        illegal = copy.deepcopy(b); illegal['actual_period_ns'] = b['timing_min_period_ns'] / 2
        try:
            engine.evaluate(case, plan, illegal)
        except AssertionError:
            timing_check['illegal_period_rejected'] = True
        else:
            raise AssertionError('illegal period was accepted')
        if cid in ('07_pcm', '09_gain_cell_edram'):
            for label in ('late_data_at_E1', 'capture_at_E1', 'phase_enable_borrows_two_cycles', 'intermediate_bank'):
                wrong = copy.deepcopy(b)
                if label == 'late_data_at_E1': wrong['source_hold_window']['edge_updates']['1'].append('input_bit')
                elif label == 'capture_at_E1': wrong['source_hold_window']['capture_enable_at_edge1'] = True
                elif label == 'intermediate_bank': wrong['source_hold_window']['no_new_intermediate_registers'] = False
                else:
                    path = next(x for x in wrong['paths'] if x['id'] == 'capture_enable_path')
                    path.update(launch_edge=0, available_cycles=2, single_cycle=False)
                try: engine.evaluate(case, plan, wrong)
                except AssertionError: timing_check[label + '_rejected'] = True
                else: raise AssertionError(label + ' was accepted')
        dump(work / 'timing_checks.json', timing_check)
        for name in ('streaming', 'resident'):
            again = engine.run(plan[name], b['actual_period_ns'], start_ns=services[name]['end_ns'])
            assert engine.close(again['latency_ns'], services[name]['latency_ns']), (cid, name, 'steady interval')
        # Full expanded schedules are diagnostic only and remain local. This also
        # proves NAND grouping preserves the actual ordering and edge waits.
        grouping = {}
        for name in ('streaming', 'resident', 'maintenance'):
            expanded = engine.run(plan[name], b['actual_period_ns'], compress=False)
            computed = services[name]
            assert engine.close(expanded['latency_ns'], computed['latency_ns']), (cid, name)
            assert expanded['_ledger'].keys() == computed['_ledger'].keys()
            for k in expanded['_ledger']:
                for field in ('count', 'duration_ns', 'boundary_wait_ns'):
                    assert engine.close(expanded['_ledger'][k][field], computed['_ledger'][k][field]), (cid, name, k, field)
            grouping[name] = {'status': 'PASS', 'expanded_vs_grouped_latency_ns': expanded['latency_ns'],
                              'stage_count_and_wait_equal': True}
            dump(work / (name + '_trace.json'), computed['trace'])
        numeric = adapter.numerical_checks(case, repo) if hasattr(adapter, 'numerical_checks') else {'status': 'NOT_IMPLEMENTED'}
        assert numeric.get('status') == 'PASS', (cid, numeric)
        dump(work / 'numerical_checks.json', numeric)
        dump(work / 'grouping_checks.json', grouping)
        dump(work / 'replay.json', replays[cid])
        resolved = {'execution_extension': 'step4-2.0.0', 'input_config_sha256': sha(own / 'configs/cases' / (cid + '.json')),
            'logical': case['logical'], 'physical': case['physical'], 'resources': case['resources'],
            'native_parameters_ns': p, 'backend': b, 'adapter': plan['snapshot'], 'source_provenance': case['provenance'],
            'schedule_policy': {'kind': 'strict_serial_ordered_templates_no_overlap',
                'edge_rule': 'physical subsequences continuous; align at explicit digital consumer or boundary',
                'steady_interval_proof': 'second full service from previous completion and expanded-template equivalence',
                'maintenance': 'separate raw request latency and long-term availability-adjusted service cost'}}
        dump(work / 'resolved.json', resolved)
        s = services['streaming']['latency_ns']; r = services['resident']['latency_ns']
        if case['logical']['resident_transaction_Byte'] == case['logical']['B_R_Byte']:
            transaction_events = plan['resident']
        else:
            transaction_events = plan.get('atomic_resident', plan['resident'][0]['steps'])
        txn = engine.run(transaction_events, b['actual_period_ns'])
        txn2 = engine.run(transaction_events, b['actual_period_ns'], start_ns=txn['end_ns'])
        assert engine.close(txn2['latency_ns'], txn['latency_ns'])
        transaction = txn['latency_ns']
        cmp = comparison(case, p, b, adapter, engine, replays[cid])
        result = {'contract_version': '3.0.0', 'case_id': cid, 'status': 'OK' if maintenance['feasible'] else 'FAILED',
            'mode': 'neurosim_native_hybrid_reference', 'execution_revision': 'step4-2.0.0',
            'identity': {'backend_sha': SHA, 'input_sha256': resolved['input_config_sha256'],
                         'patches': ['backend/constructor.patch'], 'driver_sha256': sha(__file__)},
            'effective_config': {'resolved_snapshot': 'resolved.json', 'resolved_sha256': sha(work / 'resolved.json')},
            'derived_snapshot': {'actual_period_ns': b['actual_period_ns'], 'module_returns': b['raw_module_returns'],
                                 'module_inventory': b['module_inventory'], 'coverage': b['coverage'],
                                 'partial_area_scope': b['partial_area_scope']},
            'clocks': [{'clock_id': 'lv_core', 'target_period_ns': 5.,
                'combinational_limit_ns': max(x['delay_ns'] for x in b['paths']),
                'timing_min_period_ns': b['timing_min_period_ns'], 'actual_period_ns': b['actual_period_ns'],
                'selection_policy': b['selection_policy'],
                'closure_status': b.get('closure_status', 'modeled_paths_only_with_explicit_native_and_arithmetic_budget_exclusions'),
                'constraining_paths': b['paths']}],
            'stages': [{**x, 'service_kind': name} for name, value in services.items() for x in value['stages']],
            'streaming': {'latency_ns': s, 'delta_S_ns': s, 'initiation_interval_ns': s,
                'effective_service_cost_ns': maintenance.get('effective_delta_S_ns', s),
                'latency_context': 'raw physical service without maintenance interruption; arrival-dependent maintenance waiting is not raw/availability',
                'proof': 'strict serial; two complete consecutive vectors; no overlap'},
            'resident_load': {'transaction_latency_ns': transaction, 'T_R_ns': r,
                'transaction_service_interval_ns': txn2['latency_ns'],
                'matrix_service_interval_ns': r, 'payload_Byte': case['logical']['B_R_Byte'],
                'transaction_payload_Byte': case['logical']['resident_transaction_Byte'],
                'effective_service_cost_ns': maintenance.get('effective_T_R_ns', r),
                'coverage_status': 'complete_hybrid_conditional_native_services',
                'normalized_missing_backend_write': {'value': None, 'status': 'NOT_IMPLEMENTED',
                    'reason': 'no compatible aggregate write model; complete native service plus explicit public control retained'}},
            'maintenance': maintenance, 'derived_metrics': metrics, 'comparison': cmp,
            'checks': plan['checks'], 'coverage': b['coverage']}
        schema_check(result, json.loads((own / 'contracts/output.schema.json').read_text()))
        old_result = json.loads((own / 'results/step4/reference-final-20261004' / cid / 'result.json').read_text())
        old_b = json.loads((own / 'results/step4/reference-final-20261004' / cid / 'resolved.json').read_text())['backend']
        old_adapter = module('v1_adapter_' + cid, own / 'step4/adapters' / ('nand.py' if cid == '04_nand_3d' else 'native.py'))
        old_engine = module('v1_engine_' + cid, own / 'step4/engine.py')
        old_plan = old_adapter.build(case, p, old_b)
        v1_services, v1_maintenance, _ = old_engine.evaluate(case, old_plan, old_b)
        assert engine.close(v1_services['streaming']['latency_ns'], old_result['streaming']['delta_S_ns'])
        assert engine.close(v1_services['resident']['latency_ns'], old_result['resident_load']['T_R_ns'])
        fixed_clock_b = copy.deepcopy(b); fixed_clock_b['actual_period_ns'] = old_b['actual_period_ns']
        v2_fixed, fixed_m, _ = engine.evaluate(case, adapter.build(case, p, fixed_clock_b), fixed_clock_b)
        comparison_v2 = {'status': 'PASS', 'ordering': 'first correct boundary semantics and maintenance framing at V1 clock, then qualify source lifecycle/select V2 clock',
                         'V1_recomputed_matches_archive': True, 'native_parameters_and_resources_unchanged': True,
                         'V1_period_ns': old_b['actual_period_ns'], 'V2_period_ns': b['actual_period_ns'], 'services': {}}
        for key in ('streaming', 'resident', 'maintenance'):
            a0=v1_services[key]['latency_ns']; a1=v2_fixed[key]['latency_ns']; a2=services[key]['latency_ns']
            comparison_v2['services'][key] = {'V1_ns': a0, 'V2_boundary_at_V1_clock_ns': a1, 'V2_ns': a2,
                'boundary_semantics_delta_ns': a1-a0, 'qualified_clock_and_edge_delta_ns': a2-a1, 'total_delta_ns': a2-a0}
        comparison_v2['availability'] = {'V1': v1_maintenance.get('availability', 1.),
                                        'V2_boundary_at_V1_clock': fixed_m['availability'], 'V2': maintenance['availability']}
        if maintenance['applicable']:
            comparison_v2['maintenance_frames_ns'] = {'native_retention_unchanged': maintenance['retention_limit_ns'],
                'V1_nominal_frame': v1_maintenance['period_ns'],
                'V2_legal_frame_at_V1_clock': fixed_m['scheduled_frame_period_ns'],
                'V2_legal_frame': maintenance['scheduled_frame_period_ns']}
        result['V1_comparison'] = comparison_v2
        dump(work / 'v1_v2_comparison.json', comparison_v2)
        dump(work / 'budget_sensitivity.json', budget_sensitivity(case, p, b, adapter, engine))
        dump(work / 'result.json', result)
        dump(work / 'sensitivity.json', diagnostics(case, p, b, adapter, engine, (services, maintenance, metrics)))
        print(json.dumps({'case_id': cid, 'status': 'PASS', 'period_ns': b['actual_period_ns'],
                          'delta_S_ns': s, 'T_R_ns': r, 'availability': maintenance['availability']}), flush=True)
    rows = []
    for cid in cases:
        result = json.loads((out / cid / 'result.json').read_text()); case = configs[cid]
        dump(out / cid / 'replay.json', replays[cid])
        sources = []
        for stage in result['stages']:
            raw = stage['raw_returns'][0]
            kind = ('digital' if stage['timing_kind'] == 'digital_step' else
                    'boundary' if raw['value'] == 0 and raw['unit'] == 'ns' else 'physical')
            sources.append({'stage_id': stage['stage_id'], 'service_kind': stage['service_kind'],
                'provider': stage['provider'], 'source_category': engine.source_category(stage['provider'], kind, stage['stage_id']),
                'operation_semantics': stage.get('operation_semantics', 'cycle' if kind == 'digital' else 'capture_or_included_native_boundary' if kind == 'boundary' else 'native_service'),
                'raw_service_total_ns': stage['resource_occupancy_ns']-stage['boundary_wait_ns'],
                'interface_edge_wait_ns': stage['boundary_wait_ns'],
                'timing_scope': 'schedule cycles under declared path qualification; retained arithmetic stays conditional' if kind == 'digital' else 'explicit interface edge' if kind == 'boundary' else 'provider service duration'})
        dump(out / cid / 'stage_sources.json', {'category_policy': 'classification by source and operation, never a stage-count coverage percentage', 'stages': sources})
        rows.append({'case_id': cid, 'K': case['logical']['K'], 'N': case['logical']['N'],
            'timing_min_period_ns': result['clocks'][0]['timing_min_period_ns'],
            'actual_period_ns': result['clocks'][0]['actual_period_ns'],
            'delta_S_ns': result['streaming']['delta_S_ns'], 'T_R_ns': result['resident_load']['T_R_ns'],
            'availability': result['maintenance'].get('availability', 1.),
            **{k: v for k, v in result['derived_metrics'].items() if k != 'status'},
            'v3_delta_S_ns': replays[cid]['raw_delta_S_ns'], 'v3_T_R_ns': replays[cid]['raw_T_R_ns'],
            'V1_delta_S_ns': json.loads((own / 'results/step4/reference-final-20261004' / cid / 'result.json').read_text())['streaming']['delta_S_ns'],
            'V1_T_R_ns': json.loads((own / 'results/step4/reference-final-20261004' / cid / 'result.json').read_text())['resident_load']['T_R_ns']})
    dump(out / 'summary.json', {'status': 'PASS', 'mode': 'ten_reference_typical_configurations',
        'case_results': rows, 'execution_extension': 'step4-2.0.0',
        'scope': 'public compatible modules plus retained native services; no macro PPA or analog precision certification',
        'rate_units': 'Byte/s; divide by 1e6 for decimal MB/s',
        'GC_policy': 'rho/tau/RI/U share maintenance-adjusted policy; delta_S/T_R retain raw physical service',
        'reproduction': 'new local source copies and executable; no cached build or prior result as input'})
    with (out / 'summary.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', default=os.environ.get('NEUROSIM_ROOT', str(Path.home() / 'neurosim')))
    ap.add_argument('--cxx', default=os.environ.get('NEUROSIM_CXX', 'g++-16'))
    ap.add_argument('--case', choices=['all', *CASES], default='all')
    ap.add_argument('--run-id', default='reference-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    ap.add_argument('--mode', choices=['reference', 'replay'], default='reference')
    ap.add_argument('--period-ns', type=float); ap.add_argument('--wire-um', type=float, default=10.)
    ap.add_argument('--export', action='store_true'); ap.add_argument('--no-export', action='store_true')
    ap.add_argument('--worker', help=argparse.SUPPRESS)
    a = ap.parse_args(); own = Path(__file__).resolve().parents[1]; repo = own.parents[1]
    root = Path(a.root).expanduser().resolve(); a.root = str(root)
    assert not any(x in str(root).lower() for x in ('onedrive', 'icloud', 'mobile documents'))
    assert Path(a.run_id).name == a.run_id and a.run_id not in ('.', '..')
    cases = CASES if a.case == 'all' else [a.case]
    if a.worker:
        worker(a, own, Path(a.worker), cases); return
    out = root / 'runs/step4-v2' / a.run_id; out.mkdir(parents=True, exist_ok=False)
    task = snapshot(own, out, cases)
    dump(out / 'invocation.json', {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
        'baseline': BASELINE, 'device_baseline': 'a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0',
        'status': subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True),
        'compiler': subprocess.check_output([a.cxx, '--version'], text=True).splitlines()[0],
        'python': sys.version, 'mode': a.mode, 'cases': cases, 'wire_um': a.wire_um,
        'requested_period_ns': a.period_ns, 'argv': sys.argv})
    argv = [sys.executable, '-B', str(task / 'scripts/run_step4_v2.py'), '--root', str(root), '--cxx', a.cxx,
            '--case', a.case, '--mode', a.mode, '--worker', str(out), '--wire-um', str(a.wire_um)]
    if a.period_ns is not None: argv += ['--period-ns', str(a.period_ns)]
    run = subprocess.run(argv, cwd=out, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / 'run.log').write_text(run.stdout); print(run.stdout, end='')
    if run.returncode: raise SystemExit(run.returncode)
    if a.export and not a.no_export:
        dest = own / 'results/step4_v2' / a.run_id; dest.mkdir(parents=True, exist_ok=False)
        whitelist = ['summary.json', 'snapshot_manifest.json', 'invocation.json', 'interface_checks.json']
        if a.mode != 'replay': whitelist += ['summary.csv', 'pilot_regression.json']
        for cid in cases:
            names = ['replay.json'] if a.mode == 'replay' else ['result.json', 'resolved.json', 'replay.json', 'sensitivity.json',
                'backend/source_manifest.json', 'backend/constructor.patch']
            names += [] if a.mode == 'replay' else (['timing_checks.json', 'operating_points.json'] if cid in PILOTS else ['numerical_checks.json', 'grouping_checks.json', 'timing_checks.json', 'v1_v2_comparison.json', 'budget_sensitivity.json'])
            if a.mode != 'replay': names += ['stage_sources.json']
            whitelist += [cid + '/' + name for name in names]
        for rel in whitelist:
            src = out / rel; assert src.stat().st_size < 2_000_000, rel
            target = dest / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, target)
        dump(dest.parent / 'latest.json', {'run_id': a.run_id, 'summary': str((dest / 'summary.json').relative_to(own)), 'status': 'PASS'})
    print(json.dumps({'status': 'PASS', 'run': str(out)}))


if __name__ == '__main__': main()

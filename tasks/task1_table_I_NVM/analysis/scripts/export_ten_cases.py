#!/usr/bin/env python3
"""Adapt native calculator results; no device timing model is implemented here.

The primary boundary is one complete vector and a complete resident matrix.
Local update transactions are retained separately.  --emit synchronizes existing
JSON/CSV, result cards, and the marked summary in TEN_CASE_REVIEW.zh.md.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path

A = Path(__file__).resolve().parents[1]
META = {
    '01_sram_acim': ('SRAM ACIM', 'scenarios'),
    '02_sram_dcim': ('SRAM DCIM', 'scenarios'),
    '03_nor_2d': ('2D NOR Flash', 'scenarios'),
    '04_nand_3d': ('3D NAND', 'main_scenarios'),
    '05_rram': ('RRAM', 'scenarios'),
    '06_mram': ('MRAM', 'scenarios'),
    '07_pcm': ('PCM', 'paired_scenarios'),
    '08_feram_hfo2': ('HfO₂ FeRAM', 'paired'),
    '09_gain_cell_edram': ('Gain-cell eDRAM', 'scenarios'),
    '10_fenor_3d': ('3D vertical AND FeFET (2026)', 'main_scenarios'),
}
CORE = ('B_S_Byte', 'B_R_Byte', 'delta_S_ns', 'delta_R_ns',
        'rho_Byte_per_s', 'tau_Byte_per_s', 'ridge')
PROFILES = ('short', 'reference', 'long')
MAIN_TYPES = ('recommended_reference', 'paired_conditional')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(path):
    return '#/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in path)


def walk(value, path=()):
    """Stop at the scenario, avoiding mapping/raw/effective/rewrite aliases."""
    if isinstance(value, dict):
        if 'mapping_interface' in value or all(k in value for k in CORE):
            yield path, value
            if 'append' in value:
                # Erase preparation changes the update window, never the stored
                # encoding, installed resources or numerical-service identity.
                inherited = {k: copy.deepcopy(value[k]) for k in (
                    'native_configuration', 'legacy_configuration', 'scenario_class',
                    'numerical_service_qualification', 'reference_service_status',
                    'workload_mapping_eligibility', 'eligibility_scope') if k in value}
                append = copy.deepcopy(value['append'])
                for key in inherited.keys() & append.keys():
                    assert inherited[key] == append[key], ('append changes encoding/service identity', key)
                append.update(inherited, profile=value['profile'])
                for key in ('native_configuration', 'legacy_configuration'):
                    if key in inherited:
                        append['_inherited_native_configuration_path'] = path + (key,)
                        break
                yield path + ('append',), append
            return
        for k, v in value.items():
            yield from walk(v, path + (str(k),))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, path + (str(i),))


def profile(row, path):
    for key in ('profile', 'common_profile', 'attempt_profile'):
        if row.get(key) in PROFILES:
            return row[key]
    for p in PROFILES:
        if p in row.get('id', '').split('_'):
            return p
    return None


def classify(path, row, main_key):
    if path[-1] == 'append':
        return 'finite_pre_erased_window'
    if path[0] == main_key:
        return 'recommended_reference' if profile(row, path) == 'reference' else 'paired_conditional'
    if 'infeasible' in row.get('feasibility', '') or 'infeasible' in path[0]:
        return 'pressure_infeasible'
    if 'pressure' in path[0] or 'stress' in path[0]:
        return 'pressure_near_refresh_saturation'
    declared = row.get('scenario_class')
    if declared is not None:
        declared = {
            'reference': 'reference_control',
            'fixed_resource_completion_condition_sensitivity': 'finite_retry_sensitivity',
            'same_mode_parameter_sensitivity': 'parameter_uncertainty',
        }.get(declared, declared)
        assert declared in {
            'operation_mode_comparison', 'parameter_uncertainty',
            'resource_comparison', 'maintenance_pressure',
            'finite_retry_sensitivity', 'reference_control',
            'restricted_encoding',
        }, ('unknown explicit scenario class', declared)
        return declared
    kind = row.get('kind', '') + row.get('scenario_type', '')
    if 'retry' in kind:
        return 'finite_retry_sensitivity'
    if 'schedule' in kind or row.get('schedule') == 'input_bit_then_groups':
        return 'schedule_comparison'
    if any(t in path[0] + kind for t in ('resource', 'organization', 'structur', 'capacity', 'compar', 'contrast')):
        return 'resource_or_organization_comparison'
    return 'independent_sensitivity'


def full_mapping(row, native, main=False):
    if 'mapping_interface' in row:
        return copy.deepcopy(row['mapping_interface'])
    if all(k in row for k in ('K', 'N', 'T_R_ns', 'U_star')):
        keys = CORE + ('K', 'N', 'b_S', 'b_R', 'full_resident_payload_Byte',
                       'RI_star', 'T_R_ns', 'U_star', 'average_update_ns_per_16KiB')
        return {k: row[k] for k in keys}
    assert not main, 'A primary scenario must expose the shared full-matrix mapping_interface'
    # Legacy *contrasts* with explicitly serial local transactions can be
    # aggregated without changing rates.  Main points never use this fallback.
    k, n, bs, br = (native[x] for x in ('K', 'N', 'b_S', 'b_R'))
    payload = k * n * br
    scale = payload / row['B_R_Byte']
    assert scale == int(scale), 'tail groups require a calculator-supplied full mapping'
    tr = None if row['delta_R_ns'] is None else row['delta_R_ns'] * scale
    ds = row['delta_S_ns']
    u = None if tr is None or ds is None else tr / ds
    return dict(B_S_Byte=k*bs, B_R_Byte=payload, delta_S_ns=ds, delta_R_ns=tr,
                rho_Byte_per_s=row['rho_Byte_per_s'], tau_Byte_per_s=row['tau_Byte_per_s'],
                ridge=row['ridge'], K=k, N=n, b_S=bs, b_R=br,
                full_resident_payload_Byte=payload, RI_star=row['ridge'], T_R_ns=tr,
                U_star=u, average_update_ns_per_16KiB=None if tr is None else tr*16384/payload,
                adapter_aggregation='serial identical local transactions; source payload exactly divides matrix')


def scenario_native(case_id, base, row, mapping, path):
    """Retain native data and apply only explicitly exposed comparison changes."""
    cfg = copy.deepcopy(row.get('native_configuration', row.get('legacy_configuration', base)))
    old_k, old_n = cfg['K'], cfg['N']
    cfg.update({k: mapping[k] for k in ('K', 'N', 'b_S', 'b_R')})
    cfg['effective_logical_capacity_Byte'] = mapping['full_resident_payload_Byte']
    for k in ('effective_capacity_Byte', 'resident_capacity_Byte', 'logical_capacity_Byte'):
        if k in cfg:
            cfg[k] = mapping['full_resident_payload_Byte']
    res = cfg['resources']
    if case_id == '01_sram_acim' and 'parallel_write_cells' in row:
        res['write_drivers'] = row['parallel_write_cells']
        cfg['update_mode'] = f"aligned 16 Byte update; {row['parallel_write_cells']} active binary write drivers; {row['write_batches']} complete write cycles per local transaction"
    if case_id == '02_sram_dcim' and (old_k, old_n) != (cfg['K'], cfg['N']):
        tiles = cfg['N'] // base['N']
        cfg['physical_capacity']['binary_cells'] *= tiles
        cfg['physical_capacity']['tiles'] = tiles
        res['installed_HCA_BFA'] = row['installed_output_lanes']
        res['active_HCA_BFA'] = row['active_output_lanes']
        res['output_register_bits'] = cfg['N'] * cfg['output_bits']
        cfg['configuration_kind'] = row['premise']
        cfg['update_mode'] = f"aligned 16 Byte ordinary writes; {mapping['B_R_Byte']/16:g} transactions cover all installed tiles"
    if case_id == '03_nor_2d':
        local = row['mapping']
        cfg['physical_capacity_Byte'] = local['allocated_physical_Byte']
        cfg['physical_storage_bits'] = local['allocated_physical_Byte'] * 8
        cfg['physical_binary_storage_sites'] = cfg['physical_storage_bits']
        cfg['physical_organization'] = f"{local['read_slices']} read slices; {local['read_slices_per_sector']} slices per sector; {local['sector_erases']} allocated sectors"
        cfg['update_shape'] = f"whole-matrix sustained overwrite: {local['sector_erases']} sector erases and {local['page_programs']} full page programs"
    if path[-1] == 'append':
        cfg['update_mode'] = row['precondition']
        cfg['update_classification'] = row['classification']
    if case_id == '05_rram':
        wr = row['write_details']
        res['write_driver_count'] = wr['parallel_cells']
        res['binary_window_comparators'] = wr['binary_comparators']
        res['total_program_current_rating_mA'] = wr['peak_array_current_budget_mA']
    if case_id == '07_pcm':
        for source, target in [('writeheads', 'IDAC_count'), ('active_rows', 'active_input_rows')]:
            if source in row:
                res[target] = row[source]
        if 'verify_mode' in row:
            res['verify_mode'] = row['verify_mode']
    if case_id == '08_feram_hfo2':
        cfg['read_schedule'] = row['schedule']
    if case_id == '09_gain_cell_edram':
        res.update(differential_ADC=row['adc_count'], write_pair_drivers=row['pair_write_drivers'],
                   write_branches=2*row['pair_write_drivers'], refresh_sign_decoders=row['refresh']['sign_decode_lanes'],
                   refresh_code_hold_bits=row['pair_write_drivers'], ADC_per_weight_plane=row['adc_count']//8,
                   analog_integration_total_pF=2*row['adc_count']*res['analog_integration_fF_per_branch']/1000)
        cells = row['physical_cells']
        cfg['physical_capacity'].update(gain_cells=cells, pseudodifferential_pairs=cells//2, tiles=cells//(64*64*2))
        cfg['output_bits'] = 16 + math.ceil(math.log2(cfg['K']))
        res['input_register_bits'] = cfg['K'] * 8
        res['output_register_bits'] = cfg['N'] * cfg['output_bits']
        cfg['update_mode'] = f"{row['B_R_Byte']:g} aligned INT8 Bytes per transaction; {row['full_matrix_update']['transactions']} transactions complete matrix"
        cfg['compute_release_policy'] = row['release_policy']
        if (old_k, old_n) != (cfg['K'], cfg['N']):
            cfg['native_rationale'] = 'capacity comparison with additional physical tiles; source dimensions and cell count retained'
    if case_id == '10_fenor_3d':
        count = row['resident_counts']
        res.update(parallel_write_cells=count['cells_per_batch'], parallel_write_strips=count['strips_per_batch'],
                   driven_bias_nodes=count['driven_nodes'], installed_supply_current_mA=count['installed_supply_current_mA'])
    return cfg


def dominant(row):
    names = ('streaming_dominant', 'resident_dominant', 'dominant_read_stage', 'dominant_write_stage',
             'dominant_streaming', 'dominant_resident', 'stream_dominant', 'dominant_read', 'dominant_write', 'dominant')
    return '; '.join(str(row[k]) for k in names if k in row)


def compact_resources(res):
    groups = [
        ('ADC', ('adc', 'adc_count', 'ADC_count', 'differential_ADC')),
        ('感测节点', ('binary_sense_nodes', 'sense_amplifiers', 'active_differential_digitizers')),
        ('读码保持/bit', ('operand_hold_bits', 'weight_tile_register_bits')),
        ('数字输出通道', ('digital_lanes', 'digital_output_lanes', 'digital_output_channels')),
        ('写驱动', ('write_drivers', 'write_driver_count', 'write_driver_lanes', 'external_target_BL_drivers', 'parallel_write_cells', 'write_pair_drivers', 'IDAC_count', 'IDACs', 'writeheads')),
        ('更新域', ('write_domains', 'external_update_domains')),
        ('页缓冲/bit', ('page_buffer_bits',)),
    ]
    parts = []
    for label, names in groups:
        val = next((res[k] for k in names if k in res), None)
        if val is not None:
            parts.append(f'{label}={val}')
    return '；'.join(parts)


def validate_mapping(m):
    assert m['B_S_Byte'] == m['K'] * m['b_S']
    assert m['B_R_Byte'] == m['K'] * m['N'] * m['b_R'] == m['full_resident_payload_Byte']
    if m['rho_Byte_per_s'] is None:
        assert all(m[k] is None for k in ('tau_Byte_per_s', 'ridge', 'delta_S_ns', 'T_R_ns', 'U_star'))
        return
    assert m['delta_R_ns'] == m['T_R_ns']
    expected = (m['B_S_Byte']/m['delta_S_ns']*1e9, m['B_R_Byte']/m['T_R_ns']*1e9,
                m['rho_Byte_per_s']/m['tau_Byte_per_s'], m['T_R_ns']/m['delta_S_ns'],
                m['N']*m['b_R']/m['b_S']*m['RI_star'])
    observed = (m['rho_Byte_per_s'], m['tau_Byte_per_s'], m['ridge'], m['U_star'], m['U_star'])
    assert all(math.isclose(x, y, rel_tol=1e-11) for x, y in zip(expected, observed)), (expected, observed)


def service_qualification(case, data, inputs, row, typ, diagnostic):
    """Structural mapping eligibility is distinct from an accuracy guarantee."""
    q = copy.deepcopy(data.get('numerical_service_qualification', inputs.get('numerical_service_qualification', {})))
    q.update(copy.deepcopy(row.get('numerical_service_qualification', {})))
    restricted = typ == 'restricted_encoding' or row.get('scenario_class') == 'restricted_encoding'
    if restricted:
        q = copy.deepcopy(data.get('legacy_offset_comparison', {}).get('qualification', {}))
    for key in ('reference_service_status', 'workload_mapping_eligibility', 'eligibility_scope'):
        if key in row:
            q[key] = row[key]
    eligible = q.get('workload_mapping_eligibility', True)
    if isinstance(eligible, dict):
        eligible = eligible['signed_INT8_structural_mapping']
    assert isinstance(eligible, bool)
    if restricted:
        assert eligible is False, 'restricted encoding cannot enter general signed-workload mapping'
    q['reference_service_status'] = q.get('reference_service_status', 'approximate_signed_reference' if diagnostic else 'declared_reference')
    q['workload_mapping_eligibility'] = eligible
    q['eligibility_scope'] = q.get('eligibility_scope',
        'structural_signed_INT8_approximate_mapping_requires_application_error_contract' if diagnostic else 'declared_logical_service_and_precision_contract')
    q['universal_workload_accuracy_certified'] = False
    if q.get('diagnostic_path'):
        q['diagnostic_path'] = str(Path(case, q['diagnostic_path']))
    if diagnostic:
        q.update(nominal_diagnostic_level=diagnostic['model']['level'],
                 quantization_induced_bias_assessed=diagnostic['quantization_induced_bias_assessed'],
                 physical_ADC_chain_status=diagnostic['physical_ADC_chain_status'],
                 common_diagnostic_path='shared_baseline/data/nominal_service_diagnostics.json',
                 common_diagnostic_section='restricted_offset_encoding_comparison' if restricted else 'cases',
                 nominal_diagnostic_vectors=diagnostic['diagnostic_vectors'])
    return q


def normalized():
    allrows, cases = [], []
    diagnostics = json.loads((A/'shared_baseline/data/nominal_service_diagnostics.json').read_text())
    assert all(sha(A/path) == expected for path, expected in diagnostics['source_sha256'].items()), 'stale common nominal diagnostics'
    diagnostic_by_case = {d['case_id']: d for d in diagnostics['cases']}
    for c, (technology, main_key) in META.items():
        directory = A/c
        source_bytes = {name: (directory/f'data/{name}.json').read_bytes() for name in ('inputs', 'results')}
        data = json.loads(source_bytes['results'])
        native = data['native_configuration']
        inputs = source_bytes['inputs'].decode('utf-8')
        input_data = json.loads(inputs)
        source_ids = sorted(set(re.findall(r'(?:SACIM|SDCIM|CMOS|NOR|NAND|RRAM|MRAM|PCM|FERAM|GC|FENOR)-\d{2}', inputs)))
        source_hashes = {f'{c}/data/{name}.json': hashlib.sha256(content).hexdigest() for name, content in source_bytes.items()}
        rows = []
        for path, row in walk(data):
            if path[0] != main_key and not any(t in path[0] for t in ('sensitiv', 'compar', 'contrast', 'pressure', 'stress')):
                continue
            typ = classify(path, row, main_key)
            qualification = service_qualification(c, data, input_data, row, typ, diagnostic_by_case.get(c))
            m = full_mapping(row, native, typ in MAIN_TYPES)
            cfg = scenario_native(c, native, row, m, path)
            maint = row.get('maintenance_service', {})
            raw = row.get('raw_mapping_interface', maint.get('raw', m))
            effective = row.get('effective_mapping_interface', maint.get('effective', m))
            for interface in (m, raw, effective):
                validate_mapping(interface)
            assert all(m[k] == effective[k] for k in CORE), 'main mapping and effective boundary disagree'
            periodic = row.get('refresh')
            maintenance = periodic or row.get('maintenance') or dict(periodic=False, availability=1,
                included_in_raw='required local recovery/restore/verify is included in source service stages')
            update = cfg.get('update_shape', cfg.get('update_mode', row.get('transaction_pattern', '')))
            mode = row.get('mode', cfg.get('mode', data.get('mode', cfg.get('configuration_kind', technology))))
            local = {k: row[k] for k in CORE if k in row} if all(k in row for k in CORE) else None
            if 'block_service' in row:
                local = dict(row['block_service'], relationship='native block batch; whole-matrix final overhead is retained separately in full_load')
            full_load = copy.deepcopy(row.get('full_load', row.get('write_details', {}).get('full_load', row.get('full_matrix_update', {}))))
            full_load.update(logical_payload_Byte=m['B_R_Byte'], T_R_ns=m['T_R_ns'])
            if c == '05_rram':
                local = dict(B_R_Byte=row['write_details']['local_transaction_Byte'],
                             delta_R_ns=row['write_details']['local_transaction_ns'],
                             isolated_request_ns=row['write_details']['isolated_16B_request_ns'],
                             relationship='matrix T_R includes epoch rail setup/exit; local batch rate is not the main tau')
            sid = row.get('id', '/'.join(path))
            if path[-1] == 'append':
                sid = f"{row['profile']}_append"
                mode = str(mode) + '; finite pre-erased append window'
            skip = set(CORE) | {'mapping_interface', 'raw_mapping_interface', 'effective_mapping_interface',
                               'maintenance_service', 'nominal', 'refresh', 'rewrite', 'append', 'native_configuration',
                               '_inherited_native_configuration_path'}
            parameters = {k: v for k, v in row.items() if k not in skip}
            parameters['profile'] = profile(row, path)
            result = dict(case_id=c, technology=technology, mode=mode, scenario_id=sid, scenario_profile=profile(row, path),
                scenario_type=typ, recommended=typ == 'recommended_reference', rate_unit='MB/s', payload_unit='Byte',
                K=m['K'], N=m['N'], b_S=m['b_S'], b_R=m['b_R'], B_S=m['B_S_Byte'], B_R=m['B_R_Byte'],
                effective_logical_capacity_Byte=m['full_resident_payload_Byte'], native_configuration=cfg,
                update_pattern=update, transaction_service=local,
                full_load=full_load,
                raw_service_time=dict(streaming_ns=raw['delta_S_ns'], resident_ns=raw['T_R_ns']),
                effective_service_interval=dict(streaming_ns=effective['delta_S_ns'], resident_ns=effective['T_R_ns']),
                mapping_interface=m, raw_mapping_interface=raw, effective_mapping_interface=effective,
                rho=None if m['rho_Byte_per_s'] is None else m['rho_Byte_per_s']/1e6,
                tau=None if m['tau_Byte_per_s'] is None else m['tau_Byte_per_s']/1e6,
                RI_star=m['RI_star'], U_star=m['U_star'], T_R_ns=m['T_R_ns'], delta_S_ns=m['delta_S_ns'],
                rho_raw=raw['rho_Byte_per_s']/1e6, tau_raw=raw['tau_Byte_per_s']/1e6,
                maintenance=maintenance, raw_equals_effective=raw == effective,
                feasibility='conditional_feasible' if m['rho_Byte_per_s'] is not None else 'infeasible_under_declared_schedule',
                main_assumptions=dominant(row), key_resources=cfg['resources'], source_ids=source_ids,
                numerical_service_qualification=qualification,
                reference_service_status=qualification['reference_service_status'],
                workload_mapping_eligibility=qualification['workload_mapping_eligibility'],
                mapping_eligibility_scope=qualification['eligibility_scope'],
                nominal_diagnostic_level=qualification.get('nominal_diagnostic_level'),
                shared_baseline_id='shared_baseline', source_result=f'{c}/data/results.json'+pointer(path),
                source_mapping=f'{c}/data/results.json'+pointer(path+('mapping_interface',)) if 'mapping_interface' in row else None,
                source_native_configuration=f'{c}/data/results.json'+pointer(row['_inherited_native_configuration_path']) if '_inherited_native_configuration_path' in row else
                    f'{c}/data/results.json'+pointer(path+('native_configuration',)) if 'native_configuration' in row else
                    f'{c}/data/results.json'+pointer(path+('legacy_configuration',)) if 'legacy_configuration' in row else f'{c}/data/results.json#/native_configuration',
                source_hashes=source_hashes, scenario_parameters=parameters)
            rows.append(result)
        primary = [r for r in rows if r['scenario_type'] in MAIN_TYPES]
        assert len(primary) == 3 and {r['scenario_profile'] for r in primary} == set(PROFILES), c
        assert all(r['feasibility'] == 'conditional_feasible' for r in primary), c
        assert all((r['K'], r['N'], r['key_resources']) == (primary[0]['K'], primary[0]['N'], primary[0]['key_resources']) for r in primary), 'paired scenarios change resources: '+c
        ref = next(r for r in primary if r['recommended'])
        cases.append(dict(case_id=c, technology=technology, mode=ref['mode'], native_configuration=ref['native_configuration'],
            update_pattern=ref['update_pattern'], resources=ref['key_resources'], main_assumptions=ref['main_assumptions'],
            maintenance=ref['maintenance'], source_ids=source_ids, source_hashes=source_hashes,
            service_modes=input_data.get('service_modes', {}),
            numerical_service_qualification=ref['numerical_service_qualification'],
            reference_service_status=ref['reference_service_status'],
            workload_mapping_eligibility=ref['workload_mapping_eligibility'],
            nominal_diagnostic_level=ref['nominal_diagnostic_level'],
            evidence_entries=sorted(str(p.relative_to(A)) for p in (directory/'notes').glob('*.md')),
            shared_baseline_id='shared_baseline', reference_scenario_id=ref['scenario_id'],
            conditional_paired_range={k: [min(r[k] for r in primary), max(r[k] for r in primary)] for k in ('rho', 'tau', 'RI_star')},
            range_semantics='three paired sustainable conditions in the same native organization; finite scenarios, not probability or confidence bounds'))
        allrows.extend(rows)
    return dict(schema_version='ten-case-native-3', units=dict(payload='Byte', time='ns', rho_tau='decimal MB/s (10^6 Byte/s)', RI_star='dimensionless'),
                service_boundary='one complete logical vector and one full native resident matrix; local transactions are separate',
                mapping_eligibility_meaning='Structural support for the declared logical encoding/service only. Approximate ACIM still requires an application error contract; no universal workload accuracy certification.',
                nominal_diagnostic_sha256=sha(A/'shared_baseline/data/nominal_service_diagnostics.json'),
                shared_baseline_id='shared_baseline', shared_parameter_sha256=sha(A/'shared_baseline/data/shared_parameters.json'),
                shared_api_sha256=sha(A/'shared_baseline/scripts/check_shared.py'), cases=cases, results=allrows)


def tex(s):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#',
                    '$': r'\$', '{': r'\{', '}': r'\}', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    text = ''.join(replacements.get(ch, ch) for ch in str(s))
    for symbol, math in [('μ', r'\mu'), ('Δ', r'\Delta'), ('ρ', r'\rho'), ('τ', r'\tau')]:
        text = text.replace(symbol, '$'+math+'$')
    return text.replace('HfO₂', r'HfO$_2$')


def f(value):
    return '不可行' if value is None else f'{value:.2g}'


def integer_or_decimal(value):
    return str(int(value)) if value == int(value) else str(value)


def math_number(value):
    value = f(value)
    if 'e' in value:
        mantissa, exponent = value.split('e')
        return mantissa + r'\times10^{' + str(int(exponent)) + '}'
    return value


def card_update(ref):
    """Render source-native transaction shapes as a compact Chinese sentence."""
    c, cfg, params = ref['case_id'], ref['native_configuration'], ref['scenario_parameters']
    local = ref['transaction_service'] or {}
    if c == '03_nor_2d':
        counts = params['operation_counts']
        return f"整矩阵持续重写；{counts['sector_erases']} 次 sector 擦除和 {counts['page_programs']} 次完整 page 编程。"
    if c == '04_nand_3d':
        pages = cfg['blocks'] * cfg['wordlines_per_block'] * cfg['SSL_per_block']
        return f"整矩阵持续替换；{cfg['blocks']} 次 block 擦除、{pages} 次 page 编程；包含正负幅值编码、单输出暂存、参考状态与校准。"
    payload = local['B_R_Byte']
    groups = ref['B_R'] / payload
    assert groups == int(groups)
    shape = '对齐局部组'
    if c == '07_pcm':
        shape = '同一选中行内的列条带'
    elif c == '08_feram_hfo2':
        shape = '完整局部物理行'
    elif c == '06_mram':
        shape = '互补 bit 对的对齐输出组'
    text = f"每个{shape} {payload:g} Byte；{groups:g} 个完整事务覆盖矩阵。"
    if c == '05_rram':
        text += ' 两相 RESET/SET 写验；整矩阵服务另含电压轨建立与退出。'
    return text


def card(case, rows):
    ref = next(r for r in rows if r['recommended'])
    primary = sorted((r for r in rows if r['scenario_type'] in MAIN_TYPES), key=lambda r: PROFILES.index(r['scenario_profile']))
    n = ref['native_configuration']
    shape = f"W[N,K]={ref['N']:g}×{ref['K']:g}；INT8输入与权重；有效 resident={integer_or_decimal(ref['B_R'])} Byte。"
    resource_text = compact_resources(ref['key_resources'])
    rows_text = [('原生逻辑配置', shape), ('更新组织', card_update(ref)), ('主要资源', resource_text)]
    q = ref['numerical_service_qualification']
    if not ref['workload_mapping_eligibility']:
        rows_text.append(('数值服务身份', '受限编码示例；不进入通用 signed-INT8 workload 映射。'))
    elif ref['nominal_diagnostic_level']:
        level = ('已声明理想模拟链、名义ADC与有限重构' if q['quantization_induced_bias_assessed'] else '标定后理想部分和与数字重构；物理ADC量化未实例化')
        rows_text.append(('数值检查层级', level+'。结构映射资格不构成应用准确度认证。'))
    if ref['case_id'] == '04_nand_3d':
        r = ref['key_resources']
        rows_text.append(('编码与保持', f"正负幅值分块，每次{n['parallel_output_lanes']}输出；单输出暂存{r['resident_row_staging_bits']}bit；数据页{r['data_page_effective_encoded_bits_per_tick']}bit/拍，参考页{r['reference_page_effective_encoded_bits_per_tick']}bit/拍。"))
    if ref['case_id'] == '09_gain_cell_edram':
        rows_text.append(('典型控制策略', '按模式释放：MAC脉冲后进入采样/转换；单pair刷新保持64ns积分，共同建立、恢复与维护完整计入。'))
    lines = [r'% Generated by analysis/scripts/export_ten_cases.py', r'\subsection*{统一结果卡}',
             r'\begingroup\small', r'\noindent\begin{tabularx}{\textwidth}{@{}p{24mm}X@{}}\toprule']
    lines += [tex(k) + ' & ' + tex(v) + r'\\' for k, v in rows_text]
    lines += [r'\bottomrule\end{tabularx}', r'\vspace{3mm}',
              r'\begin{center}\begin{tabular}{@{}lrrr@{}}\toprule',
              r'固定组织成对情景 & $\rho$ (MB/s) & $\tau$ (MB/s) & $\mathrm{RI}^{*}$\\\midrule']
    for r in primary:
        label = {'short': '乐观', 'reference': '典型', 'long': '悲观'}[r['scenario_profile']]
        lines.append(label + ' & ' + ' & '.join('$'+math_number(r[k])+'$' for k in ('rho', 'tau', 'RI_star')) + r'\\')
    lines += [r'\bottomrule\end{tabular}\end{center}',
              r'\noindent 典型完整求值：$B_S=' + f"{ref['B_S']:g}" + r'$ Byte，$\Delta_S=' + math_number(ref['delta_S_ns']) + r'$ ns。完整 resident 装载：$B_R=' + integer_or_decimal(ref['B_R']) + r'$ Byte，$T_R=' + math_number(ref['T_R_ns']) + r'$ ns；$U^*=' + math_number(ref['U_star']) + r'$ 个向量。',
              r'\par\smallskip\noindent 接口：$U^*=T_R/\Delta_S=N\,\mathrm{RI}^*$（两侧均为 1 Byte）。局部更新事务与完整装载关系见正文；该平衡关系不保证两路峰值能同时实现。']
    if not ref['raw_equals_effective']:
        maint = ref['maintenance']
        lines.append(r'\par\smallskip\noindent ' + tex(f"维护前ρ/τ={f(ref['rho_raw'])}/{f(ref['tau_raw'])} MB/s；刷新周期={f(maint['period_ns']/1000)} μs，可用比例={f(maint['availability'])}。表内为长期有效能力，维护不增加逻辑 payload。"))
    else:
        lines.append(r'\par\smallskip\noindent ' + tex('原始能力与长期有效能力在所声明服务窗口内相同；必要局部恢复、终验或擦除已纳入完整服务。'))
    lines += [r'\par\smallskip\noindent ' + tex('三点对应所选原生参考配置的有限工程条件，不代表等面积或等计算量排名。资源扩展、预擦除有限窗口和维护压力另列。1 MB=10^6 Byte；16 KiB辅助换算仅为平均成本。'),
              r'\endgroup', r'\clearpage']
    return '\n'.join(lines) + '\n'


def outputs(document):
    out = {'data/ten_case_results.json': json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n'}
    columns = list(document['results'][0])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    for row in document['results']:
        writer.writerow({k: json.dumps(row[k], ensure_ascii=False, separators=(',', ':')) if isinstance(row[k], (dict, list)) else row[k] for k in columns})
    out['data/ten_case_results.csv'] = buffer.getvalue()
    summary = ['<!-- Generated by scripts/export_ten_cases.py; decimal MB/s. -->',
               '| 案例（PDF） | 原生逻辑 K×N | 典型ρ | 典型τ | 典型RI* | U* |',
               '|---|---:|---:|---:|---:|---:|---:|']
    ranges = ['', '| 案例 | 条件ρ范围 | 条件τ范围 | 成对RI*范围 |', '|---|---:|---:|---:|']
    for case in document['cases']:
        c = case['case_id']
        rows = [r for r in document['results'] if r['case_id'] == c]
        ref = next(r for r in rows if r['recommended'])
        pdf = c+'/output/'+('pdf/rram' if c == '05_rram' else c[3:])+'.pdf'
        summary.append('| ['+case['technology']+']('+pdf+f") | {ref['K']:g}×{ref['N']:g} | "+' | '.join(f(ref[k]) for k in ('rho', 'tau', 'RI_star', 'U_star'))+' |')
        ranges.append('| '+case['technology']+' | '+' | '.join('–'.join(f(v) for v in case['conditional_paired_range'][k]) for k in ('rho', 'tau', 'RI_star'))+' |')
        out[c+'/tex/result_card.tex'] = card(case, rows)
    review = A/'TEN_CASE_REVIEW.zh.md'
    if review.exists():
        before, rest = review.read_text().split('<!-- BEGIN TEN CASE SUMMARY -->', 1)
        _, after = rest.split('<!-- END TEN CASE SUMMARY -->', 1)
        out['TEN_CASE_REVIEW.zh.md'] = before+'<!-- BEGIN TEN CASE SUMMARY -->\n'+'\n'.join(summary+ranges)+'\n<!-- END TEN CASE SUMMARY -->'+after
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--emit', action='store_true')
    args = parser.parse_args()
    document = normalized()
    for name, text in outputs(document).items():
        path = A/name
        if args.emit:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_text() != text:
                path.write_text(text)
        else:
            assert path.read_text() == text, f'stale {name}'
    print(f"PASS: {len(document['cases'])} native cases, {len(document['results'])} scenarios; full-matrix payload/time interfaces and synchronized cards/exports.")

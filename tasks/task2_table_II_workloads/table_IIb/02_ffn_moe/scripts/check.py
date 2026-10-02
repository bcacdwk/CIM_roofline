#!/usr/bin/env python3
"""Independent raw-dimension and identity checks; does not import the generator."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT.parents[1]
COMMON = ROOT.parent / '04_crosscheck'


def read(path):
    return json.loads(path.read_text())


def packed(n, d):
    f = Fraction(n, d)
    return f.numerator if f.denominator == 1 else {'numerator': f.numerator, 'denominator': f.denominator}


def assert_keys(obj, keys):
    assert set(obj) == set(keys), (set(obj), set(keys))


def no_float(obj):
    assert not isinstance(obj, float), obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert key not in ('ports', 'tile_layout', 'tile_evaluations', 'allocated_tile_bytes'), key
            no_float(value)
    elif isinstance(obj, list):
        for value in obj:
            no_float(value)


def raw_dimensions(model, native):
    raw = read(TASK / native['local_material']['raw_config'])
    text = raw.get('text_config', raw)
    D = text['hidden_size']
    dense = native['id'] in ('qwen35_2b', 'ministral3_8b_2512')
    F = text['intermediate_size' if dense else 'moe_intermediate_size']
    layer = model['selected_layer']
    assert 0 <= layer < text['num_hidden_layers']
    if 'first_k_dense_replace' in text:
        assert layer >= text['first_k_dense_replace']
    if 'moe_layer_freq' in text:
        assert text['moe_layer_freq'][layer] == 1
    if native['id'] == 'qwen36_35b_a3b':
        assert text['num_experts'] > 0 and 'moe_intermediate_size' in text
    assert model['parameters'] == {'D': D, 'F': F}
    assert model['model_revision'] == native['identity']['revision']
    assert layer == native['ffn']['selected_layer_index_zero_based']
    impl_path = native['local_material']['implementation']
    impl = (TASK / impl_path).read_text()
    # Check the literal logical construction without importing third-party code.
    if native['id'] in ('qwen36_35b_a3b', 'hy3_295b'):
        assert '2 * self.intermediate_dim, self.hidden_dim' in impl
        assert 'self.hidden_dim, self.intermediate_dim' in impl
        assert '.chunk(2, dim=-1)' in impl
        assert 'self.act_fn(gate) * up' in impl
    else:
        for expr in ['self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)',
                     'self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)',
                     'self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)']:
            assert expr in impl
    assert native['ffn']['matrices'] == {'gate': [F, D], 'up': [F, D], 'down': [D, F]}
    return D, F


def independent_case(c, D, F):
    U = c['U']
    # Identity pairs for one vector: each (stage source, element) belongs to one input.
    # Vector index is then accumulated over the actual U rows. gate/up have identical
    # x identities; down has distinct z identities even when D equals F.
    gate = {('x', k) for k in range(D)}
    up = {('x', k) for k in range(D)}
    down = {('z', k) for k in range(F)}
    input_union = gate | up | down
    shared = gate & up
    qs = sum(len(input_union) for _ in range(U))
    overlap = sum(len(shared) for _ in range(U))
    components = []
    for role, rows, cols, identities in [('gate', F, D, gate), ('up', F, D, up), ('down', D, F, down)]:
        # Each named matrix row contains `cols` unique weight elements, written once.
        written = sum(cols for _ in range(rows))
        read_bytes = sum(len(identities) for _ in range(U))
        components.append({'id': role, 'shape_N_K': [rows, cols], 'state_copies': 1,
                           'input_role': 'z' if role == 'down' else 'x',
                           'Q_S': read_bytes, 'Q_R': written, 'RI': packed(read_bytes, written),
                           'resident_bytes_initial': 0, 'resident_bytes_final': written})
    qr = sum(part['Q_R'] for part in components)
    expected = {'Q_S': qs, 'Q_R': qr, 'RI': packed(qs, qr),
                'resident_bytes_initial': 0, 'resident_bytes_final': qr,
                'shared_input_bytes_removed': overlap}
    assert c['components'] == components, c['case_id']
    assert c['result'] == expected, c['case_id']
    assert sum(part['Q_S'] for part in components) - overlap == qs
    return {'case_id': c['case_id'], 'status': 'PASS', 'row_and_input_identity_result': expected,
            'component_results': components}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--emit', action='store_true')
    args = parser.parse_args()
    cv = read(COMMON / 'data/conventions.json')
    config = read(ROOT / 'data/config.json')
    results = read(ROOT / 'data/results.json')
    native = {m['id']: m for m in read(TASK / 'data/models.json')['models']}
    supplied = {m['model_id']: m for m in read(COMMON / 'data/model_inputs.json')['models']}
    assert_keys(config, cv['config_root_keys'])
    assert_keys(results, cv['results_root_keys'])
    no_float(config)
    no_float(results)
    assert config['model_order'] == results['model_order'] == cv['model_order']
    assert [m['model_id'] for m in config['models']] == cv['model_order']
    assert config['reference_id'] == results['reference_id'] == cv['reference_id']
    assert config['boundary'] == results['boundary'] == 'operator_stage'
    assert config['element_bytes'] == 1
    assert config['sweeps'] == {'ffn_or_moe': {'U': [1, 16, 128, 1024, 16384]}}
    assert results['workload_ids'] == ['ffn_or_moe']
    assert_keys(config['window_rules']['ffn_or_moe'], cv['window_keys'])
    dims = {}
    for m in config['models']:
        assert_keys(m, cv['config_model_keys'])
        dims[m['model_id']] = raw_dimensions(m, native[m['model_id']])
        assert m['selected_layer'] == supplied[m['model_id']]['selected_layer']
        assert m['model_revision'] == supplied[m['model_id']]['model_revision']
    expected_ids = [f'{mid}/ffn_or_moe/{U}' for mid in cv['model_order'] for U in (1, 16, 128, 1024, 16384)]
    assert [c['case_id'] for c in results['cases']] == expected_ids
    independent = []
    legacy = {c['case_id']: c for c in read(TASK / '../archived/task2_table_IIb_previous/02_ffn_moe/data/results.json')['cases']}
    migration = []
    for c in results['cases']:
        assert_keys(c, cv['case_keys'])
        assert_keys(c['result'], cv['demand_keys'] + cv['result_additional_keys'])
        assert_keys(c['window'], cv['window_keys'])
        assert c['window'] == config['window_rules']['ffn_or_moe']
        assert all(isinstance(v, str) for v in c['window'].values())
        assert c['workload'] == 'ffn_or_moe' and c['kind'] == 'finite' and c['L'] is None
        assert [p['id'] for p in c['components']] == ['gate', 'up', 'down']
        for p in c['components']:
            assert_keys(p, cv['component_keys'])
        n = native[c['model_id']]
        assert c['selected_layer'] == n['ffn']['selected_layer_index_zero_based']
        assert c['model_revision'] == n['identity']['revision']
        D, F = dims[c['model_id']]
        assert c['parameters'] == {'D': D, 'F': F}
        independent.append(independent_case(c, D, F))
        old = legacy[f"{c['model_id']}/ffn_or_moe/8"]
        scale = Fraction(c['U'], 8)
        def scaled(value, key):
            f = Fraction(value['numerator'], value['denominator']) if isinstance(value, dict) else Fraction(value)
            if key in ('Q_S', 'RI', 'shared_input_bytes_removed'): f *= scale
            return packed(f.numerator, f.denominator)
        assert c['model_revision'] == old['model_revision'] and c['selected_layer'] == old['selected_layer']
        for k in ('Q_S', 'Q_R', 'RI'):
            assert c['result'][k] == scaled(old['result']['operator'][k], k)
        assert c['result']['resident_bytes_final'] == old['result']['capacity']['valid_resident_bytes']
        assert c['result']['shared_input_bytes_removed'] == scaled(old['result']['operator_shared_input_overlap_removed'], 'shared_input_bytes_removed')
        for part in c['components']:
            op = old['result']['parts'][part['id']]
            for k in ('Q_S', 'Q_R', 'RI'):
                assert part[k] == scaled(op['operator'][k], k)
            assert part['resident_bytes_final'] == op['layout']['valid_resident_bytes']
        migration.append({'case_id': c['case_id'], 'prior_case_id': old['case_id'], 'status': 'PASS',
                          'input_and_RI_scale': packed(scale.numerator, scale.denominator),
                          'reason': 'user changed reuse sweep; same one-load window, counts scale with U; weights unchanged'})
    source_checks = []
    source_registry = {s['local_path']: s for s in read(TASK / 'data/sources.json')}
    for s in config['sources']:
        assert_keys(s, ['path', 'sha256', 'locator'])
        digest = hashlib.sha256((TASK / s['path']).read_bytes()).hexdigest()
        assert digest == s['sha256'], s['path']
        if s['path'] in source_registry:
            assert digest == source_registry[s['path']]['sha256']
        source_checks.append({'path': s['path'], 'sha256': digest, 'status': 'PASS'})
    with (ROOT / 'data/results.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == cv['csv_columns']
        csv_rows = list(reader)
    assert len(csv_rows) == 120
    for c in results['cases']:
        selected = [r for r in csv_rows if r['case_id'] == c['case_id']]
        assert [r['component'] for r in selected] == ['total', 'gate', 'up', 'down']
        for row, value in zip(selected, [c['result']] + c['components']):
            for key in ('case_id', 'model_id', 'model_revision', 'workload', 'kind'):
                assert row[key] == c[key]
            assert int(row['selected_layer']) == c['selected_layer']
            assert int(row['U']) == c['U'] and row['L'] == ''
            if row['component'] == 'total':
                assert row['N'] == row['K'] == row['state_copies'] == ''
                assert int(row['shared_input_removed_Byte']) == value['shared_input_bytes_removed']
            else:
                assert [int(row['N']), int(row['K'])] == value['shape_N_K']
                assert int(row['state_copies']) == value['state_copies']
                assert row['shared_input_removed_Byte'] == ''
            for key, field in [('Q_S', 'Q_S_Byte'), ('Q_R', 'Q_R_Byte'), ('resident_bytes_initial', 'resident_initial_Byte'), ('resident_bytes_final', 'resident_final_Byte')]:
                assert int(row[field]) == value[key]
            ri = value['RI']
            assert row['RI_exact'] == (str(ri) if isinstance(ri, int) else f"{ri['numerator']}/{ri['denominator']}")
    checks = {'schema_version': cv['schema_version'], 'reference_id': cv['reference_id'], 'status': 'PASS',
              'case_counts': {'finite': 30, 'limit': 0}, 'independent_checks': independent,
              'legacy_comparison': migration, 'source_checks': source_checks,
              'notes': ['主计算未被导入；独立检查从原始 config 重读 D/F，按三矩阵实际行宽累计一次写入。',
                        '输入身份由源阶段与元素下标区分；同一向量的 gate/up 共用 x，down 的 z 独立；随后逐向量累计。',
                        '归档 operator 为第二条迁移回归；30 汇总与 90 分项按 U/8 对照旧档位；权重写入与容量不变，输入、RI 与共享扣除线性缩放。',
                        '初始权重为空：初始有效容量为 0；末态三权重保留；一次写入累计与末态容量相等。',
                        'CSV 120 行与 JSON 精确值一致；源码来源 SHA-256 已逐个核对。',
                        '源文件仅只读；没有执行模型、下载权重或导入旧 shared 生产 API。']}
    assert_keys(checks, cv['checks_root_keys'])
    out = json.dumps(checks, ensure_ascii=False, indent=2) + '\n'
    path = ROOT / 'data/checks.json'
    if args.emit:
        path.write_text(out)
    else:
        assert path.read_text() == out, 'checks.json stale; run check.py --emit'
    print('PASS: 30 independent cases, 90 components, 30 scaled archived comparisons, source hashes, exact CSV')


if __name__ == '__main__':
    main()

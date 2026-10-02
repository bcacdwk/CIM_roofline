#!/usr/bin/env python3
"""Independent Step 4 audit; stdlib only, never imports production generators.

Default: read-only recomputation and artifact comparison. --emit writes only D's
directory. --numeric-only checks the notified data hashes while revised document
manifests are pending; it cannot produce a final handoff.
"""
import argparse
from collections import Counter
import copy
import csv
from fractions import Fraction
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[1]
TASK = HERE.parents[1]
REPO = TASK.parents[1]
HEAD = 'e472a0d864b8fb9afb14b0c306217a0e5653e122'
REF = 'WS128-INT8-semantic-banks-v1'
NAMES = ['01_qkv_projection', '02_ffn_moe', '03_attention']
NOTIFIED_RESULTS = [
    'c342f0781f396df3d18d6bfcc94bdef95c3846f9985a8ca0e038297f0ef69a27',
    '5fc920987cd169108e39c72b5c844d0217b504dedffb8f9fbfce8f0ce40a4e8b',
    '7f552ac50508897407e7856c96221a3a73e2ac28ff5629b512a9f35736875107',
]
CAP_MEANING = 'final state capacity; distinct from cumulative Q_R and from physical encoded capacity'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def exact(qs, qr, calls=None):
    ratio = Fraction(qs, qr) if qr else 'infinity'
    if isinstance(ratio, Fraction):
        ratio = ratio.numerator if ratio.denominator == 1 else dict(numerator=ratio.numerator, denominator=ratio.denominator)
    return dict(Q_S=qs, Q_R=qr, RI=ratio, tile_evaluations=calls)


def blocks(extent):
    return [(start, min(128, extent-start)) for start in range(0, extent, 128)]


def axis(extent):
    parts = blocks(extent)
    return dict(full_128_blocks=sum(n == 128 for _, n in parts),
                tail_valid_elements=next((n for _, n in parts if n < 128), 0), blocks=len(parts))


def layout(n, k, copies=1, histogram=False):
    tiles = [(a, b) for _, a in blocks(n) for _, b in blocks(k)]
    out = dict(matrix_N_K_per_copy=[n, k], copies=copies,
               output_axis=axis(n), input_axis=axis(k), resident_tiles=len(tiles)*copies,
               valid_resident_bytes=sum(a*b for a, b in tiles)*copies,
               allocated_tile_bytes=len(tiles)*copies*128*128)
    if histogram:
        count = Counter(tiles)
        out['valid_tile_shape_histogram'] = [dict(valid_N_K=list(shape), tiles=count[shape]*copies) for shape in sorted(count)]
    return out


def capacity(parts, field='layout', meaning=True):
    out = {key: sum(p[field][key] for p in parts.values()) for key in
           ('valid_resident_bytes', 'allocated_tile_bytes', 'resident_tiles')}
    if meaning:
        out['meaning'] = CAP_MEANING
    return out


def matrix(n, k, uses, loads):
    # Each receiving (output block, input block) contributes its actual k width;
    # each write contributes its actual n*k rectangle, never padded bytes.
    tiles = [(a, b) for _, a in blocks(n) for _, b in blocks(k)]
    qs = sum(b for a, b in tiles)*uses
    qr = sum(a*b for a, b in tiles)*loads
    return dict(operator=exact(sum(b for _, b in blocks(k))*uses, qr),
                ports=exact(qs, qr, len(tiles)*uses),
                tile_layout=dict(output_block_sizes=[a for _, a in blocks(n)],
                                 input_block_sizes=[b for _, b in blocks(k)],
                                 resident_tiles=len(tiles), load_events=len(tiles)*loads),
                layout=layout(n, k), window=dict(input_vectors=uses, full_weight_loads=loads))


def matrix_stage(raw, row, B=None):
    d = raw['D']
    if row == 'qkv_projection':
        shapes = {'Q': (raw['Hq']*raw['dqk'], d)}
        if raw['gate']:
            shapes['G'] = (raw['Hq']*raw['dv'], d)
        shapes.update(K=(raw['Hkv']*raw['dqk'], d), V=(raw['Hkv']*raw['dv'], d))
        uses, loads = 1, 0
        sources = {name: ('x', d) for name in shapes}
    else:
        f = raw['F']
        shapes = {'gate': (f, d), 'up': (f, d), 'down': (d, f)}
        uses, loads = B, 1
        sources = dict(gate=('x', d), up=('x', d), down=('z', f))
    parts = {name: matrix(n, k, uses, loads) for name, (n, k) in shapes.items()}
    op = sum(width for identity, width in set(sources.values()))*uses
    removed = sum(p['operator']['Q_S'] for p in parts.values())-op
    qr = sum(p['ports']['Q_R'] for p in parts.values())
    return dict(parts=parts, operator=exact(op, qr), operator_shared_input_overlap_removed=removed,
                ports=exact(sum(p['ports']['Q_S'] for p in parts.values()), qr,
                            sum(p['ports']['tile_evaluations'] for p in parts.values())), capacity=capacity(parts))


def call_shapes(raw, L, mode):
    """Invert prefix order: each sequence tile grows once, then persists."""
    qk, av = Counter(), Counter()
    for start, final_width in blocks(L):
        if mode == 'decode':
            life = [(final_width, 1)]
        else:
            life = [(size, 1) for size in range(1, final_width+1)]
            # After this tile is full it is visited by every later query.
            if final_width == 128:
                life.append((128, L-start-128))
        for size, occurrences in life:
            for _, width in blocks(raw['dqk']):
                qk[(size, width)] += occurrences*raw['Hq']
            for _, height in blocks(raw['dv']):
                av[(height, size)] += occurrences*raw['Hq']
    return qk, av


def attention_stage(raw, L, mode):
    hq, hkv, dqk, dv = (raw[k] for k in ('Hq', 'Hkv', 'dqk', 'dv'))
    appended = L if mode == 'prefill' else 1
    initial = L-appended
    # Each score/AV-input element j participates in L-j+1 future prefixes.
    element_visits = sum(L-j+1 for j in range(1, L+1)) if mode == 'prefill' else L
    tile_visits = sum(L-start for start, _ in blocks(L)) if mode == 'prefill' else len(blocks(L))
    histograms = call_shapes(raw, L, mode)
    parts = {}
    for name, dims, initial_dims, slices, hist, op in (
        ('QK', (L, dqk), (initial, dqk), [[1, k] for _, k in blocks(dqk)], histograms[0], hq*appended*dqk),
        ('AV', (dv, L), (dv, initial), [[n, 1] for _, n in blocks(dv)], histograms[1], hq*element_visits)):
        per_token = hkv*sum(n*k for n, k in slices)
        writes = appended*per_token
        width_calls = Counter()
        for (n, k), calls in hist.items():
            width_calls[str(k)] += calls
        parts[name] = dict(operator=exact(op, writes),
                           ports=exact(sum(k*calls for (n, k), calls in hist.items()), writes, sum(hist.values())),
                           layout=layout(*dims, hkv, histogram=True),
                           initial_layout=layout(*initial_dims, hkv, histogram=True),
                           append=dict(valid_slice_N_K_per_head_per_token=slices,
                                       logical_slice_write_events=appended*hkv*len(slices),
                                       events_are_not_device_write_transactions=True,
                                       per_token_logical_slice_write_events=hkv*len(slices),
                                       valid_write_bytes_per_token=per_token),
                           valid_N_K_call_histogram=[dict(valid_N_K=list(shape), calls=hist[shape]) for shape in sorted(hist)],
                           valid_input_width_to_calls=dict(width_calls))
    result = dict(parts=parts)
    for boundary in ('operator', 'ports'):
        result[boundary] = exact(sum(p[boundary]['Q_S'] for p in parts.values()),
                                 sum(p[boundary]['Q_R'] for p in parts.values()),
                                 sum(p[boundary]['tile_evaluations'] for p in parts.values()) if boundary == 'ports' else None)
    result.update(appended_tokens=appended, kv_copies_per_head=1, group_size=hq//hkv,
                  prefix_sum_i=element_visits, prefix_sum_ceil_output=tile_visits, prefix_sum_ceil_input=tile_visits,
                  active_layout_at_L=dict(K_matrix_N_K=[L, dqk], V_matrix_N_K=[dv, L]),
                  append_shape_per_kv_head=dict(K=[1, dqk], V=[dv, 1]),
                  initial_KV_tokens=initial, final_KV_tokens=L,
                  initial_valid_resident_bytes=initial*hkv*(dqk+dv), operator_shared_input_overlap_removed=0,
                  capacity=capacity(parts), initial_capacity=capacity(parts, 'initial_layout', False))
    return result


def same(expected, actual, path='', allow_extra=False):
    """Compare every leaf, with exact integers and rationals; count checked leaves."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), path
        assert set(expected) <= set(actual), (path, 'missing', set(expected)-set(actual))
        if not allow_extra:
            assert set(expected) == set(actual), (path, 'unchecked fields', set(actual)-set(expected))
        return sum(same(value, actual[key], path+'/'+key, allow_extra) for key, value in expected.items())
    if isinstance(expected, list):
        assert isinstance(actual, list) and len(expected) == len(actual), (path, 'list length')
        return sum(same(value, actual[i], path+'/'+str(i), allow_extra) for i, value in enumerate(expected))
    assert type(expected) is type(actual) and expected == actual, (path, expected, actual)
    return 1


def scientific_plan(plan):
    return dict(parameters=plan['parameters'], model_order=plan['table_IIb']['columns_model_ids'],
                display_names=plan['table_IIb']['columns_display_names'], rows=plan['table_IIb']['rows'],
                selection_rules=plan['selection_rules'], definitions=plan['definitions'],
                reference=plan['step2_reference'], fixed_task_I=plan['fixed_task_I'])


def raw_models(models):
    raws = {}
    for m in models:
        source = TASK/m['local_material']['raw_config']
        config = read(source)
        c = config.get('text_config', config)
        impl = (TASK/m['local_material']['implementation']).read_text()
        d, hq, hkv, dqk = [c[k] for k in ('hidden_size', 'num_attention_heads', 'num_key_value_heads', 'head_dim')]
        dv = c.get('v_head_dim') or dqk
        if 'layer_types' in c:
            selected = c['layer_types'].index('full_attention')
        elif 'hybrid_layer_pattern' in c:
            selected = next(i for i, kind in enumerate(c['hybrid_layer_pattern']) if kind == 0 and c['moe_layer_freq'][i])
        else:
            selected = c.get('first_k_dense_replace', 0)
        f = c.get('moe_intermediate_size', c.get('intermediate_size'))
        raw = dict(D=d, F=f, Hq=hq, Hkv=hkv, dqk=dqk, dv=dv, gate=bool(c.get('attn_output_gate', False)),
                   selected_layer=selected, config=m['local_material']['raw_config'], config_sha256=sha(source),
                   implementation=m['local_material']['implementation'], implementation_sha256=sha(TASK/m['local_material']['implementation']))
        assert hq % hkv == 0
        assert m['backbone']['hidden_size'] == d and m['backbone']['selected_layer_index_zero_based'] == selected
        assert m['ffn']['hidden_size'] == d and m['ffn']['intermediate_size'] == f
        for key, value in dict(query_heads=hq, kv_heads=hkv, qk_head_dim=dqk, v_head_dim=dv, queries_per_kv_head=hq//hkv, output_gate=raw['gate']).items():
            assert m['attention'][key] == value, (m['id'], key)
        assert m['ffn']['matrices'] == dict(gate=[f,d], up=[f,d], down=[d,f])
        assert m['ffn']['selected_layer_index_zero_based'] == selected
        shapes = m['attention']['weight_shapes_N_K']
        assert shapes['q_logical'] == [hq*dqk,d] and shapes['k'] == [hkv*dqk,d] and shapes['v'] == [hkv*dv,d]
        if raw['gate']:
            assert 'self.head_dim * 2' in impl and 'query_states, gate = torch.chunk' in impl
            assert shapes['q_output_gate_logical'] == [hq*dv, d]
            assert shapes['q_and_gate_packed'] == [hq*(dqk+dv), d]
        if m['id'] == 'hy3_295b':
            assert hq*dqk == 8192 and 'config.num_attention_heads * self.head_dim' in impl
        if m['id'] == 'ling_1t':
            assert c['max_position_embeddings'] == 32768 and c['rope_scaling'] is None
            card = (TASK/m['local_material']['raw_model_card']).read_text()
            for marker in ('"factor": 4.0', '"original_max_position_embeddings": 32768', '"type": "yarn"', '--max-model-len'):
                assert marker in card
            assert 'qkv.split(' in impl and '(self.num_heads + 2 * self.num_key_value_heads) * self.head_dim' in impl
            ext = m['context']['extension_for_128K']
            assert ext['rope_scaling'] == dict(factor=4.0, original_max_position_embeddings=32768, type='yarn')
            assert '131072' in ext['runtime_condition']
        if m['id'] == 'mimo_v25_pro':
            assert (dqk, dv, selected) == (192,128,7)
            assert 'self.v_size = self.num_key_value_heads * self.v_head_dim' in impl
            handoff = impl[impl.index('def _forward_attention'):impl.index('def forward', impl.index('def _forward_attention'))]
            assert handoff.index('value_states = value_states * self.v_scale') < handoff.index('past_key_values.update') < handoff.index('attn_output, attn_weights = attention_interface(')
            assert c['attention_value_scale'] == 0.612 and c['add_full_attention_sink_bias'] is False
        raws[m['id']] = raw
    return raws


def verify_deliveries(numeric_only):
    records, lock = [], []
    approved = read(HERE/'data/ready_sources.json') if not numeric_only else None
    for j, name in enumerate(NAMES):
        directory = TASK/'table_IIb'/name
        rp = directory/'data/results.json'
        assert sha(rp) == NOTIFIED_RESULTS[j], (name, 'results changed: requires new READY and re-audit')
        if numeric_only:
            entry = dict(directory=str(directory.relative_to(TASK)), results_sha256=sha(rp), delivery_revision='pending_final_READY')
        else:
            manifest_path = directory/'DELIVERY.json'
            manifest = read(manifest_path)
            expected = approved['sources'][j]
            assert expected['directory'] == str(directory.relative_to(TASK))
            assert sha(manifest_path) == expected['delivery_sha256'], (name, 'DELIVERY changed without refreshed READY lock')
            assert manifest['status'] == 'ready_for_review'
            assert manifest['delivery_revision'] == expected['delivery_revision']
            assert manifest['case_count'] == [6,18,36][j] and manifest['shared_reference_id'] == REF
            entries = manifest.get('artifacts', manifest.get('files'))
            if isinstance(entries, dict):
                entries = list(entries.values())
            base = TASK if manifest['path_base'] == 'tasks/task2_table_II_workloads/' else directory
            verified = []
            for artifact in entries:
                path = base/artifact['path']
                assert path.resolve().is_relative_to(directory.resolve()), path
                assert sha(path) == artifact['sha256'], (name, artifact['path'], 'hash mismatch')
                if 'bytes' in artifact:
                    assert path.stat().st_size == artifact['bytes']
                verified.append(dict(path=str(path.relative_to(TASK)), sha256=sha(path)))
            entry = dict(directory=str(directory.relative_to(TASK)), delivery_revision=manifest['delivery_revision'],
                         delivery_sha256=sha(manifest_path), results_sha256=sha(rp), verified_artifacts=verified)
        lock.append(entry)
        source = read(rp)
        assert source['schema_version'] == ['1.0','1.0','step4-delivery-v1'][j]
        assert len(source['cases']) == [6,18,36][j]
        for index, original in enumerate(source['cases']):
            case = copy.deepcopy(original)
            case['trace'] = {k: entry[k] for k in entry if k != 'verified_artifacts'}
            case['trace'].update(results_path=str(rp.relative_to(TASK)), case_id=case['case_id'],
                                 json_pointer='/cases/'+str(index), array_index=index)
            records.append(case)
    return records, lock


def protected_files(plan):
    actual = subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip()
    assert actual == HEAD, ('HEAD changed', actual)
    changed = subprocess.check_output(['git','diff',HEAD,'--name-only'], cwd=REPO, text=True).splitlines()
    allowed = ['tasks/task2_table_II_workloads/README.md', 'tasks/task2_table_II_workloads/data/study_plan.json']
    assert set(changed) <= set(allowed), ('protected tracked content changed', changed)
    old = json.loads(subprocess.check_output(['git','show',HEAD+':tasks/task2_table_II_workloads/data/study_plan.json'], cwd=REPO, text=True))
    same(scientific_plan(old), scientific_plan(plan), 'study_plan/scientific_inputs')
    staged = subprocess.check_output(['git','diff','--cached','--name-only'], cwd=REPO, text=True).splitlines()
    assert not staged, ('unexpected staged paths', staged)
    return dict(reference_HEAD=HEAD, changed_tracked_files=changed, allowed_changes=allowed,
                scientific_study_plan_unchanged=True, protected_tracked_files_unchanged=True, staged_paths=staged)


def regressions():
    scripts = ['scripts/check_step1.py','shared/scripts/check_counting.py','shared/scripts/generate_IIa.py',
               'table_IIb/pilot/scripts/generate.py','table_IIb/pilot/scripts/check.py']
    out = []
    for script in scripts:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        proc = subprocess.run([sys.executable, str(TASK/script)], cwd=TASK, text=True, capture_output=True, env=env)
        assert proc.returncode == 0, (script, proc.stdout, proc.stderr)
        out.append(dict(script=script, sha256=sha(TASK/script), returncode=proc.returncode,
                        stdout=proc.stdout.strip(), stderr=proc.stderr.strip(), mode='default read-only'))
    return out


def ratio_text(value):
    if isinstance(value, dict):
        return str(value['numerator'])+'/'+str(value['denominator'])
    return '∞' if value == 'infinity' else str(value)


def preview(records, models, rows, plan):
    lines = ['# Table II(b) · 六模型研究预览', '',
             'Step 4 内部复核稿；主边界为 ports，对照为 operator。各格为精确 RI=Q_S/Q_R；不是性能、吞吐或硬件适合度。', '',
             '`WS128-INT8-semantic-banks-v1`；128×128；各角色 1 Byte；独立语义 bank；每 KV head 一份 K/V；逐因果前缀。', '',
             'FFN 三值依 B=8、64、512；Attention 三值依 L=1024、16384、131072（1K、16K、128K）。B 只指所选 Dense FFN／单路由专家一份驻留权重服务的实际向量数。', '']
    for boundary in ('ports','operator'):
        lines += ['## '+boundary, '', '| 行 | '+' | '.join(m['display_name'] for m in models)+' |', '|---|'+'---|'*6]
        for row in rows:
            cells = []
            for m in models:
                matches = [c for c in records if c['model_id']==m['id'] and c['row']==row['id']]
                cells.append(', '.join(ratio_text(c['result'][boundary]['RI']) for c in matches))
            lines.append('| '+row['label']+' | '+' | '.join(cells)+' |')
        lines.append('')
    lines += ['## 阅读条件', '',
              '- QKV 是一个 token、权重预驻留，Q_R=0；两款 Qwen 的 output gate 单独保留，∞ 不说明需求量相同。Hy3 的原生 Q 输出为 8192，不能用 hidden size 4096 替代。',
              '- FFN 只取一层 Dense FFN 或一个路由专家，三矩阵各装载一次；不乘 top-k、总专家、共享专家或层数。所有所选 D/F 整除128，故 ports RI 均为 B/128；operator 和容量仍不同。',
              '- Ling-1T 的固定 config 上限为32768，128K 条件是官方 vLLM YaRN 配方：factor=4、original_max_position_embeddings=32768、type=yarn，并设置 --max-model-len 131072。本地原始 config 未改。',
              '- MiMo 取第7层 global GQA，d_QK=192、d_V=128；QK 每头输入切片为128+64 Byte，两次调用都保留。最终有效 KV 容量与 tile 分配容量分开报告。',
              '- 原生 BF16/FP8 只作来源记录；INT8 是本文逻辑参考，不是六模型精度验证。模型子层和研究窗口不代表整个模型实际调度。', '',
              '完整字节、调用、分项、容量、append、来源哈希与 JSON 位置见 [results.json](data/results.json)；平面精确记录见 [results.csv](data/results.csv)。', '']
    return '\n'.join(lines)


def csv_text(records):
    columns = ['case_id','model_id','model_revision','selected_layer','row','B','L','component','boundary',
               'Q_S','Q_R','RI','tile_evaluations','matrix_N_K_per_copy','copies','valid_resident_bytes',
               'allocated_tile_bytes','resident_tiles','operator_shared_input_overlap_removed',
               'initial_KV_tokens','final_KV_tokens','initial_valid_resident_bytes','appended_tokens',
               'append','directory','results_path','results_sha256','delivery_revision','delivery_sha256','json_pointer']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, columns, lineterminator='\n')
    writer.writeheader()
    for case in records:
        for component, item in [('total',case['result']), *case['result']['parts'].items()]:
            for boundary in ('ports','operator'):
                row = {key:case.get(key,'') for key in columns[:7]}
                row.update(component=component, boundary=boundary)
                row.update(item[boundary]); row['RI'] = ratio_text(row['RI'])
                cap = item.get('capacity',item.get('layout',{}))
                row.update({key:cap[key] for key in ('matrix_N_K_per_copy','copies','valid_resident_bytes','allocated_tile_bytes','resident_tiles') if key in cap})
                row.update({key:item[key] for key in ('operator_shared_input_overlap_removed','initial_KV_tokens','final_KV_tokens','initial_valid_resident_bytes','appended_tokens','append') if key in item})
                row.update({key:case['trace'][key] for key in ('directory','results_path','results_sha256','delivery_revision','delivery_sha256','json_pointer')})
                row['json_pointer'] += '/result'+('' if component=='total' else '/parts/'+component)+'/'+boundary
                for key,value in list(row.items()):
                    if isinstance(value,(dict,list)):
                        row[key] = json.dumps(value,separators=(',',':'),ensure_ascii=False)
                writer.writerow(row)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--emit', action='store_true')
    parser.add_argument('--numeric-only', action='store_true')
    args = parser.parse_args()
    assert not (args.emit and args.numeric_only), 'Numeric-only mode cannot publish artifacts'
    plan = read(TASK/'data/study_plan.json')
    models = read(TASK/'data/models.json')['models']
    conventions = read(TASK/'shared/data/conventions.json')
    assert conventions['reference_id'] == REF
    assert conventions['mapping']['tile_N'] == conventions['mapping']['tile_K'] == 128
    assert set(conventions['precision']['role_bytes'].values()) == {1}
    assert conventions['boundaries']['ports']['primary'] is True
    assert plan['step2']['reference_id'] == REF
    assert [m['id'] for m in models] == plan['table_IIb']['columns_model_ids']
    assert plan['parameters']['B'] == [8,64,512] and plan['parameters']['L_tokens'] == [1024,16384,131072]
    rows = plan['table_IIb']['rows']
    assert [r['id'] for r in rows] == ['qkv_projection','ffn_or_moe','attention_prefill','attention_decode']
    raws = raw_models(models)
    records, lock = verify_deliveries(args.numeric_only)
    expected_ids = [m['id']+'/'+r['id']+'/'+str(value)
                    for m in models for r in rows
                    for value in (['one_token'] if r['sweep'] is None else plan['parameters']['B' if r['sweep']=='B' else 'L_tokens'])]
    by_id = {c['case_id']:c for c in records}
    assert len(by_id) == len(records) == 60 and set(by_id) == set(expected_ids)
    # Upstream ordering is model-major, then each owned row and B/L sequence.
    for name in NAMES:
        actual = [c['case_id'] for c in records if c['trace']['directory'].endswith(name)]
        assert actual == [key for key in expected_ids if key in actual], (name,'model/row/sweep order')
    records = [by_id[key] for key in expected_ids]
    checked = []
    for case in records:
        m = next(m for m in models if m['id'] == case['model_id'])
        raw = raws[m['id']]
        assert case['model_revision'] == m['identity']['revision']
        assert case['selected_layer'] == raw['selected_layer'] and case['shared_reference_id'] == REF
        if case['row'] == 'qkv_projection':
            assert case.get('L') is None and 'B' not in case and case['case_id'].endswith('/one_token')
        else:
            parameter = 'B' if case['row'] == 'ffn_or_moe' else 'L'
            assert type(case[parameter]) is int and str(case[parameter]) == case['case_id'].rsplit('/',1)[1]
        if case['row'].startswith('attention_'):
            expected = attention_stage(raw, case['L'], case['row'].split('_')[1])
            same(dict(query_heads=raw['Hq'],kv_heads=raw['Hkv'],qk_head_dim=raw['dqk'],v_head_dim=raw['dv'],queries_per_kv_head=raw['Hq']//raw['Hkv']),case['configuration'],case['case_id']+'/configuration')
            index = plan['parameters']['L_tokens'].index(case['L'])
            assert case['context_support'] == m['context']['support'][index]
            assert case['context_extension_condition'] == (m['context']['extension_for_128K'] if case['L']==131072 else None)
        else:
            expected = matrix_stage(raw,case['row'],case.get('B'))
        leaves = same(expected,case['result'],case['case_id']+'/result')
        checked.append(dict(case_id=case['case_id'], result_leaf_checks=leaves, status='PASS'))
    pilot = read(TASK/'table_IIb/pilot/data/results.json')
    overlaps = []
    for previous in pilot['cases']:
        now = by_id[previous['case_id']]
        count = same(previous,now,previous['case_id']+'/pilot',allow_extra=True)
        overlaps.append(dict(case_id=previous['case_id'],existing_semantic_leaves_compared=count,differences=[],status='PASS'))
    assert len(overlaps) == 22
    guard = protected_files(plan)
    if args.numeric_only:
        print(dump(dict(status='PASS numeric preparation only; final READY locks pending',cases=60,parts=sum(len(c['result']['parts']) for c in records),
                        oracle_result_leaf_checks=sum(c['result_leaf_checks'] for c in checked),pilot_cases=22,
                        pilot_existing_leaf_checks=sum(c['existing_semantic_leaves_compared'] for c in overlaps))))
        return
    regression = regressions()
    protected_files(plan)
    config = dict(schema_version='step4-crosscheck-inputs-v1', reference_id=REF, tile_N_K=[128,128],
                  precision_role_bytes=conventions['precision']['role_bytes'], scientific_study_plan=scientific_plan(plan),
                  model_order=[m['id'] for m in models], raw_inputs=raws,
                  fixed_source_hashes={p:sha(TASK/p) for p in ('data/models.json','data/sources.json','shared/data/conventions.json','shared/scripts/counting.py','shared/tex/counting_method.zh.tex','table_IIb/pilot/data/results.json')},
                  deliveries=lock)
    checks = dict(schema_version='step4-crosscheck-checks-v1',status='PASS',case_count=60,
                  part_count=sum(len(c['result']['parts']) for c in records),case_checks=checked,
                  oracle_result_leaf_checks=sum(c['result_leaf_checks'] for c in checked),
                  pilot_overlap_count=22,pilot_existing_leaf_checks=sum(c['existing_semantic_leaves_compared'] for c in overlaps),
                  pilot_overlap_checks=overlaps,regressions=regression,protected_files=guard,
                  production_code_imported_for_oracle=False, upstream_data_changes_required=False,
                  method='Raw configuration and pinned implementation checks; explicit matrix tile rectangles; operator source identities; inverse sequence-tile lifetime/call-shape histograms and element participation; exact rational comparisons.')
    results = dict(schema_version='step4-unified-v1',reference_id=REF,case_count=60,
                   model_order=plan['table_IIb']['columns_model_ids'],row_order=[r['id'] for r in rows],
                   B=plan['parameters']['B'],L=plan['parameters']['L_tokens'],precision_role_bytes=conventions['precision']['role_bytes'],
                   tile_N_K=[128,128],primary_boundary='ports',contrast_boundary='operator',cases=records)
    csv_data = csv_text(records)
    assert len(list(csv.DictReader(io.StringIO(csv_data)))) == 412
    products = {'data/config.json':dump(config),'data/checks.json':dump(checks),'data/results.json':dump(results),
                'data/results.csv':csv_data,'PREVIEW.zh.md':preview(records,models,rows,plan)}
    for relative,content in products.items():
        dest = HERE/relative
        if args.emit:
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content)
        else:
            assert dest.read_text()==content, ('stale D artifact',relative)
    print('PASS: 60 cases / 146 parts; '+str(checks['oracle_result_leaf_checks'])+' independent result leaves; 22 pilot overlaps / '+str(checks['pilot_existing_leaf_checks'])+' existing leaves; 5 read-only regressions; final delivery hashes and protected scientific inputs verified.')


if __name__ == '__main__':
    main()

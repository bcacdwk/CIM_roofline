#!/usr/bin/env python3
"""Six static QKV cases. Shared API is the primary calculator, never the oracle."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'shared/scripts'))
import counting as c

START = 'e472a0d864b8fb9afb14b0c306217a0e5653e122'
SHORT = ['Qwen3.5-2B', 'Ministral 3 8B', 'Qwen3.6-35B-A3B', 'Hy3 (295B)', 'Ling-1T', 'MiMo-V2.5-Pro']


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def axis(n):
    full, tail = divmod(n, 128)
    return dict(full_128_blocks=full, tail_valid_elements=tail, blocks=full + bool(tail))


def layout(n, k):
    nt = c.ceildiv(n, 128) * c.ceildiv(k, 128)
    return {'matrix_N_K_per_copy': [n, k], 'copies': 1,
            'output_axis': axis(n), 'input_axis': axis(k),
            'resident_tiles': nt, 'valid_resident_bytes': n*k,
            'allocated_tile_bytes': nt*16384}


def make():
    plan = read('data/study_plan.json')
    contract = read('shared/data/conventions.json')
    models = {m['id']: m for m in read('data/models.json')['models']}
    ids = plan['table_IIb']['columns_model_ids']
    assert len(ids) == 6
    assert contract['reference_id'] == 'WS128-INT8-semantic-banks-v1'
    assert all(v == 1 for v in contract['precision']['role_bytes'].values())
    assert contract['mapping']['tile_N'] == contract['mapping']['tile_K'] == 128
    manifest = {'schema_version': '1.0', 'task': 'Task II Step 4 QKV Projection',
                'shared_reference_id': contract['reference_id'], 'reviewed_step3_and_start_HEAD': START,
                'model_order': ids, 'tile_N_K': [128, 128], 'precision_role_bytes': contract['precision']['role_bytes'],
                'primary_boundary': 'ports', 'contrast_boundary': 'operator',
                'window': 'one input token; weights pre-resident; no weight writes inside window',
                'scope': 'one selected full/global GQA projection per model; includes native output gate; excludes W_O and KV writes',
                'models': {}, 'source_files_sha256': {}, 'source_registry_entries': {}}
    paths = ['data/models.json', 'shared/data/conventions.json', 'shared/scripts/counting.py',
             'shared/tex/counting_method.zh.tex']
    registry = {s['local_path']: s for s in read('data/sources.json')}
    cases = []
    for mid in ids:
        m = models[mid]; a = m['attention']; D = m['backbone']['hidden_size']
        shapes = {'Q': a['weight_shapes_N_K']['q_logical']}
        if a['output_gate']:
            shapes['G'] = a['weight_shapes_N_K']['q_output_gate_logical']
        shapes.update(K=a['weight_shapes_N_K']['k'], V=a['weight_shapes_N_K']['v'])
        result = c.qkv(D, a['query_heads'], a['kv_heads'], a['qk_head_dim'], a['v_head_dim'],
                       gate_width=shapes.get('G', [0])[0])
        for name, (n, k) in shapes.items():
            result['parts'][name]['layout'] = layout(n, k)
            result['parts'][name]['window'] = {'input_vectors': 1, 'full_weight_loads': 0}
        result['capacity'] = {key: sum(p['layout'][key] for p in result['parts'].values())
                              for key in ['valid_resident_bytes', 'allocated_tile_bytes', 'resident_tiles']}
        result['capacity']['meaning'] = 'final state capacity; distinct from cumulative Q_R and from physical encoded capacity'
        layer = m['backbone']['selected_layer_index_zero_based']
        cases.append({'case_id': f'{mid}/qkv_projection/one_token', 'model_id': mid,
                      'row': 'qkv_projection', 'L': None, 'model_revision': m['identity']['revision'],
                      'selected_layer': layer, 'shared_reference_id': contract['reference_id'], 'result': result})
        manifest['models'][mid] = {'display_name': m['display_name'], 'identity': m['identity'],
                                  'selected_layer': layer, 'layer_type': m['backbone']['selected_layer_type'],
                                  'D': D, 'Hq': a['query_heads'], 'Hkv': a['kv_heads'],
                                  'dqk': a['qk_head_dim'], 'dv': a['v_head_dim'],
                                  'output_gate': a['output_gate'], 'native_projection_layout': a['projection_layout'],
                                  'semantic_shapes_N_K': shapes, 'native_weight_shapes_N_K': a['weight_shapes_N_K'],
                                  'native_precision': m['precision'], 'attention_evidence': a['evidence'],
                                  'local_material': m['local_material']}
        local = m['local_material']
        paths += [local[key] for key in ['raw_config', 'implementation', 'structure_card']]
        paths.append(str(Path(local['raw_config']).with_name('hf_metadata.json')))
    paths.append('literature/02_ministral3_8b/raw/params.json')
    for path in sorted(set(paths)):
        manifest['source_files_sha256'][path] = sha(path)
        if path in registry:
            manifest['source_registry_entries'][path] = registry[path]
    return manifest, c.encode({'schema_version': '1.0', 'cases': cases})


def tables(config, data):
    totals = [r'\begin{tabular}{@{}lrrrr@{}}\toprule',
              r'模型 & $Q_S^{\rm ports}$ (Byte) & $Q_S^{\rm op}$ (Byte) & 调用 / tile & 容量 (MiB)\\\midrule']
    parts = [r'\begin{tabular}{@{}llrrr@{}}\toprule',
             r'模型 & 分项 & $Q_S^{\rm ports}$ (Byte) & 调用 / tile & 容量 (MiB)\\\midrule']
    shapes = [r'\begin{tabular}{@{}lrrrrl@{}}\toprule',
              r'模型 / 层 & $D$ & $H_q/H_{kv}$ & $d_{QK}/d_V$ & $G$ 宽 & $N_Q,N_G,N_K,N_V$\\\midrule']
    md = ['# 六模型 QKV 概览', '', '一个 token，权重预驻留；所有分项和汇总在 ports/operator 两边界均为 Q_R=0、RI=∞。', '',
          '| 模型 | 层 (0 起) | Q/G/K/V 输出宽度（无 G 用 —） | ports Q_S (Byte) | operator Q_S (Byte) | 调用 / resident tiles | 有效/分配容量 (Byte) |',
          '|---|---:|---|---:|---:|---:|---:|']
    for label, record in zip(SHORT, data['cases']):
        r = record['result']; m = config['models'][record['model_id']]
        cap = r['capacity']['valid_resident_bytes']
        assert cap % 1048576 == 0
        totals.append(f"{label} & {r['ports']['Q_S']:,} & {r['operator']['Q_S']:,} & {r['ports']['tile_evaluations']:,} & {cap//1048576}" + r'\\')
        widths = [str(m['semantic_shapes_N_K'][j][0]) if j in m['semantic_shapes_N_K'] else '-' for j in ['Q','G','K','V']]
        shapes.append(f"{label} / {record['selected_layer']} & {m['D']} & {m['Hq']}/{m['Hkv']} & {m['dqk']}/{m['dv']} & {widths[1]} & " + ', '.join(widths) + r'\\')
        md.append(f"| {m['display_name']} | {record['selected_layer']} | {' / '.join(widths)} | {r['ports']['Q_S']} | {r['operator']['Q_S']} | {r['ports']['tile_evaluations']} | {cap} / {r['capacity']['allocated_tile_bytes']} |")
        for i, (name,p) in enumerate(r['parts'].items()):
            parts.append(f"{label if i==0 else ''} & {name} & {p['ports']['Q_S']:,} & {p['ports']['tile_evaluations']:,} & {p['layout']['valid_resident_bytes']//1048576}" + r'\\')
        parts.append(r'\addlinespace[3pt]')
    for table in [totals, parts, shapes]: table.append(r'\bottomrule\end{tabular}')
    md += ['', 'MiMo 的 Q/K 输出宽度为 24576/1536；虽然 head_dim=192，各语义投影 N 与输入 D 均整除 128，QKV 行没有半宽尾片。', '',
           '每个分项的 operator 输入都是同一 D 维 x 的独立入口；汇总按输入身份去重为 D Byte。', '',
           '[精确 JSON](data/results.json) · [CSV](data/results.csv) · [中文研究稿](output/pdf/qkv.zh.pdf) · [独立检查](data/checks.json)', '']
    return {'tex/totals.generated.tex': '\n'.join(totals)+'\n',
            'tex/parts.generated.tex': '\n'.join(parts)+'\n',
            'tex/shapes.generated.tex': '\n'.join(shapes)+'\n', 'OVERVIEW.zh.md': '\n'.join(md)}


def outputs():
    config, data = make()
    files = tables(config, data)
    files['data/config.json'] = json.dumps(config, ensure_ascii=False, indent=2)+'\n'
    files['data/results.json'] = json.dumps(data, ensure_ascii=False, indent=2)+'\n'
    out = io.StringIO(); w = csv.writer(out, lineterminator='\n')
    w.writerow(['case_id','component','boundary','Q_S_Byte','Q_R_Byte','RI','tile_evaluations','valid_resident_Byte','allocated_tile_Byte','resident_tiles'])
    for r in data['cases']:
        for name,p in [('total',r['result']), *r['result']['parts'].items()]:
            cap = p.get('capacity', p.get('layout'))
            for b in ['ports','operator']:
                d=p[b]
                w.writerow([r['case_id'], name, b, *[d[k] for k in ['Q_S','Q_R','RI','tile_evaluations']],
                            *[cap[k] for k in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']]])
    files['data/results.csv'] = out.getvalue()
    return files


def main():
    p=argparse.ArgumentParser(); p.add_argument('--emit',action='store_true'); args=p.parse_args()
    files=outputs()
    for name, content in files.items():
        path=HERE/name
        if args.emit: path.write_text(content)
        else: assert path.read_text()==content, f'stale artifact: {name}'
    print(f'PASS: six QKV cases, 20 semantic matrices, {len(files)} generated artifacts')


if __name__=='__main__': main()

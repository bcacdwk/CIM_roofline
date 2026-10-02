#!/usr/bin/env python3
"""Step 3 only: two full pilots + MiMo attention at 1024. Exact, no weights.

Default checks committed artifacts; --emit refreshes them. Shared counting.py is
the primary calculator. check.py derives expectations separately from raw config.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys

PILOT = Path(__file__).resolve().parents[1]
ROOT = PILOT.parents[1]
sys.path.insert(0, str(ROOT / 'shared/scripts'))
import counting as c

IDS = ['ministral3_8b_2512', 'qwen36_35b_a3b', 'mimo_v25_pro']
ROWS = ['qkv_projection', 'ffn_or_moe', 'attention_prefill', 'attention_decode']
LABELS = ['QKV Projection', 'FFN / MoE', 'Attention Prefill', 'Attention Decode']
START = '2eb7e7c59242c675594537002cc1316131be9226'


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def blocks(n):
    full, tail = divmod(n, 128)
    return {'full_128_blocks': full, 'tail_valid_elements': tail,
            'blocks': full + bool(tail)}


def layout(n, k, copies=1):
    nt = c.ceildiv(n, 128) * c.ceildiv(k, 128) * copies
    return {'matrix_N_K_per_copy': [n, k], 'copies': copies,
            'output_axis': blocks(n), 'input_axis': blocks(k),
            'resident_tiles': nt, 'valid_resident_bytes': n*k*copies,
            'allocated_tile_bytes': nt*128*128}


def add_matrix_layout(result, shapes, uses, loads):
    for name, (n, k) in shapes.items():
        p = result['parts'][name]
        p['layout'] = layout(n, k)
        p['window'] = {'input_vectors': uses, 'full_weight_loads': loads}
    add_capacity(result)


def add_capacity(result):
    result['capacity'] = {key: sum(p['layout'][key] for p in result['parts'].values())
                          for key in ['valid_resident_bytes', 'allocated_tile_bytes', 'resident_tiles']}
    result['capacity']['meaning'] = 'final state capacity; distinct from cumulative Q_R and from physical encoded capacity'


def add_attention_layout(result, a, L, mode):
    h, dq, dv = a['kv_heads'], a['qk_head_dim'], a['v_head_dim']
    appended = L if mode == 'prefill' else 1
    for name, n, k, shapes in [('QK', L, dq, [[1,w] for w in c.widths(dq,128)]),
                                ('AV', dv, L, [[w,1] for w in c.widths(dv,128)])]:
        p = result['parts'][name]
        p['layout'] = layout(n,k,h)
        p['append'] = {'valid_slice_N_K_per_head_per_token': shapes,
                       'logical_slice_write_events': appended*h*len(shapes),
                       'events_are_not_device_write_transactions': True}
    result['initial_KV_tokens'] = 0 if mode == 'prefill' else L-1
    result['final_KV_tokens'] = L
    result['initial_valid_resident_bytes'] = result['initial_KV_tokens']*h*(dq+dv)
    add_capacity(result)


def make():
    models = {m['id']: m for m in read('data/models.json')['models']}
    contract = read('shared/data/conventions.json')
    plan = read('data/study_plan.json')
    assert contract['reference_id'] == 'WS128-INT8-semantic-banks-v1'
    assert all(v == 1 for v in contract['precision']['role_bytes'].values())
    assert contract['mapping']['tile_N'] == contract['mapping']['tile_K'] == 128
    assert plan['parameters']['B'] == [8,64,512]
    assert plan['parameters']['L_tokens'] == [1024,16384,131072]
    manifest = {'pilot_version': 'task2-step3-pilot-v1', 'shared_reference_id': contract['reference_id'],
                'reviewed_step2_and_start_HEAD': START, 'date': '2026-09-24',
                'precision_role_bytes': contract['precision']['role_bytes'],
                'tile_N_K': [128,128], 'primary_boundary': 'ports', 'contrast_boundary': 'operator',
                'B': plan['parameters']['B'], 'L': plan['parameters']['L_tokens'],
                'mimo_L': [1024], 'scope': '20 full-pilot cases + 2 MiMo attention spot cases; no Step 4',
                'models': {}, 'source_files_sha256': {}}
    source_paths = ['data/models.json', 'shared/data/conventions.json', 'shared/scripts/counting.py',
                    'shared/tex/counting_method.zh.tex']
    records = []
    for mid in IDS:
        m = models[mid]; a = m['attention']; f = m['ffn']; D = m['backbone']['hidden_size']
        manifest['models'][mid] = {'display_name': m['display_name'], 'identity': m['identity'],
                                  'selected_layer': m['backbone']['selected_layer_index_zero_based'],
                                  'layer_type': m['backbone']['selected_layer_type'], 'D': D,
                                  'attention': a, 'ffn': f if mid != IDS[2] else 'not evaluated',
                                  'local_material': m['local_material']}
        source_paths += [m['local_material'][key] for key in ['raw_config','implementation','structure_card']]
        shapes = {'Q': a['weight_shapes_N_K']['q_logical']}
        if a['output_gate']:
            shapes['G'] = a['weight_shapes_N_K']['q_output_gate_logical']
        shapes.update(K=a['weight_shapes_N_K']['k'], V=a['weight_shapes_N_K']['v'])
        args = (a['query_heads'],a['kv_heads'],a['qk_head_dim'],a['v_head_dim'])
        cases = []
        if mid != IDS[2]:
            result = c.qkv(D,*args,gate_width=shapes.get('G',[0])[0])
            add_matrix_layout(result,shapes,1,0)
            cases.append(('qkv_projection',None,result))
            for B in manifest['B']:
                result = c.ffn(D,f['intermediate_size'],B)
                add_matrix_layout(result,f['matrices'],B,1)
                cases.append(('ffn_or_moe',B,result))
        for mode in ['prefill','decode']:
            for L in manifest['L'] if mid != IDS[2] else manifest['mimo_L']:
                result = c.attention(*args,L,mode)
                add_attention_layout(result,a,L,mode)
                cases.append(('attention_'+mode,L,result))
        for row, parameter, result in cases:
            records.append({'case_id': f'{mid}/{row}/{parameter if parameter else "one_token"}',
                            'model_id': mid,'row': row,'B' if row=='ffn_or_moe' else 'L': parameter,
                            'model_revision': m['identity']['revision'],
                            'selected_layer': manifest['models'][mid]['selected_layer'],
                            'shared_reference_id': contract['reference_id'], 'result': result})
    source_paths.append('literature/02_ministral3_8b/raw/params.json')
    for path in sorted(set(source_paths)):
        manifest['source_files_sha256'][path] = sha(path)
    # One explicit mapping contrast: persist one KV copy per query head.
    ref = next(r['result'] for r in records if r['case_id']==f'{IDS[1]}/attention_decode/1024')
    g = models[IDS[1]]['attention']['queries_per_kv_head']
    contrast = {'case': f'{IDS[1]}/attention_decode/1024',
                'choice': 'persist one KV copy per query head instead of one per KV head',
                'main_reference_replaced': False, 'copy_multiplier': g,
                'reference': {b: ref[b] for b in ['ports','operator']},
                'replicated': {b: c.demand(ref[b]['Q_S'],ref[b]['Q_R']*g,ref[b]['tile_evaluations']) for b in ['ports','operator']},
                'reference_capacity_bytes': ref['capacity']['valid_resident_bytes'],
                'replicated_capacity_bytes': ref['capacity']['valid_resident_bytes']*g,
                'interpretation': 'same input receiver demand and evaluation calls, more writes/state; no parallelism or time claim'}
    return manifest, {'schema_version':'1.0','cases':records,'minimal_mapping_contrast':contrast}


def exact_text(x):
    return 'infinity' if x == 'infinity' else str(x)


def tex_num(x):
    if x == 'infinity': return r'\infty'
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else rf'\frac{{{x.numerator}}}{{{x.denominator}}}'


def preview(data, boundary):
    lines = [r'\begin{tabular}{@{}lll@{}}\toprule',
             r'Workload & Ministral 3 8B (2512) & Qwen3.6-35B-A3B\\\midrule']
    for row,label in zip(ROWS,LABELS):
        cells=[]
        for mid in IDS[:2]:
            values=[r['result'][boundary]['RI'] for r in data['cases'] if r['model_id']==mid and r['row']==row]
            cells.append('$'+r',\;'.join(tex_num(v) for v in values)+'$')
        lines.append(label+' & '+' & '.join(cells)+r'\\[4pt]')
    return '\n'.join(lines+[r'\bottomrule\end{tabular}',''])


def csv_data(data):
    out=io.StringIO(); w=csv.writer(out,lineterminator='\n')
    w.writerow(['case_id','component','boundary','Q_S_Byte_exact','Q_R_Byte_exact','RI_exact','tile_evaluations','final_valid_resident_Byte','allocated_tile_Byte'])
    for record in data['cases']:
        result=record['result']
        for component,p in [('total',result),*result['parts'].items()]:
            cap=p.get('capacity',p.get('layout'))
            for boundary in ['ports','operator']:
                d=p[boundary]
                w.writerow([record['case_id'],component,boundary,*[exact_text(d[k]) for k in ['Q_S','Q_R','RI']],
                            d['tile_evaluations'],cap['valid_resident_bytes'],cap['allocated_tile_bytes']])
    return out.getvalue()


def outputs():
    config,data=make()
    files={'data/config.json':json.dumps(config,ensure_ascii=False,indent=2)+'\n',
           'data/results.json':json.dumps(c.encode(data),ensure_ascii=False,indent=2)+'\n',
           'data/results.csv':csv_data(data)}
    for b in ['ports','operator']:
        files[f'tex/preview_{b}.generated.tex']=preview(data,b)
    md=['# Step 3 两模型四行预览','',
        '精确 RI；FFN 顺序 B=8,64,512，Attention 顺序 L=1024,16384,131072。QKV 为一个 token。','']
    for b in ['ports','operator']:
        md += [f'## {b}（'+('主口径' if b=='ports' else '对照口径')+'）','',
               '| Workload | Ministral 3 8B (2512) | Qwen3.6-35B-A3B |','|---|---|---|']
        for row,label in zip(ROWS,LABELS):
            values=[', '.join(exact_text(r['result'][b]['RI']) for r in data['cases'] if r['model_id']==mid and r['row']==row) for mid in IDS[:2]]
            md.append('| '+label+' | '+' | '.join(values)+' |')
        md.append('')
    md += ['原始 Byte、精确分数、分项与容量见 [JSON](data/results.json) / [CSV](data/results.csv)。显示不先取整再求比值。','']
    files['PREVIEW.md']='\n'.join(md)
    return files


def main():
    p=argparse.ArgumentParser(); p.add_argument('--emit',action='store_true'); args=p.parse_args()
    files=outputs()
    for name,content in files.items():
        path=PILOT/name
        if args.emit:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content)
        else:
            assert path.read_text()==content, f'stale artifact: {name}; use --emit'
    print(f'PASS: 22 pilot cases; exact data and two-boundary previews; {len(files)} generated artifacts')


if __name__=='__main__': main()

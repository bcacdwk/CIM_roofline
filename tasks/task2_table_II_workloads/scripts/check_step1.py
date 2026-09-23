#!/usr/bin/env python3
"""Read-only Step 1 checks. Standard library; no model import, network or workload counting."""
from pathlib import Path
import ast
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return json.loads((ROOT / rel).read_text())

sources = read('data/sources.json')
registry = {s['id']: s for s in sources}
assert len(registry) == len(sources), 'duplicate source ID'
for s in sources:
    p = ROOT / s['local_path']
    assert p.is_file(), f'missing source: {p} (download exact URL in sources.json if locally ignored)'
    data = p.read_bytes()
    assert len(data) == s['bytes'], p
    assert hashlib.sha256(data).hexdigest() == s['sha256'], p
    assert s['acquired_at'] and s['revision'] and 'publication_date' in s
    if p.suffix == '.json':
        json.loads(data)
    elif p.suffix == '.py':
        ast.parse(data.decode('utf-8'))
    elif p.suffix == '.pdf':
        assert data.startswith(b'%PDF-'), p
    else:
        assert data.decode('utf-8').strip(), p

plan = read('data/study_plan.json')
assert plan['parameters']['B'] == [8, 64, 512]
assert plan['parameters']['L_tokens'] == [1024, 16384, 131072]
assert plan['parameters']['K_in_L_labels'] == 1024
assert plan['table_IIa']['columns_N_K'] == [[128, 128], [1024, 1024], [4096, 4096], [1024, 4096], [4096, 1024]]
assert [x['id'] for x in plan['table_IIa']['rows']] == ['weight_static', 'per_use_reloaded']
assert [x['id'] for x in plan['table_IIb']['rows']] == ['qkv_projection', 'ffn_or_moe', 'attention_prefill', 'attention_decode']
assert [x['sweep'] for x in plan['table_IIb']['rows']] == [None, 'B', 'L', 'L']
assert plan['actual_start_head'] == '81b7c332c20b9b5be6890256e9cf0d3edab12785'
assert plan['fixed_task_I']['resident_matrix_bytes'] == 16384

models = read('data/models.json')['models']
assert [m['id'] for m in models] == plan['table_IIb']['columns_model_ids']
assert len(models) == 6
for i, m in enumerate(models):
    local = m['local_material']
    raw = read(local['raw_config'])
    c = raw.get('text_config', raw)
    identity, b, a, f = (m[k] for k in ['identity', 'backbone', 'attention', 'ffn'])
    metadata = json.loads((ROOT / local['raw_config']).with_name('hf_metadata.json').read_text())
    assert metadata['sha'] == identity['revision']
    assert metadata['id'] == identity['official_repository']
    assert re.fullmatch('[0-9a-f]{40}', identity['revision'])
    cfg_source = next(s for s in sources if s['local_path'] == local['raw_config'])
    assert cfg_source['revision'] == identity['revision']
    assert all((ROOT / local[k]).is_file() for k in ['structure_card', 'raw_config', 'raw_model_card', 'implementation'])
    H, hq, hk, dq, dv = (c['hidden_size'], c['num_attention_heads'], c['num_key_value_heads'], c['head_dim'], c.get('v_head_dim', c['head_dim']))
    assert (b['hidden_size'], a['query_heads'], a['kv_heads'], a['qk_head_dim'], a['v_head_dim']) == (H, hq, hk, dq, dv)
    assert hq % hk == 0 and a['queries_per_kv_head'] == hq // hk
    s = a['weight_shapes_N_K']
    assert s['q_logical'] == [hq*dq, H] and s['k'] == [hk*dq, H] and s['v'] == [hk*dv, H]
    assert s['output'] == [H, hq*dv]
    if a['output_gate']:
        assert c['attn_output_gate'] is True
        assert s['q_and_gate_packed'] == [2*hq*dq, H]
        assert s['q_output_gate_logical'] == [hq*dv, H]
    if a['projection_layout'] == 'fused_qkv':
        assert s['qkv_packed'] == [hq*dq+hk*dq+hk*dv, H]
    assert a['kv_cache']['logical_key_layout'] == ['sequence_batch', hk, 'tokens', dq]
    assert a['kv_cache']['logical_value_layout'] == ['sequence_batch', hk, 'tokens', dv]
    n = c['num_hidden_layers']
    if 'layer_types' in c:
        assert len(c['layer_types']) == n
        full = [j for j,t in enumerate(c['layer_types']) if t == 'full_attention']
    elif 'hybrid_layer_pattern' in c:
        assert len(c['hybrid_layer_pattern']) == n
        full = [j for j,t in enumerate(c['hybrid_layer_pattern']) if t == 0]
        assert len(c['moe_layer_freq']) == n
    else:
        full = list(range(n))
    assert b['full_gqa_layer_indices_zero_based'] == full
    assert b['selected_layer_index_zero_based'] in full
    assert b['num_hidden_layers'] == n and sum(b['attention_layer_counts'].values()) == n
    dense_count = sum(t == 0 for t in c['moe_layer_freq']) if i == 5 else c.get('first_k_dense_replace', 0) if i in [3,4] else n if i < 2 else 0
    assert b['ffn_layer_counts'] == {'dense': dense_count, 'moe': n-dense_count}
    if i >= 2:
        assert b['selected_layer_index_zero_based'] >= dense_count
    F = c['intermediate_size'] if i < 2 else c['moe_intermediate_size']
    assert f['intermediate_size'] == F
    assert f['matrices'] == {'gate': [F,H], 'up': [F,H], 'down': [H,F]}
    counts = f['parameter_element_counts']
    assert counts['selected_ffn_or_single_expert'] == sum(x[0]*x[1] for x in f['matrices'].values())
    if i >= 2:
        E = c.get('num_experts', c.get('n_routed_experts'))
        assert (f['routed_expert_count'],f['routed_top_k']) == (E,c['num_experts_per_tok'])
        assert counts['all_routed_experts_in_one_layer'] == 3*H*F*E
        assert counts['active_routed_expert_set'] == 3*H*F*c['num_experts_per_tok']
        assert f['router_matrix'] == [E,H]
    assert m['context']['config_max_position_embeddings'] == c['max_position_embeddings']
    assert m['context']['L_tokens'] == plan['parameters']['L_tokens']
    if i == 4:
        assert m['context']['extension_for_128K']['rope_scaling']['factor']*32768 == 131072
        assert c['rope_scaling'] is None, 'do not alter original Ling config'
    else:
        assert max(plan['parameters']['L_tokens']) <= c['max_position_embeddings']
    assert all(m['precision'][k] is None for k in ['inference_activation_payload_dtype','inference_kv_payload_dtype','cim_reference_dtype'])
    if i == 1:
        native = json.loads((ROOT / local['raw_config']).with_name('params.json').read_text())
        for k,other in [('hidden_size','dim'),('num_hidden_layers','n_layers'),('intermediate_size','hidden_dim'),('num_attention_heads','n_heads'),('num_key_value_heads','n_kv_heads'),('head_dim','head_dim')]:
            assert c[k] == native[other]
    for field in ['attention','ffn','backbone','precision','context']:
        for evidence in m[field]['evidence']:
            assert evidence['source_id'] in registry
            if evidence['source_id'] == cfg_source['id']:
                value = raw
                for key in evidence['locator'].split('.'):
                    value = value[key]
    def check_refs(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if (k == 'source_id' or k.endswith('_source_id')) and v is not None:
                    assert v in registry, v
                check_refs(v)
        elif isinstance(value,list):
            for v in value: check_refs(v)
    check_refs(m)

# Only authored Markdown links: vendor READMEs retain their original remote assets/links.
link_count = 0
for p in [ROOT/'README.md', ROOT/'STEP1_REVIEW.zh.md', ROOT/'literature/00_shared/README.md', *ROOT.glob('literature/*/STRUCTURE.zh.md')]:
    for link in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        if '://' in link or link.startswith('#'):
            continue
        path = link.split('#')[0]
        assert (p.parent/path).exists(), f'broken local link in {p}: {path}'
        link_count += 1
print(json.dumps({'status':'PASS','models':len(models),'raw_sources_verified':len(sources),'authored_local_links_checked':link_count,'config_and_matrix_consistency':'PASS','scenario_workload_computation':'not performed'},ensure_ascii=False))

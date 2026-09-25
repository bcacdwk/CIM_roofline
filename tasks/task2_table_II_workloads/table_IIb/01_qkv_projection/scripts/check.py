#!/usr/bin/env python3
"""Independent raw-config + real-tile audit. No production module is imported.

Inputs are read from fixed raw config, not generate.py/config.json dimensions.
Each tile contributes its input interval and effective resident rectangle.
Operator inputs are a union of (token identity, element index), so sharing is
checked without the production subtraction formula. No model code is executed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
SOURCE_DIRS=['01_qwen35_2b','02_ministral3_8b','03_qwen36_35b_a3b','04_hy3_295b','05_ling_1t','06_mimo_v25_pro']
IDS=['qwen35_2b','ministral3_8b_2512','qwen36_35b_a3b','hy3_295b','ling_1t','mimo_v25_pro']
LAYERS=[3,0,3,1,4,7]
IMPL=['00_shared/raw/transformers/modeling_qwen3_5.py','00_shared/raw/transformers/modeling_ministral3.py',
      '00_shared/raw/transformers/modeling_qwen3_5_moe.py','00_shared/raw/transformers/modeling_hy_v3.py',
      '05_ling_1t/raw/modeling_bailing_moe_v2.py','06_mimo_v25_pro/raw/modeling_mimo_v2.py']


def read(path): return json.loads((ROOT/path).read_text())
def sha(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def anchors(path, snippets):
    lines=(ROOT/path).read_text().splitlines(); out=[]
    for snippet in snippets:
        loc=[i for i,line in enumerate(lines,1) if snippet in line]
        assert loc, (path,snippet)
        out.append({'path':path,'lines':loc,'literal_anchor':snippet})
    return out


def raw_inputs():
    raw={}; audit=[]
    for mid, folder, impl, layer in zip(IDS,SOURCE_DIRS,IMPL,LAYERS):
        path=f'literature/{folder}/raw/config.json'; native=read(path); cfg=native.get('text_config',native)
        D=cfg['hidden_size']; q=cfg['num_attention_heads']; h=cfg['num_key_value_heads']; d=cfg['head_dim']
        v=cfg.get('v_head_dim',d); gate=mid in ['qwen35_2b','qwen36_35b_a3b']
        shape={'Q':[q*d,D]}
        if gate: shape['G']=[q*d,D]
        shape.update(K=[h*d,D],V=[h*v,D])
        snippets=[]; packed={}
        fields=['hidden_size','num_attention_heads','num_key_value_heads','head_dim']
        if gate:
            assert cfg['layer_types'][layer]=='full_attention' and cfg['attn_output_gate'] is True
            fields+=['attn_output_gate','layer_types']
            snippets=['config.hidden_size, config.num_attention_heads * self.head_dim * 2',
                      'self.q_proj(hidden_states).view(*input_shape, -1, self.head_dim * 2), 2, dim=-1',
                      'attn_output = attn_output * torch.sigmoid(gate)']
            qrows={2*i*d+j for i in range(q) for j in range(d)}
            grows={2*i*d+d+j for i in range(q) for j in range(d)}
            assert not qrows & grows and qrows | grows==set(range(2*q*d))
            packed={'kind':'Q/G interleaved by head', 'packed_N_K':[2*q*d,D],
                    'Q_rows':len(qrows),'G_rows':len(grows),'disjoint_and_complete':True,
                    'Q_row_rule':'2*head*d + channel', 'G_row_rule':'2*head*d + d + channel'}
        elif mid=='ministral3_8b_2512':
            params=read(f'literature/{folder}/raw/params.json')
            for key,other in [('hidden_size','dim'),('num_attention_heads','n_heads'),('num_key_value_heads','n_kv_heads'),('head_dim','head_dim')]:
                assert cfg[key]==params[other]
            assert params['v_head_dim'] is None and v==d==128
            assert cfg['sliding_window'] is None
            fields+=['sliding_window']
            snippets=['self.q_proj = nn.Linear(config.hidden_size, config.num_attention_heads * self.head_dim, bias=False)',
                      'self.k_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=False)',
                      'self.v_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=False)']
        elif mid=='hy3_295b':
            assert d==128 and q==64 and D==4096 and cfg['first_k_dense_replace']==layer
            fields+=['first_k_dense_replace']
            snippets=['self.head_dim = getattr(config, "head_dim", config.hidden_size // config.num_attention_heads)',
                      'config.hidden_size, config.num_attention_heads * self.head_dim, bias=config.attention_bias',
                      'config.hidden_size, config.num_key_value_heads * self.head_dim, bias=config.attention_bias']
        elif mid=='ling_1t':
            assert cfg['first_k_dense_replace']==layer and not cfg['using_split_qkv_in_self_attention']
            assert cfg['use_qkv_bias'] is False
            fields+=['first_k_dense_replace','using_split_qkv_in_self_attention','use_qkv_bias']
            snippets=['self.head_dim = config.head_dim or self.hidden_size // self.num_heads',
                      '(self.num_heads + 2 * self.num_key_value_heads) * self.head_dim',
                      '[self.num_heads, self.num_key_value_heads, self.num_key_value_heads], dim=-2']
        else:
            assert cfg['hybrid_layer_pattern'][layer]==0
            assert cfg['attention_projection_layout']=='fused_qkv'
            assert (d,v)==(192,128) and cfg['add_full_attention_sink_bias'] is False
            fields+=['v_head_dim','hybrid_layer_pattern','attention_projection_layout','add_full_attention_sink_bias']
            snippets=['self.v_head_dim = getattr(config, "v_head_dim", self.head_dim)',
                      'self.q_size = self.num_attention_heads * self.head_dim',
                      'self.k_size = self.num_key_value_heads * self.head_dim',
                      'self.v_size = self.num_key_value_heads * self.v_head_dim',
                      'self.q_size + self.k_size + self.v_size',
                      'qkv_states.split([self.q_size, self.k_size, self.v_size], dim=-1)',
                      'is_swa_layer = config.hybrid_layer_pattern[layer_idx] == 1']
        if mid in ['ling_1t','mimo_v25_pro']:
            ranges={}; offset=0; rows=set()
            for name,(n,k) in shape.items():
                part=set(range(offset,offset+n)); assert not part & rows
                rows|=part; ranges[name]=[offset,offset+n]; offset+=n
            assert rows==set(range(offset))
            packed={'kind':'fused Q/K/V contiguous semantic slices','packed_N_K':[offset,D],
                    'half_open_row_ranges':ranges,'disjoint_and_complete':True}
        impl_path='literature/'+impl
        metadata_path=f'literature/{folder}/raw/hf_metadata.json'
        raw[mid]={'D':D,'Hq':q,'Hkv':h,'dqk':d,'dv':v,'output_gate':gate,
                  'semantic_shapes_N_K':shape,'selected_layer':layer,'revision':read(metadata_path)['sha']}
        prefix='text_config.' if 'text_config' in native else ''
        audit.append({'model_id':mid,'raw_dimensions':raw[mid],
                      'config_path':path,'config_locators':[prefix+f for f in fields],
                      'config_value_evidence':{prefix+f:cfg[f] for f in fields},
                      'metadata_path':metadata_path,'metadata_revision_locator':'sha',
                      'implementation_anchors':anchors(impl_path,snippets),'native_packing_audit':packed,
                      'finding':'PASS: raw config and static implementation agree with selected-layer dimensions'})
    return raw,audit


def matrix(name,n,k):
    hist=Counter(); inputs=0; valid=0; calls=0
    out_widths=[]; in_widths=[]
    for col in range(0,k,128): in_widths.append(len(range(col,min(col+128,k))))
    for row in range(0,n,128):
        height=len(range(row,min(row+128,n))); out_widths.append(height)
        for col in range(0,k,128):
            width=len(range(col,min(col+128,k)))
            inputs+=width; valid+=height*width; calls+=1; hist[(height,width)]+=1
    def axis(ws):
        tails=[w for w in ws if w!=128]
        assert len(tails)<=1
        return {'full_128_blocks':ws.count(128),'tail_valid_elements':tails[0] if tails else 0,'blocks':len(ws)}
    source_ids={('token_0_x',i) for i in range(k)}
    return {'ports':{'Q_S':inputs,'Q_R':0,'RI':'infinity','tile_evaluations':calls},
            'operator':{'Q_S':len(source_ids),'Q_R':0,'RI':'infinity','tile_evaluations':None},
            'tile_layout':{'output_block_sizes':out_widths,'input_block_sizes':in_widths,'resident_tiles':calls,'load_events':0},
            'layout':{'matrix_N_K_per_copy':[n,k],'copies':1,'output_axis':axis(out_widths),'input_axis':axis(in_widths),
                      'resident_tiles':calls,'valid_resident_bytes':valid,'allocated_tile_bytes':sum(16384 for _ in range(calls))},
            'window':{'input_vectors':1,'full_weight_loads':0}}, source_ids, hist


def oracle(d):
    parts={}; sources=set(); op_standalone=0; hist={}
    for name,(n,k) in d['semantic_shapes_N_K'].items():
        p,ids,calls=matrix(name,n,k); parts[name]=p; sources.update(ids); op_standalone+=len(ids)
        hist[name]=[{'valid_N_K':list(shape),'calls':count} for shape,count in sorted(calls.items())]
    out={'parts':parts}
    out['ports']={'Q_S':sum(p['ports']['Q_S'] for p in parts.values()),'Q_R':0,'RI':'infinity',
                  'tile_evaluations':sum(p['ports']['tile_evaluations'] for p in parts.values())}
    out['operator']={'Q_S':len(sources),'Q_R':0,'RI':'infinity','tile_evaluations':None}
    out['operator_shared_input_overlap_removed']=op_standalone-len(sources)
    out['capacity']={key:sum(p['layout'][key] for p in parts.values())
                     for key in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']}
    out['capacity']['meaning']='final state capacity; distinct from cumulative Q_R and from physical encoded capacity'
    return out,hist


def compare_all(got,expected,path=''):
    """Validate every key and every leaf, also null/string/array/layout fields."""
    if isinstance(expected,dict):
        assert isinstance(got,dict) and set(got)==set(expected),(path,'keys')
        return sum(compare_all(got[k],v,path+'/'+k) for k,v in expected.items())
    if isinstance(expected,list):
        assert isinstance(got,list) and len(got)==len(expected),(path,'list length')
        return sum(compare_all(a,b,f'{path}/{i}') for i,(a,b) in enumerate(zip(got,expected)))
    assert got==expected and type(got)==type(expected),(path,got,expected)
    return 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    config=json.loads((HERE/'data/config.json').read_text())
    data=json.loads((HERE/'data/results.json').read_text())
    raw,audit=raw_inputs(); models={m['id']:m for m in read('data/models.json')['models']}
    registry={s['local_path']:s for s in read('data/sources.json')}
    hashes=[]
    for path,digest in config['source_files_sha256'].items():
        assert sha(path)==digest,path
        if path in registry: assert registry[path]['sha256']==digest,path
        hashes.append({'path':path,'sha256':digest,'registered_original':path in registry,'pass':True})
    assert [r['model_id'] for r in data['cases']]==IDS
    assert [r['model_id'] for r in data['cases']]==read('data/study_plan.json')['table_IIb']['columns_model_ids']
    results=[]
    for r in data['cases']:
        mid=r['model_id']; d=raw[mid]; m=models[mid]; a=m['attention']
        assert r['selected_layer']==d['selected_layer']==m['backbone']['selected_layer_index_zero_based']
        assert r['model_revision']==d['revision']==m['identity']['revision']
        assert r['case_id']==mid+'/qkv_projection/one_token' and r['row']=='qkv_projection' and r['L'] is None
        assert r['shared_reference_id']==config['shared_reference_id']=='WS128-INT8-semantic-banks-v1'
        assert d['D']==m['backbone']['hidden_size']
        assert [d['Hq'],d['Hkv'],d['dqk'],d['dv']]==[a['query_heads'],a['kv_heads'],a['qk_head_dim'],a['v_head_dim']]
        assert d['semantic_shapes_N_K']==config['models'][mid]['semantic_shapes_N_K']
        packing=next(item['native_packing_audit'] for item in audit if item['model_id']==mid)
        if packing:
            packed_key='q_and_gate_packed' if d['output_gate'] else 'qkv_packed'
            assert packing['packed_N_K']==a['weight_shapes_N_K'][packed_key]
        for role,key in [('Q','q_logical'),('G','q_output_gate_logical'),('K','k'),('V','v')]:
            if role in d['semantic_shapes_N_K']: assert d['semantic_shapes_N_K'][role]==a['weight_shapes_N_K'][key]
        expected,hist=oracle(d); leaves=compare_all(r['result'],expected)
        results.append({'case_id':r['case_id'],'pass':True,'compared_result_leaf_count':leaves,
                        'independent_result':expected,'valid_N_K_call_histograms':hist})
    pilot=read('table_IIb/pilot/data/results.json'); lookup={r['case_id']:r for r in pilot['cases']}
    regression=[]
    for r in data['cases']:
        if r['case_id'] not in lookup: continue
        leaves=compare_all(r,lookup[r['case_id']])
        regression.append({'case_id':r['case_id'],'pass':True,'every_leaf_equal':True,
                           'compared_leaf_count':leaves,'baseline':'table_IIb/pilot/data/results.json'})
    assert len(regression)==2
    checks={'status':'PASS','main_case_count':6,'semantic_matrix_count':sum(len(r['result']['parts']) for r in data['cases']),
            'method':'Raw pinned config and inspected implementation; explicit real tile rectangles; union of input identities for operator; no production counting import.',
            'source_hash_checks':hashes,'source_audit':audit,'main_checks':results,
            'pilot_regressions':regression,'pilot_results_sha256':sha('table_IIb/pilot/data/results.json'),
            'shared_method_corrections_required':False,
            'scope_guards':['one token','pre-resident weights, zero window writes','Q/G/K/V semantic banks','no W_O or KV writes','no per-head partition inside a projection semantic matrix','no hardware timing']}
    content=json.dumps(checks,ensure_ascii=False,indent=2)+'\n'
    dest=HERE/'data/checks.json'
    if args.emit:dest.write_text(content)
    else:assert dest.read_text()==content,'stale independent checks'
    print(f"PASS: 6 raw-config/tile cases, {checks['semantic_matrix_count']} matrices, 2 entire-case pilot regressions, {len(hashes)} source hashes")


if __name__=='__main__':main()

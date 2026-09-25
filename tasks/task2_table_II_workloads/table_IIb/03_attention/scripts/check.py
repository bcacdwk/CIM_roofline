#!/usr/bin/env python3
"""Independent raw-config + tile-lifetime oracle; never imports production code."""
import argparse, hashlib, json, sys
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[1]; ROOT=HERE.parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def encode(v):
    if isinstance(v,F):return v.numerator if v.denominator==1 else dict(numerator=v.numerator,denominator=v.denominator)
    if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [encode(x) for x in v]
    return v
def decode(v):
    if isinstance(v,dict):
        if set(v)=={'numerator','denominator'}:return F(v['numerator'],v['denominator'])
        return {k:decode(x) for k,x in v.items()}
    if isinstance(v,list):return [decode(x) for x in v]
    return v
def slices(n):return [(s,min(n,s+128)) for s in range(0,n,128)]
def demand(s,r,c=None):return dict(Q_S=s,Q_R=r,RI=F(s,r) if r else 'undefined_empty',tile_evaluations=c)
def layout(n,k,h):
    hist=Counter((b-a,d-c) for a,b in slices(n) for c,d in slices(k))
    axis=lambda x: dict(full_128_blocks=sum(b-a==128 for a,b in slices(x)),tail_valid_elements=next((b-a for a,b in slices(x) if b-a<128),0),blocks=len(slices(x)))
    return dict(matrix_N_K_per_copy=[n,k],copies=h,output_axis=axis(n),input_axis=axis(k),resident_tiles=h*sum(hist.values()),valid_resident_bytes=h*sum(nw*kw*v for (nw,kw),v in hist.items()),allocated_tile_bytes=h*sum(hist.values())*16384,valid_tile_shape_histogram=[dict(valid_N_K=list(sh),tiles=h*v) for sh,v in sorted(hist.items())])
def oracle(q,h,dq,dv,L,mode):
    # Invert prefix summation: walk absolute sequence tiles. A tile spends one
    # evaluation at each partial size then remains full for later prefixes.
    life=Counter()
    for begin,end in slices(L):
        if mode=='decode':life[end-begin]+=1
        else:
            for stop in range(begin+1,end):life[stop-begin]+=1
            life[end-begin]+=L-end+1
    first=0 if mode=='prefill' else L-1
    parts={}
    for name,n,k,dim in [('QK',L,dq,dq),('AV',dv,L,dv)]:
        hist=Counter()
        for start,stop in slices(dim):
            for sw,uses in life.items():hist[(sw,stop-start) if name=='QK' else (stop-start,sw)]+=q*uses
        # Count actual append slices. No cumulative capacity as write proxy.
        writes=events=0
        for token in range(first,L):
            for start,stop in slices(dim):writes+=h*(stop-start);events+=h
        op=0
        for token in range(first,L):op+=q*(dq if name=='QK' else token+1)
        p=dict(ports=demand(sum(kw*v for (nw,kw),v in hist.items()),writes,sum(hist.values())),operator=demand(op,writes),layout=layout(n,k,h),initial_layout=layout(first,dq,h) if name=='QK' else layout(dv,first,h),append=dict(valid_slice_N_K_per_head_per_token=[[1,b-a] if name=='QK' else [b-a,1] for a,b in slices(dim)],logical_slice_write_events=events,per_token_logical_slice_write_events=h*len(slices(dim)),valid_write_bytes_per_token=h*sum(b-a for a,b in slices(dim))),valid_N_K_call_histogram=[dict(valid_N_K=list(sh),calls=v) for sh,v in sorted(hist.items())],valid_input_width_to_calls={str(kw):sum(v for (nw,k),v in hist.items() if k==kw) for kw in sorted({k for n,k in hist})})
        parts[name]=p
    out=dict(parts=parts,initial_KV_tokens=first,final_KV_tokens=L,initial_valid_resident_bytes=sum(p['initial_layout']['valid_resident_bytes'] for p in parts.values()),appended_tokens=L-first,kv_copies_per_head=1,group_size=q//h,operator_shared_input_overlap_removed=0,append_shape_per_kv_head=dict(K=[1,dq],V=[dv,1]),active_layout_at_L=dict(K_matrix_N_K=[L,dq],V_matrix_N_K=[dv,L]))
    for boundary in ['ports','operator']:
        out[boundary]=demand(sum(p[boundary]['Q_S'] for p in parts.values()),sum(p[boundary]['Q_R'] for p in parts.values()),sum(p[boundary]['tile_evaluations'] for p in parts.values()) if boundary=='ports' else None)
    for field,lf in [('capacity','layout'),('initial_capacity','initial_layout')]:out[field]={k:sum(p[lf][k] for p in parts.values()) for k in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']}
    return out

def subset(actual,expected,path=''):
    if isinstance(expected,dict):
        for k,v in expected.items():assert k in actual,(path,k);subset(actual[k],v,path+'/'+k)
    else:assert actual==expected,(path,actual,expected)

def explicit_decode(q,h,dq,dv,L):
    # Small boundary cases: service identifiers include the query and KV head.
    parts={}
    group=Counter(qhead//(q//h) for qhead in range(q));assert set(group.values())=={q//h}
    for name,n,k,dim in [('QK',L,dq,dq),('AV',dv,L,dv)]:
        calls=set();inputs=set();op=set();writes=set()
        for qhead in range(q):
            kv=qhead//(q//h)
            for col in range(k):op.add((qhead,col))
            for a,b in slices(n):
                for c,d in slices(k):
                    calls.add((qhead,kv,a,c))
                    for col in range(c,d):inputs.add((qhead,kv,a,c,col))
        for kv in range(h):
            for x in range(dim):writes.add((kv,L-1,x) if name=='QK' else (kv,x,L-1))
        parts[name]={b:demand(s,len(writes),len(calls) if b=='ports' else None) for b,s in [('ports',len(inputs)),('operator',len(op))]}
    return parts

def audit(cfg):
    raw={}; rows=[]; models={m['id']:m for m in read('data/models.json')['models']}
    registry={s['local_path']:s for s in read('data/sources.json')}
    for p,digest in cfg['source_files_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,p
        if p in registry:assert registry[p]['sha256']==digest,p
    for mid,m in models.items():
        lm=m['local_material']; native=read(lm['raw_config']); c=native.get('text_config',native); a=m['attention']; layer=m['backbone']['selected_layer_index_zero_based']
        q,h,dq,dv=c['num_attention_heads'],c['num_key_value_heads'],c['head_dim'],c.get('v_head_dim',c['head_dim'])
        assert [q,h,dq,dv]==[a[k] for k in ['query_heads','kv_heads','qk_head_dim','v_head_dim']]
        assert h*(q//h)==q and a['queries_per_kv_head']==q//h
        meta=read(str(Path(lm['raw_config']).with_name('hf_metadata.json')))
        assert meta['sha']==m['identity']['revision']==cfg['models'][mid]['identity']['revision']
        assert cfg['models'][mid]['selected_layer']==layer
        text=(ROOT/lm['implementation']).read_text(); anchors=['repeat_kv','self.is_causal = True']
        if mid.startswith('qwen'):
            assert c['layer_types'][layer]=='full_attention' and layer==3
            anchors += ['config.num_key_value_heads * self.head_dim','key_states, value_states = past_key_values.update','self.q_proj(hidden_states).view(*input_shape, -1, self.head_dim * 2), 2, dim=-1']
        elif mid=='ministral3_8b_2512':
            p=read('literature/02_ministral3_8b/raw/params.json')
            assert c['sliding_window'] is None and layer==0 and p['v_head_dim'] is None
            assert [p[k] for k in ['n_heads','n_kv_heads','head_dim']]==[q,h,dq]
            anchors += ['self.v_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=False)','key_states, value_states = past_key_values.update']
        elif mid=='hy3_295b':
            assert layer==1
            anchors += ['config.num_key_value_heads * self.head_dim','key_states, value_states = past_key_values.update']
        elif mid=='ling_1t':
            assert layer==4 and c['max_position_embeddings']==32768 and c['rope_scaling'] is None
            anchors += ['(self.num_heads + 2 * self.num_key_value_heads) * self.head_dim','key_states, value_states = past_key_value.update','key_states = repeat_kv(key_states, self.num_key_value_groups)']
            card=(ROOT/lm['raw_model_card']).read_text(); assert all(s in card for s in ['"factor": 4.0','"original_max_position_embeddings": 32768','"type": "yarn"','--max-model-len'])
            assert a['qk_head_dim']==128
        else:
            assert mid=='mimo_v25_pro' and layer==7 and c['hybrid_layer_pattern'][layer]==0
            assert (dq,dv)==(192,128) and c['attention_value_scale']==0.612 and c['add_full_attention_sink_bias'] is False
            anchors += ['self.v_head_dim = getattr(config, "v_head_dim", self.head_dim)','self.sliding_window = getattr(config, "sliding_window", None) if is_swa else None','value_states = value_states * self.v_scale','key_states, value_states = past_key_values.update']
        evidence=[]
        for snippet in anchors:
            lines=[i for i,line in enumerate(text.splitlines(),1) if snippet in line];assert lines,(mid,snippet)
            evidence.append(dict(path=lm['implementation'],lines=lines,literal_anchor=snippet))
        assert a['kv_cache']['logical_key_layout']==['sequence_batch',h,'tokens',dq]
        assert a['kv_cache']['logical_value_layout']==['sequence_batch',h,'tokens',dv]
        raw[mid]=(q,h,dq,dv)
        rows.append(dict(model_id=mid,selected_layer=layer,revision=meta['sha'],raw_dimensions=dict(Hq=q,Hkv=h,dQK=dq,dV=dv),implementation_anchors=evidence,pass_check=True))
    return raw,rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    cfg=json.loads((HERE/'data/config.json').read_text()); data=decode(json.loads((HERE/'data/results.json').read_text())); raw,audits=audit(cfg)
    assert len(data['cases'])==36 and len({r['case_id'] for r in data['cases']})==36
    assert Counter(r['model_id'] for r in data['cases'])==Counter({mid:6 for mid in raw})
    assert {(r['model_id'],r['row'],r['L']) for r in data['cases']}=={(mid,row,L) for mid in raw for row in ['attention_prefill','attention_decode'] for L in [1024,16384,131072]}
    mainchecks=[];telescopes=[];boundarychecks=[]
    for r in data['cases']:
        dims=raw[r['model_id']];mode=r['row'].removeprefix('attention_');L=r['L']
        assert r['model_revision']==cfg['models'][r['model_id']]['identity']['revision']
        assert r['selected_layer']==cfg['models'][r['model_id']]['selected_layer']
        assert r['shared_reference_id']=='WS128-INT8-semantic-banks-v1'
        assert [r['configuration'][k] for k in ['query_heads','kv_heads','qk_head_dim','v_head_dim']]==list(dims)
        o=oracle(*dims,L,mode);subset(r['result'],o,r['case_id'])
        mainchecks.append(dict(case_id=r['case_id'],pass_check=True,independent_result=o))
        if mode=='decode':
            p=oracle(*dims,L,'prefill'); prev=oracle(*dims,L-1,'prefill')
            for name in [None,'QK','AV']:
                x,y,z=[obj if name is None else obj['parts'][name] for obj in [p,prev,o]]
                for b in ['ports','operator']:
                    for key in ['Q_S','Q_R']+(['tile_evaluations'] if b=='ports' else []):assert x[b][key]-y[b][key]==z[b][key]
            telescopes.append(dict(case_id=r['case_id'],pass_check=True))
    for mid,dims in raw.items():
        for L in [1,127,128,129]:
            o=oracle(*dims,L,'decode'); e=explicit_decode(*dims,L)
            for name in ['QK','AV']:subset(o['parts'][name],e[name])
            boundarychecks.append(dict(model_id=mid,L=L,pass_check=True,explicit_decode=e))
    pilot=decode(read('table_IIb/pilot/data/results.json')); candidates={r['case_id']:r for r in data['cases']}; regress=[]
    for p in pilot['cases']:
        if not p['row'].startswith('attention_'):continue
        subset(candidates[p['case_id']],p,p['case_id'])
        regress.append(dict(case_id=p['case_id'],all_existing_semantic_fields_equal=True))
    assert len(regress)==14
    report=dict(schema_version='step4-attention-check-v1',status='PASS',oracle='raw config + absolute sequence-tile lifetime inversion; no production imports or formula calls',large_case_memory='O(128) sequence width histogram + resident tile grid; never LxL or per-call event lists',source_audit=audits,main_case_count=36,main_checks=mainchecks,explicit_boundary_count=24,explicit_boundary_checks=boundarychecks,primary_prefix_deltas=telescopes,pilot_regression_count=14,pilot_regression=regress,pilot_results_sha256=hashlib.sha256((ROOT/'table_IIb/pilot/data/results.json').read_bytes()).hexdigest())
    target=HERE/'data/checks.json';s=json.dumps(encode(report),ensure_ascii=False,indent=2)+'\n'
    if args.emit:target.write_text(s)
    else:assert target.read_text()==s,'stale checks.json'
    print('PASS: 36 independent cases; 24 explicit boundaries; 18 prefix deltas; 14 pilot regressions; 6 raw source audits')
if __name__=='__main__':main()

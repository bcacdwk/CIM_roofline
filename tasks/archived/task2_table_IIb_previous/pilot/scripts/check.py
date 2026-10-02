#!/usr/bin/env python3
"""Independent expectations from raw configs, matrix slices and tile lifetimes.

No counting.py helpers are used in the oracle. The shared calculator is imported
only in main() to obtain candidate boundary results. No model code is executed.
Large attention uses O(L) scalar work / O(128) shape histograms, never L x L data.
"""
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

PILOT=Path(__file__).resolve().parents[1]
ROOT=PILOT.parents[1]
IDS=['ministral3_8b_2512','qwen36_35b_a3b','mimo_v25_pro']


def read(path): return json.loads((ROOT/path).read_text())


def encode(x):
    if isinstance(x,F): return x.numerator if x.denominator==1 else {'numerator':x.numerator,'denominator':x.denominator}
    if isinstance(x,dict): return {k:encode(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [encode(v) for v in x]
    return x


def decode(x):
    if isinstance(x,dict):
        if set(x)=={'numerator','denominator'}: return F(x['numerator'],x['denominator'])
        return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list): return [decode(v) for v in x]
    return x


def demand(qs,qr,calls=None):
    return dict(Q_S=qs,Q_R=qr,RI=F(qs,qr) if qr else ('infinity' if qs else 'undefined_empty'),tile_evaluations=calls)


def slices(n):
    return [(start,min(start+128,n)) for start in range(0,n,128)]


def matrix(n,k,uses,loads):
    shapes=Counter((r1-r0,c1-c0) for r0,r1 in slices(n) for c0,c1 in slices(k))
    writes=sum(nv*kv*count for (nv,kv),count in shapes.items())*loads
    return {'ports':demand(sum(kv*count for (nv,kv),count in shapes.items())*uses,writes,sum(shapes.values())*uses),
            'operator':demand(sum(b-a for a,b in slices(k))*uses,writes),
            'valid_resident_bytes':sum(nv*kv*count for (nv,kv),count in shapes.items()),
            'resident_tiles':sum(shapes.values()),'call_histogram':{shape:count*uses for shape,count in shapes.items()}}


def aggregate(parts,op_input=None):
    out={'parts':parts}
    for boundary in ['ports','operator']:
        qs=sum(p[boundary]['Q_S'] for p in parts.values())
        if boundary=='operator' and op_input is not None: qs=op_input
        out[boundary]=demand(qs,sum(p[boundary]['Q_R'] for p in parts.values()),
                            sum(p[boundary]['tile_evaluations'] for p in parts.values()) if boundary=='ports' else None)
    return out


def bank_workload(shapes,uses,loads,sources):
    parts={name:matrix(n,k,uses,loads) for name,(n,k) in shapes.items()}
    # Explicit (phase/source, vector) identities share x across branches, not z.
    entries={}
    for name,(_,k) in shapes.items():
        for vector in range(uses):
            key=(sources[name],vector)
            assert key not in entries or entries[key]==k
            entries[key]=k
    return aggregate(parts,sum(entries.values()))


def attention(q,h,dq,dv,L,mode):
    # Invert the prefix loop: each absolute sequence tile has a lifetime.
    # A partial width occurs once; after becoming full it serves every remaining
    # prefix. This is independent of the production sum-ceil/triangle formulas.
    seq_lifetimes=Counter()
    for start,end in slices(L):
        if mode=='decode': seq_lifetimes[end-start]+=1
        else:
            for partial_end in range(start+1,end): seq_lifetimes[partial_end-start]+=1
            seq_lifetimes[end-start]+=L-end+1
    hist={'QK':Counter(),'AV':Counter()}
    for seq_width,lifetime in seq_lifetimes.items():
        for a,b in slices(dq): hist['QK'][(seq_width,b-a)]+=q*lifetime
        for a,b in slices(dv): hist['AV'][(b-a,seq_width)]+=q*lifetime
    prefixes=range(1,L+1) if mode=='prefill' else [L]
    op_qk=op_av=0
    for prefix in prefixes:
        op_qk+=q*dq; op_av+=q*prefix
    append_tokens=range(L) if mode=='prefill' else [L-1]
    writes={'QK':0,'AV':0}; events={'QK':0,'AV':0}
    for token in append_tokens:
        # Absolute token coordinates, only new 1 x k and n x 1 slices.
        for name,dim in [('QK',dq),('AV',dv)]:
            for a,b in slices(dim):
                writes[name]+=h*(b-a); events[name]+=h
    parts={}
    for name,n,k,op in [('QK',L,dq,op_qk),('AV',dv,L,op_av)]:
        resident=matrix(n,k,1,0)
        parts[name]={'ports':demand(sum(kw*count for (nw,kw),count in hist[name].items()),writes[name],sum(hist[name].values())),
                     'operator':demand(op,writes[name]),'call_histogram':dict(hist[name]),
                     'valid_resident_bytes':h*resident['valid_resident_bytes'],
                     'resident_tiles':h*resident['resident_tiles'],'append_slice_events':events[name]}
    return aggregate(parts)


def enum_decode(q,h,dq,dv,L):
    """Actual receiver/input identities for small real-head boundary cases."""
    parts={}; groups={}
    for qhead in range(q): groups[qhead]=qhead//(q//h)
    assert Counter(groups.values())==Counter({head:q//h for head in range(h)})
    for name,n,k in [('QK',L,dq),('AV',dv,L)]:
        inputs=set(); ops=set(); calls=set(); writes=set()
        for qhead,kvhead in groups.items():
            for input_index in range(k): ops.add((qhead,input_index))
            for row0,row1 in slices(n):
                for col0,col1 in slices(k):
                    calls.add((qhead,kvhead,row0,col0))
                    for col in range(col0,col1):
                        inputs.add((qhead,kvhead,row0,col0,col))
        for kvhead in range(h):
            if name=='QK':
                for col in range(dq): writes.add((kvhead,L-1,col))
            else:
                for row in range(dv): writes.add((kvhead,row,L-1))
        parts[name]={'ports':demand(len(inputs),len(writes),len(calls)),
                     'operator':demand(len(ops),len(writes))}
    return aggregate(parts)


def compare(candidate,oracle):
    for boundary in ['ports','operator']:
        assert candidate[boundary]==oracle[boundary],(boundary,candidate[boundary],oracle[boundary])
    for name,p in oracle['parts'].items():
        for boundary in ['ports','operator']:
            assert candidate['parts'][name][boundary]==p[boundary],(name,boundary)
        if 'layout' in candidate['parts'][name]:
            a=candidate['parts'][name]['layout']
            for key in ['valid_resident_bytes','resident_tiles']: assert a[key]==p[key],(name,key)
            assert a['allocated_tile_bytes']==p['resident_tiles']*16384
            if 'append' in candidate['parts'][name]:
                assert candidate['parts'][name]['append']['logical_slice_write_events']==p['append_slice_events']


def compact(oracle):
    result={b:oracle[b] for b in ['ports','operator']}
    result['parts']={}
    for name,p in oracle['parts'].items():
        item={k:v for k,v in p.items() if k!='call_histogram'}
        if 'call_histogram' in p:
            # Preserve actual valid input widths and service calls independently.
            h=Counter()
            for (n,k),count in p['call_histogram'].items(): h[k]+=count
            item['valid_input_width_to_calls']={str(k):count for k,count in sorted(h.items())}
            item['distinct_valid_N_K_shapes']=len(p['call_histogram'])
            item['valid_N_K_call_histogram']=[{'valid_N_K':[n,k],'calls':count}
                for (n,k),count in sorted(p['call_histogram'].items())]
        result['parts'][name]=item
    return result


def source_audit(config):
    models={m['id']:m for m in read('data/models.json')['models']}
    registry={s['local_path']:s for s in read('data/sources.json')}
    raw={}; audit=[]
    for path,digest in config['source_files_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
        if path in registry: assert registry[path]['sha256']==digest,path
    anchors={
        IDS[0]: ['self.q_proj = nn.Linear(config.hidden_size, config.num_attention_heads * self.head_dim, bias=False)',
                 'self.v_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=False)',
                 'key_states, value_states = past_key_values.update',
                 'self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))'],
        IDS[1]: ['config.hidden_size, config.num_attention_heads * self.head_dim * 2',
                 'self.q_proj(hidden_states).view(*input_shape, -1, self.head_dim * 2), 2, dim=-1',
                 'attn_output = attn_output * torch.sigmoid(gate)',
                 'key_states, value_states = past_key_values.update',
                 'self.num_experts, 2 * self.intermediate_dim, self.hidden_dim',
                 'self.num_experts, self.hidden_dim, self.intermediate_dim',
                 'gate, up = nn.functional.linear(current_state, self.gate_up_proj[expert_idx]).chunk(2, dim=-1)'],
        IDS[2]: ['self.v_head_dim = getattr(config, "v_head_dim", self.head_dim)',
                 'self.q_size + self.k_size + self.v_size',
                 'value_states = value_states * self.v_scale',
                 'key_states, value_states = past_key_values.update',
                 'is_swa_layer = config.hybrid_layer_pattern[layer_idx] == 1']}
    for mid in IDS:
        m=models[mid]; p=m['local_material']; native=read(p['raw_config']); cfg=native.get('text_config',native)
        a=m['attention']; layer=m['backbone']['selected_layer_index_zero_based']; D=cfg['hidden_size']
        q,h,dq,dv=cfg['num_attention_heads'],cfg['num_key_value_heads'],cfg['head_dim'],cfg.get('v_head_dim',cfg['head_dim'])
        assert [q,h,dq,dv]==[a['query_heads'],a['kv_heads'],a['qk_head_dim'],a['v_head_dim']]
        assert D==m['backbone']['hidden_size'] and config['models'][mid]['selected_layer']==layer
        for field,n in [('q_logical',q*dq),('k',h*dq),('v',h*dv)]: assert a['weight_shapes_N_K'][field]==[n,D]
        assert a['kv_cache']['logical_key_layout']==['sequence_batch',h,'tokens',dq]
        assert a['kv_cache']['logical_value_layout']==['sequence_batch',h,'tokens',dv]
        metadata=read(str(Path(p['raw_config']).with_name('hf_metadata.json')))
        assert metadata['sha']==m['identity']['revision']==config['models'][mid]['identity']['revision']
        if mid==IDS[0]:
            native_params=read(str(Path(p['raw_config']).with_name('params.json')))
            for key,other in [('hidden_size','dim'),('intermediate_size','hidden_dim'),('num_attention_heads','n_heads'),('num_key_value_heads','n_kv_heads'),('head_dim','head_dim')]: assert cfg[key]==native_params[other]
            assert native_params['v_head_dim'] is None and dv==dq==128
            assert cfg['sliding_window'] is None and layer==0
            width=cfg['intermediate_size']
        elif mid==IDS[1]:
            assert cfg['layer_types'][layer]=='full_attention' and layer==3 and cfg['attn_output_gate']
            assert a['weight_shapes_N_K']['q_and_gate_packed']==[2*q*dq,D]
            assert a['weight_shapes_N_K']['q_output_gate_logical']==[q*dv,D]
            # Native q_proj output is interleaved by head; logical split is a
            # permutation, not "first half is Q" and not a weight replication.
            qrows={2*head*dq+d for head in range(q) for d in range(dq)}
            grows={2*head*dq+dq+d for head in range(q) for d in range(dq)}
            assert not qrows & grows and qrows | grows==set(range(2*q*dq))
            assert cfg['num_experts']==256 and cfg['num_experts_per_tok']==8
            width=cfg['moe_intermediate_size']
        else:
            assert layer==7 and cfg['hybrid_layer_pattern'][layer]==0
            assert cfg['head_dim']==192 and cfg['v_head_dim']==128
            assert cfg['attention_value_scale']==a['value_scale']==0.612
            assert cfg['add_full_attention_sink_bias'] is False
            assert cfg['attention_projection_layout']=='fused_qkv'
            width=None
        if width:
            assert m['ffn']['matrices']=={'gate':[width,D],'up':[width,D],'down':[D,width]}
        text=(ROOT/p['implementation']).read_text()
        evidence=[]
        for snippet in anchors[mid]:
            matches=[i for i,line in enumerate(text.splitlines(),1) if snippet in line]
            assert matches,(mid,snippet)
            evidence.append({'path':p['implementation'],'lines':matches,'literal_anchor':snippet})
        raw[mid]=dict(D=D,q=q,h=h,dq=dq,dv=dv,width=width,gate=mid==IDS[1])
        audit.append({'model_id':mid,'revision':metadata['sha'],'selected_layer':layer,
                      'raw_dimensions':raw[mid],'implementation_anchors':evidence,
                      'finding':'PASS; raw config + inspected static source support Step 1 extraction'})
    return raw,audit


def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    config=json.loads((PILOT/'data/config.json').read_text())
    data=decode(json.loads((PILOT/'data/results.json').read_text()))
    raw,audit=source_audit(config); checks=[]
    assert Counter(r['model_id'] for r in data['cases'])==Counter({IDS[0]:10,IDS[1]:10,IDS[2]:2})
    for record in data['cases']:
        d=raw[record['model_id']];D,q,h,dq,dv,width,gate=[d[k] for k in ['D','q','h','dq','dv','width','gate']]
        row=record['row']
        if row=='qkv_projection':
            shapes={'Q':(q*dq,D),'K':(h*dq,D),'V':(h*dv,D)}
            if gate: shapes['G']=(q*dv,D)
            oracle=bank_workload(shapes,1,0,{key:'x' for key in shapes})
        elif row=='ffn_or_moe':
            oracle=bank_workload({'gate':(width,D),'up':(width,D),'down':(D,width)},record['B'],1,{'gate':'x','up':'x','down':'z'})
        else:
            oracle=attention(q,h,dq,dv,record['L'],row.removeprefix('attention_'))
        compare(record['result'],oracle)
        checks.append({'case_id':record['case_id'],'pass':True,'independent_result':compact(oracle)})
    # Candidate is isolated from all oracle functions above.
    sys.path.insert(0,str(ROOT/'shared/scripts'))
    import counting as candidate
    boundaries=[]
    for mid,d in raw.items():
        a=[d[k] for k in ['q','h','dq','dv']]
        for L in [1,127,128,129]:
            dec=enum_decode(*a,L); compare(candidate.attention(*a,L,'decode'),dec)
            pre=attention(*a,L,'prefill'); prev=attention(*a,L-1,'prefill')
            compare(candidate.attention(*a,L,'prefill'),pre)
            compare(candidate.attention(*a,L-1,'prefill'),prev)
            for obj in [None,'QK','AV']:
                x,y,z=(item if obj is None else item['parts'][obj] for item in [pre,prev,dec])
                for b in ['ports','operator']:
                    for field in ['Q_S','Q_R']+(['tile_evaluations'] if b=='ports' else []): assert x[b][field]-y[b][field]==z[b][field]
            boundaries.append({'model_id':mid,'L':L,'decode_explicit_events':compact(dec),'prefix_delta_pass':True})
    # Primary-size differences checked independently, including 128K.
    for r in data['cases']:
        if r['row']!='attention_decode': continue
        d=raw[r['model_id']]; a=[d[k] for k in ['q','h','dq','dv']]; L=r['L']
        pre=attention(*a,L,'prefill'); prev=attention(*a,L-1,'prefill')
        for b in ['ports','operator']:
            for field in ['Q_S','Q_R']+(['tile_evaluations'] if b=='ports' else []):
                assert pre[b][field]-prev[b][field]==r['result'][b][field]
    contrast=data['minimal_mapping_contrast'];d=raw[IDS[1]]
    alt=attention(d['q'],d['q'],d['dq'],d['dv'],1024,'decode')
    for b in ['ports','operator']: assert alt[b]==contrast['replicated'][b]
    assert sum(p['valid_resident_bytes'] for p in alt['parts'].values())==contrast['replicated_capacity_bytes']
    output={'status':'PASS','main_case_count':22,'real_head_boundary_positions':[1,127,128,129],
            'boundary_case_count':len(boundaries),'source_audit':audit,'main_checks':checks,'boundary_checks':boundaries,
            'large_prefix_delta_checks':7,'minimal_replication_contrast':'PASS',
            'method':'Raw-config inputs; matrix tile slices; source/vector identity dedup; inverse tile lifetimes; explicit small decode receiver/write identities. No oracle calls to production formulas.',
            'no_L_by_L_allocation':True,'step1_step2_corrections_required':False}
    text=json.dumps(encode(output),ensure_ascii=False,indent=2)+'\n';dest=PILOT/'data/checks.json'
    if args.emit: dest.write_text(text)
    else: assert dest.read_text()==text,'stale independent checks; use --emit'
    print('PASS: 22 independent cases, 12 real-head boundary cases, 7 primary prefix deltas, raw source audit, replication contrast')


if __name__=='__main__': main()

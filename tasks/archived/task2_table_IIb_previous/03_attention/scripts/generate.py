#!/usr/bin/env python3
"""36 exact Attention cases. Shared closed-form primary; no LxL arrays."""
import argparse, csv, hashlib, io, json, sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'shared/scripts'))
import counting as c
START='e472a0d864b8fb9afb14b0c306217a0e5653e122'
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def blocks(n):
    f,t=divmod(n,128)
    return dict(full_128_blocks=f,tail_valid_elements=t,blocks=f+bool(t))
def layout(n,k,copies):
    tiles=c.ceildiv(n,128)*c.ceildiv(k,128)*copies
    hist=Counter((a,b) for a in c.widths(n,128) for b in c.widths(k,128))
    return dict(matrix_N_K_per_copy=[n,k],copies=copies,output_axis=blocks(n),input_axis=blocks(k),resident_tiles=tiles,valid_resident_bytes=n*k*copies,allocated_tile_bytes=tiles*16384,valid_tile_shape_histogram=[dict(valid_N_K=list(s),tiles=v*copies) for s,v in sorted(hist.items())])
def seq_hist(L,mode):
    if mode=='decode': return Counter(c.widths(L,128))
    m,r=divmod(L,128)
    h=Counter({w:(L-w)//128+1 for w in range(1,min(127,L)+1)})
    h[128]=128*m*(m-1)//2+m*(r+1)
    return +h

def result(a,L,mode):
    q,h,dq,dv=[a[k] for k in ['query_heads','kv_heads','qk_head_dim','v_head_dim']]
    res=c.attention(q,h,dq,dv,L,mode)
    initial=0 if mode=='prefill' else L-1; appended=L-initial
    sh=seq_hist(L,mode)
    for name,n,k,dim in [('QK',L,dq,dq),('AV',dv,L,dv)]:
        p=res['parts'][name]; p['layout']=layout(n,k,h)
        p['initial_layout']=layout(initial,dq,h) if name=='QK' else layout(dv,initial,h)
        slices=[[1,w] if name=='QK' else [w,1] for w in c.widths(dim,128)]
        p['append']=dict(valid_slice_N_K_per_head_per_token=slices,logical_slice_write_events=appended*h*len(slices),events_are_not_device_write_transactions=True,per_token_logical_slice_write_events=h*len(slices),valid_write_bytes_per_token=h*dim)
        hist=Counter()
        for sw,lifetime in sh.items():
            for dw in c.widths(dim,128): hist[(sw,dw) if name=='QK' else (dw,sw)]+=q*lifetime
        p['valid_N_K_call_histogram']=[dict(valid_N_K=list(s),calls=v) for s,v in sorted(hist.items())]
        p['valid_input_width_to_calls']={str(w):sum(v for (n,k),v in hist.items() if k==w) for w in sorted({k for n,k in hist})}
    res.update(initial_KV_tokens=initial,final_KV_tokens=L,initial_valid_resident_bytes=initial*h*(dq+dv),operator_shared_input_overlap_removed=0)
    fields=['valid_resident_bytes','allocated_tile_bytes','resident_tiles']
    res['capacity']={k:sum(p['layout'][k] for p in res['parts'].values()) for k in fields}
    res['capacity']['meaning']='final state capacity; distinct from cumulative Q_R and from physical encoded capacity'
    res['initial_capacity']={k:sum(p['initial_layout'][k] for p in res['parts'].values()) for k in fields}
    return res

def make():
    models=read('data/models.json')['models']; plan=read('data/study_plan.json'); conv=read('shared/data/conventions.json')
    assert [m['id'] for m in models]==plan['table_IIb']['columns_model_ids']
    assert plan['parameters']['L_tokens']==[1024,16384,131072]
    assert conv['reference_id']=='WS128-INT8-semantic-banks-v1'
    assert all(v==1 for v in conv['precision']['role_bytes'].values())
    assert conv['mapping']['tile_N']==conv['mapping']['tile_K']==128
    cfg=dict(schema_version='step4-attention-input-v1',step3_reviewed_HEAD=START,shared_reference_id=conv['reference_id'],tile_N_K=[128,128],precision_role_bytes=conv['precision']['role_bytes'],L=plan['parameters']['L_tokens'],primary_boundary='ports',contrast_boundary='operator',models={},source_files_sha256={})
    paths=['data/models.json','shared/data/conventions.json','shared/scripts/counting.py','shared/tex/counting_method.zh.tex','literature/02_ministral3_8b/raw/params.json']
    records=[]
    for m in models:
        mid=m['id']; local=m['local_material']; a=m['attention']
        cfg['models'][mid]=dict(display_name=m['display_name'],identity=m['identity'],selected_layer=m['backbone']['selected_layer_index_zero_based'],layer_type=m['backbone']['selected_layer_type'],attention=a,context=m['context'],local_material=local)
        paths += [local[k] for k in ['raw_config','raw_model_card','implementation','structure_card']]
        paths.append(str(Path(local['raw_config']).with_name('hf_metadata.json')))
        for mode in ['prefill','decode']:
            for L in cfg['L']:
                records.append(dict(case_id=f'{mid}/attention_{mode}/{L}',model_id=mid,row='attention_'+mode,L=L,model_revision=m['identity']['revision'],selected_layer=cfg['models'][mid]['selected_layer'],shared_reference_id=conv['reference_id'],configuration={k:a[k] for k in ['query_heads','kv_heads','qk_head_dim','v_head_dim','queries_per_kv_head']},context_support=m['context']['support'][cfg['L'].index(L)],context_extension_condition=m['context']['extension_for_128K'] if L==131072 else None,result=result(a,L,mode)))
    cfg['source_files_sha256']={p:sha(p) for p in sorted(set(paths))}
    return cfg,dict(schema_version='step4-delivery-v1',case_count=36,cases=records)

def texnum(x):
    x=Fraction(x)
    return str(x.numerator) if x.denominator==1 else rf'\frac{{{x.numerator}}}{{{x.denominator}}}'
def outputs():
    cfg,data=make(); files={}
    files['data/config.json']=json.dumps(cfg,ensure_ascii=False,indent=2)+'\n'
    files['data/results.json']=json.dumps(c.encode(data),ensure_ascii=False,indent=2)+'\n'
    out=io.StringIO(); w=csv.writer(out,lineterminator='\n')
    w.writerow(['case_id','component','boundary','Q_S_Byte','Q_R_Byte','RI','tile_evaluations','final_valid_Byte','allocated_Byte'])
    for rec in data['cases']:
        for name,r in [('total',rec['result']),*rec['result']['parts'].items()]:
            cap=r.get('layout',r.get('capacity'))
            for b in ['ports','operator']: w.writerow([rec['case_id'],name,b,*[str(r[b][k]) for k in ['Q_S','Q_R','RI','tile_evaluations']],cap['valid_resident_bytes'],cap['allocated_tile_bytes']])
    files['data/results.csv']=out.getvalue()
    md=['# 六模型 Attention 概览','','固定顺序 L=1024 / 16384 / 131072；所有 RI 为精确分数。每行只代表所选完整/global GQA 子层。','']
    for b in ['ports','operator']:
        md += [f'## {b}', '', '| 模型 | Prefill RI | Decode RI |','|---|---|---|']
        tex=[r'\begin{tabular}{@{}lrrr@{}}\toprule',r'模型 & $L$ & Prefill RI & Decode RI\\\midrule']
        for mid,m in cfg['models'].items():
            vals={mode:[r['result'][b]['RI'] for r in data['cases'] if r['model_id']==mid and r['row']=='attention_'+mode] for mode in ['prefill','decode']}
            md.append('| '+m['display_name']+' | '+' | '.join(', '.join(map(str,vals[mode])) for mode in ['prefill','decode'])+' |')
            for j,L in enumerate(cfg['L']):
                tex.append((m['display_name'] if j==0 else '')+f' & {L} & $'+texnum(vals['prefill'][j])+'$ & $'+texnum(vals['decode'][j])+r'$\\[5pt]')
            tex.append(r'\addlinespace[2pt]')
        files[f'tex/{b}.generated.tex']='\n'.join(tex+[r'\bottomrule\end{tabular}',''])
        md.append('')
    md += ['Ling 128K 保留官方 YaRN factor=4 / original_max_position_embeddings=32768 / type=yarn，并设置运行端 --max-model-len 131072；原始 config 不改。','','[精确字节、分项、状态和调用](data/results.json)；[独立校验](data/checks.json)。','']
    files['OVERVIEW.zh.md']='\n'.join(md)
    return files

def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    for name,text in outputs().items():
        f=HERE/name
        if args.emit: f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
        else: assert f.read_text()==text, f'stale artifact: {name}'
    print('PASS: 36 Attention cases generated/recomputed; exact fractions and both boundaries')
if __name__=='__main__':main()

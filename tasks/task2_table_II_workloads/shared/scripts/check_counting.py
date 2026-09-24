#!/usr/bin/env python3
"""Independent block sums and explicit event enumeration vs closed forms.

--emit writes only synthetic checks. No import or iteration over model structures.
"""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import argparse
import json
import counting as c

ROOT=Path(__file__).resolve().parents[2]


def report(qs,qr,calls=None):
    # Deliberately not using the production demand/ratio helper.
    return {'Q_S':F(qs),'Q_R':F(qr),'RI':F(qs)/F(qr) if qr else ('infinity' if qs else 'undefined_empty'), 'tile_evaluations':calls}


def block_matrix(n,k,U,A,bs,br,tn,tk):
    tiles=[(min(tn,n-i),min(tk,k-j)) for i in range(0,n,tn) for j in range(0,k,tk)]
    return {'operator':report(U*k*F(bs),A*sum(a*b for a,b in tiles)*F(br)),
            'ports':report(U*sum(b for a,b in tiles)*F(bs),A*sum(a*b for a,b in tiles)*F(br),U*len(tiles))}


def enum_banks(specs,tn,tk):
    """Enumerate input identities, tile receiver events and writes, including load index."""
    operator_inputs={};inputs={};writes={};calls=set();shapes=Counter()
    for name,n,k,U,A,source,bs,br in specs:
        for load in range(A):
            for row in range(n):
                for col in range(k):writes[(name,load,row,col)]=F(br)
        for use in range(U):
            for col in range(k):operator_inputs[(source,use,col)]=F(bs)
            for i in range(0,n,tn):
                for j in range(0,k,tk):
                    calls.add((name,use,i,j));shapes[(name,min(tn,n-i),min(tk,k-j))]+=1
                    for col in range(j,min(j+tk,k)):
                        inputs[(name,use,i,j,col)]=F(bs)
    qr=sum(writes.values())
    return {'operator':report(sum(operator_inputs.values()),qr),'ports':report(sum(inputs.values()),qr,len(calls)),
            'call_shape_histogram':[{'matrix':name,'valid_N_K':[n,k],'calls':v} for (name,n,k),v in sorted(shapes.items())]}


def block_attention(Hq,Hkv,dq,dv,L,mode,bq,bp,bk,bv,tn,tk):
    # Loop all prefixes and tile ranges; no ceil helper, triangular formula or sum_ceil_prefix.
    stages=[('QK',0,0,0),('AV',0,0,0)]
    totals={name:{'op':0,'port':0,'calls':0} for name,*_ in stages}
    prefix_list=range(1,L+1) if mode=='prefill' else [L]
    for i in prefix_list:
        for name,n,k,bs in [('QK',i,dq,F(bq)),('AV',dv,i,F(bp))]:
            totals[name]['op']+=Hq*k*bs
            for row in range(0,n,tn):
                for col in range(0,k,tk):
                    totals[name]['port']+=Hq*len(range(col,min(col+tk,k)))*bs
                    totals[name]['calls']+=Hq
    app=L if mode=='prefill' else 1
    parts={}
    for name,dim,br in [('QK',dq,F(bk)),('AV',dv,F(bv))]:
        x=totals[name];qr=app*Hkv*dim*br
        parts[name]={'operator':report(x['op'],qr),'ports':report(x['port'],qr,x['calls'])}
    return join_parts(parts)


def join_parts(parts):
    out={'parts':parts}
    for boundary in ['operator','ports']:
        out[boundary]=report(sum(x[boundary]['Q_S'] for x in parts.values()),sum(x[boundary]['Q_R'] for x in parts.values()),
                             sum(x[boundary]['tile_evaluations'] for x in parts.values()) if boundary=='ports' else None)
    return out


def enum_attention(Hq,Hkv,dq,dv,L,mode,bq,bp,bk,bv,tn,tk):
    group=Hq//Hkv
    keys=set();values=set();writes={'QK':{},'AV':{}}
    inputs={'QK':{},'AV':{}};ops={'QK':{},'AV':{}};calls={'QK':set(),'AV':set()}
    def append(token,charge):
        for h in range(Hkv):
            for d in range(dq):
                coord=(h,token,d);assert coord not in keys;keys.add(coord)
                if charge:writes['QK'][coord]=F(bk)
            for d in range(dv):
                coord=(h,d,token);assert coord not in values;values.add(coord)
                if charge:writes['AV'][coord]=F(bv)
    if mode=='decode':
        for token in range(L-1):append(token,False)
    for i in (range(1,L+1) if mode=='prefill' else [L]):
        append(i-1,True)
        for qh in range(Hq):
            h=qh//group
            for d in range(dq):ops['QK'][(i,qh,d)]=F(bq)
            for token in range(i):ops['AV'][(i,qh,token)]=F(bp)
            for row in range(0,i,tn):
                for col in range(0,dq,tk):
                    calls['QK'].add((i,qh,h,row,col))
                    for d in range(col,min(col+tk,dq)):
                        inputs['QK'][(i,qh,h,row,col,d)]=F(bq)
                        for token in range(row,min(row+tn,i)):assert (h,token,d) in keys
            for row in range(0,dv,tn):
                for col in range(0,i,tk):
                    calls['AV'].add((i,qh,h,row,col))
                    for token in range(col,min(col+tk,i)):
                        inputs['AV'][(i,qh,h,row,col,token)]=F(bp)
                        for d in range(row,min(row+tn,dv)):assert (h,d,token) in values
    parts={name:{'operator':report(sum(ops[name].values()),sum(writes[name].values())),
                 'ports':report(sum(inputs[name].values()),sum(writes[name].values()),len(calls[name]))} for name in ['QK','AV']}
    out=join_parts(parts)
    out['final_unique_resident_elements']={'K':len(keys),'V':len(values)}
    return out


def same(a,b):
    for boundary in ['operator','ports']:
        assert a[boundary]==b[boundary], (boundary,a[boundary],b[boundary])
    if 'parts' in a and 'parts' in b:
        assert a['parts'].keys()==b['parts'].keys()
        for name in a['parts']:same(a['parts'][name],b['parts'][name])


def main(emit=False):
    contract=json.loads((ROOT/'shared/data/conventions.json').read_text())
    assert contract['mapping']['tile_N']==contract['mapping']['tile_K']==128
    assert all(x==1 for x in contract['precision']['role_bytes'].values())
    assert contract['boundaries']['ports']['primary'] is True and contract['no_results_for_six_models'] is True
    for source in contract['sources']:
        assert (ROOT/'shared/data'/source['path']).is_file(),source['path']
    checks=[]
    # Rectangles, tails on each axis, static, multi-use one-load, per-use loads, symbolic precision.
    cases=[(5,7,1,0,1,1,3,2),(5,7,1,1,1,1,3,2),(5,7,4,1,1,1,3,2),
           (5,7,4,4,1,1,3,2),(7,5,2,1,2,F(1,2),3,2),(1,1,1,0,1,1,128,128),
           (129,130,2,1,1,1,128,128),(128,129,1,1,1,1,128,128),(130,1,3,1,1,2,128,128)]
    for n,k,U,A,bs,br,tn,tk in cases:
        a=c.matvec(n,k,U,A,bs,br,tn,tk);b=block_matrix(n,k,U,A,bs,br,tn,tk)
        e=enum_banks([('W',n,k,U,A,'x',bs,br)],tn,tk);same(a,b);same(a,e)
        checks.append({'kind':'generic_matrix','inputs':dict(N=n,K=k,uses=U,loads=A,b_s=bs,b_r=br,tile_N=tn,tile_K=tk),
                       'result':{x:a[x] for x in ['operator','ports','tile_layout']},'explicit_call_shapes':e['call_shape_histogram'],'methods':['closed','tile sums','explicit input/write identities'],'pass':True})
    for D,Hq,Hkv,dq,dv,dg,tn,tk in [(5,4,2,3,2,0,3,2),(5,4,2,3,2,8,3,2),(7,2,1,2,3,6,4,3)]:
        a=c.qkv(D,Hq,Hkv,dq,dv,dg,tile_n=tn,tile_k=tk)
        dims={'Q':Hq*dq,'K':Hkv*dq,'V':Hkv*dv}
        if dg:dims['G']=dg
        e=enum_banks([(j,n,D,1,0,'x',1,1) for j,n in dims.items()],tn,tk);same(a,e)
        # Stored fusion is not an input: semantic banks must remain invariant after unpacking.
        assert a['ports']['Q_S']>=a['operator']['Q_S']
        checks.append({'kind':'synthetic_QKV','inputs':dict(D=D,H_q=Hq,H_kv=Hkv,d_QK=dq,d_V=dv,D_g=dg,tile_N=tn,tile_K=tk),'result':a,'methods':['closed','explicit semantic-bank events'],'pass':True})
    for D,Fwidth,B,tn,tk in [(5,7,4,3,2),(7,5,1,3,2),(129,3,2,128,128)]:
        a=c.ffn(D,Fwidth,B,tile_n=tn,tile_k=tk)
        e=enum_banks([('gate',Fwidth,D,B,1,'x',1,1),('up',Fwidth,D,B,1,'x',1,1),('down',D,Fwidth,B,1,'z',1,1)],tn,tk);same(a,e)
        for name,n,k,source in [('gate',Fwidth,D,'x'),('up',Fwidth,D,'x'),('down',D,Fwidth,'z')]:
            same(a['parts'][name],enum_banks([(name,n,k,B,1,source,1,1)],tn,tk))
        checks.append({'kind':'synthetic_FFN','inputs':dict(D=D,F=Fwidth,B=B,tile_N=tn,tile_K=tk),'result':a,'methods':['closed','explicit branches and shared input identities'],'pass':True})
    a=c.ffn(5,7,3,b_x=2,b_z=1,b_gate=2,b_up=F(1,2),b_down=1,tile_n=3,tile_k=2)
    e=enum_banks([('gate',7,5,3,1,'x',2,2),('up',7,5,3,1,'x',2,F(1,2)),('down',5,7,3,1,'z',1,1)],3,2);same(a,e)
    checks.append({'kind':'symbolic_role_widths_FFN','inputs':{'D':5,'F':7,'B':3,'b_x':2,'b_z':1,'b_gate':2,'b_up':F(1,2),'b_down':1,'tile_N':3,'tile_K':2},'result':a,'methods':['closed','explicit weighted events'],'pass':True})
    # Exact ceil sums: starts, full blocks and nonzero remainders; no L^2/2 approximation.
    for T in [1,2,3,4,128]:
        for L in sorted(set([0,1,T-1,T,T+1,2*T,2*T+1])):
            direct=sum(len(range(0,i,T)) for i in range(1,L+1))
            assert c.sum_ceil_prefix(L,T)==direct
    checks.append({'kind':'ceil_prefix_identity','T':[1,2,3,4,128],'positions':'0,1,T-1,T,T+1,2T,2T+1','pass':True})
    acases=[(4,2,3,5,7,1,1,1,1,3,2),(6,2,5,2,8,2,1,1,2,4,3),
            (2,2,2,3,1,1,1,1,1,3,2),(1,1,2,2,0,1,1,1,1,3,2),
            (2,1,3,5,129,1,1,1,1,128,128)]
    for Hq,Hkv,dq,dv,L,bq,bp,bk,bv,tn,tk in acases:
        for mode in ['prefill','decode'] if L else ['prefill']:
            args=(Hq,Hkv,dq,dv,L,mode,bq,bp,bk,bv,tn,tk)
            a=c.attention(*args);b=block_attention(*args);e=enum_attention(*args);same(a,b);same(a,e)
            checks.append({'kind':'synthetic_attention_'+mode,'inputs':dict(H_q=Hq,H_kv=Hkv,d_QK=dq,d_V=dv,L=L,b_q=bq,b_p=bp,b_K=bk,b_V=bv,tile_N=tn,tile_K=tk),'result':a,'enumerated_unique_state':e['final_unique_resident_elements'],'methods':['closed','prefix tile sums','explicit append and receiver events'],'pass':True})
        if L:
            # Compare cumulative step-by-step decode with exact prefill, and each boundary increment.
            prefix=c.attention(Hq,Hkv,dq,dv,L,'prefill',bq,bp,bk,bv,tn,tk)
            prev=c.attention(Hq,Hkv,dq,dv,L-1,'prefill',bq,bp,bk,bv,tn,tk)
            step=c.attention(Hq,Hkv,dq,dv,L,'decode',bq,bp,bk,bv,tn,tk)
            steps=[enum_attention(Hq,Hkv,dq,dv,j,'decode',bq,bp,bk,bv,tn,tk) for j in range(1,L+1)]
            for boundary in ['operator','ports']:
                for field in ['Q_S','Q_R']+(['tile_evaluations'] if boundary=='ports' else []):
                    assert prefix[boundary][field]-prev[boundary][field]==step[boundary][field]
                    assert sum(x[boundary][field] for x in steps)==prefix[boundary][field]
            # GQA group size affects streaming, not one-copy writes or resident capacity.
            doubled=c.attention(2*Hq,Hkv,dq,dv,L,'prefill',bq,bp,bk,bv,tn,tk)
            assert doubled['ports']['Q_R']==prefix['ports']['Q_R']
            assert doubled['ports']['Q_S']==2*prefix['ports']['Q_S']
    checks.append({'kind':'prefill_decode_telescoping_and_GQA','verified':'both boundaries, subtask-compatible totals; L=1,7,8,129; resident writes invariant under doubled query heads','pass':True})
    # Independent block sums for all formal II(a) cells; no large element enumeration.
    plan=json.loads((ROOT/'data/study_plan.json').read_text())
    for n,k in plan['table_IIa']['columns_N_K']:
        for loads in [0,1]:same(c.matvec(n,k,1,loads),block_matrix(n,k,1,loads,1,1,128,128))
    checks.append({'kind':'IIa_all_cells','shapes':plan['table_IIa']['columns_N_K'],'rows':2,'boundaries':2,'methods':['closed','independent tile sums'],'pass':True})
    result={'status':'PASS','check_records':len(checks),'no_model_numeric_results':True,'checks':checks}
    dest=ROOT/'shared/data/synthetic_checks.json'
    if emit:dest.write_text(json.dumps(c.encode(result),ensure_ascii=False,indent=2)+'\n')
    else:assert json.loads(dest.read_text())==c.encode(result),'stale synthetic output; rerun --emit'
    print(f'PASS: {len(checks)} records; closed forms, independent block sums and explicit events; no model batch calculation.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');main(p.parse_args().emit)

#!/usr/bin/env python3
"""Independent one-load input/write counts and symbolic limit verification."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT.parent


def decode(x):
    if isinstance(x,dict):
        if set(x)=={'numerator','denominator'}:return F(x['numerator'],x['denominator'])
        return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list):return [decode(v) for v in x]
    return x


def encode(x):
    if isinstance(x,F):return x.numerator if x.denominator==1 else dict(numerator=x.numerator,denominator=x.denominator)
    if isinstance(x,dict):return {k:encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [encode(v) for v in x]
    return x


def result(inputs,weights,bx,bw):
    qs,qr=inputs*bx,weights*bw
    return dict(Q_S=qs,Q_R=qr,RI=F(qs)/qr,resident_capacity_bytes=qr)


def rows(U,N,K,bx=F(1),bw=F(1)):
    return result(sum(len(range(K)) for vector in range(U)),
        sum(len(range(K)) for output in range(N)),bx,bw)


def events(U,N,K,bx,bw):
    inputs={(vector,k) for vector in range(U) for k in range(K)}
    writes={(0,n,k) for n in range(N) for k in range(K)}
    return result(len(inputs),len(writes),bx,bw)


def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    cfg=json.loads((ROOT/'data/config.json').read_text());data=decode(json.loads((ROOT/'data/results.json').read_text()))
    plan=json.loads((TASK/'data/study_plan.json').read_text())['table_IIa']
    shapes=[[128,128],[1024,1024],[4096,4096],[1024,4096],[4096,1024]];levels=[1,128,1024,16384,131072,1048576,'infinity']
    assert cfg['matrix_cases_N_K']==plan['matrix_cases_N_K']==data['matrix_cases_N_K']==shapes
    assert cfg['U_values']==plan['U_values']==data['U_values']==levels
    assert cfg['complete_weight_loads']==plan['complete_weight_loads']==1
    assert cfg['reference_id']==data['reference_id']==plan['reference_id']=='OPERATOR-RESIDENCY-v2'
    assert cfg['boundary']==data['boundary']==plan['primary_boundary']=='operator'
    assert [c['case_id'] for c in data['cases']]==[f'N{N}/K{K}/U{U}' for N,K in shapes for U in levels]
    checks=[];limits=[]
    for c in data['cases']:
        U,N,K=c['U'],c['N'],c['K'];assert c['weight_shape']==[N,K] and c['complete_weight_loads']==1
        if U=='infinity':
            assert c['kind']=='limit' and c['input_shape'] is None and c['output_shape'] is None
            slope=rows(1,N,K);assert slope['Q_S']>0 and slope['Q_R']>0
            expected=dict(Q_S='infinity',Q_R=slope['Q_R'],RI='infinity',resident_capacity_bytes=slope['Q_R'])
            assert c['result']==expected
            limits.append(dict(case_id=c['case_id'],argument='positive input bytes per vector, fixed positive one-load writes; numerator unbounded',pass_check=True))
        else:
            assert c['kind']=='finite' and c['input_shape']==[U,K] and c['output_shape']==[U,N]
            expected=rows(U,N,K);assert c['result']==expected,c['case_id']
            checks.append(dict(case_id=c['case_id'],independent_result=expected,pass_check=True))
    assert len(checks)==30 and len(limits)==5 and data['table_cell_count']==35
    import generate as candidate
    extra=[]
    for U,N,K,bx,bw in [(4,3,5,F(1),F(1)),(5,7,3,F(2),F(1,2)),(1,129,7,F(1),F(1)),
        (3,1,1,F(1),F(1)),(2,7,129,F(1),F(1))]:
        expected=events(U,N,K,bx,bw)
        assert rows(U,N,K,bx,bw)==candidate.count(U,N,K,bx,bw)==expected
        extra.append(dict(U=U,N=N,K=K,b_x=bx,b_w=bw,result=expected))
    base=rows(8,7,5);moreB=rows(64,7,5);moreK=rows(8,7,10)
    assert moreB['Q_S']==8*base['Q_S'] and moreB['Q_R']==base['Q_R'] and moreB['RI']==8*base['RI']
    assert moreK['Q_S']==2*base['Q_S'] and moreK['Q_R']==2*base['Q_R'] and moreK['RI']==base['RI']
    assert rows(8,14,5)['RI']==base['RI']/2
    assert all('tile' not in k and k!='ports' for c in data['cases'] for k in c['result'])
    snapshots=json.loads((ROOT/'data/rewrite_provenance.json').read_text())['snapshots']
    for s in snapshots:assert hashlib.sha256((ROOT/s['snapshot_path']).read_bytes()).hexdigest()==s['sha256']
    report=dict(status='PASS',reference_id=cfg['reference_id'],finite_checks=checks,limit_checks=limits,
        explicit_event_cases=extra,scaling_checks=['U scales input and RI','K scales both demands, not RI','doubling N halves RI'],
        historical_snapshots_verified=len(snapshots),hardware_partition_parameters_used=False,
        method='Independent input/weight row counts; explicit identities for small, non-aligned and unequal-byte-width cases; infinity verified as a symbolic linear-growth limit, not a zero-write finite window.')
    text=json.dumps(encode(report),ensure_ascii=False,indent=2)+'\n';out=ROOT/'data/checks.json'
    if args.emit:out.write_text(text)
    else:assert out.read_text()==text,'stale II(a) checks.json'
    print('PASS: 30 finite row counts, 5 symbolic limits, 5 event cases, U/N/K scaling and historical snapshot hashes')


if __name__=='__main__':main()

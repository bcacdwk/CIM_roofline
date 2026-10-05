#!/usr/bin/env python3
"""Post-run nominal physical-map/register-lifecycle checks, never a timed CPU datapath."""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode=True
K,N=256,31

def h(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def round_code(x):return math.floor(x+0.5+1e-9)
def patterns():
    dense=[[((r*37+c*19)%256)-128 for c in range(N)] for r in range(K)]
    return {'zero':([0]*K,dense),'positive_max':([127]*K,[[127]*N for _ in range(K)]),'negative_min':([-128]*K,[[-128]*N for _ in range(K)]),'opposite':([-128]*K,[[127]*N for _ in range(K)]),'mixed':([((r*53)%256)-128 for r in range(K)],dense),'bank_boundary':([-128 if r in (15,16,31,32,239,240) else 0 for r in range(K)],dense),'cancellation':([127 if r%2 else -127 for r in range(K)],[[127]*N for _ in range(K)])}

def correction(A,B,bits):
    s1=[a-(A[-1]<<7) for a in A[:-1]]
    s2=[a-(b<<8) for a,b in zip(s1,B[:-1])]
    Y=[a+(B[-1]<<15) for a in s2]
    assert all(-(1<<(bits-1))<=x<(1<<(bits-1)) for stage in (s1,s2,Y) for x in stage)
    return Y,max(abs(x) for stage in (s1,s2,Y) for x in stage)

def analog(x,W,bank_rows,rram,p):
    banks=K//bank_rows;memory=[]
    for b in range(banks):
        memory.append([[((W[b*bank_rows+r][j]+128) if j<N else 1)>>bit&1 for bit in range(8)] + ([0] if rram else []) for r in range(bank_rows) for j in range(32)])
    passes=[];traces=[];max_code=0;word_beats=0
    frac=p.get('output_fractional_bits',0) if rram else 0;scale=1<<frac
    gon=1/(p['resistance_on_ohm']+p['access_resistance_ohm']) if rram else 1
    goff=1/(p['resistance_off_ohm']+p['access_resistance_ohm']) if rram else 0
    offset=scale*goff/(gon-goff) if rram else 0
    for phase in range(2):
        bank_outputs=[]
        for bank in range(banks):
            input_acc=[0]*32
            for plane in range(8):
                q=[(x[bank*bank_rows+r]&255) if phase==0 else int(x[bank*bank_rows+r]<0) for r in range(bank_rows)]
                active=[r for r in range(bank_rows) if (q[r]>>plane)&1]
                weight_acc=[0]*32
                for j in range(32):
                    # Physical column slot8 is read/captured before its eight data columns.
                    ref=round_code(len(active)*offset) if rram else 0
                    for bit in range(8):
                        count=sum(memory[bank][r*32+j][bit] for r in active)
                        adc=round_code(len(active)*offset+scale*count) if rram else count
                        assert 0<=adc<2**p['adc_bits'];max_code=max(max_code,adc)
                        difference=adc-ref
                        assert difference==scale*count
                        # Native ShiftAdd LSB-first register alignment, not a post-hoc dot product.
                        weight_acc[j]=(weight_acc[j]>>1)+(difference<<7)
                        assert weight_acc[j]<2**(p['adc_bits']+8)
                    input_acc[j]=(input_acc[j]>>1)+(weight_acc[j]<<7)
                    assert input_acc[j]<2**(p['adc_bits']+16)
                traces.append([phase,bank,plane,h(input_acc)])
            bank_outputs.append(input_acc)
        if rram:
            staging=[None]*(banks*32)
            for bank in range(banks):
                for word in range(32):
                    value=bank_outputs[bank][word];assert 0<=value<2**24
                    staging[bank*32+word]=value;word_beats+=1
            assert all(v is not None for v in staging)
            level=[staging[b*32:(b+1)*32] for b in range(banks)];depth=0
            while len(level)>1:
                level=[[u+v for u,v in zip(level[i],level[i+1])] for i in range(0,len(level),2)];depth+=1
                assert all(v<2**(24+depth) for lane in level for v in lane)
            assert depth==4;result=level[0]
        else:result=bank_outputs[0]
        if phase==0:held=tuple(result)
        else:assert tuple(passes[0])==held
        passes.append(result)
    Y,maxinter=correction(*passes,29 if rram else 25)
    expected=[sum(x[r]*W[r][j] for r in range(K)) for j in range(N)]
    assert Y==[scale*v for v in expected]
    if rram:assert word_beats==1024
    return {'matched':True,'output_fractional_bits':frac,'max_ADC_code':max_code,'max_abs_intermediate':maxinter,'register_trace_hash':h(traces),'tracked_bank_bit_steps':len(traces),'shared_bus_word_beats':word_beats,'output_hash':h(Y),'min_output_code':min(Y),'max_output_code':max(Y)}

def digital(x,W):
    memory=[[((W[r][c//8]+128) if c<248 else 1)>>(c%8)&1 for c in range(256)] for r in range(K)]
    passes=[];trace=[]
    for phase in range(2):
        accum=[0]*64;tree=[0]*64
        for cycle in range(9):
            if cycle:
                accum=[(a>>1)+(p<<7) for a,p in zip(accum,tree)]
                assert all(v<2**20 for v in accum)
            if cycle<8:
                q=[(v&255) if phase==0 else int(v<0) for v in x];plane=[v>>cycle&1 for v in q]
                tree=[sum(sum((1-((1-plane[r])|(1-memory[r][4*t+bit])))<<bit for bit in range(4)) for r in range(K)) for t in range(64)]
                assert all(v<2**12 for v in tree)
            trace.append([phase,cycle,h(accum)])
        merged=[accum[2*j]+(accum[2*j+1]<<4) for j in range(32)]
        if phase==0:held=tuple(merged)
        else:assert tuple(passes[0])==held
        passes.append(merged)
    Y,inter=correction(*passes,25)
    assert Y==[sum(x[r]*W[r][j] for r in range(K)) for j in range(N)]
    return {'matched':True,'cycles':26,'native_cycles_per_pass':9,'trees':64,'tree_bits':4,'tree_register_bits':12,'native_shift_register_bits':20,'A_C_held_during_B_D':True,'max_abs_intermediate':inter,'register_trace_hash':h(trace),'output_hash':h(Y)}

def verify_lifecycle():
    def accepted(flags):
        sticky=[False]*32
        for group in flags:sticky=[a or b for a,b in zip(sticky,group)]
        return not any(sticky)
    clean=[[False]*32 for _ in range(9)];early=[[False]*32 for _ in range(9)];early[0][3]=True
    late=[[False]*32 for _ in range(9)];late[-1][-1]=True
    assert accepted(clean) and not accepted(early) and not accepted(late)
    def bounded(history):
        for attempt,flags in enumerate(history[:2],1):
            if accepted(flags):return {'ready':True,'attempts':attempt}
        return {'ready':False,'attempts':2,'performance_point':None}
    assert bounded([early,clean])['ready'] and not bounded([early,late])['ready']
    return {'early_failure_sticky':True,'late_failure_sticky':True,'phase_clear_required':True,'second_attempt_success':bounded([early,clean]),'failure_not_published':bounded([early,late])}

def main(out):
    rows=json.loads((out/'summary.json').read_text())['case_results'];result={}
    for cid in sorted(set(r['case_id'] for r in rows)):
        points=[r for r in rows if r['case_id']==cid];inp=json.loads((out/cid/points[0]['scenario']/'input.json').read_text());p=inp['resolved_parameters']
        invariants=[{k:v for k,v in json.loads((out/cid/r['scenario']/'input.json').read_text())['resolved_parameters'].items() if k!='temperature_K'} for r in points]
        assert all(v==invariants[0] for v in invariants)
        reports={}
        for name,(x,w) in patterns().items():
            reports[name]=digital(x,w) if cid=='ns_sram_dcim' else analog(x,w,p.get('bank_rows',K),cid=='ns_rram_1t1r',p)
        result[cid]={'paired_ids':[r['paired_id'] for r in points],'configuration_invariants_checked':True,'patterns':reports}
    data={'status':'PASS_nominal_mapping_and_register_lifecycle_only','qualification':'This is a post-run hardware-sequence emulator. It is neither silicon/ENOB validation nor an untimed CPU stage used by the performance path. Analog physical residuals are reported separately.','cases':result,'verify_failure_lifecycle':verify_lifecycle(),'DCIM_short_sign_alternative':'Deleting seven zero slots leaves native LSB-first ShiftAdd result shifted by7; no shortened service is published without additional extraction/bypass, state and timing.'}
    (out/'numeric.json').write_text(json.dumps(data,indent=2)+'\n');print(data['status'])
if __name__=='__main__':main(Path(sys.argv[1]))

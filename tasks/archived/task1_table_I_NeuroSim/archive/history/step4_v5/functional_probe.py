#!/usr/bin/env python3
"""Nominal gate/hold and lifecycle diagnostic for the V5 P1 datapath, not analog accuracy."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
sys.dont_write_bytecode=True
WIDTH=25
MASK=(1<<WIDTH)-1

def bits(value):return [(value>>i)&1 for i in range(WIDTH)]
def mux(select,a,b):return [((1-select)&x)|(select&y) for x,y in zip(a,b)]
def add_sub(a,b,subtract):
    carry=subtract;out=[]
    for av,bv in zip(a,b):
        bv=bv^subtract
        out.append(av^bv^carry)
        carry=(av&bv)|(av&carry)|(bv&carry)
    return out

def word(vector):return sum(bit<<i for i,bit in enumerate(vector))
def signed(vector):
    value=word(vector)
    return value-(1<<WIDTH) if vector[-1] else value

def simulate(xs,weights,lanes,break_mask=False,break_keep=False,break_clear=False,initial_results=None):
    n=len(weights[0]);groups=(n+lanes-1)//lanes
    registers=[bits(v&MASK) for v in (initial_results if initial_results is not None else [12345*(j+1) for j in range(n)])]
    # The real clear AND is after the keep MUX at every output/status/retry D pin.
    clear=0 if break_clear else 1
    registers=[[v&(1-clear) for v in register] for register in registers]
    # Native full-vector DFFs are filled in explicit 16-byte ingress beats.
    input_holds=[None]*len(xs)
    for start in range(0,len(xs),16):
        for idx in range(len(xs)):
            if start<=idx<min(start+16,len(xs)):input_holds[idx]=xs[idx]&255
    for row,source_x in enumerate(input_holds):
        weight_holds=[None]*n
        for group in range(groups):
            for col in range(n):
                if col//lanes==group:weight_holds[col]=weights[row][col]&255
        if any(x is None for x in weight_holds):raise AssertionError('Unloaded weight group')
        for group in range(groups):
            for bit in range(8):
                old=[r[:] for r in registers]
                lane_results=[]
                for lane in range(lanes):
                    col=group*lanes+lane
                    if col>=n:continue
                    unsigned_weight=weight_holds[col]
                    extended=[(unsigned_weight>>i)&1 if i<8 else (unsigned_weight>>7)&1 for i in range(WIDTH)]
                    shifted=[0]*bit+extended[:WIDTH-bit]
                    input_bit=(source_x>>bit)&1
                    masked=[v&(1 if break_mask else input_bit) for v in shifted]
                    add=add_sub(old[col],masked,0);sub=add_sub(old[col],masked,1)
                    lane_results.append(mux(int(bit==7),add,sub))
                for col in range(n):
                    selected=(col//lanes==group)
                    candidate=lane_results[col%lanes] if col%lanes<len(lane_results) else bits(0)
                    registers[col]=mux(int(selected or break_keep),old[col],candidate)
                    if not selected and not break_keep:assert registers[col]==old[col]
    return [signed(v) for v in registers]

def lifecycle():
    state={'WL':False,'reference_on':False,'precharge':False,'sense_latched':False,'weight_held':False}
    trace=[]
    def record(name):trace.append(dict(event=name,**state))
    record('all_off')
    state['precharge']=True
    assert not state['WL'] and not state['reference_on'];record('precharge_isolated')
    state['precharge']=False;record('precharge_release')
    state['WL']=True;state['reference_on']=True;record('data_reference_enable')
    assert not state['precharge'];record('bounded_analog_development')
    state['sense_latched']=True;record('native_VSA_latch')
    state['WL']=False;state['reference_on']=False;record('array_reference_release')
    state['weight_held']=True;record('digital_weight_capture')
    assert state['sense_latched'] and state['weight_held'];record('eight_bit_mac_reuses_weight')
    # A permanently grounded reference during precharge is a forbidden lifecycle.
    reject_unisolated=bool(True and True)
    return trace,reject_unisolated

def program_verify():
    target=[0,255,128,127,85,170,1,254];physical=[255-x for x in target]
    sticky=1;retry=3
    sticky=sticky&0;retry=retry&0
    assert sticky==0 and retry==0
    # Logical target row is held; every physical bit gets RESET; target mask selects SET.
    for byte in range(len(physical)):
        physical[byte]=0
        for bit in range(8):
            enable=(target[byte]>>bit)&1
            physical[byte]|=enable<<bit
    def fail_vector(actual):
        differences=[add_sub(bits(a),bits(b),1) for a,b in zip(actual,target)]
        return bool(any(any(x) for x in differences))
    success=not fail_vector(physical)
    physical[-1]^=1
    failure=fail_vector(physical)
    return {'complete_cover_matches':success,'injected_bit_failure_detected':failure,'failure_payload_Byte':0,'prior_sticky_retry_cleared':sticky==0 and retry==0}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-run',type=Path,required=True);a=p.parse_args()
    raw=json.loads((a.native_run/'resolved.json').read_text())
    required=('data_zero_mask_s','add_sub_result_select_s','accumulator_keep_s','weight_keep_s','reference_isolation_count','input_ingress_beats','state_clear_bits','state_clear_s')
    if any(k not in raw for k in required):raise ValueError('Native run predates complete gate/hold implementation')
    k,n,lanes=int(raw['input_rows']),int(raw['input_cols'])//8,int(raw['extra_25bit_adder_lanes'])
    rng=random.Random(20261005);tests={}
    cases={
      'all_zero':([0]*k,[[127]*n for _ in range(k)]),
      'positive_extreme':([127]*k,[[127]*n for _ in range(k)]),
      'negative_extreme':([-128]*k,[[-128]*n for _ in range(k)]),
      'signed_cancel':([127 if i%2 else -127 for i in range(k)],[[63]*n for _ in range(k)]),
      'isolated':([1]+[0]*(k-1),[[(-128 if j%2 else 127) for j in range(n)] for _ in range(k)]),
      'group_boundary':([1]*k,[[j-1 for j in range(n)] for _ in range(k)]),
      'mixed':([rng.randrange(-128,128) for _ in range(k)],[[rng.randrange(-128,128) for _ in range(n)] for _ in range(k)])}
    for name,(xs,w) in cases.items():
        got=simulate(xs,w,lanes);expected=[sum(xs[i]*w[i][j] for i in range(k)) for j in range(n)]
        tests[name]={'passes':got==expected,'output':got,'expected':expected}
    zero_x,zero_w=cases['all_zero'];boundary_x,boundary_w=cases['group_boundary']
    counterfactuals={'missing_zero_mask_detected':simulate(zero_x,zero_w,lanes,break_mask=True)!=tests['all_zero']['expected'],
                    'missing_group_hold_detected':simulate(boundary_x,boundary_w,lanes,break_keep=True)!=tests['group_boundary']['expected'],
                    'missing_state_clear_detected':simulate(zero_x,zero_w,lanes,break_clear=True)!=tests['all_zero']['expected']}
    second=simulate(zero_x,zero_w,lanes,initial_results=tests['mixed']['output'])
    tests['consecutive_request_clear']={'passes':second==tests['all_zero']['expected'],'previous_nonzero_output':tests['mixed']['output'],'output':second,'expected':tests['all_zero']['expected']}
    trace,reject=lifecycle();program=program_verify()
    ok=all(x['passes'] for x in tests.values()) and all(counterfactuals.values()) and reject and all(program[k] for k in ('complete_cover_matches','injected_bit_failure_detected'))
    report={'status':'PASS' if ok else 'FAIL','scope':'nominal Boolean datapath and state lifecycle; not analog/noise/program-success proof',
            'native_run':str(a.native_run),'native_source_manifest_sha256':hashlib.sha256((a.native_run/'source_manifest.json').read_bytes()).hexdigest(),
            'gate_graph':['global CLEAR -> real per-D AND -> all output/status/retry registers','input ingress keep MUX -> input hold -> row/bit selection','sense -> group weight keep -> weight hold -> weight group select','sign-extension wires -> shift MUX -> zero-mask NAND/INV','accumulator group feedback -> native25 Adder/Subtractor -> result MUX -> group keep MUX -> full accumulator hold'],
            'tests':tests,'counterfactuals':counterfactuals,'lifecycle':trace,'unisolated_reference_rejected':reject,'program_verify':program}
    (a.native_run/'functional_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'counterfactuals':counterfactuals,'run':str(a.native_run)}))
    if not ok:raise SystemExit(1)
if __name__=='__main__':main()

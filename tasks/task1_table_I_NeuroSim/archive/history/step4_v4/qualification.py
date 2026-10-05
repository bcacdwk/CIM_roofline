#!/usr/bin/env python3
"""Finite distributed-column diagnostics using actual resolved circuit inputs.
A conditional linear DC consistency check, not SPICE, material statistics or ENOB.
"""
import functools
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode=True

def ladder(states,line,series,ron,roff,voltage):
    n=len(states);segment=line/n;equiv=math.inf;down=[]
    for state in reversed(states):
        g=0 if state<0 else 1/(ron if state else roff)
        future=0 if math.isinf(equiv) else 1/(segment+equiv)
        equiv=1/(g+future) if g+future else math.inf
    current=0 if math.isinf(equiv) else voltage/(series+segment+equiv)
    flow=current;v=voltage-current*series;active_v=[]
    for state in states:
        v-=flow*segment
        if state>=0:
            active_v.append(v);flow-=v/(ron if state else roff)
    return current,min(active_v,default=voltage)

def mode_probe(n,line,series,ron,roff,voltage):
    dg=1/ron-1/roff;records=[]
    for active_count in (1,n//2,n):
        for placement in ('near','far','spread'):
            active=list(range(active_count)) if placement=='near' else list(range(n-active_count,n)) if placement=='far' else [i*n//active_count for i in range(active_count)]
            for count in sorted(set([0,1,active_count//2,active_count])):
                for data_place in ('near','far'):
                    chosen=set(active[:count] if data_place=='near' else (active[-count:] if count else []));active_set=set(active)
                    states=tuple(1 if r in chosen else 0 if r in active_set else -1 for r in range(n))
                    reference=tuple(0 if r in active_set else -1 for r in range(n))
                    data_i,minv=ladder(states,line,series,ron,roff,voltage);ref_i,_=ladder(reference,line,series,ron,roff,voltage)
                    estimate=(data_i-ref_i)/(voltage*dg)
                    records.append({'active':active_count,'ones':count,'placement':placement,'ones_placement':data_place,'count_estimate':estimate,'error_count':estimate-count,'min_cell_voltage_V':minv})
    dense=next(r for r in records if r['active']==n and r['ones']==n)
    worst=max(records,key=lambda r:abs(r['error_count']))
    return {'rows':n,'line_ohm':line,'terminal_mux_ohm':series,'dense_count_estimate':dense['count_estimate'],'dense_gain_ratio':dense['count_estimate']/n,'max_abs_error_count':abs(worst['error_count']),'worst_pattern':worst,'minimum_cell_voltage_V':min(r['min_cell_voltage_V'] for r in records),'sample_count':len(records),'samples':records}

def vector_probe(p,raw):
    n=p['bank_rows'];banks=p['banks'];K=n*banks;N=p['logical_N'];line=raw['res_col_ohm'];series=raw['mux_res_tg_ohm'];ron=raw['r_on_ohm'];roff=raw['r_off_ohm'];v=p['read_voltage_V'];gain=raw['nominal_adc_gain_codes_per_A'];levels=raw['resolved_adc_levels'];scale=raw['nominal_adc_codes_per_count']
    @functools.lru_cache(None)
    def adc(states):
        current,_=ladder(states,line,series,ron,roff,v);code=math.floor(current*gain+.5+1e-10)
        assert 0<=code<levels
        return code
    dense=[[((r*37+j*19)%256)-128 for j in range(N)] for r in range(K)]
    patterns={'zero_input':([0]*K,dense),'zero_weights':([((r*53)%256)-128 for r in range(K)],[[0]*N for _ in range(K)]),'full_positive':([127]*K,[[127]*N for _ in range(K)]),'negative_extremes':([-128]*K,[[-128]*N for _ in range(K)]),'signed_cancel':([127 if r%2 else -127 for r in range(K)],[[127]*N for _ in range(K)]),'mixed':([((r*53)%256)-128 for r in range(K)],dense)}
    result={}
    for name,(x,W) in patterns.items():
        pass_values=[]
        for phase in range(2):
            total=[0]*32
            for b in range(banks):
                accum=[0]*32
                for plane in range(8):
                    q=[(x[b*n+r]&255) if phase==0 else int(x[b*n+r]<0) for r in range(n)]
                    active=[r for r in range(n) if (q[r]>>plane)&1];active_set=set(active)
                    ref=adc(tuple(0 if r in active_set else -1 for r in range(n)))
                    for j in range(32):
                        weight_state=0
                        for bit in range(8):
                            states=tuple((((W[b*n+r][j]+128) if j<N else 1)>>bit)&1 if r in active_set else -1 for r in range(n))
                            diff=adc(states)-ref
                            assert diff>=0
                            weight_state=(weight_state>>1)+(diff<<7)
                        accum[j]=(accum[j]>>1)+(weight_state<<7)
                total=[a+b for a,b in zip(total,accum)]
            pass_values.append(total)
        A,B=pass_values
        got=[(A[j]-(A[-1]<<7)-(B[j]<<8)+(B[-1]<<15))/scale for j in range(N)]
        wanted=[sum(x[r]*W[r][j] for r in range(K)) for j in range(N)]
        errors=[a-b for a,b in zip(got,wanted)]
        result[name]={'max_abs_output_error':max(map(abs,errors)),'mean_signed_error':sum(errors)/N,'max_error_over_INT8_dot_fullscale':max(map(abs,errors))/(K*128*128),'exact_min':min(wanted),'exact_max':max(wanted),'observed_min':min(got),'observed_max':max(got),'zero_exact_output_max_abs_residual':max([abs(a) for a,b in zip(got,wanted) if b==0],default=0),'max_relative_error_nonzero_only':max([abs((a-b)/b) for a,b in zip(got,wanted) if b!=0],default=None)}
    return result

def main(out):
    rows=json.loads((out/'summary.json').read_text())['case_results'];records={}
    for r in rows:
        if r['case_id']!='ns_rram_1t1r':continue
        base=out/r['case_id']/r['scenario'];raw=json.loads((base/'resolved.json').read_text());p=json.loads((base/'input.json').read_text())['resolved_parameters']
        args=(p['bank_rows'],raw['res_col_ohm'],raw['mux_res_tg_ohm'],raw['r_on_ohm'],raw['r_off_ohm'],p['read_voltage_V'])
        actual=mode_probe(*args);twice=mode_probe(args[0],args[1],args[2]*2,*args[3:]);source=mode_probe(args[0],args[1],args[2]+args[3]*.25,*args[3:])
        old=mode_probe(p['logical_K'],args[1]*p['banks'],0,*args[3:])
        records[r['paired_id']]={'status':'conditional_linear_DC_consistency_diagnostic','actual_resolved_inputs':{'Ron_path_ohm':args[3],'Roff_path_ohm':args[4],'column_line_ohm':args[1],'mux_series_ohm':args[2],'read_voltage_V':args[5]},'actual':actual,'two_times_mux_resistance_diagnostic':{k:v for k,v in twice.items() if k!='samples'},'nonstiff_source_counterfactual':{k:v for k,v in source.items() if k!='samples'},'unsegmented_256row_counterfactual':{k:v for k,v in old.items() if k!='samples'},'quantized_Q4_mapped_vectors':vector_probe(p,raw),'ADC_gain_codes_per_A':raw['nominal_adc_gain_codes_per_A'],'verify_codes':[raw['verify_expected_HRS_code'],raw['verify_expected_LRS_code']]}
    result={'status':'DIAGNOSTIC_CONDITIONAL_NOT_PRECISION_CERTIFICATION','model':'linear distributed column ladder with ideal CMOS+RRAM path resistors and stiff opposite rail; actual native mux terminal resistance','limitations':['No stochastic RRAM, nonlinear access I-V, ADC noise/ENOB, supply compliance or complete layout extraction.','Finite input/state patterns; reported extrema are not an all-matrix mathematical bound.','No fitted endpoint correction is applied to performance or numerical output.','Q4 labels preserve quantizer resolution, not measured analog accuracy. Signed cancellation may have nonzero absolute residual.'],'SRAM_ACIM':'256-row read stability and analog transfer remain assumed and unverified; timing improvements do not establish them.','DCIM':'Nominal digital mapping and register lifecycle checked separately, not SRAM stability or clock-tree signoff.','paired_results':records}
    (out/'qualification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(result['status'])
if __name__=='__main__':main(Path(sys.argv[1]))

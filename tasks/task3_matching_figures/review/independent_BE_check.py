#!/usr/bin/env python3
"""Independent audit of candidates B/E from original accepted Task I/II values.

Does not import the Task III interface or either candidate's implementation.
Writes only this report's JSON and Markdown files in review/.
"""
import json
import csv
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASK3=HERE.parent
REPO=TASK3.parent.parent
TASK1=REPO/'tasks/task1_table_I_NVM/analysis'
TASK2=REPO/'tasks/task2_table_II_workloads/table_IIb/04_crosscheck/data'


def read_json(path):
    return json.loads(path.read_text())


def follow_pointer(root, pointer):
    path, fragment=pointer.split('#')
    value=read_json(root/path)
    for bit in fragment.strip('/').split('/'):
        value=value[int(bit)] if isinstance(value,list) else value[bit]
    return value


def approx(actual, expected):
    assert math.isclose(actual, expected, rel_tol=2e-12, abs_tol=1e-12), (actual,expected)


def status_from_times(stream_ns, resident_ns):
    if math.isclose(stream_ns,resident_ns,rel_tol=1e-12): return 'balanced'
    return 'resident-bound' if resident_ns>stream_ns else 'streaming-bound'


def main():
    shared=read_json(TASK3/'shared/data.json')
    raw={}
    # Source locators come from the index, but every numerical expectation below
    # is recomputed from each accepted source's original mapping interface.
    for row in shared['hardware']:
        raw[(row['case_id'],row['profile'])]=follow_pointer(TASK1,row['source_mapping'])
    source_workloads={r['case_id']:r for r in read_json(TASK2/'results.json')['cases']}
    source_models={r['model_id']:r for r in read_json(TASK2/'model_inputs.json')['models']}
    b=read_json(TASK3/'02_demand_dual/plotted_data.json')
    b_checks=[]
    neighborhood=[]
    for w in b['workloads']:
        src=source_workloads[w['case_id']]
        model=source_models[w['model_id']]
        D=model['D']; u=src['U']
        components=src['components']
        nproj=sum(c['shape_N_K'][0] for c in components)
        assert all(c['shape_N_K'][1]==D for c in components)
        qs=u*D; qr=D*nproj
        assert sum(c['Q_S'] for c in components)-src['result']['shared_input_bytes_removed']==qs
        assert sum(c['Q_R'] for c in components)==qr
        assert src['result']['Q_S']==w['Q_S_Byte']==qs
        assert src['result']['Q_R']==w['Q_R_Byte']==qr
        assert src['result']['shared_input_bytes_removed']==w['shared_input_bytes_removed']
        assert D%128==0 and nproj%128==0
        mk=D//128; mn=nproj//128; tiles=mk*mn
        assert (w['m_K'],w['m_N'],w['tile_count'])==(mk,mn,tiles)
        assert w['native_accumulated_Q_S_Byte']==tiles*u*128==mn*qs
        assert w['native_accumulated_Q_R_Byte']==tiles*128**2==qr
        for ray in [r for r in b['rays'] if r['model_id']==w['model_id']]:
            h=raw[(ray['case_id'],ray['profile'])]
            assert h['K']==h['N']==128 and h['b_S']==h['b_R']==1
            tr=h['T_R_ns']; ds=h['delta_S_ns']
            # Derive by accumulated service time rather than the shared formula.
            t_stream=tiles*u*ds; t_resident=tiles*tr
            effective_rho=qs/t_stream*1000
            effective_tau=qr/t_resident*1000
            slope=effective_rho/effective_tau
            for actual,expected in [
                (ray['rho_effective_MB_per_s'],effective_rho),
                (ray['tau_effective_MB_per_s'],effective_tau),
                (ray['RI_star_effective'],slope),
                (ray['U_star'],tr/ds),
                (ray['T_R_all_tiles_ns'],t_resident),
                (ray['streaming_ns_per_model_vector'],tiles*ds),
            ]: approx(actual,expected)
            c=next(c for c in b['classifications'] if c['workload_case_id']==w['case_id'] and c['hardware_case_id']==ray['case_id'])
            expected_status=status_from_times(t_stream,t_resident)
            assert c['bottleneck']==expected_status
            approx(c['demand_above_ray_factor'],qs/(slope*qr))
            approx(c['component_T_S_over_T_R'],t_stream/t_resident)
            # Capability-plane sign is opposite to demand-plane sign.
            sigma=(h['N']*h['B_S_Byte']/ds)*1000
            tau=(h['B_R_Byte']/tr)*1000
            cap_status='resident-bound' if sigma>u*tau else 'streaming-bound'
            demand_status='streaming-bound' if qs>slope*qr else 'resident-bound'
            assert cap_status==demand_status==expected_status
            b_checks.append({'workload':w['case_id'],'hardware':ray['case_id'],
                'native_tiles':tiles,'logical_Q_S_Byte':qs,'logical_Q_R_Byte':qr,
                'native_input_replay':mn,'T_S_ns':t_stream,'T_R_ns':t_resident,
                'effective_ray_slope':slope,'classification':expected_status})
    for ray in b['rays']:
        h=raw[(ray['case_id'],ray['profile'])]
        model=source_models[ray['model_id']]
        source=next(w for w in source_workloads.values() if w['model_id']==ray['model_id'] and w['workload']=='qkv_projection' and w['kind']=='finite')
        nproj=sum(c['shape_N_K'][0] for c in source['components'])
        threshold=h['T_R_ns']/h['delta_S_ns']
        for multiple in [.999,1,1.001]:
            u=multiple*threshold
            time_status=status_from_times(u*h['delta_S_ns'],h['T_R_ns'])
            demand_ratio=(u*model['D'])/(ray['RI_star_effective']*model['D']*nproj)
            approx(demand_ratio,multiple)
            expected='balanced' if multiple==1 else ('resident-bound' if multiple<1 else 'streaming-bound')
            assert time_status==expected
            neighborhood.append({'candidate':'B','model':ray['model_id'],'hardware':ray['case_id'],
                'threshold_multiplier':multiple,'classification':expected,'demand_above_ray_factor':demand_ratio})
    e=read_json(TASK3/'05_improvement_payoff/plotted_data.json')
    e_checks=[]
    e_neighborhood=[]
    curve_count=0
    for case in e['cases']:
        h=raw[(case['hardware_case_id'],case['profile'])]
        u=case['U']; k=h['K']; n=h['N']
        tr=h['T_R_ns']; ds=h['delta_S_ns']
        ts=u*ds; qs=u*k; qr=k*n
        denom=max(ts,tr)
        base=qs/denom*1000
        status=status_from_times(ts,tr)
        assert case['baseline_bottleneck']==status
        assert case['native_demand']['Q_S_Byte']==qs
        assert case['native_demand']['Q_R_Byte']==qr
        approx(case['baseline_bound_MB_per_s'],base)
        limit=max(ts,tr)/min(ts,tr)
        approx(case['gain_ceiling_for_improving_bottleneck_route'],limit)
        approx(case['bottleneck_route_capability_multiplier_at_balance'],limit)
        # Improving a capability factor f divides that component's service time.
        # This independently derives the gain as max(TS,TR)/max(TS/f,TR).
        for factor,gs,gr in zip(case['factor'],case['streaming_only_gain'],case['resident_only_gain']):
            expected_s=denom/max(ts/factor,tr)
            expected_r=denom/max(ts,tr/factor)
            approx(gs,expected_s); approx(gr,expected_r);curve_count+=2
        sg2=denom/max(ts/2,tr);rg2=denom/max(ts,tr/2)
        approx(case['gain_at_2x']['streaming_only'],sg2)
        approx(case['gain_at_2x']['resident_only'],rg2)
        e_checks.append({'hardware':case['hardware_case_id'],'U':u,'K':k,'N':n,
            'U_star':tr/ds,'T_S_ns':ts,'T_R_ns':tr,'baseline_bound_MB_per_s':base,
            'classification':status,'streaming_gain_at_2x':sg2,'resident_gain_at_2x':rg2,
            'bottleneck_gain_cap':limit})
    for cid in sorted({c['hardware_case_id'] for c in e['cases']}):
        h=raw[(cid,'reference')]
        threshold=h['T_R_ns']/h['delta_S_ns']
        for multiple in [.999,1,1.001]:
            u=multiple*threshold;ts=u*h['delta_S_ns'];tr=h['T_R_ns']
            normalized_bound=(u*h['K']/max(ts,tr))/(h['K']/h['delta_S_ns'])
            approx(normalized_bound,min(multiple,1))
            status=status_from_times(ts,tr)
            expected='balanced' if multiple==1 else ('resident-bound' if multiple<1 else 'streaming-bound')
            assert status==expected
            e_neighborhood.append({'hardware':cid,'threshold_multiplier':multiple,
                'normalized_bound':normalized_bound,'classification':status,
                'streaming_gain_at_2x':max(ts,tr)/max(ts/2,tr),
                'resident_gain_at_2x':max(ts,tr)/max(ts,tr/2)})
    # Check actual exported candidate records where hardware/reuse cases overlap.
    with (TASK3/'03_reuse_threshold/data/plotted_thresholds.csv').open() as f:
        c_rows={(r['case_id'],r['profile']):r for r in csv.DictReader(f)}
    with (TASK3/'04_normalized_response/data/scan_points.csv').open() as f:
        d_rows={(r['case_id'],int(r['U'])):r for r in csv.DictReader(f)}
    a_points={(r['case_id'],r['profile']):r for r in read_json(TASK3/'01_hardware_overlay/plotted_data.json')['points']}
    cross_checks=[]
    for r in b_checks+e_checks:
        cid=r['hardware']
        u=r.get('U', source_workloads[r['workload']]['U'] if 'workload' in r else None)
        status=r['classification']
        ref=c_rows[(cid,'reference')]
        approx(float(ref['U_star']),raw[(cid,'reference')]['T_R_ns']/raw[(cid,'reference')]['delta_S_ns'])
        targets=[]
        if f'at_U_{u}' in ref:
            assert ref[f'at_U_{u}']==status;targets.append('C')
        if (cid,u) in d_rows:
            assert d_rows[(cid,u)]['classification']==status;targets.append('D')
        if u==128:
            assert a_points[(cid,'reference')]['at_U128']==status;targets.append('A')
        if targets:cross_checks.append({'hardware':cid,'U':u,'classification':status,'agree_with':targets})
    report={'status':'pass' ,'independence':'No shared/interface.py or candidate build module imported; expectations use original Task I mapping-interface T_R and delta_S plus original Task II model inputs/components.',
            'B':{'workload_points':len(b['workloads']),'rays':len(b['rays']),
                 'cross_plane_checks':b_checks,'threshold_neighborhood':neighborhood,
                 'logical_resident_load_ratio_MiMo_over_Qwen':166723584/10485760,
                 'logical_streaming_demand_ratio_at_equal_U':6144/2048,
                 'ray_slope_ratio_Qwen_over_MiMo':27136/5120},
            'E':{'cases':e_checks,'analytic_curve_values_checked':curve_count,'threshold_neighborhood':e_neighborhood},
            'cross_candidate_export_checks':cross_checks,
            'visual_review':{'B':'PASS: final merged-PDF 144 dpi render viewed; last 1 GiB tick is inside page, logical byte positions/model-specific rays/side labels consistent; caption read.','E':'PASS: final 7.16 x 4.15 in PNG viewed; bottom legend/xlabel and note/footer collisions resolved; gain-cap wording and caption consistent.'}}
    (HERE/'independent_BE_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],len(b_checks),'B component-time checks;',curve_count,'E curve values;',len(neighborhood)+len(e_neighborhood),'threshold checks;',len(cross_checks),'cross-candidate comparisons')

if __name__=='__main__': main()

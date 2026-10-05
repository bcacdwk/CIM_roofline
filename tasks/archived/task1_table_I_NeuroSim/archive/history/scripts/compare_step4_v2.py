#!/usr/bin/env python3
"""Read-only V3 -> Step4 V1 -> V2 comparison, after actual service runs.

python3 compare_step4_v2.py <new_local_run> [--out <small_artifact_directory>]
No saved total is fed into production simulation.
"""
import argparse
import csv
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args(); out = args.out or args.run; out.mkdir(parents=True, exist_ok=True)
    task = args.run / 'snapshot/tasks/task1_table_I_NeuroSim'
    summary = json.loads((args.run / 'summary.json').read_text()); rows = []; details = []
    names = ['SRAM ACIM','SRAM DCIM','2D NOR','3D NAND','RRAM','MRAM','PCM','HZO FeRAM','GC-04','垂直 AND FeFET']
    for row in summary['case_results']:
        cid = row['case_id']; name=names[int(cid[:2])-1]
        new = json.loads((args.run / cid / 'result.json').read_text())
        old = json.loads((task / 'results/step4/reference-final-20261004' / cid / 'result.json').read_text())
        assert new['identity']['input_sha256'] == old['identity']['input_sha256']
        new_resolved=json.loads((args.run/cid/'resolved.json').read_text())
        old_resolved=json.loads((task/'results/step4/reference-final-20261004'/cid/'resolved.json').read_text())
        assert new_resolved['native_parameters_ns'] == old_resolved['native_parameters_ns']
        replay = json.loads((args.run / cid / 'replay.json').read_text())
        case = json.loads((task / 'configs/cases' / (cid+'.json')).read_text()); l = case['logical']
        alpha = replay.get('maintenance_availability', 1.)
        native_s, native_r = replay['raw_delta_S_ns'], replay['raw_T_R_ns']
        n_rho = l['B_S_Byte']*1e3/native_s*alpha; n_tau=l['B_R_Byte']*1e3/native_r*alpha
        current = dict(case_id=cid, name=name, K=l['K'], N=l['N'],
            NVM_delta_S_ns=native_s, NVM_T_R_ns=native_r, NVM_rho_MB_s=n_rho, NVM_tau_MB_s=n_tau,
            V1_delta_S_ns=old['streaming']['delta_S_ns'], V1_T_R_ns=old['resident_load']['T_R_ns'],
            V1_rho_MB_s=old['derived_metrics']['rho_Byte_per_s']/1e6,
            V1_tau_MB_s=old['derived_metrics']['tau_Byte_per_s']/1e6,
            V2_delta_S_ns=new['streaming']['delta_S_ns'], V2_T_R_ns=new['resident_load']['T_R_ns'],
            V2_rho_MB_s=new['derived_metrics']['rho_Byte_per_s']/1e6,
            V2_tau_MB_s=new['derived_metrics']['tau_Byte_per_s']/1e6,
            V1_period_ns=old['clocks'][0]['actual_period_ns'], V2_period_ns=new['clocks'][0]['actual_period_ns'],
            V2_RI_star=new['derived_metrics']['RI_star'], V2_U_star=new['derived_metrics']['U_star'],
            V2_availability=new['maintenance'].get('availability',1.))
        pe = sum(s.get('service_time_total_ns',0.) for s in new['stages'] if s['service_kind']=='resident' and
                 (s['stage_id'].startswith('page_program') or s['stage_id'] in ('sector_erase.complete_cycle','block_erase')))
        rows.append(current)
        details.append({'case_id': cid, 'native_PE_retained_ns': pe or None,
            'native_PE_fraction_of_resident_time': pe/new['resident_load']['T_R_ns'] if pe else None,
            'V1_to_V2': new.get('V1_comparison'), 'NVM_to_V2': new['comparison'],
            'maintenance': new['maintenance'], 'preserved_native_parameters': True})
    payload = {'units': 'ns, decimal MB/s; logical Byte only', 'comparison_inputs_usage':'comparison after new actual aggregation only',
               'GC_policy': 'rho/tau effective in all three columns; raw S/R separately saved; V2 actual frame obeys retention',
               'rows': rows, 'causes': details}
    (out/'comparison.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    with (out/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    lines=['|案例；K×N|NVM ρ / τ|V1 ρ / τ|V2 ρ / τ|周期 V1→V2 ns|V2 RI* / U*|',
           '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"|{r['name']}；{r['K']}×{r['N']}|{r['NVM_rho_MB_s']:.6g} / {r['NVM_tau_MB_s']:.6g}|{r['V1_rho_MB_s']:.6g} / {r['V1_tau_MB_s']:.6g}|{r['V2_rho_MB_s']:.6g} / {r['V2_tau_MB_s']:.6g}|{r['V1_period_ns']:g} → {r['V2_period_ns']:g}|{r['V2_RI_star']:.6g} / {r['V2_U_star']:.6g}|")
    (out/'comparison_table.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'PASS','comparison_rows':len(rows),'out':str(out)},ensure_ascii=False))


if __name__=='__main__': main()

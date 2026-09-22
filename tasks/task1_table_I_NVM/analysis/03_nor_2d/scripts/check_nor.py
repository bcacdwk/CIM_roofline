#!/usr/bin/env python3
"""Read-only recomputation/validation; --emit explicitly refreshes JSON and TeX."""
import argparse
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SHARED = BASE.parent / 'shared_baseline'
CORPUS = BASE.parents[1]
spec = importlib.util.spec_from_file_location('shared_nor_api', SHARED/'scripts/check_shared.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
I = json.loads((BASE/'data/inputs.json').read_text())
L, R, C = s.L, s.R, s.C

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def provenance():
    ids = {e['source_id'] for e in I['reported_evidence']}
    manifest = json.loads((CORPUS/'source_manifest.json').read_text())
    sources = {x['source_id']: {k:x[k] for k in ['title','year','pdf']} for x in manifest['sources'] if x['source_id'] in ids}
    for x in sources.values():
        assert digest(CORPUS/x['pdf']['path']) == x['pdf']['sha256']
    return {'baseline_id':s.D['baseline_id'], 'shared_sha256': {
        'data/shared_parameters.json':digest(SHARED/'data/shared_parameters.json'),
        'scripts/check_shared.py':digest(SHARED/'scripts/check_shared.py')}, 'sources':sources}

def layout(slices_per_sector):
    slices = R['dcim']['rows_per_group']
    capacity = L['resident_capacity_Byte']
    native = I['mapping']
    per_slice = capacity//slices
    assert capacity % slices == 0
    assert slices % slices_per_sector == 0
    pages_per_slice = per_slice//native['page_Byte']
    assert per_slice % native['page_Byte'] == 0
    assert slices_per_sector*per_slice <= native['sector_Byte']
    return dict(read_slices=slices, read_slices_per_sector=slices_per_sector,
        sense_amplifiers_per_slice=R['dcim']['output_lanes']*int(8*L['b_R']),
        sense_amplifiers_total=slices*R['dcim']['output_lanes']*int(8*L['b_R']),
        logical_Byte_per_slice=per_slice, pages_per_slice=pages_per_slice,
        page_Byte=native['page_Byte'], sector_Byte=native['sector_Byte'],
        page_programs=slices*pages_per_slice, sector_erases=slices//slices_per_sector,
        effective_pages_per_erase=slices_per_sector*pages_per_slice,
        allocated_physical_Byte=slices//slices_per_sector*native['sector_Byte'],
        logical_capacity_Byte=capacity, logical_storage_bits=int(capacity*8),
        write_domains=R['resident']['write_domains'],
        write_data_lanes=R['resident']['physical_write_data_lanes'])

def evaluate(x, name='main', slices_per_sector=None, read_override=None):
    m = layout(slices_per_sector or I['mapping']['read_slices_per_sector'])
    v = C['propagation']['profile_values'][x['profile']]
    read = x['read_full_ns'] if read_override is None else read_override
    ds, counts = s.dcim_service(R['dcim'], v, read)
    p = dict(logical_page_Byte=m['page_Byte'], mapped_page_bits=m['page_Byte']*8,
        first_data_in_command=False, page_program_full_us=x['page_program_ms']*1000,
        erase_us=x['sector_erase_ms']*1000, pages_per_erase=m['effective_pages_per_erase'])
    br_page, dr_page, beats = s.page_service(p,v['digital_tick'])
    erase_control = R['resident']['control_ticks']*v['digital_tick']
    dr_page += erase_control/m['effective_pages_per_erase']
    dr = m['page_programs']*dr_page
    br = m['page_programs']*br_page
    page_front = s.front_ns(p['mapped_page_bits'],v['digital_tick'],False)[0]
    stages = dict(page_data_and_control=m['page_programs']*page_front,
        erase_control=m['sector_erases']*erase_control,
        internal_page_program=m['page_programs']*x['page_program_ms']*1e6,
        internal_sector_erase=m['sector_erases']*x['sector_erase_ms']*1e6)
    read_stages = dict(binary_read=counts['read_rounds']*read,
        digital_reduction=counts['digital_ticks']*v['digital_tick'],
        input_output_boundary=R['dcim']['boundary_ticks']*v['digital_tick'])
    result = dict(id=name+'_'+x['id'], profile=x['profile'], baseline_id=s.D['baseline_id'],
        configuration_id=R['id'], mode=I['mode'], mapping=m,
        periphery_ns=v, media_budget=dict(read_full_ns=read,page_program_ms=x['page_program_ms'],
            sector_erase_ms=x['sector_erase_ms'], write_column=x['write_evidence_column']),
        operation_counts={**counts, 'page_programs':m['page_programs'],'sector_erases':m['sector_erases'],
            'data_beats_per_page':beats,'data_beats_total':beats*m['page_programs']},
        read_stages_ns=read_stages, write_stages_ns=stages,
        page_equivalent=dict(B_R_Byte=br_page,delta_R_ns=dr_page,
            effective_pages_per_erase=m['effective_pages_per_erase']),
        dominant_read_stage=max(read_stages,key=read_stages.get),
        dominant_write_stage=max(stages,key=stages.get),
        binary_read_fraction=read_stages['binary_read']/ds,
        erase_fraction=stages['internal_sector_erase']/dr,
        source_ids=['NOR-01','NOR-02'], source_role='complementary transferred binary budgets',
        **s.metrics(L['B_S_Byte'],br,ds,dr))
    assert math.isclose(sum(stages.values()),dr,rel_tol=1e-12)
    assert math.isclose(sum(read_stages.values()),ds,rel_tol=1e-12)
    assert br == L['resident_capacity_Byte']
    assert math.isclose(br_page/s.seconds(dr_page,'ns'), result['tau_Byte_per_s'],rel_tol=1e-12)
    return result

def compute():
    main=[evaluate(x) for x in I['scenarios']]
    ref=next(x for x in I['scenarios'] if x['id']=='reference')
    contrast=evaluate(ref,'private_sector',I['mapping']['private_sector_contrast_read_slices_per_sector'])
    reference=main[1]
    contrast['ratios_to_reference']={key:contrast[key]/reference[key] for key in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    sensitivity=[evaluate(ref,f'read_x{f:g}',read_override=ref['read_full_ns']*f) for f in [.8,1.2]]
    for row in sensitivity:
        row['rho_relative_change']=row['rho_Byte_per_s']/reference['rho_Byte_per_s']-1
        row['ridge_relative_change']=row['ridge']/reference['ridge']-1
    return dict(case_id=I['case_id'],baseline_id=s.D['baseline_id'],mode=I['mode'],
        units=dict(payload='Byte',interval='ns',rate='Byte/s',display_rate='decimal MB/s',ridge='dimensionless'),
        provenance=provenance(), scenarios=main, organization_contrast=contrast,
        read_budget_sensitivity=sensitivity,
        paired_ranges={key:[min(r[key] for r in main),max(r[key] for r in main)] for key in ['rho_Byte_per_s','tau_Byte_per_s','ridge']},
        interpretation='conditional paired reference designs, not material bounds or same-chip measured pairs')

def tex_results(d):
    lines=[r'% Generated by scripts/check_nor.py --emit.',r'\begin{table}[htbp]\centering\small',
        r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
        r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ms) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\mathrm{RI}^{*}$\\\midrule']
    for label,row in zip(['短','参考','长'],d['scenarios']):
        lines.append(f"{label} & {row['delta_S_ns']/1000:.3f} & {row['delta_R_ns']/1e6:.6f} & {row['rho_Byte_per_s']/1e6:.4g} & {row['tau_Byte_per_s']/1e6:.4g} & {row['ridge']:.4g}\\\\")
    lines += [r'\bottomrule\end{tabular}',r'\caption{同一 binary 本地感测＋数字归约映射的三组条件配对预算。MB/s 为十进制。每行 $B_S=128$ Byte、$B_R=16384$ Byte；显示位数仅供复算。}\label{03_nor_2d:tab:nor-results}\end{table}']
    return '\n'.join(lines)+'\n'

def tex_contrast(d):
    lines=[r'% Generated by scripts/check_nor.py --emit.',r'\begin{table}[htbp]\centering\small',
        r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
        r'组织 & 分配容量 & 擦除数 & $\Delta_R$ (ms) & $\tau$ (MB/s) & $\mathrm{RI}^{*}$\\\midrule']
    for label,row in [('主布局',d['scenarios'][1]),('独占 sector',d['organization_contrast'])]:
        lines.append(f"{label} & {row['mapping']['allocated_physical_Byte']//1024} KiB & {row['mapping']['sector_erases']} & {row['delta_R_ns']/1e6:.6f} & {row['tau_Byte_per_s']/1e6:.4g} & {row['ridge']:.4g}\\\\")
    lines += [r'\bottomrule\end{tabular}',r'\caption{保持 32 个读分片、4096 SA 和参考读时间，只改变读分片与擦除域的归属。两行 $\rho$ 相同，物理容量不要求相等。}\label{03_nor_2d:tab:nor-contrast}\end{table}']
    return '\n'.join(lines)+'\n'

def validate(d):
    assert I['baseline_id']==s.D['baseline_id']
    assert R['resident']['write_domains']==I['mapping']['write_domains']==1
    m=d['scenarios'][1]['mapping']; n=d['scenarios'][1]['operation_counts']
    assert (m['read_slices'],m['sense_amplifiers_total'],m['page_programs'],m['sector_erases'])==(32,4096,64,4)
    assert n['compute_rounds']==n['read_rounds']==256
    # Independent enumeration of bit products, slice and native page placement.
    seen=set()
    for i in range(L['n_in']):
        sl=i % m['read_slices']; local_row=i//m['read_slices']
        sector=sl//m['read_slices_per_sector']; slot=sl % m['read_slices_per_sector']
        for o in range(L['n_out']):
            address=slot*m['logical_Byte_per_slice']+local_row*L['n_out']+o
            assert 0<=address<m['sector_Byte']
            seen.add((sector,address))
    assert len(seen)==L['resident_capacity_Byte']
    assert len({(sec,adr//m['page_Byte']) for sec,adr in seen})==m['page_programs']
    assert n['compute_rounds']*R['dcim']['rows_per_group']*R['dcim']['output_lanes']*8==8*8*L['n_in']*L['n_out']
    # Hand arithmetic check uses the recorded reference evidence, without reusing service functions.
    rr=d['scenarios'][1]
    assert rr['delta_S_ns']==256*(120+5)+2*5==32010
    assert rr['delta_R_ns']==4*45e6+64*.4e6+(64*18+4*2)*5==205605800
    assert math.isclose(rr['ridge'],(128/16384)*205605800/32010,rel_tol=1e-12)
    private=d['organization_contrast']
    assert private['mapping']['effective_pages_per_erase']==2
    assert private['mapping']['allocated_physical_Byte']==131072
    assert private['delta_S_ns']==rr['delta_S_ns']
    assert private['delta_R_ns']==32*45e6+64*.4e6+(64*18+32*2)*5
    for row in d['scenarios']+[private]+d['read_budget_sensitivity']:
        assert row['B_S_Byte']==L['B_S_Byte'] and row['B_R_Byte']==L['resident_capacity_Byte']
        assert math.isclose(row['ridge'],row['rho_Byte_per_s']/row['tau_Byte_per_s'],rel_tol=1e-12)
        assert 0<row['erase_fraction']<1
    assert I['stage_coverage']['read_write_overlap'] is False
    return dict(passed=True,checks=['shared API/hash/source PDF identity','R0 operation counts and binary exactness coverage',
        'matrix-to-slice-to-page-to-sector bijection','single update domain and physical sector utilization',
        'complete self-timed stage coverage without added verify/HV retries','page versus matrix aggregation',
        'reference independent hand arithmetic and SI units','paired scenarios and organization contrast'])

def files():
    d=compute();checks=validate(d)
    return {'data/results.json':json.dumps(d,ensure_ascii=False,indent=2)+'\n',
        'data/provenance.json':json.dumps(provenance(),ensure_ascii=False,indent=2)+'\n',
        'data/validation.json':json.dumps(checks,ensure_ascii=False,indent=2)+'\n',
        'tex/generated_results.tex':tex_results(d),'tex/generated_contrast.tex':tex_contrast(d)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--emit',action='store_true');args=ap.parse_args()
    for path,value in files().items():
        if args.emit:(BASE/path).write_text(value)
        else:assert (BASE/path).read_text()==value,'stale or absent generated artifact: '+path
    print('NOR: shared baseline, source hashes, mapping, paired services and generated files verified.')
    ref=compute()['scenarios'][1]
    print(json.dumps({k:ref[k] for k in ['delta_S_ns','delta_R_ns','rho_Byte_per_s','tau_Byte_per_s','ridge']},ensure_ascii=False))

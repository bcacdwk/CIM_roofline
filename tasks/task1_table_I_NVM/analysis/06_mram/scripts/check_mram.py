#!/usr/bin/env python3
"""Read-only recomputation/contract checks. --emit explicitly refreshes results/TeX."""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[1]
SHARED = BASE.parent / 'shared_baseline'
CORPUS = BASE.parents[1]
spec = importlib.util.spec_from_file_location('shared_model', SHARED/'scripts/check_shared.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
I = json.loads((BASE/'data/inputs.json').read_text())
M = I['mapping']
CFG = {**api.R['dcim'], **I['stream_configuration_overrides']}
L = api.logical_configuration(**{k:I['logical_configuration'][k] for k in ['K','N','b_S','b_R']})


def calculate(s, attempts=None):
    v = api.C['propagation']['profile_values'][s['profile']]
    td = v['digital_tick']
    ds, counts = api.dcim_service(CFG, v, s['read_response_ns'],L)
    front, beats = api.front_ns(M['encoded_load_bits'], td, M['first_data_in_command'])
    physical_writes = M['first_phase_active_MTJs'] + M['second_phase_active_MTJs']
    steps = [dict(count=1, drive_program_ns=s['write_access_slot_ns'], verify_ns=0, recover_ns=M['polarity_switch_ticks']*td),
             dict(count=1, drive_program_ns=s['write_access_slot_ns'], verify_ns=0, recover_ns=0),
             dict(count=M['verify_branch_batches'], drive_program_ns=0, verify_ns=s['read_response_ns'],
                  recover_ns=(M['verify_capture_ticks_per_batch']+M['compare_ticks_per_verify_batch'])*td)]
    one = api.program_sequence_ns(0, 0, steps)
    finite_attempts = I['retry_model']['main_attempts'] if attempts is None else attempts
    dr = front + finite_attempts*one
    br = M['logical_weights_per_write_group']*L['b_R']
    result = api.metrics(L['B_S_Byte'], br, ds, dr)
    load=api.full_load_service(L,[dict(payload_Byte=br,service_ns=dr,count=L['resident_capacity_Byte']//br)])
    interface=api.mapping_metrics(L,ds,load['T_R_ns'])
    result.update(mapping_interface=interface,full_load=load,
                  maintenance_service=dict(raw=dict(interface),effective=dict(interface),availability=1,feasible=True,
                      maintenance_payload_Byte=0,refresh_ns=0,restore_ns=0),
                  scenario_type='paired_engineering_scenario' if attempts is None else 'finite_retry_comparison',profile=s['profile'], baseline_id=api.D['baseline_id'], mode=I['mode'],
                  granularity='one vector / one 8-Byte completed write group',
                  read_response_ns=s['read_response_ns'], write_access_slot_ns=s['write_access_slot_ns'],
                  stream_counts=counts, resident_counts=dict(encoded_data_beats=beats,
                      first_phase_MTJ_commands=M['first_phase_active_MTJs'], second_phase_MTJ_commands=M['second_phase_active_MTJs'],
                      total_MTJ_commands_per_attempt=physical_writes, verify_batches=M['verify_branch_batches'],
                      verified_MTJs_per_attempt=M['verify_branch_batches']*M['verify_single_ended_sense_lanes'],
                      finite_attempts=finite_attempts,verify_capture_ticks=M['verify_branch_batches']*M['verify_capture_ticks_per_batch'],
                      write_driver_lanes=M['physical_direction_driver_lanes'],
                      first_phase_current_capacity_mA=M['first_phase_active_MTJs']*I['driver_budget']['current_rating_uA_per_path']/1000,
                      second_phase_current_capacity_mA=M['second_phase_active_MTJs']*I['driver_budget']['current_rating_uA_per_path']/1000),
                  service_interpretation='one complete attempt, all branch states verified' if attempts is None else 'exactly two attempts, second succeeds',
                  write_breakdown_ns=dict(front=front, one_attempt=one, write_slots=2*s['write_access_slot_ns'],
                      polarity_switch=td, verify_read=2*s['read_response_ns'], verify_capture=2*td, verify_compare=2*td,
                      retries=(finite_attempts-1)*one),
                  stream_breakdown_ns=dict(media=counts['read_rounds']*s['read_response_ns'],
                      capture=counts['capture_ticks']*td,digital=counts['digital_ticks']*td, boundary=CFG['boundary_ticks']*td),
                  dominant='stream: finite digital AND/reduction rounds after native tile read; resident: two complete write slots and absolute branch verify',
                  sources=['MRAM-06 pp.2,4,5,9 / SI p.4','MRAM-03 pp.5-7','MRAM-04 pp.1-2','shared_baseline'],
                  assumptions=I['retry_model']['assumptions'])
    return result


def results():
    rows = [calculate(s) for s in I['scenarios']]
    ref = next(s for s in I['scenarios'] if s['profile']=='reference')
    comp = calculate(ref, I['comparison']['attempts'])
    comp['id'] = I['comparison']['id']
    mapping = dict(logical_capacity_Byte=L['resident_capacity_Byte'],
                   logical_weight_bits=8*L['resident_capacity_Byte'],
                   physical_MTJs=8*L['resident_capacity_Byte']*M['MTJs_per_weight_bit'],
                   groups_per_matrix=L['resident_capacity_Byte']//M['logical_weights_per_write_group'], **M)
    native=dict(K=L['K'],N=L['N'],b_S=L['b_S'],b_R=L['b_R'],
        logical_capacity_Byte=L['resident_capacity_Byte'],effective_logical_capacity_Byte=L['resident_capacity_Byte'],
        physical_MTJs=mapping['physical_MTJs'],physical_storage_bits=mapping['physical_MTJs'],
        physical_capacity_Byte=mapping['physical_MTJs']/8,
        encoding='two complementary MTJs per binary weight bit; eight pairs per signed INT8 weight',
        signal_enhancement_replication=1,independent_service_units=1,
        physical_organization='64 native banks x 256 rows x four IBMD columns; two banks per INT8 output',
        output_container_bits=L['output_container_bits'],input_register_bits=L['input_register_bits'],
        output_register_bits=L['output_register_bits'],update_payload_Byte=rows[1]['B_R_Byte'],
        update_shape='one selected row x eight aligned INT8 outputs; sixteen banks, 64 complementary pairs',
        full_load_transactions=rows[1]['full_load']['transactions'],
        resources=dict(installed_ibmd_bitcells=M['installed_ibmd_bitcells'],
            native_ibmd_latch_stages=M['native_ibmd_latch_stages'],active_differential_digitizers=M['active_compute_pairs'],
            active_physical_MTJs=2*M['active_compute_pairs'],read_tap_lanes=M['read_tap_lanes'],
            tile_selection_mux_inputs_per_lane=M['tile_selection_mux_inputs_per_lane'],
            weight_tile_register_bits=M['digital_weight_hold_bits'],weight_tile_register_banks=1,
            added_digital_AND_gates=M['new_digital_AND_gates'],digital_output_lanes=CFG['output_lanes'],
            active_input_rows=CFG['rows_per_group'],partial_sum_register_bits=CFG['output_lanes']*L['output_container_bits'],
            capture_ticks_per_read=1,adc_count=0,write_domains=M['write_domains'],
            write_driver_lanes=M['physical_direction_driver_lanes'],write_driver_current_uA=I['driver_budget']['current_rating_uA_per_path'],
            write_SL_rating_mA=I['driver_budget']['aggregate_SL_rating_mA'],target_register_bits=M['encoded_load_bits'],
            absolute_verify_sense_lanes=M['verify_single_ended_sense_lanes'],verify_state_latch_bits=M['verify_state_latch_bits'],
            verify_comparators=M['verify_expected_bit_comparators'],streaming_update_overlap=False),
        display_conversion='average_update_ns_per_16KiB = T_R_ns * 16384 / logical_capacity_Byte; not a native request')
    return dict(case_id=I['case_id'], baseline_id=api.D['baseline_id'], baseline_hashes=I['baseline_hashes'],
                input_sha256=hashlib.sha256((BASE/'data/inputs.json').read_bytes()).hexdigest(),
                units={'time':'ns','rho_tau':'Byte/s','ridge':'dimensionless'}, mode=I['mode'],
                native_configuration=native,mapping=mapping, scenarios=rows, comparison=comp,
                paired_ranges={k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']})



def generated():
    r = results()
    lines = [r'% Generated by check_mram.py --emit.', r'\begin{table}[htbp]\centering\small',
             r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
             r'情景 & $t_m/t_W$ (ns) & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\mathrm{RI}^{*}$\\\midrule']
    labels={'short':'乐观','reference':'典型','long':'悲观'}
    for s in r['scenarios']:
        lines.append(f"{labels[s['profile']]} & {s['read_response_ns']:g}/{s['write_access_slot_ns']:g} & {s['delta_S_ns']:g} & {s['delta_R_ns']:g} & {s['rho_Byte_per_s']/1e6:.3f} & {s['tau_Byte_per_s']/1e6:.3f} & {s['ridge']:.4f}\\\\")
    s=r['comparison']
    lines.extend([r'\midrule',f"典型，重写一次 & 5/30 & {s['delta_S_ns']:g} & {s['delta_R_ns']:g} & {s['rho_Byte_per_s']/1e6:.3f} & {s['tau_Byte_per_s']/1e6:.3f} & {s['ridge']:.4f}\\\\",
                  r'\bottomrule\end{tabular}',
                  r'\caption{条件配对情景，MB/s 为十进制：$B_S=256$ Byte，$B_R=8$ Byte。前三行为单轮完整写验通过的有限预算；末行为恰好一次整组重写且随后成功的占用对照，未纳入前三行情景范围。}',r'\end{table}'])
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_results.tex':'\n'.join(lines)+'\n'}


class Checks(unittest.TestCase):
    def test_shared_and_source_hashes(self):
        for path,h in I['baseline_hashes'].items():
            self.assertEqual(hashlib.sha256((SHARED/path).read_bytes()).hexdigest(),h)
        manifest={s['source_id']:s for s in json.loads((CORPUS/'source_manifest.json').read_text())['sources']}
        for key,s in I['sources'].items():
            self.assertEqual(s['pdf'],manifest[key]['pdf'])
            for p in [s['pdf']]+s['supplements']:
                self.assertEqual(hashlib.sha256((CORPUS/p['path']).read_bytes()).hexdigest(),p['sha256'])

    def test_mapping_resource_and_precision(self):
        n=api.dcim_counts(CFG,L)
        self.assertEqual(n['compute_rounds'],128)
        self.assertEqual(n['read_rounds'],16)
        self.assertEqual(n['capture_ticks'],16)
        self.assertEqual(n['max_tile_bits'],4096)
        self.assertEqual(M['active_compute_pairs'],CFG['rows_per_group']*CFG['output_lanes']*CFG['weight_bits_per_round'])
        self.assertEqual(M['encoded_load_bits'],M['logical_weights_per_write_group']*8*M['MTJs_per_weight_bit'])
        self.assertEqual(M['first_phase_active_MTJs'],M['selected_pairs_per_write_group']*2)
        self.assertEqual(M['second_phase_active_MTJs'],M['selected_pairs_per_write_group'])
        self.assertEqual(M['verify_single_ended_sense_lanes']*M['verify_branch_batches'],M['encoded_load_bits'])
        self.assertEqual(M['physical_direction_driver_lanes'],M['first_phase_active_MTJs'])
        # Exact address map into the original 64 x 256 x 4 bitcell banks.
        physical={(2*o+b//4,i,b%4) for i in range(L['K']) for o in range(L['N']) for b in range(8)}
        self.assertEqual(len(physical),M['banks']*M['rows_per_bank']*M['weight_bits_per_bank_row'])
        self.assertEqual(len(physical),L['resident_capacity_Byte']*8)
        self.assertEqual(2*len(physical),results()['mapping']['physical_MTJs'])
        self.assertLess(L['K']*128*128,2**(L['output_container_bits']-1))
        # Every selected OUT is a distinct physical IBMD node; no bank-sum read masquerades as W.
        tile_nodes={(2*o+b//4,i,b%4) for i in range(32) for o in range(16) for b in range(8)}
        self.assertEqual(len(tile_nodes),M['read_tap_lanes'])
        self.assertEqual(len(physical)//len(tile_nodes),M['tile_selection_mux_inputs_per_lane'])
        self.assertLessEqual(M['first_phase_active_MTJs']*I['driver_budget']['current_rating_uA_per_path']/1000,
                             I['driver_budget']['aggregate_SL_rating_mA'])

    def test_independent_arithmetic_and_aggregation(self):
        for row in results()['scenarios']:
            td=api.C['propagation']['profile_values'][row['profile']]['digital_tick']
            tm,tw=row['read_response_ns'],row['write_access_slot_ns']
            # Native eight row groups x two output groups; eight input bits per held tile.
            ds=16*tm+(16+128+2)*td
            one=2*tw+2*tm+5*td  # turn, two captures, two comparisons
            dr=2*td+one
            self.assertAlmostEqual(row['delta_S_ns'],ds)
            self.assertAlmostEqual(row['delta_R_ns'],dr)
            self.assertAlmostEqual(row['ridge'],32*dr/ds)
            self.assertAlmostEqual(row['tau_Byte_per_s'],8192/(1024*dr*1e-9))
            self.assertEqual(row['resident_counts']['verified_MTJs_per_attempt'],128)
            self.assertEqual(sum(row['stream_breakdown_ns'].values()),ds)
            mi=row['mapping_interface']
            self.assertEqual(mi['T_R_ns'],1024*dr)
            self.assertAlmostEqual(mi['U_star'],L['N']*L['b_R']/L['b_S']*row['ridge'])
        ref=results()['scenarios'][1]
        self.assertEqual(ref['delta_S_ns'],16*5+16*5+128*5+2*5)
        self.assertEqual(ref['write_breakdown_ns']['one_attempt'],2*30+5+2*(5+5+5))
        self.assertEqual(ref['delta_R_ns'],105)
        self.assertEqual(results()['comparison']['delta_R_ns'],10+2*95)

    def test_generated_contract(self):
        for p,text in generated().items():
            self.assertEqual((BASE/p).read_text(),text)
        for word in ['互补','单端','192','自终止','条件','MRAM-01']:
            self.assertIn(word,(BASE/'tex/06_mram.tex').read_text())
        self.assertIn('generated_results',(BASE/'tex/06_mram.tex').read_text())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emit',action='store_true')
    args=p.parse_args()
    if args.emit:
        for path,text in generated().items():
            (BASE/path).write_text(text)
    raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks)).wasSuccessful() else 1)

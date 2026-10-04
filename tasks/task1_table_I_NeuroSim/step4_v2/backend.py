"""Step4 explicit module adapter; fresh builds from immutable V1.4 sources.

Only public low-voltage peripherals are modeled. MemCell is unused constructor
context, not a replacement storage identity. Paths use original register
boundaries; held-data windows require explicit lifecycle evidence and late control remains single-cycle. No SubArray default is inherited.
"""
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

SHA = '8a88abf85844c0e1ba17cc771ea535fff6040456'
IDS = {'03_nor_2d': 3, '04_nand_3d': 4, '06_mram': 6, '07_pcm': 7,
       '08_feram_hfo2': 8, '09_gain_cell_edram': 9, '10_fenor_3d': 10}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def dimensions(case):
    cid = case['case_id']
    if cid not in IDS:
        raise ValueError('No approved Step4 module route: ' + cid)
    ins = case['resources']['installed']
    active = case['resources']['active']['streaming']
    native = case['resources']['native_declared']
    logical = case['logical']
    lanes = active['output_lanes']
    extra = resident = mask = 0
    named_extra = {}
    if cid == '04_nand_3d':
        resident = native['resident_row_staging_bits']
        names = ['input_sign_register_bits', 'input_sign_phase_control_bits',
                 'affine_count_stage_register_bits', 'magnitude_sum_stage_register_bits',
                 'polarity_difference_stage_register_bits', 'intermediate_accumulator_bits',
                 'calibration_gain_offset_register_bits']
        named_extra = {key: native[key] for key in names}
        extra = sum(named_extra.values())
    elif cid == '03_nor_2d':
        named_extra = {'partial_sum_register_bits': native['partial_sum_register_bits']}
        extra = sum(named_extra.values())
    elif cid == '06_mram':
        resident = native['target_register_bits']
        named_extra = {key: native[key] for key in ['partial_sum_register_bits', 'verify_state_latch_bits']}
        extra = sum(named_extra.values())
    elif cid == '07_pcm':
        resident, mask = native['transaction_buffer_bits'], native['mask_done_bits']
    elif cid == '08_feram_hfo2':
        resident = ins['encoded_interface_bits']
    elif cid == '09_gain_cell_edram':
        # operand_hold_bits is precisely the declared refresh code hold.
        resident = 0
    elif cid == '10_fenor_3d':
        resident = native['encoded_update_register_bits']
        named_extra = {'partial_sum_register_bits': native['partial_sum_register_bits']}
        extra = sum(named_extra.values())
    # Address/control bits are explicitly allocated here as engineering
    # implementation state, never data/code/shadow registers. The complete
    # native read/write blocks still own their native peripheral state.
    resident_active = case['resources']['active']['resident']
    counters = {'native_row_index': logical['K'], 'logical_column_index': logical['N'],
                'full_matrix_transaction_index': logical['B_R_Byte'] // logical['resident_transaction_Byte']}
    if cid == '04_nand_3d':
        counters['physical_page_index'] = resident_active['physical_pages_per_matrix']
    if cid == '03_nor_2d':
        counters['native_page_index'] = case['resources']['write_semantics']['page_count']['value']
    state_cardinalities = {'input_row_group': math.ceil(logical['K'] / active['input_terms_per_group']),
                           'output_group': math.ceil(logical['N'] / lanes),
                           'input_bit_or_digit': 4 if cid == '04_nand_3d' else 8,
                           'resident_transaction': counters['full_matrix_transaction_index'],
                           'operation_phase': 16, 'completion_flags': 16}
    if cid == '03_nor_2d':
        state_cardinalities.update(native_page=64, native_sector=4, page_load_beat=16)
    elif cid == '04_nand_3d':
        state_cardinalities.update(input_encoding_group=288, input_sign_phase=2,
                                  native_page=6144, data_page_beat=288,
                                  calibration_pair=256, calibration_iteration=24)
    elif cid == '06_mram':
        state_cardinalities.update(write_direction=2, absolute_verify_branch=2)
    elif cid == '07_pcm':
        state_cardinalities.update(weight_plane=8, verify_pass=2, load_beat=2)
    elif cid == '09_gain_cell_edram':
        state_cardinalities.update(refresh_row=64, refresh_output_group=4, service_mode=2, load_beat=2)
    elif cid == '10_fenor_3d':
        state_cardinalities.update(verify_compare_group=8, write_phase=2)
    state_bits = {key: math.ceil(math.log2(value)) if value > 1 else 0 for key, value in state_cardinalities.items()}
    counter_bits = max(1, max(state_bits.values()))
    dims = {'CASE_KIND': IDS[cid], 'ACTIVE_TERMS': active['input_terms_per_group'],
            'ADC_COUNT': ins['adc_count'], 'LANES': lanes,
            'INPUT_BITS': ins['input_register_bits'], 'OUTPUT_BITS': ins['output_register_bits'],
            'OUTPUT_WIDTH': logical['output_bits'],
            'OUTPUT_BANKS': math.ceil(logical['N'] / lanes),
            'OPERAND_BITS': ins['operand_hold_bits'], 'RESIDENT_BITS': resident,
            'MASK_BITS': mask, 'EXTRA_BITS': extra, 'CONTROL_BITS': counter_bits,
            'CONTROL_STATE_BITS': sum(state_bits.values()),
            'INPUT_GROUPS': math.ceil(logical['K'] / active['input_terms_per_group']),
            'NAND_WORD_BANKS': math.ceil(logical['K'] / 16) if cid == '04_nand_3d' else 1,
            'CONTROL_SINKS': max(ins['encoded_interface_bits'], lanes * logical['output_bits']),
            'VERIFY_LANES': native.get('verify_comparators', native.get('write_compare_lanes', native.get('ADC_per_plane', 32)))}
    assert dims['ADC_COUNT'] > 0 if cid in {'04_nand_3d', '07_pcm', '09_gain_cell_edram'} else dims['ADC_COUNT'] == 0
    if cid in {'03_nor_2d', '06_mram', '08_feram_hfo2', '10_fenor_3d'}:
        assert dims['ACTIVE_TERMS'] == 32 and dims['LANES'] == 16
    return dims, named_extra, {'concurrent_state_bits': state_bits, 'counter_cardinalities': state_cardinalities}


def build(case, root: Path, out: Path, cxx: str, own: Path):
    dims, extras, counters = dimensions(case)
    cid = case['case_id']
    root, out, own = map(Path, (root, out, own))
    out.mkdir(parents=True)
    src = out / 'src'
    src.mkdir()
    (out / 'tmp').mkdir()
    tree = Path(json.loads((root / 'worktrees.json').read_text())['2DInferenceV1.4'])
    actual = subprocess.check_output(['git', '-C', str(tree), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == SHA, ('wrong locked backend', actual)
    core = tree / 'Inference_pytorch/NeuroSIM'
    hashes = {}
    for path in sorted(core.iterdir()):
        if path.suffix not in ('.cpp', '.h'):
            continue
        blob = subprocess.check_output(['git', '-C', str(tree), 'show', SHA + ':Inference_pytorch/NeuroSIM/' + path.name])
        assert hashlib.sha256(blob).hexdigest() == sha(path), ('dirty locked source', path.name)
        hashes[path.name] = sha(path)
        shutil.copy2(path, src / path.name)
    # Audit the complete files, a stronger condition than just the methods we
    # execute. Constructors store the reference but no member reads occur.
    fields_audit = {}
    for name in ('DFF', 'Adder', 'SarADC'):
        contents = (src / (name + '.cpp')).read_text()
        reads = re.findall(r'\bcell\s*\.\s*([A-Za-z_]\w*)', contents)
        assert not reads, (name, 'MemCell use changed', reads)
        fields_audit[name] = {'cpp_sha256': hashes[name + '.cpp'], 'MemCell_field_reads_in_complete_cpp': reads,
                              'methods': ['Initialize', 'CalculateArea', 'CalculateLatency'] + (['CalculateUnitArea'] if name == 'SarADC' else [])}
    original = (src / 'Param.cpp').read_text()
    patched = original
    primaries = {'technode': 22, 'temp': 300, 'deviceroadmap': 2, 'memcelltype': 1}
    for key, value in primaries.items():
        patched, count = re.subn(r'(?m)^(\s*' + key + r'\s*=\s*)[^;]+;',
                                 lambda m: m[1] + str(value) + ';', patched, count=1)
        assert count == 1, key
    (src / 'Param.cpp').write_text(patched)
    (out / 'constructor.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True), fromfile='a/Param.cpp', tofile='b/Param.cpp')))
    (src / 'request.h').write_text(''.join('#define %s %s\n' % item for item in dims.items()))
    shutil.copy2(own / 'backend.cpp', src / 'step4.cpp')
    for path in sorted(own.glob('*.h')):
        shutil.copy2(path, src / path.name)
    commands = []

    def command(argv, label):
        result = subprocess.run(list(map(str, argv)), cwd=out,
                                env=dict(os.environ, TMPDIR=str(out / 'tmp')),
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / (label + '.log')).write_text(result.stdout)
        commands.append({'argv': list(map(str, argv)), 'returncode': result.returncode, 'log': label + '.log'})
        dump(out / 'commands.json', commands)
        if result.returncode:
            raise RuntimeError(str(out / (label + '.log')))
        return result.stdout

    exe = out / 'step4-backend'
    cpp = [src / name for name in ('step4.cpp', 'Param.cpp', 'Technology.cpp', 'formula.cpp',
                                   'FunctionUnit.cpp', 'DFF.cpp', 'Adder.cpp', 'SarADC.cpp')]
    command([cxx, '-std=c++11', '-O2', '-fopenmp', '-w', '-I', src, *cpp, '-o', exe], 'build')
    manifest = {'backend_sha': SHA, 'upstream_files': hashes,
                'constructor_inputs': primaries, 'constructor_patch_sha256': sha(out / 'constructor.patch'),
                'request_header_sha256': sha(src / 'request.h'), 'explicit_request': dims,
                'adapter_sha256': sha(own / 'backend.cpp'), 'python_adapter_sha256': sha(own / 'backend.py'),
                'compiled_translation_units': [path.name for path in cpp],
                'adapter_headers': {path.name: sha(path) for path in sorted(own.glob('*.h'))},
                'MemCell_use_audit': fields_audit}
    dump(out / 'source_manifest.json', manifest)

    def execute(label, wire_um=10., bits=10, operating_period_ns=None):
        if not math.isfinite(wire_um) or wire_um < 0:
            raise ValueError('wire_um must be finite and nonnegative')
        if not isinstance(bits, int) or not 7 <= bits <= 16:
            raise ValueError('Step4 diagnostic ADC precision must be in 7..16 bits')

        def run(hz, suffix):
            raw = {}
            for line in command([exe, hz, wire_um, bits], label + suffix).splitlines():
                if '=' not in line:
                    continue
                key, value = line.split('=', 1)
                try:
                    raw[key] = float(value)
                except ValueError:
                    pass
            assert raw and all(math.isfinite(value) for value in raw.values())
            return raw

        raw = run(2e8, '-physical')
        paths = []
        for key, value in raw.items():
            if not key.endswith('_path_s'):
                continue
            pid = key[:-2]
            phase2 = pid in ('pcm_decode_reconstruct_path', 'gc_decode_reconstruct_path')
            conditional = cid == '07_pcm' and pid in ('pcm_decode_reconstruct_path', 'verify_compare_path')
            boundaries = {
                'capture_enable_path': ('existing_phase_state_updated_at_E1', 'existing_selected_output_accumulator_capture_enable_at_E2'),
                'digital_mac_path': ('4096bit_operand_hold_and_Kx8_input_register_with_rowgroup_mux_plus_ibit_and_output_accumulator', 'existing_selected_output_or_partial_sum_register'),
                'nand_sign_magnitude_path': ('existing_input_or_resident_staging_byte_register', 'existing_magnitude_byte_and_sign_register'),
                'nand_page_formatter_path': ('existing_4608x9bit_resident_staging_via_288to1_word_bank_mux', 'existing_page_data_port_capture_boundary'),
                'nand_base4_merge_path': ('64x14bit_affine_count_register', '16x20bit_magnitude_sum_register'),
                'nand_polarity_subtract_path': ('16x20bit_magnitude_sum_register', '8x21bit_polarity_difference_register'),
                'nand_shift_accumulate_path': ('8x21bit_difference_register_and_240x29bit_intermediate_accumulator_plus_digit_sign', 'selected_existing_240x29bit_intermediate_accumulator'),
                'gc_refresh_sign_path': ('existing_SAR_signed_code_state', 'existing_128bit_refresh_code_hold'),
                'verify_compare_path': ('existing_native_sensed_state_or_SAR_code_and_target_register', 'existing_mask_or_verify_done_control_state'),
            }
            start, end = boundaries.get(pid, ('held_native_SAR_code_input_and_old_accumulator' if phase2 else 'declared_data_or_controller_register',
                                              'existing_selected_output_accumulator' if phase2 else 'declared_data_or_controller_register'))
            paths.append({'id': pid, 'delay_ns': value * 1e9,
                          'start_register': start, 'end_register': end,
                          'constraint_clock_id': 'lv_core', 'single_cycle': not phase2,
                          'launch_edge': 1 if pid == 'capture_enable_path' else 0,
                          'capture_edge': 2 if phase2 or pid == 'capture_enable_path' else 1,
                          'available_cycles': 2 if phase2 else 1, 'complete_serial_path': True,
                          'stable_sources': (['SAR_codes', 'input_register', 'input_bit', 'output_group', 'old_accumulator', 'PCM_calibration_thresholds' if cid == '07_pcm' else 'GC_popcount_input_bits'] if phase2 else []),
                          'path_class': 'held_reconstruction_data' if phase2 else 'single_cycle_control_or_data',
                          'required_period_ns': value * 1e9 / (2 if phase2 else 1),
                          'actual_load': {'wire_per_logic_segment_um': wire_um,
                                          'wire_cap_F': raw['wire_cap_F'],
                                          'destination_DFF_data_cap_F': raw['dff_data_cap_F'],
                                          'fanout': 'actual declared DAG pins; shared inputs distributed at fanout <=4; bank mux pad-to-power-of-two'},
                          'path_status': 'conditional_calibrated_threshold_input_structural_envelope' if conditional else 'formula_based_bit_arrival_envelope',
                          'eligibility_limit': 'threshold stability/storage/values are native calibration obligations' if conditional else None})
        assert paths and all(p['delay_ns'] > 0 and p['available_cycles'] in (1, 2) for p in paths)
        minimum = max(path['required_period_ns'] for path in paths)
        floor = max(5., minimum)
        if operating_period_ns is None:
            selected = math.ceil(floor * 2 - 1e-10) / 2
            policy = 'target_5ns_else_upward_0.5ns_grid'
        else:
            selected = float(operating_period_ns)
            if not math.isfinite(selected) or selected + 1e-10 < floor:
                raise ValueError('Requested period below qualified launch/capture timing/policy floor: ' + str(floor))
            policy = 'explicit_fixed_legal_operating_point'
        final = run(1e9 / selected, '-count')
        for key, value in raw.items():
            if key.endswith('_path_s'):
                assert math.isclose(value, final[key], rel_tol=1e-12)
        assert final['dff_cycle'] == 1 and final['same_graph_arithmetic_fixtures'] > 0
        coverage = {
            'case_id': cid, 'route': 'public_module_plus_native_service', 'SubArray_used': False,
            'array_or_device_material_simulated': False,
            'MemCell_context': {'type': 'SRAM', 'purpose': 'mandatory constructor context only',
                                'field_reads_in_called_modules': [], 'electrical_fields': 'zero/unused; native service fields are bound by the case adapter'},
            'digital_scope': 'declared gate topology and electrical load envelope; no sensitized STA or extracted wiring',
            'aggregate_write_return': None, 'native_frontend_loads_validated': False,
            'whole_macro_timing_validated': False,
            'full_arithmetic_paths': cid != '04_nand_3d',
            'conditional_paths': ['pcm_decode_reconstruct_path', 'verify_compare_path'] if cid == '07_pcm' else [],
            'retained_unverified_arithmetic': [],
            'SAR_scope': 'nominal code width dependent conversion-latency fit; no power, array electrical accuracy, or current/voltage transfer claim' if dims['ADC_COUNT'] else 'not instantiated',
        }
        if cid == '04_nand_3d':
            coverage['retained_unverified_arithmetic'] = [
                {'operation': '10bit code x Q8.16 gain + Q12.12 offset, half-up count',
                 'budget': 'first of four existing digital ticks per conversion; 960 normal occurrences plus retained calibration work',
                 'timing_status': 'full_multiplier_rounding_path_not_instantiated'},
                {'operation': 'calibration fixed-point division and coefficient update',
                 'budget': '450 existing digital ticks per full resident calibration',
                 'timing_status': 'divider_working_state_and_full_path_not_instantiated'}]
            coverage['clock_qualification_scope'] = 'modeled encoding/merge/subtract/accumulation/control only; native affine and calibration tick budgets remain conditional'
            coverage['NAND_word_selection'] = {'streaming_magnitude': 'existing 4608x8 input bank, 16 lanes and 288:1 word-bank mux followed by sign/magnitude',
                                                'resident_formatter': 'existing 4608x9 staging, 16 lanes and 288:1 word-bank mux; digit pair selection, polarity mask, LSB/MSB/MSB fixed replication -> 48 useful bits',
                                                'mux_timing': 'padded 512:1 balanced two-input tree; data and select arrival/fanout included; no intermediate selected-word register',
                                                'external_resident_magnitude_encoding': 'same encoding cells, external 128bit port source; streaming bank path is conservative bound'}
        if cid == '07_pcm':
            coverage['PCM_decoder'] = {'implementation': '8 parallel unsigned threshold comparators then thermometer popcount per SAR; weighted reconstruction in same serial path',
                                       'threshold_source': 'already-declared column-dependent calibrated decoder; stable threshold metadata required',
                                       'threshold_storage_or_generation_modeled': False,
                                       'actual_threshold_table_available': False,
                                       'new_threshold_register_bits': 0,
                                       'numerical_scope': 'generic comparator truth table and ideal class arithmetic; fixture thresholds are not a physical PCM transfer'}
            coverage['PCM_endpoint'] = {'implementation': 'strict code<lower / code>upper comparisons, 32-to-16 target-byte parity selection then plane selection, both-rail rejection, 16-lane accepted-state reduction',
                                       'threshold_equality': 'reject at both lower and upper; matches native below/above acceptance',
                                       'native_threshold_stability_and_calibration_required': True,
                                       'read_mode': 'single-WL fresh frontend and shared installed SAR; conditional native settle retained'}
        if cid in {'06_mram', '07_pcm', '10_fenor_3d'}:
            coverage['verify_source_access'] = {
                '06_mram': '128bit complementary target -> 2:1 branch mux -> 64 absolute-state comparators; native branch read provides 64 sensed bits',
                '07_pcm': '32byte target -> 2:1 parity-group mux -> 16 target bytes -> 8:1 plane-bit mux -> 16 ADC endpoint comparators',
                '10_fenor_3d': '128bit target and native 128bit captured read -> separate 8:1 group muxes -> 16 comparators per tick',
            }[cid] + '; data and group-select fanout included; no preselected shadow register'
        preselection = None
        if cid in {'03_nor_2d', '06_mram', '08_feram_hfo2', '10_fenor_3d'}:
            early = ['input_data', 'input_group_select', 'output_group_select']
            prefix = 'digital_mac_source_'
            settle = max(final[prefix + name + '_pin_s'] * 1e9 for name in early)
            key = {'03_nor_2d': 'nor_read', '06_mram': 'ibmd_read',
                   '08_feram_hfo2': 'feram_sense', '10_fenor_3d': 'binary_read'}[cid]
            available = next(x['normalized']['value'] * 1e9 for x in case['device']['primitives'] if x['id'] == key)
            assert settle <= available + 1e-10, 'preselection not established during native read; cannot use this frame qualification'
            preselection = {'early_sources': early, 'settle_to_existing_combinational_pins_ns': settle,
                'available_native_lead_ns': available, 'lead_source_parameter': key,
                'source_pin_settle_ns': {name: final[prefix + name + '_pin_s']*1e9 for name in early},
                'full_source_to_capture_delay_ns': {name: value*1e9 for name, value in final.items() if name.startswith(prefix) and name.endswith('_full_s')},
                'V1_all_sources_relaunched_delay_ns': final['digital_mac_conservative_all_sources_s'] * 1e9,
                'dynamic_complete_path_delay_ns': final['digital_mac_path_s']*1e9,
                'per_cycle_sources': ['input_bit_index', 'selected_accumulator_feedback'],
                'first_bit_source': 'new weight hold output at operand capture; conservatively one full MAC period even for native early capture',
                'lifecycle': 'input vector and group selection stable from native-read launch through all eight bit MACs; selected input combinational nodes already settled before first MAC launch',
                'weight_lifecycle': 'first MAC launches from completed operand capture; same weight hold persists through remaining seven bits',
                'no_preselected_cache_or_pipeline': True,
                'first_capture_qualification': 'each early full source-to-capture delay must fit native lead plus first MAC period, checked in engine',
                'clock_dependency': 'native lead is a qualification check, not a per-cycle clock bound; no analog-time subtraction from MAC delay'}
            for path in paths:
                if path['id'] == 'digital_mac_path':
                    path['start_register'] = 'changing_ibit_or_accumulator_and_first_weight_capture_with_frame_stable_input_and_group'
                    path['path_class'] = 'single_cycle_dynamic_MAC_sources'
                    path['stable_preselected_signals'] = early
                    path['source_decomposition'] = preselection
        hold = None
        if cid in {'07_pcm', '09_gain_cell_edram'}:
            sources = ['SAR_codes', 'input_register', 'input_bit', 'output_group', 'old_accumulator',
                       'PCM_calibration_thresholds' if cid == '07_pcm' else 'GC_popcount_input_bits']
            hold = {'source_codes': 'existing SAR result state; no E0 recapture bank',
                    'stable_sources': sources, 'source_stability': {name: [0, 2] for name in sources},
                    'source_stability_edges': [0, 2], 'capture_edges': [2],
                    'edge_updates': {'0': ['launch_reconstruction'], '1': ['phase_only'],
                                     '2': ['selected_output_accumulator', 'next_batch_control']},
                    'phase_enable_launch_edge': 1, 'phase_enable_capture_edge': 2,
                    'capture_enable_at_edge1': False, 'phase1_action': 'continuous combinational propagation; no capture',
                    'data_path_qualification': 'E0 to E2 continuous two-period window; E1 does not restart the data graph',
                    'no_new_intermediate_registers': True, 'overlap': False,
                    'input_validity': ('column threshold metadata must already be stable before E0 and through E2; remains unvalidated native calibration obligation' if cid == '07_pcm' else
                                       'input vector and bit select already drove the native integration; popcount is combinational from those same held inputs, no popcount register'),
                    'resource_release': 'after E2 capture; no next SAR, refresh, group change or accumulator write before release'}
        inventory = {'input_DFF': dims['INPUT_BITS'], 'output_DFF': dims['OUTPUT_BITS'],
                     'operand_hold_DFF': dims['OPERAND_BITS'], 'resident_staging_DFF': dims['RESIDENT_BITS'],
                     'mask_DFF': dims['MASK_BITS'], 'declared_extra_DFF': extras,
                     'controller_address_state_DFF': dims['CONTROL_STATE_BITS'],
                     'longest_increment_counter_bits': dims['CONTROL_BITS'],
                     'controller_state_allocation': 'separate concurrent row/group/digit/page/phase/counter state; only the longest increment counter is on the controller critical path',
                     'controller_counter_cardinalities': counters,
                     'SAR': dims['ADC_COUNT'], 'arithmetic_lanes': dims['LANES'],
                     'output_bits': dims['OUTPUT_WIDTH'], 'active_terms': dims['ACTIVE_TERMS'],
                     'output_bank_mux_fanin': dims['OUTPUT_BANKS'],
                     'input_row_group_mux_fanin': dims['INPUT_GROUPS'] if cid in {'03_nor_2d', '06_mram', '08_feram_hfo2', '10_fenor_3d'} else None,
                     'input_row_group_mux_organization': 'Kx8 input register -> 32x8 selected combinational bytes -> 16 lane fanout; no shadow bank' if cid in {'03_nor_2d', '06_mram', '08_feram_hfo2', '10_fenor_3d'} else None,
                     'added_payload_or_code_banks': 0,
                     'native_page_buffers_or_native_capture': 'owned by retained native full service; not modeled a second time'}
        inventory['actual_Adder_modules'] = {key[:-11]: {'bits': int(value), 'count': int(final[key[:-11] + '_adder_count'])}
                                             for key, value in final.items() if key.endswith('_adder_bits')}
        result = {'execution_revision': 'step4-2.0.0', 'case_id': cid,
                  'actual_period_ns': selected, 'timing_min_period_ns': minimum,
                  'policy_min_period_ns': floor, 'selection_policy': policy,
                  'critical_path': max(paths, key=lambda p: p['required_period_ns'])['id'],
                  'boundary_setup_ns': final['boundary_setup_s'] * 1e9,
                  'sar_ns': final.get('sar_s', 0.) * 1e9 if dims['ADC_COUNT'] else None,
                  'adc_bits': bits if dims['ADC_COUNT'] else None, 'wire_um': wire_um,
                  'paths': paths, 'raw_module_returns': final, 'module_inventory': inventory,
                  'coverage': coverage, 'source_hold_window': hold, 'frame_preselection': preselection,
                  'arithmetic_checks': {'same_timed_gate_graph_fixture_count': int(final['same_graph_arithmetic_fixtures']),
                                        'passed': True, 'native_analog_accuracy_validated': False,
                                        'fixture_role': 'logic of instantiated gates; separate native numerical diagnostic remains authoritative'},
                  'engineering_conditions': {'node_nm': 22, 'roadmap': 'LSTP', 'temperature_K': 300,
                                              'wire_um_per_local_logic_net': wire_um,
                                              'wire_capacitance_fF_per_um': .2,
                                              'wire_resistance': 'locked Param.cpp 22nm wire model',
                                              'DFF_boundary': 'two loaded inverter engineering clock-Q/setup envelope; not library characterization',
                                              'gate_cell': 'locked public Adder NAND dimensions/caps and formula.h Horowitz propagation',
                                              'multicycle_paths': [p['id'] for p in paths if p['available_cycles'] == 2],
                                              'native_array_loads': 'not replaced by local 10um wiring'},
                  'partial_area_scope': 'initialized DFF/SAR/Adder only, excludes formula mux/control and all native arrays/frontends/drivers; not macro PPA',
                  'source_manifest': 'source_manifest.json', 'constructor_inputs': primaries,
                  'closure_status': 'modeled_paths_only; NAND retained affine and calibration budgets not timing certified' if cid == '04_nand_3d' else 'declared_launch_capture_windows_with_native_service_and_calibration_qualifications'}
        dump(out / (label + '.json'), result)
        return result

    return execute

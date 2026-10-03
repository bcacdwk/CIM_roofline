#!/usr/bin/env python3
"""Small deterministic, noise-free ACIM service diagnostics; not accuracy certification.

One vector generator and one signed bit-plane reconstruction serve all five cases.
Only declared physical transfer models are quantized.  A missing analog transfer
or calibration-code table remains missing, rather than being replaced by a curve.
Default is read-only; --emit writes the one common JSON diagnostic artifact.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SHARED = Path(__file__).resolve().parents[1]
A = SHARED.parent
OUTPUT = SHARED / 'data/nominal_service_diagnostics.json'
COEFFICIENTS = (1, 2, 4, 8, 16, 32, 64, -128)
CASES = ('01_sram_acim', '04_nand_3d', '05_rram', '07_pcm', '09_gain_cell_edram')


def load(case):
    return json.loads((A / case / 'data/inputs.json').read_text())


def imported(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vectors(k, rows):
    """Identical categories, adapted only to actual K and physical row boundaries."""
    yield 'zero', 'x=w=0', [0]*k, [0]*k
    yield 'zero_input', 'x=0; w[i]=(73*i)%256-128', [0]*k, [(73*i)%256-128 for i in range(k)]
    yield 'zero_weight', 'x[i]=i%256-128; w=0', [i%256-128 for i in range(k)], [0]*k
    yield 'unit_positive', 'x=w=1', [1]*k, [1]*k
    yield 'unit_negative', 'x=-1,w=1', [-1]*k, [1]*k
    yield 'alternating_cancel', 'x[i]=(-1)**i,w=1', [1 if i%2==0 else -1 for i in range(k)], [1]*k
    x = [1 if i%2==0 else -1 for i in range(k)]; x[-1] = 0
    yield 'near_cancel_unit', 'alternating +/-1; last -1 changed to0; w=1', x, [1]*k
    yield 'small_ramp', 'x[i]=i%7-3,w[i]=i%5-2', [i%7-3 for i in range(k)], [i%5-2 for i in range(k)]
    yield 'large_positive', 'x=w=127', [127]*k, [127]*k
    yield 'large_negative', 'x=-128,w=127', [-128]*k, [127]*k
    yield 'large_cancel', 'x[i]=127*(-1)**i,w=127', [127 if i%2==0 else -127 for i in range(k)], [127]*k
    yield 'wide_ramp', 'x[i]=i%256-128,w[i]=(73*i)%256-128', [i%256-128 for i in range(k)], [(73*i)%256-128 for i in range(k)]
    x = [0]*k; w = [0]*k; x[k//2] = w[k//2] = 1
    yield 'isolated_unit', 'one central x=w=1, other terms0', x, w
    # Across an actual group boundary; for one group use the two vector ends.
    left, right = (rows-1, rows) if rows < k else (0, k-1)
    x = [0]*k; w = [0]*k
    x[left], x[right], w[left], w[right] = 127, -127, 127, 127
    yield 'group_boundary_cancel', f'x[{left}]=127,x[{right}]=-127; corresponding w=127; others0', x, w
    x = [0]*k; w = [0]*k
    x[left], x[right], w[left], w[right] = 1, -1, 1, -1
    yield 'group_boundary_small', f'x[{left}]=w[{left}]=1,x[{right}]=w[{right}]=-1; others0', x, w


def signed_bitplane(x, w, rows, partial):
    """Group -> input bit -> weight bit -> finite decoder -> signed reconstruction."""
    groups = []; total = 0; affine_total = 0; saturation = 0; clipping = 0
    max_partial_residual = 0.; partial_count = 0
    for start in range(0, len(x), rows):
        gx, gw = x[start:start+rows], w[start:start+rows]
        value = 0; affine = 0
        for u, cu in enumerate(COEFFICIENTS):
            a = [(v & 255) >> u & 1 for v in gx]
            p = sum(a)
            for b, cb in enumerate(COEFFICIENTS):
                q = sum(ai*((wi & 255) >> b & 1) for ai, wi in zip(a, gw))
                decoded = partial(q, p)
                value += cu*cb*decoded['q']
                affine += cu*cb*decoded.get('affine_q', decoded['q'])
                saturation += decoded.get('code_saturation', 0)
                clipping += decoded.get('analog_clipping', 0)
                max_partial_residual = max(max_partial_residual, abs(decoded.get('affine_q', decoded['q'])-q))
                partial_count += 1
        truth = sum(a*b for a, b in zip(gx, gw))
        groups.append(dict(group=start//rows, start=start, terms=len(gx), truth=truth,
                           reconstructed=value, before_partial_rounding=affine))
        total += value; affine_total += affine
    return dict(ideal=sum(a*b for a, b in zip(x, w)), reconstructed=total,
                before_partial_rounding_reconstructed=affine_total,
                analog_clipped_partials=clipping, code_saturated_partials=saturation,
                max_partial_affine_absolute_residual=max_partial_residual,
                scalar_partials_one_output=partial_count, groups=groups)


def calibrated_partial(q, p):
    # q is the already-decoded ideal class, not a fabricated raw SAR voltage code.
    return {'q': q}


def gc_partial(q, p, model):
    d = 2*q-p
    mv_per_d = model['endpoint_current_nA']*model['mac_pulse_ns']/model['integration_capacitance_fF']
    lo, hi = model['adc_range_mV']
    step = (hi-lo)/2**model['adc_nominal_bits']
    v = d*mv_per_d
    # Signed zero-centred ADC: zero -> zero, half-up ties, positive endpoint clips.
    raw_code = math.floor(v/step+.5)
    code_lo, code_hi = -2**(model['adc_nominal_bits']-1), 2**(model['adc_nominal_bits']-1)-1
    code = min(code_hi, max(code_lo, raw_code))
    affine_q = (code*step/mv_per_d+p)/2
    assert model['partial_sum_rounding'] == 'nearest_integer_half_up_before_bit_weighting'
    return dict(q=math.floor(affine_q+.5), affine_q=affine_q,
                code_saturation=int(code != raw_code), analog_clipping=int(v < lo or v > hi))


def summary_row(identifier, definition, x, w, result, full_chain, output_bits):
    truth = sum(a*b for a, b in zip(x, w)); reconstructed = result['reconstructed']
    assert result['ideal'] == truth, ('ideal encoding/reconstruction mismatch', identifier)
    error = reconstructed-truth
    assert -(2**(output_bits-1)) <= reconstructed < 2**(output_bits-1), ('container overflow', identifier)
    return dict(id=identifier, deterministic_vector_definition=definition, logical_terms=len(x),
                truth=truth, reconstructed=reconstructed, signed_residual=error,
                absolute_residual=abs(error), nonzero_relative_absolute_residual=None if truth == 0 else abs(error)/abs(truth),
                zero_or_exact_cancellation=truth == 0, nonzero_output_collapsed_to_zero=truth != 0 and reconstructed == 0,
                sign_reversal=truth*reconstructed < 0,
                residual_scope='nominal_ADC_and_finite_digital_path' if full_chain else 'ideal_calibrated_partial_sum_and_digital_reconstruction_only',
                output_container_overflow=False, path_diagnostics={k: v for k, v in result.items() if k not in ('truth', 'ideal', 'reconstructed')})


def diagnose():
    cases = []; sources = [Path(__file__)]
    nand = imported('nand_nominal_adapter', A/'04_nand_3d/scripts/check_nand.py')
    for case in CASES:
        inputs = load(case); sources.append(A/case/'data/inputs.json')
        if case == '04_nand_3d':
            k, rows, output_bits = nand.M['K'], nand.M['rows_per_group'], nand.L['output_container_bits']
            model = dict(level='declared_ideal_current_ADC_calibration_and_finite_reconstruction',
                         adc_nominal_bits=10, adc_ENOB_scale_only=8, output_container_bits=output_bits,
                         physical_transfer_instantiated=True,
                         analog_full_scale=dict(value=25, unit='uA'),
                         encoding='positive/negative magnitude block groups and input-sign BL masks; base4 digit slices',
                         source='04_nand_3d/data/inputs.json; evaluate_nominal implementation',
                         claim_boundary='Ideal current and declared finite calibration only; no state variability or network accuracy qualification.')
            model['adc_code_convention'] = dict(raw_integer_code_range=[0, 1023], zero_code=0,
                physical_input_range=dict(values=[0, 25], unit='uA'),
                step=dict(value=25/1024, unit='uA', definition='full_scale_range / 2**nominal_bits =25uA/1024'),
                rounding='nearest integer; ties toward +infinity, implemented as floor(value/step+0.5)',
                endpoint_clipping='Clamp rounded raw code to0..1023;25uA gives raw1024 then clips to1023.',
                reference_calibration='10368 units at2nA=20.736uA -> code849; gain=round_half_up((10368/849)*2**16) in Q8.16; each decoded partial is rounded half-up before radix/sign reconstruction.')
            evaluate = nand.evaluate_nominal
            sources.append(A/'04_nand_3d/scripts/check_nand.py')
        else:
            model = dict(inputs['nominal_diagnostic_model'])
            k, rows, output_bits = model['logical_K'], model['rows_per_group'], model['output_container_bits']
            if case == '09_gain_cell_edram':
                model['adc_code_convention'] = dict(raw_integer_code_range=[-512, 511], zero_code=0,
                    physical_input_range=dict(values=[-224, 224], unit='mV'),
                    step=dict(value=448/1024, unit='mV', definition='full_scale_range / 2**nominal_bits =448mV/1024'),
                    rounding='nearest integer; ties toward +infinity, implemented as floor(value/step+0.5)',
                    endpoint_clipping='Clamp rounded raw code to-512..511;-224mV is code-512;+224mV gives raw512 then clips to511.',
                    partial_reconstruction='d_hat=code/8;q_affine=(d_hat+input_popcount)/2;q_hat=floor(q_affine+0.5) before signed bit weighting;no parity-lattice lookup.')
                evaluate = lambda x, w: signed_bitplane(x, w, rows, lambda q, p: gc_partial(q, p, model))
            else:
                model['adc_code_convention'] = None
                evaluate = lambda x, w: signed_bitplane(x, w, rows, calibrated_partial)
        full = model['physical_transfer_instantiated']
        results = [summary_row(name, desc, x, w, evaluate(x, w), full, output_bits)
                   for name, desc, x, w in vectors(k, rows)]
        level_count = rows+1
        entry = dict(case_id=case, model=model, logical_K=k, rows_per_group=rows,
                     quantization_induced_bias_assessed=full,
                     diagnostic_vectors=len(results), cases=results,
                     nominal_code_capacity_check=dict(adc_codes=2**model['adc_nominal_bits'],
                       ideal_binary_partial_sum_levels=level_count if case != '04_nand_3d' else None,
                       sufficient_number_of_codes=(level_count <= 2**model['adc_nominal_bits']) if case != '04_nand_3d' else None,
                       meaning='Code-count necessity only; no claim that analog class voltages or margins are resolved.'),
                     physical_ADC_chain_status='instantiated_for_ideal_declared_transfer' if full else 'not_instantiated_missing_transfer_or_calibration_codes',
                     maximum_absolute_residual=max(r['absolute_residual'] for r in results),
                     zero_output_residuals={r['id']: r['signed_residual'] for r in results if r['zero_or_exact_cancellation']},
                     collapsed_nonzero_vectors=[r['id'] for r in results if r['nonzero_output_collapsed_to_zero']],
                     sign_reversal_vectors=[r['id'] for r in results if r['sign_reversal']])
        if not full:
            entry['raw_ADC_quantization_residual'] = None
            entry['finding'] = 'No ideal encoding/decoding bias in the tested categories. Physical nominal ADC quantization remains unresolved; zero code-level residuals are not analog validation.'
        elif case == '09_gain_cell_edram':
            entry['nominal_code_capacity_check']['differential_normalized_levels'] = 2*rows+1
            lo, hi = model['adc_range_mV']
            entry['ENOB_resolution_scale_only'] = dict(ENOB=8, full_range_divided_by_2_to_ENOB_mV=(hi-lo)/256,
                interpretation='Resolution scale, not an actual8bit quantizer, noise model or error bound.')
            entry['refresh_sign_check'] = [dict(stored_sign=s, ideal_voltage_mV=s*model['endpoint_current_nA']*model['single_pair_refresh_ns']/model['integration_capacitance_fF'],
                reconstructed_sign=s, physical_drift_or_repeated_refresh_validated=False) for s in (-1, 1)]
            entry['finding'] = 'Integer partial rounding preserves the tested ideal signed results; positive endpoint code saturation and pre-rounding affine residuals are retained. This does not validate mismatch, settling or repeated refresh.'
        else:
            entry['nominal_code_capacity_check'].update(base4_unit_count_levels=rows*9+1,
                exact_unit_count_representation=False,
                interpretation='The nominal10bit ADC represents approximate current, not every integer unit count; no14bit ADC requirement is inferred.')
            legacy_results = []
            for name, desc, x, w in vectors(k, rows):
                old = nand.evaluate_nominal_legacy(x, w)
                legacy_results.append(summary_row(name, desc, x, w, old, True, output_bits))
            entry['restricted_offset_encoding_comparison'] = dict(
                reference_service_status='restricted_encoding_only',
                signed_INT8_structural_mapping=False,
                same_vectors_ADC_current_range_and_calibration=True,
                cases=legacy_results,
                meaning='Numerical encoding comparison only. Original offset organization is excluded from automatic general signed-workload mapping and is not the selected reference.')
            entry['ENOB_resolution_scale_only'] = dict(ENOB=8, full_range_divided_by_2_to_ENOB_nA=25000/256,
                interpretation='Resolution scale only; all reported ADC simulations use nominal10bit codes.')
            entry['finding'] = 'Separated magnitudes remove the offset-created zero bias. Finite range resolution still loses sparse units and can dominate small residuals after cancellation; no universal relative-error guarantee.'
        cases.append(entry)
    # Independent arithmetic checks on canonical vector definitions and bit signs.
    for case in cases:
        rows_by_id = {r['id']: r for r in case['cases']}
        assert rows_by_id['unit_positive']['truth'] == case['logical_K']
        assert rows_by_id['unit_negative']['truth'] == -case['logical_K']
        assert rows_by_id['near_cancel_unit']['truth'] == 1
        assert rows_by_id['group_boundary_cancel']['truth'] == 0
        assert rows_by_id['group_boundary_small']['truth'] == 2
        if not case['model']['physical_transfer_instantiated']:
            assert case['maximum_absolute_residual'] == 0
    return dict(schema_version='five-acim-nominal-services-1',
                method='Deterministic zero/noise-free service diagnostics at explicitly different physical or calibrated-code levels; no fitted device curve or random error.',
                qualification='Execution success is not a common accuracy pass. Nominal diagnostics, timing arithmetic, analog nonidealities and workload accuracy remain separate.',
                common_vector_categories=15, cases=cases,
                source_sha256={p.relative_to(A).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--emit', action='store_true')
    args = parser.parse_args(); report = diagnose()
    content = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if args.emit:
        OUTPUT.write_text(content)
    else:
        assert OUTPUT.read_text() == content, 'stale shared nominal_service_diagnostics.json'
    print('PASS: 5 ACIM cases × 15 deterministic categories; levels and adverse residuals recorded; no common accuracy certification.')

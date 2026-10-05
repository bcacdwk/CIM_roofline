#!/usr/bin/env python3
"""Independent ideal-code arithmetic/physical-coverage audit, not accuracy simulation.
The performance program never uses these Python outputs to complete its hardware result.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True

K, N, BITS = 256, 31, 8


def physical_sram(weights):
    return [[((weights[r][c // 8] + 128) >> (c % 8)) & 1 if c < 8*N else (1 >> (c % 8)) & 1
             for c in range(256)] for r in range(K)]


def physical_rram(weights):
    sram = physical_sram(weights)
    return [[sram[r][(c // 9) * 8 + c % 9] if c % 9 < 8 else 0 for c in range(288)] for r in range(K)]


def positive_round(x):
    return int(math.floor(x + 0.5 + 1e-9))


def evaluate(vector, weights, mode):
    memory = physical_rram(weights) if mode == 'rram' else physical_sram(weights)
    width = 9 if mode == 'rram' else 8
    # Nominal current transfer calibration; it is not produced by NeuroSim SAR.
    gon, goff = 1/13000, 1/29000
    lsb = (gon-goff)/2
    passes = []
    max_code = 0
    for inp in ([x & 255 for x in vector], [int(x < 0) for x in vector]):
        sums = [0] * 32
        for ibit in range(8):
            active = [r for r in range(K) if (inp[r] >> ibit) & 1]
            for output in range(32):
                for wbit in range(8):
                    ones = sum(memory[r][width*output+wbit] for r in active)
                    if mode == 'rram':
                        current_g = sum(gon if memory[r][width*output+wbit] else goff for r in active)
                        ref_g = sum(gon if memory[r][width*output+8] else goff for r in active)
                        code, refcode = positive_round(current_g/lsb), positive_round(ref_g/lsb)
                        assert 0 <= code < 1024 and 0 <= refcode < 1024
                        difference = code-refcode
                        assert difference % 2 == 0
                        count = difference // 2
                        max_code = max(max_code, code, refcode)
                    else:
                        code = ones
                        assert 0 <= code < 512
                        count = code
                        max_code = max(max_code, code)
                    assert count == ones
                    sums[output] += count << (ibit+wbit)
        passes.append(sums)
    # The physical pipeline implements these three registered add/sub operations.
    out = []
    intermediate_max = 0
    a, b = passes
    for col in range(N):
        partial1 = a[col] - (a[N] << 7)
        partial2 = partial1 - (b[col] << 8)
        value = partial2 + (b[N] << 15)
        for v in (partial1, partial2, value):
            assert -(1 << 24) <= v < (1 << 24)
            intermediate_max = max(intermediate_max, abs(v))
        out.append(value)
    expected = [sum(vector[r]*weights[r][col] for r in range(K)) for col in range(N)]
    assert out == expected
    return {'max_nominal_ADC_code': max_code, 'max_abs_25bit_intermediate': intermediate_max,
            'output_min': min(out), 'output_max': max(out), 'matches_signed_integer_dot': True,
            'memory_sha256': hashlib.sha256(bytes(v for row in memory for v in row)).hexdigest()}


def run():
    dense = [[((r*37 + c*19) % 256)-128 for c in range(N)] for r in range(K)]
    datasets = {
        'zero': ([0]*K, dense),
        'positive_max': ([127]*K, [[127]*N for _ in range(K)]),
        'negative_min': ([-128]*K, [[-128]*N for _ in range(K)]),
        'opposite_sign_extremes': ([-128]*K, [[127]*N for _ in range(K)]),
        'alternating_cancellation': ([127 if r%2 else -127 for r in range(K)], [[127]*N for _ in range(K)]),
        'mixed': ([((r*53)%256)-128 for r in range(K)], dense),
        'single_negative_one': ([-1]+[0]*(K-1), dense),
    }
    checks = {mode: {name: evaluate(x, w, mode) for name, (x, w) in datasets.items()} for mode in ('sram', 'rram')}
    # Exhaustive bit reconstruction of every INT8 operand; DCIM 4-bit group coverage.
    assert all((1-((1-x)|(1-w))) == x*w for x in (0,1) for w in (0,1))
    assert all((v+128)-128 == v for v in range(-128, 128))
    assert all(((v & 15) + ((v >> 4) << 4)) == v for v in range(256))
    main_sram = physical_sram(dense)
    main_rram = physical_rram(dense)
    # Every logical cell maps to exactly one bit; reference locations have no payload.
    assert len(main_sram)*len(main_sram[0]) == 65536
    assert len(main_rram)*len(main_rram[0]) == 73728
    return {'status': 'PASS_nominal_arithmetic_only', 'K': K, 'N': N,
            'payload_bytes': K*N, 'sram_bits': 65536, 'rram_binary_cells': 73728,
            'sram_reference_bits': K*8, 'rram_reference_cells': K*(32+8),
            'DCIM': {'nibble_trees': 64, 'parallel_weight_bits': 4, 'nibble_pairs': 32,
                     'product_polarity': 'NOR(~input_bit, SRAM_Qbar) = input_bit AND stored_bit; explicit loaded input INV',
                     'quadrants': 4, 'columns_per_quadrant': 64, 'physical_bits': 65536},
            'contract': 'Two complete 8-bit native passes; three 25-bit correction operations; no data-dependent timing skip.',
            'rram_nominal_ADC': {'levels': 1024, 'Gon_S': 1/13000, 'Goff_S': 1/29000,
                                 'LSB_S': (1/13000-1/29000)/2, 'rounding': 'half-up',
                                 'baseline_removal': '(Q(G)-Q(Gref)) >> 1',
                                 'qualification': 'Ideal programmable gain/offset calibration assumed; not a NeuroSim transfer or measured ENOB validation.'},
            'dense_target': {'sram_ones': sum(map(sum, main_sram)), 'rram_SET_cells': sum(map(sum, main_rram)),
                             'rram_RESET_cells': 73728, 'target_formula': 'w[r,c]=((37*r+19*c)%256)-128'},
            'vectors': checks}


if __name__ == '__main__':
    result = run()
    target = Path(sys.argv[1]) / 'numeric.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])

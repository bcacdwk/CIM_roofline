"""Deterministic nonempty V1.4 original-main inputs and numeric assertions."""
import hashlib
import json
import math
from pathlib import Path
import re

def generate_inputs(directory):
    directory = Path(directory)
    directory.mkdir()
    # Network columns: IFM H,W,C; kernel H,W; output channels; maxpool; stride.
    # The upstream novel-mapping floorplanner requires at least 128 mapped rows
    # and 256 physical columns (32 outputs * 8 weight bits) for 128-row arrays.
    (directory / "network.csv").write_text("1,1,128,1,1,32,0,1\n")
    weights = [-0.75, -0.5, -0.25, 0.25, 0.5, 0.75]
    (directory / "weights.csv").write_text("".join(
        ",".join(str(weights[(3*r+c) % len(weights)]) for c in range(32))+"\n" for r in range(128)))
    # One activation vector, represented as 8 binary columns per input feature.
    activations = [(37*r+19) % 256 for r in range(128)]
    (directory / "input.csv").write_text("".join(
        ",".join(str((value >> bit) & 1) for bit in range(7,-1,-1))+"\n" for value in activations))
    metadata = {"network_rows": 1, "network_columns": 8, "weight_shape": [128, 32],
                "input_bit_trace_shape": [128, 8], "activation_vectors": 1,
                "weight_domain": [-1, 1], "generated_weight_min": -0.75, "generated_weight_max": 0.75,
                "input_domain": [0, 1], "nonzero_weight_count": 4096,
                "one_bits_in_input": sum(v.bit_count() if hasattr(int, "bit_count") else bin(v).count("1") for v in activations),
                "semantic_multiply_accumulates": 4096, "upstream_numComputation": 8192,
                "synapseBit": 8, "numBitInput": 8, "numRowSubArray": 128, "numRowParallel": 128,
                "format_evidence": ["main.cpp: getNetStructure/argv[1..7]", "Chip.cpp: LoadInWeightData/LoadInInputData", "Chip.cpp: numInVector * param->numBitInput"],
                "size_rationale": "Preserves default 128x128 SRAM; 128 logical input rows and 32 output channels meet original ChipFloorPlan novel-mapping hierarchy without source changes."}
    metadata["input_hashes"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.iterdir())}
    (directory / "input_manifest.json").write_text(json.dumps(metadata, indent=2)+"\n")
    return metadata

def validate_output(text):
    checks = {}
    checks["no_error_markers"] = not bool(re.search(r"\b(error|nan|inf|infinity)\b", text, re.I))
    checks["original_main_completion_marker"] = "Hardware Performance Done" in text
    checks["layer1_read_latency_present"] = "layer1's readLatency is:" in text
    checks["subarray_size_128x128"] = "User-defined SubArray Size: 128x128" in text
    checks["nonempty_tile_mapping"] = bool(re.search(r"# of tile used for each layer.*?layer1:\s*[1-9]", text, re.S))
    specifications = {
        "chip_area_um2": r"^ChipArea\s*:\s*(\S+)um\^2$",
        "cim_array_area_um2": r"^Chip total CIM array\s*:\s*(\S+)um\^2$",
        "chip_clock_period_ns": r"^Chip clock period is:\s*(\S+)ns$",
        "pipeline_cycle_ns": r"^Chip pipeline-system-clock-cycle \(per image\) is:\s*(\S+)ns$",
        "chip_read_dynamic_energy_pj": r"^Chip pipeline-system readDynamicEnergy \(per image\) is:\s*(\S+)pJ$",
        "layer1_read_latency_ns": r"^layer1's readLatency is:\s*(\S+)ns$",
        "layer1_read_dynamic_energy_pj": r"^layer1's readDynamicEnergy is:\s*(\S+)pJ$",
        "throughput_tops": r"^Throughput TOPS \(Pipelined Process\):\s*(\S+)$",
    }
    metrics = {}
    for name, pattern in specifications.items():
        match = re.search(pattern, text, re.M)
        try:
            value = float(match.group(1)) if match else None
        except ValueError:
            value = None
        checks[name+"_finite_positive"] = value is not None and math.isfinite(value) and value > 0
        metrics[name] = value
    # Compare every numeric line from the simulator, except elapsed wall time.
    numeric_lines = [line.rstrip() for line in text.splitlines()
                     if re.search(r"\d", line) and "Total Run-time" not in line]
    return {"status": "PASS" if all(checks.values()) else "FAIL", "assertions": checks,
            "metrics": metrics, "stable_numeric_lines": numeric_lines,
            "write_metrics": {"status": "NOT_REPORTED", "value": None},
            "rho_tau": "NOT_EVALUATED"}

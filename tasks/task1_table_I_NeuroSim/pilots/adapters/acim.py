"""SRAM ACIM reference adapter: explicit native events and SAR-code ownership.

The primitive dictionary is derived from input specifications, never saved v3
service totals.  The common backend owns all NeuroSim initialization and calls;
this module owns the reference topology, actual loop counts, and arithmetic
contract.  No generic SRAM SubArray latency enters this path.
"""

from collections import Counter
import math


COEFFICIENTS = (1, 2, 4, 8, 16, 32, 64, -128)


def _require(condition, message):
    if not condition:
        raise ValueError("ACIM adapter: " + message)


def _numerical_checks(k, n):
    """Check ideal calibrated code semantics; this is not analog precision QA.

    q = 4 * binary_partial_sum is an explicit operating-range condition, not a
    measured ADC transfer.  A fixed wiring shift q >> 2 returns the nominal count.
    The 10-bit converter retains q in its existing result state for both phases.
    """
    vectors = {
        "zero": ([0] * k, lambda o, i: (o * 29 + i * 17) % 256 - 128),
        "positive_extreme": ([-128] * k, lambda o, i: -128),
        "negative_extreme": ([-128] * k, lambda o, i: 127),
        "alternating_signs": ([127 if i % 2 else -128 for i in range(k)],
                              lambda o, i: -128 if (o + i) % 2 else 127),
        "deterministic_mixed": ([(i * 73 + 19) % 256 - 128 for i in range(k)],
                                lambda o, i: (o * 53 + i * 97 + 11) % 256 - 128),
    }
    result = {}
    max_code = 0
    max_abs_accumulator = 0
    min_leaf = 0
    max_leaf = 0
    signed_msb_witness = False
    normalization_witness = False
    for name, (x, weight_at) in vectors.items():
        outputs = []
        expected = []
        for out in range(n):
            weights = [weight_at(out, i) for i in range(k)]
            accumulator = 0
            no_input_sign = 0
            unnormalized = 0
            for ibit, input_coefficient in enumerate(COEFFICIENTS):
                raw_codes = []
                for wbit in range(8):
                    count = sum(((a & 255) >> ibit & 1) *
                                ((b & 255) >> wbit & 1)
                                for a, b in zip(x, weights))
                    code = 4 * count
                    _require(0 <= code < 2**10, "nominal SAR container overflow")
                    raw_codes.append(code)
                    max_code = max(max_code, code)
                # Phase one has no destination register.  It neither changes
                # the SAR source state nor captures an invented tree-result bank.
                phase_one = sum((q >> 2) * c for q, c in zip(raw_codes, COEFFICIENTS))
                held_codes = tuple(raw_codes)
                # Phase two recomputes the same combinational reduction, then
                # shifts/signs it and captures only the existing output bank.
                leaves = [(q >> 2) * c for q, c in zip(held_codes, COEFFICIENTS)]
                plane_sum = sum(leaves)
                _require(plane_sum == phase_one, "source code changed before consumption")
                min_leaf = min(min_leaf, *leaves)
                max_leaf = max(max_leaf, *leaves)
                _require(all(-2**17 <= leaf < 2**17 for leaf in leaves), "18-bit leaf overflow")
                _require(-2**20 <= plane_sum < 2**20, "21-bit reduction overflow")
                accumulator += plane_sum * input_coefficient
                no_input_sign += plane_sum * (1 << ibit)
                unnormalized += sum(q * c for q, c in zip(held_codes, COEFFICIENTS)) * input_coefficient
                _require(-2**22 <= accumulator < 2**22, "23-bit accumulator overflow")
                max_abs_accumulator = max(max_abs_accumulator, abs(accumulator))
            exact = sum(a * b for a, b in zip(x, weights))
            outputs.append(accumulator)
            expected.append(exact)
            signed_msb_witness |= no_input_sign != exact
            normalization_witness |= unnormalized != exact
        _require(outputs == expected, "signed reconstruction mismatch in " + name)
        result[name] = {"outputs_checked": n, "minimum": min(outputs), "maximum": max(outputs), "pass": True}
    all_counts = all(((4 * s) >> 2) == s and 4 * s < 2**10 for s in range(k + 1))
    return {
        "nominal_signed_reconstruction": True,
        "all_129_nominal_partial_counts": all_counts,
        "detects_missing_input_msb_sign": signed_msb_witness,
        "detects_missing_code_normalization": normalization_witness,
        "existing_containers_suffice": max_abs_accumulator < 2**22,
    }, {
        "scope": "nominal arithmetic under the declared q=4*s condition; not analog ENOB or accuracy validation",
        "fixtures": result,
        "observed_nominal_code_max": max_code,
        "observed_signed_leaf_range": [min_leaf, max_leaf],
        "observed_max_abs_accumulator": max_abs_accumulator,
        "tested_output_vectors": len(vectors),
        "tested_output_elements": len(vectors) * n,
    }


def build(case, p, backend):
    """Return unscheduled events; the common scheduler alone owns edge waits."""
    _require(case["case_id"] == "01_sram_acim", "wrong case identity")
    logical = case["logical"]
    k, n = logical["K"], logical["N"]
    installed = case["resources"]["installed"]
    native = case["resources"]["native_declared"]
    physical = case["physical"]["physical_capacity"]
    _require((k, n, logical["input_bits"], logical["weight_bits"], logical["output_bits"]) == (128, 128, 8, 8, 23), "reference geometry or encoding changed")
    _require(logical["signed"] is True, "signed INT8 contract required")
    _require(installed["adc_count"] == 128 and installed["digital_output_channels"] == 16, "ADC/lane inventory changed")
    _require(installed["existing_SAR_code_bits"] == 1280 and installed["new_intermediate_hold_bits"] == 0, "source-hold inventory changed")
    _require(installed["input_register_bits"] == k * 8 and installed["output_register_bits"] == n * 23, "register inventory changed")
    _require(physical == {"binary_cells": k * n * 8, "weight_planes": 8, "rows_per_plane": k, "columns_per_plane": n}, "physical planes changed")
    _require(native["adc_nominal_bits"] == 10 and native["partial_sum_levels"] == k + 1, "ADC/count semantics changed")
    _require(native["digital_ticks_per_batch"] == 2 and native["write_drivers"] == 128, "native service resources changed")
    _require(all(math.isfinite(float(backend[key])) and float(backend[key]) > 0 for key in ("sar_ns", "actual_period_ns")), "backend service time missing")
    _require(backend["dff_cycle"] == 1, "DFF must be the one-cycle timer")
    _require(all(math.isfinite(float(p[key])) and float(p[key]) > 0 for key in ("charge_front", "sram_write_cycle")), "native primitive missing")

    stages = {stage["id"]: stage for stage in case["services"]}

    def event(sid, kind, value=None, context=None):
        provider = "retained_native_complete_service" if sid in ("charge_front", "sram_write") else "neurosim_composed" if sid == "reconstruct" else "neurosim_native"
        data = {"id": sid, "kind": kind, "provider": provider,
                "resources": list(stages[sid]["resources"]) + (["existing_SAR_code_bits", "adc_count", "output_register_bits"] if sid == "reconstruct" else []), "context": dict(context or {})}
        if kind == "physical":
            data["ns"] = float(value)
        else:
            data["cycles"] = value
        return data

    streaming = [event("input_capture", "digital", 1, {"numDff": k * 8})]
    coverage = set()
    groups = n // installed["digital_output_channels"]
    for ibit in range(logical["input_bits"]):
        for group in range(groups):
            context = {"input_bit": ibit, "output_group": group,
                       "first_output": group * 16, "output_lanes": 16,
                       "parallel_weight_planes": 8, "adc_count": 128}
            streaming.append(event("charge_front", "physical", p["charge_front"], context))
            streaming.append(event("sar", "physical", backend["sar_ns"], context))
            for phase in (1, 2):
                streaming.append(event("reconstruct", "digital", 1,
                    {**context, "phase": phase,
                     "SAR_result_state_held_bits": 1280,
                     "new_intermediate_register_bits": 0,
                     "captures_output": phase == 2,
                     "recompute_tree_without_intermediate_register": phase == 2}))
            for weight_plane in range(8):
                for out in range(group * 16, (group + 1) * 16):
                    key = ibit, weight_plane, out
                    _require(key not in coverage, "duplicated scalar conversion")
                    coverage.add(key)
    streaming.append(event("output_commit", "digital", 1,
                           {"numDff": n * 23, "same_existing_output_bank": True,
                            "new_output_copy_bank_bits": 0}))

    payload = logical["resident_transaction_Byte"]
    _require(payload == 16 and logical["B_R_Byte"] % payload == 0, "resident payload cannot tile matrix")
    transactions = logical["B_R_Byte"] // payload
    resident = []
    for transaction in range(transactions):
        context = {"transaction": transaction, "logical_payload_Byte": payload,
                   "encoded_bits": 128, "selected_binary_cells": 128,
                   "input_row": transaction // groups, "output_group": transaction % groups}
        resident.append({"id": "native_write_accept", "kind": "boundary",
            "provider": "explicit_public_port_acceptance", "resources": ["encoded_interface_bits"],
            "margin_ns": 0, "context": {**context, "setup_capture_included_in_native_cycle": True}})
        resident.append(event("sram_write", "physical", p["sram_write_cycle"], context))
    resident.append({"id": "matrix_ready", "kind": "boundary",
        "provider": "explicit_public_compute_ready_acceptance", "resources": ["physical.native"],
        "margin_ns": 0, "context": {"complete_matrix": True, "no_extra_capture_cycle": True}})

    counts = Counter(item["id"] for item in streaming + resident if item["kind"] != "boundary")
    expected = {sid: stage["count"]["value"] for sid, stage in stages.items()}
    _require(dict(counts) == expected, "executed loops differ from frozen stage inventory")
    checks, numeric_details = _numerical_checks(k, n)
    checks.update({
        "frozen_stage_counts_preserved": dict(counts) == expected,
        "exact_scalar_conversion_coverage": len(coverage) == 8 * 8 * n == 8192,
        "full_matrix_payload": transactions * payload == k * n,
        "one_copy_eight_plane_capacity": physical["binary_cells"] == logical["B_R_Byte"] * 8,
        "no_added_operand_or_analog_hold": installed["operand_hold_bits"] == installed["analog_cross_group_hold_slots"] == 0,
        "SAR_state_held_through_both_reconstruction_cycles": all(
            [x["id"] for x in streaming[1 + batch * 4:1 + batch * 4 + 4]] ==
            ["charge_front", "sar", "reconstruct", "reconstruct"] for batch in range(64)),
        "native_complete_write_charged_once": counts["sram_write"] == transactions,
    })
    _require(all(checks.values()), "numerical/resource check failed")
    if backend.get("reconstruction_window"):
        for item in streaming:
            if item["id"] in ("reconstruct", "digital_reconstruct"):
                item["timing_window"] = backend["reconstruction_window"]
                phase = item.get("context", {}).get("phase")
                item["launch_offset_cycle"] = 1 if phase == 2 else 0
                item["capture_offset_cycles"] = [] if phase == 1 else [2]
                item["context"].update({
                    "propagation": "continuous E0 to E2; no restart and no capture at E1",
                    "first_edge_update": "phase only; SAR/input bit/output group/old accumulator held",
                    "phase_1": "propagate held operands; no intermediate capture",
                    "phase_2": "same propagation completes; capture existing accumulator at E2",
                    "recompute_tree_without_intermediate_register": False})
    streaming[0].setdefault("context", {}).update({
        "accumulator_initialization": "synchronous clear all existing output containers during input_capture; clear mux/control path included in backend",
        "new_register_or_cycle": False})
    return {"streaming": streaming, "resident": resident, "checks": checks,
        "snapshot": {
            "case_id": case["case_id"], "logical_K_N": [k, n],
            "physical_planes": dict(physical), "counts": dict(counts),
            "scalar_conversions": len(coverage),
            "native_front_ns": float(p["charge_front"]),
            "native_write_cycle_ns": float(p["sram_write_cycle"]),
            "SAR_conversion_ns": float(backend["sar_ns"]),
            "actual_public_period_ns": float(backend["actual_period_ns"]),
            "source_result_lifetime": {
                "owner": "existing SAR converter result state", "bits": 1280,
                "start": "SAR conversion complete", "end": "phase-two output capture complete",
                "next_conversion_before_release": False, "new_intermediate_hold_bits": 0,
            },
            "code_normalization": {
                "status": "explicit_engineering_operating_range_condition",
                "ideal_raw_code": "q=4*s, s=sum of 128 binary products in [0,128]",
                "nominal_ADC_bits": 10, "target_effective_bits": native["adc_effective_bits_target"],
                "raw_code_range": [0, 512], "normalization": "q >> 2, fixed wiring; two raw LSBs discarded",
                "normalized_partial_count_levels": 129,
                "weight_and_input_coefficients": list(COEFFICIENTS),
                "accuracy_caveat": "No measured voltage/code transfer, calibration circuitry, ENOB or exact integer accuracy is claimed; timing is conditional on this operating range.",
            },
            "register_allocation": {
                "input_bits": 1024, "SAR_owned_bits": 1280, "output_accumulator_bits": 2944,
                "active_output_bits": 16 * 23, "new_intermediate_bits": 0,
                "phase_one": "source held, combinational weighted reduction, no intermediate capture",
                "phase_two": "E2 capture from continuous E0 propagation" if backend.get("reconstruction_window") else "V1 single-cycle conservative recomputation",
                "output_commit": "publish existing output bank; no second bank or extra per-batch register",
            },
            "resident": {
                "transactions": transactions, "logical_Byte_per_transaction": payload,
                "native_local_latency_ns": float(p["sram_write_cycle"]),
                "service_interval_policy": "one 128-bit word accepted at an eligible public edge; native complete cycle includes capture; next word waits for physical completion and next public edge",
                "matrix_completion_policy": "last native completion accepted at matrix-ready public boundary; zero extra tick, margin included by retained native cycle",
                "additional_write_capture_cycles": 0, "additional_driver_cycles": 0,
            },
            "numerical_validation": numeric_details,
            "evidence": [
                "configs/cases/01_sram_acim.json: logical, resources, services, service_schedules",
                "tasks/task1_table_I_NVM/analysis/01_sram_acim/data/inputs.json: scenarios[1], write_resources, update_geometry",
                "tasks/task1_table_I_NVM/analysis/01_sram_acim/notes/method_review.zh.md: sections 1-4",
                "tasks/task1_table_I_NVM/analysis/01_sram_acim/scripts/check_sram_acim.py: calculate, test_signed_reconstruction_contract",
            ],
        }}

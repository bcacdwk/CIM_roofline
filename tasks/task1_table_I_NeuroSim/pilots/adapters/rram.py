"""WH-2T1R reference adapter: native physical service + public LV periphery.

This module never reads a saved performance result.  ``p`` contains primitive
input budgets; the supervisor's backend owns actual NeuroSim calls and timing.
The event lists are serial, with no overlapping ADC, write or holding resource.
"""
from collections import Counter
from functools import lru_cache
import hashlib
import json


def _physical(sid, ns, resources, context=None, provider="v3_native_service"):
    return dict(id=sid, kind="physical", ns=float(ns), provider=provider,
                resources=list(resources), context=context or {})


def _digital(sid, cycles, resources, context=None):
    return dict(id=sid, kind="digital", cycles=cycles,
                provider="neurosim_composed", resources=list(resources),
                context=context or {})


def _window_pass(target, resistance_ohm):
    """Two-sided LRS acceptance is required; binary state alone is insufficient."""
    return 8000 <= resistance_ohm <= 12000 if target else resistance_ohm >= 70000


def _controller_fixture(target, reset_reads, set_read):
    """Finite reference controller, given deterministic fresh window readings.

    Synthetic readings exercise protocol truth conditions, not switching yield.
    Every reserved slot is paid by the service schedule even when lanes mask off.
    """
    assert len(target) == 128 and len(reset_reads) == 2 and len(set_read) == 128
    remaining = [True] * 128
    history = []
    for index, readings in enumerate(reset_reads):
        assert len(readings) == 128
        active_before = sum(remaining)
        # A successful RESET lane is masked for the next pulse, but all 128
        # lanes are freshly sensed. A later disturbance is therefore detected.
        remaining = [not _window_pass(0, value) for value in readings]
        history.append(dict(phase="RESET", attempt=index + 1,
                            pulse_active_lanes=active_before,
                            failing_lanes=sum(remaining)))
    if any(remaining):
        return dict(published=False, successful_payload_Byte=0,
                    failure="RESET_budget_exhausted", history=history)
    passing = [_window_pass(bit, value) for bit, value in zip(target, set_read)]
    history.append(dict(phase="SET", attempt=1, pulse_active_lanes=sum(target),
                        terminal_verify_lanes=128, failing_lanes=passing.count(False)))
    if not all(passing):
        return dict(published=False, successful_payload_Byte=0,
                    failure="terminal_window_failure", history=history)
    return dict(published=True, successful_payload_Byte=16, failure=None,
                history=history)


@lru_cache(maxsize=1)
def _protocol_checks():
    target = [i % 2 for i in range(128)]
    first = [60000 if i % 17 == 0 else 100000 for i in range(128)]
    complete_reset = [100000] * 128
    complete_set = [10000 if bit else 100000 for bit in target]
    good = _controller_fixture(target, [first, complete_reset], complete_set)
    failed_reset = list(complete_reset)
    failed_reset[0] = 60000
    reset_fail = _controller_fixture(target, [first, failed_reset], complete_set)
    overshot = list(complete_set)
    overshot[1] = 7000
    low_fail = _controller_fixture(target, [first, complete_reset], overshot)
    under_set = list(complete_set)
    under_set[1] = 13000
    high_fail = _controller_fixture(target, [first, complete_reset], under_set)
    disturbed = list(complete_set)
    disturbed[0] = 60000
    hrs_fail = _controller_fixture(target, [first, complete_reset], disturbed)
    all_zero = _controller_fixture([0] * 128, [complete_reset] * 2, complete_reset)
    return dict(
        finite_two_reset_one_set_success=good["published"],
        failed_reset_never_publishes=not reset_fail["published"],
        LRS_lower_bound_enforced=not low_fail["published"],
        LRS_upper_bound_enforced=not high_fail["published"],
        terminal_verify_checks_masked_HRS=not hrs_fail["published"],
        all_zero_retains_SET_slot=len(all_zero["history"]) == 3,
        no_success_payload_on_failure=all(q["successful_payload_Byte"] == 0
            for q in (reset_fail, low_fail, high_fail, hrs_fail)),
    ), dict(success=good, reset_timeout=reset_fail, LRS_overshoot=low_fail,
            LRS_underprogram=high_fail, masked_HRS_disturbance=hrs_fail,
            all_zero=all_zero,
            scope="synthetic endpoint inputs; no predicted switching probability")


@lru_cache(maxsize=1)
def _nominal_checks():
    """Ideal calibrated partial sums -> signed plane arithmetic -> INT23.

    q=16*s is an explicit nominal diagnostic encoding, not the physical ADC
    transfer. Missing current-to-code calibration is not silently manufactured.
    """
    coeff = [1, 2, 4, 8, 16, 32, 64, -128]
    fixtures = [
        ("both_minimum", [-128] * 128, lambda n, k: -128),
        ("minimum_times_maximum", [-128] * 128, lambda n, k: 127),
        ("mixed_signed", [((37*k + 19) % 256) - 128 for k in range(128)],
         lambda n, k: ((n*11 + k*23 + 5) % 256) - 128),
    ]
    rows = []
    max_code = 0
    max_abs_intermediate = 0
    all_equal = True
    all_bounded = True
    for name, inputs, weight_fn in fixtures:
        expected = []
        reconstructed = []
        for n in range(64):
            weights = [weight_fn(n, k) for k in range(128)]
            expected.append(sum(x*w for x, w in zip(inputs, weights)))
            accum = 0
            for ib in range(8):
                for row_group in range(4):
                    plane_sum = 0
                    for wb in range(8):
                        partial = sum(((inputs[k] & 255) >> ib & 1) *
                                      ((weights[k] & 255) >> wb & 1)
                                      for k in range(row_group*32, row_group*32+32))
                        q = 16 * partial
                        assert 0 <= q <= 512 < 2**10 and q % 16 == 0
                        max_code = max(max_code, q)
                        plane_sum += coeff[wb] * (q >> 4)
                    accum += coeff[ib] * plane_sum
                    max_abs_intermediate = max(max_abs_intermediate, abs(accum))
                    all_bounded &= -(2**22) <= accum < 2**22
            reconstructed.append(accum)
        equal = reconstructed == expected
        all_equal &= equal
        rows.append(dict(name=name, direct_min=min(expected), direct_max=max(expected),
                         pass_equal=equal,
                         outputs_sha256=hashlib.sha256(json.dumps(reconstructed).encode()).hexdigest()))
    return dict(nominal_signed_reconstruction=all_equal,
                nominal_accumulator_fits_INT23=all_bounded,
                nominal_code_fits_10_bits=max_code <= 1023), dict(
        fixtures=rows, max_code=max_code,
        max_abs_partial_accumulator=max_abs_intermediate,
        diagnostic_code="q = 16 * ideal calibrated 32-term partial sum; q >> 4 decodes",
        nominal_ADC_code_bits=10, reference_ENOB_scale_only_bits=8,
        effective_precision_verified=False,
        physical_ADC_transfer_instantiated=False,
        device_or_analog_accuracy_verified=False,
        qualification="Diagnostic scaling only; physical calibration and error bounds are not provided by SarADC latency model")


def build(case, p, backend):
    assert case["case_id"] == "05_rram"
    logical = case["logical"]
    assert (logical["K"], logical["N"], logical["input_bits"], logical["weight_bits"]) == (128, 64, 8, 8)
    installed = case["resources"]["installed"]
    native = case["resources"]["native_declared"]
    assert (installed["adc_count"], installed["digital_output_channels"]) == (128, 16)
    assert native["write_driver_count"] == 128 and native["binary_window_comparators"] == 256
    assert installed["existing_SAR_code_bits"] == 128 * 10
    assert installed["new_intermediate_hold_bits"] == 0
    assert backend["sar_ns"] > 0 and backend["actual_period_ns"] > 0

    streaming = [_digital("input_capture", 1, ["input_register_1024b", "controller_32b"])]
    for ib in range(8):
        for row_group in range(4):
            for output_group in range(4):
                ctx = dict(input_bit=ib, row_group=row_group, output_group=output_group,
                           active_terms=32, output_lanes=16, parallel_weight_planes=8)
                streaming.extend([
                    _physical("cim_input_select", p["input_step"], ["CIMSEL", "input_register_1024b"], ctx),
                    _physical("cim_front", p["cim_front"], ["native_CIM_T2_shared_TBL"], ctx),
                    _physical("sar", backend["sar_ns"], ["SAR_128", "existing_SAR_code_1280b"], ctx, "neurosim_native"),
                    _digital("digital_reconstruct", 2, ["SAR_128", "existing_SAR_code_1280b", "digital_lanes_16", "output_register_1472b"],
                             {**ctx, "source_retention": "freeze 128 existing SAR result codes through both ticks",
                              "phase_1": "weighted reduction; no intermediate capture",
                              "phase_2": "recompute reduction, signed input shift, accumulator capture"}),
                ])
    streaming.append(_digital("output_commit", 1, ["output_register_1472b", "controller_32b"]))

    def transaction(out, group, half):
        context = dict(transaction=out*8 + group*2 + half, output=out,
                       native_subarray=group, selected_half=half,
                       logical_payload_Byte=16, physical_binary_targets=128)
        events = [_digital("resident_front", 2, ["encoded_staging_128b", "mask_done_128b", "controller_32b"], context)]
        for phase, attempts in (("RESET", 2), ("SET", 1)):
            for attempt in range(attempts):
                ctx = {**context, "phase": phase, "attempt": attempt + 1,
                       "pulse_V": (1.5 if phase == "RESET" else 1.2) + 0.1*attempt,
                       "pulse_mask": "unfinished RESET targets" if phase == "RESET" else "target-one and unfinished lanes",
                       "verify_targets": "all 128 HRS" if phase == "RESET" else "all 128 lanes against target-specific LRS/HRS windows"}
                events.extend([
                    _digital("attempt_control", 1, ["encoded_staging_128b", "mask_done_128b", "controller_32b"], ctx),
                    _physical("local_setup", p["local_setup"], ["native_program_drivers_128", "local_BL_SL"], ctx),
                    _physical(phase.lower() + "_pulse", p[phase.lower() + "_pulse"], ["native_program_drivers_128", "shared_program_rail"], ctx),
                    _physical("local_return", p["local_return"], ["native_program_drivers_128", "local_BL_SL"], ctx),
                    _physical("verify_input_select", p["input_step"], ["native_memory_T1_BL_SL"], ctx),
                    _physical("memory_verify_front", p["memory_verify_front"], ["native_memory_T1_BL_SL"], ctx),
                    _physical("binary_window_sense", p["binary_verify_sense_ns"], ["native_window_comparators_256_and_latches"], ctx),
                    _digital("attempt_done", 1, ["native_window_latches", "mask_done_128b", "controller_32b"], ctx),
                ])
        return events

    rail_setup = _physical("rail_setup", p["rail_setup"], ["shared_program_rail"])
    rail_exit = _physical("rail_exit", p["rail_exit"], ["shared_program_rail"])
    publish = dict(id="matrix_publish", kind="boundary", margin_ns=backend["boundary_setup_ns"],
                   provider="neurosim_composed", resources=["controller_32b"],
                   context=dict(condition="all 512 transactions terminal-verified, no sticky fail, rail released",
                                operation="ready capture at first setup-eligible clock edge; no added full tick"))
    resident = [rail_setup]
    covered_weights = set()
    for out in range(64):
        for group in range(4):
            for half in range(2):
                resident.extend(transaction(out, group, half))
                for bank in range(2):
                    for lane in range(8):
                        key = (out, group*32 + bank*16 + half*8 + lane)
                        assert key not in covered_weights
                        covered_weights.add(key)
    resident.extend([rail_exit, publish])
    local = transaction(0, 0, 0)
    isolated = [rail_setup, *local, rail_exit, publish]
    counts = Counter(event["id"] for event in resident)
    protocol_checks, protocol_evidence = _protocol_checks()
    nominal_checks, nominal_evidence = _nominal_checks()
    checks = {
        "physical_mapping_covers_8192_weights_once": len(covered_weights) == 8192,
        "streaming_has_128_batches": sum(e["id"] == "sar" for e in streaming) == 128,
        "streaming_has_256_reconstruction_ticks": sum(e.get("cycles", 0) for e in streaming if e["id"] == "digital_reconstruct") == 256,
        "resident_has_512_local_transactions": counts["resident_front"] == 512,
        "RESET_and_SET_slots_counted": counts["reset_pulse"] == 1024 and counts["set_pulse"] == 512,
        "every_attempt_has_fresh_verify": counts["binary_window_sense"] == counts["attempt_done"] == 1536,
        "shared_rail_lifecycle_counted_once": counts["rail_setup"] == counts["rail_exit"] == 1,
        "independent_window_budget_not_SAR_linked": all(e["ns"] == p["binary_verify_sense_ns"] for e in resident if e["id"] == "binary_window_sense"),
        "no_SAR_in_memory_verify": not any(e["id"] == "sar" for e in resident),
        "code_retention_uses_existing_inventory": installed["existing_SAR_code_bits"] == 1280 and installed["new_intermediate_hold_bits"] == 0,
        **protocol_checks, **nominal_checks,
    }
    streaming[0].setdefault("context", {}).update({
        "accumulator_initialization": "synchronous clear all existing output containers during input_capture; clear mux/control path included in backend",
        "new_register_or_cycle": False})
    return dict(streaming=streaming, resident=resident,
                local_transaction=local, isolated_transaction=isolated,
                checks=checks, snapshot=dict(
                    adapter="WH-2T1R native geometry / public SAR and LV digital",
                    logical_shape=[128, 64], native_macro_shape=[64, 128], native_macros=8,
                    subarrays_per_macro=4, native_subarray_shape=[64, 32],
                    streaming_batches=128, digital_reconstruction_ticks=256,
                    resident_transactions=512, payload_Byte_per_transaction=16,
                    independent_window_sense_ns=p["binary_verify_sense_ns"],
                    shared_rail_lifecycle="one establishment and one exit for full matrix",
                    programming="reserved two RESET / one masked SET attempt per group; no early-done throughput credit",
                    controller_state_bits=32,
                    controller_inventory="9 transaction-address bits; 2 retry, 2 phase, ready/fail and control state fit within 32 bits",
                    native_window_latches="included in native 20 ns window sense, not added again",
                    native_window_reference_selection="two comparators per lane: target-one selects LRS 8/12 kOhm limits; target-zero selects HRS 70 kOhm threshold; second output unused for HRS",
                    matrix_publish="existing controller ready capture after rail exit; setup/edge boundary charged by scheduler",
                    terminal_verify="last SET window read checks all 128 targets including target-zero HRS; no unsourced extra matrix scan",
                    sar_retention="128 existing 10-bit SAR codes frozen through both ticks; next conversion starts only after accumulation",
                    additional_data_hold_bits=0,
                    controller_inventory_explicit_step3_addition=True,
                    numerical_diagnostics=nominal_evidence, protocol_diagnostics=protocol_evidence,
                    source_inputs=case["provenance"]["sources"]["inputs"],
                    raw_NeuroSim_aggregate_writeLatency=None,
                    aggregate_write_qualification="V1.4 lacks an aggregate write result; T_R is the sum of native write stages and modeled LV control schedule",
                    completion_condition="all active cells reach declared windows within finite attempts; fail has zero successful payload",
                    cross_stack_condition="1 us program waveform and 2/1 completion remain sourced engineering conditions, not same-stack measured switching/accuracy"))

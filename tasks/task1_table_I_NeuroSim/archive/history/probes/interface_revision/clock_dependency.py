#!/usr/bin/env python3
"""Step 2 revision: explicit clock ownership and executable dependency slices.

This module does not predict case performance.  Synthetic serial events test the
new boundary policy; bound contribution evaluation tests parameter propagation.
Original-v3 replay is a separate mode and must not call serial_events().
"""
import copy
import json
import math
import sys
sys.dont_write_bytecode = True

VERSION = "3.0.0"
CLOCK_RULE = ("max(target_period_ns, complete measured single-cycle register-to-register "
              "paths assigned to this clock domain); independent analog/ADC/native "
              "service durations never constrain this clock")
BOUNDARY_RULE = ("Keep physical completion time; align once when the next declared digital "
                 "consumer accepts it. Do not round every native/internal substage. "
                 "The declared setup/handshake margin is included before alignment; "
                 "an exactly eligible edge adds no extra cycle. No added overlap or registers.")

# Only these linear dependency slices are evaluated by this probe. Other native
# services keep their existing schedule/operation expression (e.g. FeNOR max
# guard, selected RESET versus SET, or GC refresh period). A period is not a
# latency contribution, nor are mutually exclusive pulses summed here.
def _slice_bindings(case_id):
    return {"input_step", "adc_batch", "digital_tick", "binary_verify_sense_ns"} | {
        "04_nand_3d": {"wl_setup", "bl_setup", "sl_setup"},
        "07_pcm": {"shared_voltage_front"},
        "09_gain_cell_edram": {"common_read_overhead", "program_complete"},
    }.get(case_id, set())


def policy_fragment():
    return {
        "clock": {
            "clock_id": "lv_core", "target_period_ns": 5,
            "actual_rule": CLOCK_RULE,
            "constraint_input_kind": "combinational_path",
            "required_path_evidence": ["constraint_clock_id", "start_register", "end_register", "single_cycle", "complete_serial_path", "actual_load", "path_status"],
            "non_constraints": ["SarADC conversion", "analog frontend integration/settling", "complete program/erase", "restore/refresh native operation", "complete local SRAM memory cycle"],
            "single_cycle_sensing_exception": "Only an explicitly bounded register-to-register path assigned to this domain may include sensing; do not infer this from SubArray or wrapper membership.",
            "cycle_conversion": "raw_cycles * clocks[clock_id].actual_period_ns exactly once",
            "seconds_conversion": "raw_seconds * 1e9 exactly once",
            "physical_time_clock_id": None,
            "constraint_clock_field": "constraint_clock_id (not a conversion clock)",
            "service_boundary_rule": BOUNDARY_RULE,
            "native_cycle_interface": "A retained complete cycle owns its internal clock/command/data/recovery. Dispatch at an eligible interface boundary, preserve its physical duration, and align completion only at the declared next digital consumer; no extra capture of included command/data.",
            "legacy_replay": "Use v3 durations/counts without new clock selection or edge alignment; compare independent stage aggregation with saved v3 results.",
            "main_route": "Keep upstream slow-target-clock reproduction as upstream behavior evidence only; its sensing critical path is not a primitive-service clock constraint.",
            "dff_caveat": "DFF cycles are a schedule timer, not frequency closure evidence.",
            "no_implicit_pipeline": True,
        },
        "dependency_types": {
            "physical_shared_circuit": "The same declared circuit is used in multiple modes; preserve each mode's bias/load/count.",
            "shared_physical_parameter": "One physical quantity affects multiple consumers, without asserting identical circuit or service timing.",
            "adopted_capability_policy": "Explicit modeling policy; neither an electrical identity nor physical resource sharing.",
            "dedicated_parameter": "One local native service parameter; no asserted cross-mode sharing.",
        },
        "rram_binary_verify": {
            "primary_parameter": "binary_verify_sense_ns", "reference_value_ns": 20,
            "primary_provider": "v3_native_service", "same_physical_ADC": False,
            "replacement": "Independent memory-window decision/latch budget retained until a compatible analog window-sense model is instantiated; digital Comparator is not that model.",
            "historical_source": "inputs:/adopted_inputs/binary_sense_slot_ns plus shared:/common_conditions/propagation/profile_values/reference/adc_batch",
            "capability_policy_comparison": {"id": "rram_TB_equals_TA_capability_policy", "enabled": False, "dependency_type": "adopted_capability_policy", "rule": "binary_verify_sense_ns = adc_batch only when explicitly selected as a separate comparison"},
        },
    }


def _finite_nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(name + " must be finite and nonnegative")
    return value


def _period(clocks, clock_id):
    if not clock_id or clock_id not in clocks:
        raise ValueError("missing clock: " + str(clock_id))
    p = clocks[clock_id]
    p = p.get("actual_period_ns") if isinstance(p, dict) else p
    _finite_nonnegative(p, "clock period")
    if p == 0:
        raise ValueError("zero clock period")
    return p


def normalize_time(raw, clocks):
    """Typed raw -> ns; never accept an already normalized record a second time."""
    if raw.get("normalized") is True or "normalized_ns" in raw:
        raise ValueError("time already normalized")
    value = _finite_nonnegative(raw.get("value"), "time")
    unit = raw.get("unit")
    if unit == "cycles":
        value *= _period(clocks, raw.get("clock_id"))
    elif unit in ("s", "ns"):
        if raw.get("clock_id") is not None:
            raise ValueError("physical time cannot carry a conversion clock")
        value *= 1e9 if unit == "s" else 1
    else:
        raise ValueError("unknown time unit")
    return {"normalized_ns": value, "normalized": True, "raw_unit": unit}


def _leaves(records):
    """Transparent packaging cannot create clock constraints or edge waits."""
    for record in records:
        if "children" in record:
            if any(k in record for k in ("constraint_clock_id", "clock_id", "align_clock_id", "timing_kind")):
                raise ValueError("transparent wrapper cannot own timing semantics")
            yield from _leaves(record["children"])
        else:
            yield record


def clockpolicy(target_period_ns, clock_id, paths):
    target = _finite_nonnegative(target_period_ns, "target period")
    if target == 0:
        raise ValueError("zero target period")
    accepted = []
    for path in _leaves(paths):
        owner = path.get("constraint_clock_id")
        if path.get("timing_kind") != "combinational_path":
            if owner is not None:
                raise ValueError("service duration is not a combinational clock constraint")
            continue
        if not owner:
            raise ValueError("combinational path needs an explicit clock owner")
        if owner != clock_id:
            continue
        if not path.get("single_cycle") or not path.get("start_register") or not path.get("end_register"):
            raise ValueError("clock constraint needs an explicit single-cycle register boundary")
        if not path.get("complete_serial_path"):
            raise ValueError("a primitive fragment does not establish a complete path")
        if path.get("path_status") not in ("actual_case_path_instantiated", "synthetic_fixture"):
            raise ValueError("pending/uninstantiated path cannot constrain a case clock")
        load = path.get("actual_load")
        if not isinstance(load, dict) or load.get("status") != "specified" or not load.get("evidence"):
            raise ValueError("clock constraint requires specified actual-load evidence")
        if path["path_status"] == "synthetic_fixture" and load.get("kind") != "synthetic_fixed_load":
            raise ValueError("synthetic path must state its fixed synthetic load")
        ns = normalize_time(path["raw"], {})["normalized_ns"]
        accepted.append({"id": path["id"], "duration_ns": ns, "path_status": path["path_status"]})
    return {"clock_id": clock_id, "target_period_ns": target,
            "actual_period_ns": max([target] + [x["duration_ns"] for x in accepted]),
            "constraining_paths": accepted}


def serial_events(events, clocks, start_ns=0):
    """No overlap. Physical steps stay continuous; an explicit digital entry aligns.

    A native event blocks only its named resources. boundary_hold_resources names
    resources deliberately retained while waiting for the consumer edge. This
    is accounting, not a permission for any other service to overlap.
    """
    now = _finite_nonnegative(start_ns, "start")
    out, occupancy = [], {}
    for event in _leaves(events):
        kind = event.get("timing_kind")
        if kind not in ("service_duration", "digital_step"):
            raise ValueError("event needs a service or digital-step timing kind")
        if event.get("constraint_clock_id") is not None:
            raise ValueError("service event cannot constrain clock")
        wait = 0
        if kind == "digital_step":
            if event["raw"].get("unit") != "cycles":
                raise ValueError("digital step must retain cycle return")
            period = _period(clocks, event["raw"].get("clock_id"))
            margin = _finite_nonnegative(event.get("interface_setup_margin_ns", 0), "interface margin")
            eligible = now + margin
            # 1e-12 relative tolerance only suppresses FP round-off at exact edges.
            edge = math.ceil(eligible / period - 1e-12) * period
            wait = max(0, edge - now)
        elif event["raw"].get("unit") == "cycles":
            raise ValueError("native physical service must not impersonate digital cycles")
        for resource in event.get("boundary_hold_resources", []):
            occupancy[resource] = occupancy.get(resource, 0) + wait
        begin = now + wait
        duration = normalize_time(event["raw"], clocks)["normalized_ns"]
        now = begin + duration
        for resource in event.get("resources", []):
            occupancy[resource] = occupancy.get(resource, 0) + duration
        out.append({"id": event["id"], "start_ns": begin, "boundary_wait_ns": wait,
                    "service_duration_ns": duration, "completion_ns": now,
                    "resources": event.get("resources", [])})
    return {"completion_ns": now, "events": out, "resource_occupancy_ns": occupancy,
            "overlap": False, "scope": "synthetic interface accounting; not case performance"}


def _digital_coefficient(case_id, service):
    sid = service["id"]
    ins = service["call"]["inputs"]
    if sid == "load_calibration":
        return ins["arithmetic_cycles"]
    if sid == "refresh_decode_load_rewrite":
        return ins["sign_decode_cycles"] + ins["front_control_cycles"] + ins["data_beats"] - int(ins["first_data_in_command"])
    if sid == "terminal_verify":
        return ins.get("capture_cycles_per_branch", ins.get("capture_cycles", 0)) + ins.get("compare_cycles_per_branch", ins.get("compare_cycles", 0))
    for key in ("control_cycles_per_erase", "control_cycles_per_attempt", "selection_cycles_per_batch", "comparison_cycles"):
        if key in ins:
            return ins[key]
    if sid == "page_load" and case_id == "04_nand_3d":
        return {"by_schedule_page_kind": {"data": ins["control_cycles"] + ins["data_page_beats"], "reference": ins["control_cycles"] + ins["reference_page_beats"]}}
    return ins.get("front_reference_cycles", 1)


def _coefficient(case_id, service, binding_id):
    if binding_id == "digital_tick":
        return _digital_coefficient(case_id, service)
    if service["id"] == "load_calibration":
        if binding_id == "wl_setup":
            return service["call"]["inputs"]["wl_setup_count"]
        if binding_id in ("adc_batch", "bl_setup", "sl_setup"):
            return service["call"]["inputs"]["analog_rounds"]
    if binding_id == "drive_transition" and service["id"] == "program_reset_set":
        return service["call"]["inputs"]["driver_transitions_per_batch"]
    return 1


def _binding_type(case_id, bid, consumers):
    if bid == "digital_tick":
        return "physical_shared_circuit", "declared common lv_core clock/control domain"
    if bid == "adc_batch":
        return "physical_shared_circuit", "installed SAR lanes; sequential native mode usage; no new ADC"
    if bid == "input_step":
        return "adopted_capability_policy", "v3 selected input/reset budget; common value is not proof of circuit identity"
    shared = {
        "04_nand_3d": {"sl_setup", "bl_setup", "wl_setup"},
        "07_pcm": {"shared_voltage_front"},
        "09_gain_cell_edram": {"common_read_overhead", "program_complete"},
    }
    if bid in shared.get(case_id, set()):
        return "physical_shared_circuit", "same declared front/program path reused in separately biased/timed modes"
    return ("shared_physical_parameter", "one native physical parameter; mode-specific use retained") if len(consumers) > 1 else ("dedicated_parameter", "local native input")


def revise_case(case):
    """Called after legacy specify()+add_bindings(); mutate only timing/dependencies."""
    cid = case["case_id"]
    case["contract_version"] = VERSION
    case["periphery"]["clock"] = {
        "clock_id": "lv_core", "target_period_ns": 5, "actual_period_ns": None,
        "status": "pending_actual_case_register_path_instantiation",
        "rule": CLOCK_RULE, "constraints": [],
        "service_boundary_rule": BOUNDARY_RULE,
        "constraint_status": "module probe is not actual-case timing closure",
    }
    if cid == "05_rram":
        service = next(s for s in case["services"] if s["id"] == "endpoint_verify")
        call = service["call"]
        call["inputs"].pop("adc_batch", None)
        call["inputs"]["binary_verify_sense_ns"] = "binding"
        call["policy_link"] = copy.deepcopy(policy_fragment()["rram_binary_verify"]["capability_policy_comparison"])
        call["policy_link"].update(same_physical_ADC=False, physical_resource="256 independent analog window-decision nodes; T1/IO/BL/SL memory path")
        call["entrypoint"] = "retained memory frontend + independent binary window sense/latch budget"
        call["components"] = []
        call["native_components"] = [
            {"provider": "v3_native_service", "parameter": "memory_verify_front", "count": 1},
            {"provider": "v3_native_service", "parameter": "binary_verify_sense_ns", "count": 1, "includes": ["window decision", "latch"]},
            {"provider": "v3_native_service", "binding": "input_step", "count": 1},
        ]
        call["outputs"] = [{"field": "independent_window_service", "unit": "ns", "clock_id": None, "status": "retained_native_service_budget"}]
        call["timing_role"] = "independent physical memory-window service; no SAR formula and no digital Comparator substitution"
        service["provider"] = "v3_native_service"
        source_refs = [
            {"source_id": "inputs", "json_pointer": "/adopted_inputs/binary_sense_slot_ns"},
            {"source_id": "shared", "json_pointer": "/common_conditions/propagation/profile_values/reference/adc_batch"},
        ]
        old = next((p for p in case["device"]["primitives"] if p["id"] == "binary_verify_sense_ns"), None)
        if old is None:
            case["device"]["primitives"].append({
                "id": "binary_verify_sense_ns", "original": {"value": 20, "unit": "ns"},
                "normalized": {"value": 20e-9, "unit": "s"},
                "status": "retained_v3_reference_budget_now_independently_bound",
                "kind": "native_window_sense_budget", "mode": "memory_endpoint",
                "included_stages": ["window decision", "latch"], "source_refs": source_refs,
                "provenance_note": "v3 reference T_B was 20ns through an explicit T_B=T_A capability policy, not a measured same-ADC fact; keep numeric reference and provenance, remove default cross-dependency.",
            })
        for binding in case["parameter_bindings"]:
            if binding["id"] == "adc_batch":
                binding["consumers"] = [x for x in binding["consumers"] if x != "endpoint_verify"]
        if not any(b["id"] == "binary_verify_sense_ns" for b in case["parameter_bindings"]):
            case["parameter_bindings"].append({
                "id": "binary_verify_sense_ns", "status": "active",
                "single_source": {"local_json_pointer": "/device/primitives/" + str(len(case["device"]["primitives"]) - 1) + "/normalized", "source_refs": source_refs, "v3_reference_value_ns": 20},
                "replacement_status": "retained_v3_native_window_budget", "replacement_value_ns": 20,
                "clock_id": None, "consumers": ["endpoint_verify"],
                "selected_implementation": "v3_native_service; compatible analog window-sensing implementation pending; Comparator is not a replacement",
                "conversion": "native normalized seconds * 1e9 once", "included_overhead": ["window decision", "latch"],
                "maintenance_recompute": "Only declared independent memory-window consumers; no dependence on CIM SAR precision.",
            })
        case["device"]["mode_inputs"]["memory_endpoint"]["binary_verify_sense_ns"] = 20
        case["device"]["mode_inputs"]["memory_endpoint"]["binary_verify_sense_provider"] = "v3_native_service"

    bindings = {b["id"]: b for b in case["parameter_bindings"]}
    services = {s["id"]: s for s in case["services"]}
    for bid, b in bindings.items():
        kind, reason = _binding_type(cid, bid, b["consumers"])
        b["dependency_type"] = kind
        b["dependency_reason"] = reason
        b["consumer_dependencies"] = [
            {"service_id": sid,
             "coefficient_per_occurrence": _coefficient(cid, services[sid], bid) if bid in _slice_bindings(cid) else None,
             "coefficient_status": "evaluated_linear_dependency_slice" if bid in _slice_bindings(cid) else "use_original_operation_expression; not evaluated by dependency probe",
             "dependency_type": kind, "scope": "per schedule occurrence, not stage.count aggregate",
             "role": "digital_step" if bid == "digital_tick" else "service_duration_or_native_physical_parameter"}
            for sid in b["consumers"]
        ]
    for service in case["services"]:
        call, sid = service["call"], service["id"]
        has_digital = sid in bindings["digital_tick"]["consumers"]
        has_native = bool(call.get("native_components")) or service["provider"] == "v3_native_service"
        kind = "mixed_service" if has_digital and has_native else "digital_step" if has_digital else "service_duration"
        service["clock_role"] = {
            "timing_kind": kind, "constraint_clock_id": None,
            "digital_clock_id": "lv_core" if has_digital else None,
            "reason": "Only separately identified complete register paths constrain lv_core; a service or wrapper never does.",
        }
        service["service_timing"] = {
            "duration_class": kind, "blocks_resources": list(service["resources"]),
            "determines_digital_period": False,
            "digital_step_clock_id": "lv_core" if has_digital else None,
            "boundary_alignment": "at explicit next digital consumer only; nested analog/native substages remain physical time",
            "boundary_implementation_status": "pending_case_handshake_and_setup_margin; legacy replay bypasses new alignment",
            "included_native_capture_not_repeated": True,
            "bound_contribution_scope": "dependency slices only; not a complete service latency or new PPA",
            "bound_time_terms": [],
        }
        for bid, binding in bindings.items():
            if sid not in binding["consumers"]:
                continue
            if bid not in _slice_bindings(cid):
                continue
            primitive = next((p for p in case["device"]["primitives"] if p["id"] == bid), None)
            if primitive and primitive["normalized"]["unit"] != "s":
                continue
            service["service_timing"]["bound_time_terms"].append({
                "parameter": bid, "coefficient": _coefficient(cid, service, bid),
                "dependency_type": binding["dependency_type"],
                "timing_kind": "digital_step" if bid == "digital_tick" else "service_duration",
                "constraint_clock_id": None,
            })
        if sid == "sram_write":
            service["service_timing"]["native_cycle_interface"] = {
                "internal_timing_domain": "retained native complete SRAM memory cycle",
                "local_clock_id": "native_sram_memory",
                "local_cycle_parameter": "sram_write_cycle", "conversion_clock_id": None,
                "dispatch": "accepted transaction at an eligible interface edge; included command/data capture charged only inside the native cycle",
                "completion": "native cycle may end between lv_core edges; retain native completion and align once before the next digital acceptance",
                "local_cycle_is_not_lv_core_period": True,
            }
        plan = call.get("timing_plan")
        if plan:
            plan["actual_clock_rule"] = CLOCK_RULE
            plan["closure_status"] = "pending_actual_case_complete_path_and_load"
            plan["combinational_path_rule"] = "Register boundaries determine paths; sum serial components within each actual path, then constrain that domain. Retained analog/native services and transparent wrappers do not enter the sum."
        for output in call.get("outputs", []):
            if not isinstance(output, dict):
                continue
            output.pop("qualification_clock_id", None)
            field = output.get("field", "")
            if field.startswith(("Adder.", "AdderTree.")):
                output["timing_kind"] = "combinational_path_fragment"
                output["constraint_clock_id"] = "lv_core"
                output["constraint_status"] = "candidate_fragment_pending_complete_register_path"
            elif field.startswith("DFF."):
                output["timing_kind"] = "digital_step"
                output["constraint_clock_id"] = None
            else:
                output["timing_kind"] = "service_duration"
                output["constraint_clock_id"] = None
            if output.get("unit") in ("s", "ns"):
                output["clock_id"] = None
    return case


def resolve_binding_contributions(case, overrides=None, context=None):
    """Evaluate actual parameter terms per stage occurrence, without case totals.

    Only the explicitly selected linear dependency slices are evaluated.
    Native max/conditional schedules, periods and electrical parameters do not
    become latency terms. Other native service terms are deliberately omitted.
    RRAM capability comparison is disabled; it is never silently enabled here.
    """
    values = {"input_step": 5, "adc_batch": 20, "digital_tick": 5}
    for primitive in case["device"]["primitives"]:
        if primitive["normalized"]["unit"] == "s":
            values[primitive["id"]] = primitive["normalized"]["value"] * 1e9
    for key, value in (overrides or {}).items():
        if key not in values:
            raise ValueError("unknown time parameter " + key)
        values[key] = _finite_nonnegative(value, key)
    result = {}
    for service in case["services"]:
        contributions = {}
        for term in service["service_timing"]["bound_time_terms"]:
            count = term["coefficient"]
            if isinstance(count, dict):
                page_kind = (context or {}).get("page_kind")
                if page_kind not in count["by_schedule_page_kind"]:
                    # A symbolic context must remain symbolic, never truncated.
                    contributions[term["parameter"]] = {k: n * values[term["parameter"]] for k, n in count["by_schedule_page_kind"].items()}
                    continue
                count = count["by_schedule_page_kind"][page_kind]
            contributions[term["parameter"]] = count * values[term["parameter"]]
        result[service["id"]] = contributions
    return result


def run_checks(cases, policy):
    cases = list(cases.values()) if isinstance(cases, dict) else list(cases)
    by_id = {c["case_id"]: c for c in cases}
    checks, observations = [], {}
    def check(cid, ok, evidence=None):
        checks.append({"id": cid, "status": "PASS" if ok else "FAIL", "evidence": evidence})
    def reject(cid, fn):
        try:
            fn()
        except (ValueError, TypeError):
            check(cid, True)
        else:
            check(cid, False, "invalid input was accepted")
    def path(delay):
        return {"id": "registered_sum", "timing_kind": "combinational_path", "constraint_clock_id": "lv_core", "single_cycle": True, "start_register": "held_code", "end_register": "accumulator", "complete_serial_path": True, "path_status": "synthetic_fixture", "actual_load": {"status": "specified", "kind": "synthetic_fixed_load", "evidence": "Fixed idealized test load folded into independently supplied path delay; no actual case qualification."}, "raw": {"value": delay, "unit": "ns", "clock_id": None}}
    def service(delay, name="analog"):
        return {"id": name, "timing_kind": "service_duration", "constraint_clock_id": None, "raw": {"value": delay, "unit": "ns", "clock_id": None}, "resources": ["analog_front"]}
    digital = {"id": "accumulate", "timing_kind": "digital_step", "raw": {"value": 2, "unit": "cycles", "clock_id": "lv_core"}, "resources": ["accumulator"], "boundary_hold_resources": ["analog_front"], "interface_setup_margin_ns": 0}
    fast = clockpolicy(5, "lv_core", [path(3), service(7)])
    slow = clockpolicy(5, "lv_core", [path(3), service(17)])
    a = serial_events([service(7), digital], {"lv_core": fast})
    b = serial_events([service(17), digital], {"lv_core": slow})
    check("clock_A_independent_analog_never_slows_digital", fast["actual_period_ns"] == slow["actual_period_ns"] == 5, {"analog_ns": [7, 17], "period_ns": [fast["actual_period_ns"], slow["actual_period_ns"]]})
    check("clock_A_only_service_and_boundary_wait_charge", a["completion_ns"] == 20 and b["completion_ns"] == 30 and a["events"][1]["boundary_wait_ns"] == b["events"][1]["boundary_wait_ns"] == 3 and b["resource_occupancy_ns"]["accumulator"] == 10, {"before": a, "after": b})
    edge_before = serial_events([service(8), digital], {"lv_core": fast})
    edge_after = serial_events([service(14), digital], {"lv_core": fast})
    check("clock_A_service_delta_and_boundary_wait_delta_separate", edge_before["completion_ns"] == 20 and edge_after["completion_ns"] == 25 and edge_before["events"][1]["boundary_wait_ns"] == 2 and edge_after["events"][1]["boundary_wait_ns"] == 1 and edge_after["completion_ns"] - edge_before["completion_ns"] == (14 - 8) + (1 - 2) and edge_before["resource_occupancy_ns"]["accumulator"] == edge_after["resource_occupancy_ns"]["accumulator"] == 10, {"before": edge_before, "after": edge_after, "digital_period_ns": fast["actual_period_ns"]})
    slow_path = clockpolicy(5, "lv_core", [path(7), service(7)])
    c = serial_events([service(7), digital], {"lv_core": slow_path})
    check("clock_B_actual_register_path_constrains_domain", slow_path["actual_period_ns"] == 7 and c["completion_ns"] == 21 and c["resource_occupancy_ns"]["accumulator"] == 14, c)
    wrapped_paths = [{"id": "pack", "children": [path(3), {"id": "pack2", "children": [service(17)]}]}]
    wrapped_events = [{"id": "service_pack", "children": [service(17), digital]}]
    check("clock_C_transparent_packaging_preserves_ownership", clockpolicy(5, "lv_core", wrapped_paths) == slow and serial_events(wrapped_events, {"lv_core": slow}) == b)
    split = serial_events([{"id": "opaque_package", "children": [service(2, "subA"), service(2, "subB")]}, digital], {"lv_core": 5})
    check("boundary_round_only_actual_digital_consumer", split["completion_ns"] == 15 and split["events"][1]["completion_ns"] == 4 and sum(e["boundary_wait_ns"] for e in split["events"]) == 1 and split["events"][2]["service_duration_ns"] == 10 and split["completion_ns"] != 20, {"actual": split, "incorrect_per_internal_stage_ceiling_completion_ns": 20})
    local = serial_events([service(5, "native_sram_cycle"), digital], {"lv_core": 7})
    check("native_sram_local_cycle_distinct_from_public_clock", local["events"][0]["service_duration_ns"] == 5 and local["events"][1]["boundary_wait_ns"] == 2 and local["completion_ns"] == 21)
    check("seconds_ns_cycles_each_convert_once", normalize_time({"value": 2e-9, "unit": "s"}, {})["normalized_ns"] == normalize_time({"value": 2, "unit": "ns"}, {})["normalized_ns"] == 2 and normalize_time({"value": 2, "unit": "cycles", "clock_id": "lv_core"}, {"lv_core": 5})["normalized_ns"] == 10)
    reject("reject_missing_cycle_clock", lambda: normalize_time({"value": 2, "unit": "cycles"}, {}))
    reject("reject_seconds_carrying_conversion_clock", lambda: normalize_time({"value": 2e-9, "unit": "s", "clock_id": "lv_core"}, {"lv_core": 5}))
    reject("reject_double_normalization", lambda: normalize_time(normalize_time({"value": 1, "unit": "ns"}, {}), {}))
    reject("reject_service_as_clock_constraint", lambda: clockpolicy(5, "lv_core", [dict(service(100), constraint_clock_id="lv_core")]))
    reject("reject_path_without_register_boundaries", lambda: clockpolicy(5, "lv_core", [dict(path(7), start_register=None)]))
    reject("reject_fragment_as_complete_path", lambda: clockpolicy(5, "lv_core", [dict(path(7), complete_serial_path=False)]))
    reject("reject_path_without_actual_load", lambda: clockpolicy(5, "lv_core", [dict(path(7), actual_load=None)]))
    reject("reject_pending_case_path", lambda: clockpolicy(5, "lv_core", [dict(path(7), path_status="pending_actual_case_load")]))
    reject("reject_wrapper_clock_override", lambda: clockpolicy(5, "lv_core", [{"children": [path(3)], "constraint_clock_id": "lv_core"}]))
    reject("reject_nan_duration", lambda: normalize_time({"value": float("nan"), "unit": "ns"}, {}))
    rram = by_id["05_rram"]
    rb = resolve_binding_contributions(rram)
    r9 = resolve_binding_contributions(rram, {"adc_batch": 9})
    r11 = resolve_binding_contributions(rram, {"adc_batch": 11})
    check("RRAM_SAR_8_to_10_bit_does_not_change_window", r9["endpoint_verify"] == r11["endpoint_verify"] == rb["endpoint_verify"] and r9["sar"]["adc_batch"] == 9 and r11["sar"]["adc_batch"] == 11, {"sar_8bit_ns": 9, "sar_10bit_ns": 11, "window_components_ns": rb["endpoint_verify"]})
    changed = resolve_binding_contributions(rram, {"binary_verify_sense_ns": 27})
    affected = {sid for sid in rb if rb[sid] != changed[sid]}
    check("RRAM_window_parameter_only_actual_consumer", affected == {"endpoint_verify"} and changed["endpoint_verify"]["binary_verify_sense_ns"] - rb["endpoint_verify"]["binary_verify_sense_ns"] == 7, sorted(affected))
    check("RRAM_named_equality_policy_disabled", not next(s for s in rram["services"] if s["id"] == "endpoint_verify")["call"]["policy_link"]["enabled"])
    check("RRAM_window_no_SAR_or_digital_Comparator", next(s for s in rram["services"] if s["id"] == "endpoint_verify")["call"]["components"] == [] and next(b for b in rram["parameter_bindings"] if b["id"] == "adc_batch")["consumers"] == ["sar"])
    shared_tests = [
        ("04_nand_3d", "adc_batch", {"sar": 1, "load_calibration": 12}),
        ("04_nand_3d", "wl_setup", {"native_wl": 1, "load_calibration": 2}),
        ("04_nand_3d", "bl_setup", {"native_bl_sl": 1, "load_calibration": 12}),
        ("04_nand_3d", "sl_setup", {"native_bl_sl": 1, "load_calibration": 12}),
        ("07_pcm", "adc_batch", {"sar": 1, "endpoint_verify": 1}),
        ("07_pcm", "shared_voltage_front", {"analog_front": 1, "endpoint_verify": 1}),
        ("09_gain_cell_edram", "adc_batch", {"sar": 1, "refresh_read": 1}),
        ("09_gain_cell_edram", "common_read_overhead", {"analog_front": 1, "refresh_read": 1}),
        ("09_gain_cell_edram", "program_complete", {"current_program": 1, "refresh_decode_load_rewrite": 1}),
    ]
    for cid, param, expected in shared_tests:
        case = by_id[cid]
        before = resolve_binding_contributions(case)
        first_sid, coef = next(iter(expected.items()))
        basevalue = before[first_sid][param] / coef
        after = resolve_binding_contributions(case, {param: basevalue + 3})
        impacted = {sid for sid in before if before[sid] != after[sid]}
        delta = {sid: after[sid][param] - before[sid][param] for sid in impacted}
        check("shared_" + cid + "_" + param, impacted == set(expected) and all(math.isclose(delta[sid], 3 * n, abs_tol=1e-8) for sid, n in expected.items()), {"delta_ns_per_occurrence": delta})
    # Independent oracle: the stated native digital schedule coefficients, not
    # values obtained by calling the binding resolver under test.
    digital_expected = {
        "01_sram_acim": {"input_capture":1,"reconstruct":1,"output_commit":1},
        "02_sram_dcim": {"input_capture":1,"output_commit":1},
        "03_nor_2d": {"input_capture":1,"operand_capture":1,"digital_mac":1,"page_load":18,"sector_erase":2,"output_commit":1},
        "04_nand_3d": {"input_capture":1,"input_magnitude_sign":1,"affine_merge_sign":1,"resident_encode":1,"page_load":290,"load_calibration":450,"output_commit":1},
        "05_rram": {"input_capture":1,"digital_reconstruct":1,"program_attempts":1,"output_commit":1,"resident_front":2,"attempt_done":1},
        "06_mram": {"input_capture":1,"operand_capture":1,"digital_mac":1,"encoded_load":2,"terminal_verify":2,"output_commit":1,"polarity_turn":1},
        "07_pcm": {"input_capture":1,"digital_reconstruct":1,"resident_front":3,"program_reset_set":1,"endpoint_verify":1,"output_commit":1},
        "08_feram_hfo2": {"input_capture":1,"digital_mac":1,"external_load":2,"output_commit":1},
        "09_gain_cell_edram": {"input_capture":1,"digital_reconstruct":1,"resident_load":3,"refresh_decode_load_rewrite":4,"output_commit":1},
        "10_fenor_3d": {"input_capture":1,"operand_capture":1,"digital_mac":1,"resident_load":2,"terminal_verify":9,"output_commit":1},
    }
    for cid, expected in digital_expected.items():
        case = by_id[cid]
        before = resolve_binding_contributions(case, context={"page_kind": "data"})
        after = resolve_binding_contributions(case, {"digital_tick":7}, context={"page_kind": "data"})
        impacted = {sid for sid in before if before[sid] != after[sid]}
        delta = {sid: after[sid]["digital_tick"] - before[sid]["digital_tick"] for sid in impacted}
        check("digital_domain_all_real_steps_" + cid, impacted == set(expected) and all(delta[sid] == 2 * count for sid, count in expected.items()), {"per_occurrence_delta_ns": delta})
    check("policy_target_and_service_boundary", policy["clock"]["target_period_ns"] == 5 and "independent" in policy["clock"]["actual_rule"] and "service_boundary_rule" in policy["clock"])
    check("all_services_explicit_clock_ownership", all(s["clock_role"]["constraint_clock_id"] is None and s["service_timing"]["determines_digital_period"] is False for c in cases for s in c["services"]))
    check("all_bindings_typed_dependencies", all(b.get("dependency_type") in policy_fragment()["dependency_types"] for c in cases for b in c["parameter_bindings"]))
    observations["scope"] = "Synthetic policy tests + executable dependency slices; no ten-case new latency/PPA computation. Separate original-time replay applies no new alignment."
    observations["upstream_main"] = "Keep existing read_timing slow-target witness unchanged; not a constraint on the composed primitive-service clock."
    observations["RRAM"] = "20ns retained reference native window budget; SAR conversion and binary window slot are independent by default."
    return {"status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL", "checks": checks, "observations": observations}


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = [json.loads(p.read_text()) for p in sorted(args.cases.glob("*.json"))]
    policy = json.loads(args.policy.read_text())
    summary = run_checks(cases, policy)
    args.out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": summary["status"], "checks": len(summary["checks"])}))
    sys.exit(0 if summary["status"] == "PASS" else 1)

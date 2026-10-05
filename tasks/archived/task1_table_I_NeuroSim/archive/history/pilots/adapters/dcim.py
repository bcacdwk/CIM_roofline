"""D6CIM adapter: one native 128 x 16 INT8 tile, no ADC.

The public driver owns model execution and timing; this module expands the
frozen input specification into resource-serial events.  It never reads a saved
performance result or imports the original calculator.
"""
import math


NATIVE = "v3_native_complete_service"
DIGITAL = "neurosim_DFF_and_qualified_public_control"


def _require(condition, description):
    if not condition:
        raise ValueError("D6CIM: " + description)


def _signed_weight(raw):
    """Reconstruct the eight binary storage cells, including the sign plane."""
    return sum(((raw >> b) & 1) * (-(1 << b) if b == 7 else 1 << b)
               for b in range(8))


def nominal_checks():
    """Check the native 16-term / 8-input-bit expansion against integer VMM.

    This is a semantic check of encoding, count and container width; it does
    not claim transistor-level simulation of the retained HCA/BFA service.
    """
    patterns = [
        ("zero", [0] * 128,
         [[((n * 31 + k * 13) % 256) - 128 for k in range(128)]
          for n in range(16)]),
        ("signed_extremes_positive", [-128] * 128, [[-128] * 128 for _ in range(16)]),
        ("signed_extremes_negative", [-128] * 128, [[127] * 128 for _ in range(16)]),
        ("mixed", [((k * 37 + 19) % 256) - 128 for k in range(128)],
         [[((n * 29 + k * 53 + 7) % 256) - 128 for k in range(128)]
          for n in range(16)]),
    ]
    samples = []
    for name, x, w in patterns:
        encoded = [[v & 255 for v in row] for row in w]
        decoded = [[_signed_weight(v) for v in row] for row in encoded]
        actual = [0] * 16
        rounds = 0
        max_intermediate_abs = 0
        # Native static row connection remains selected for all eight bits.
        for group in range(8):
            for bit in range(8):
                coefficient = -(1 << bit) if bit == 7 else 1 << bit
                for lane in range(16):
                    partial = sum(((x[k] & 255) >> bit & 1) * decoded[lane][k]
                                  for k in range(group * 16, (group + 1) * 16))
                    actual[lane] += coefficient * partial
                    max_intermediate_abs = max(max_intermediate_abs, abs(actual[lane]))
                    _require(-(1 << 22) <= actual[lane] < (1 << 22),
                             "23-bit signed accumulator overflow")
                rounds += 1
        expected = [sum(a * b for a, b in zip(x, row)) for row in w]
        _require(decoded == w and actual == expected and rounds == 64,
                 "nominal two's-complement expansion or round count mismatch")
        samples.append({"name": name, "rounds": rounds, "outputs": actual,
                        "max_intermediate_abs": max_intermediate_abs,
                        "matches_integer_vmm": actual == expected})
    return samples


def build(case, p, backend):
    """Return streaming/resident events plus resolved organization and checks.

    Physical native MAC rounds are autonomous after vector admission.  The
    external 128-bit update port, in contrast, accepts the next transaction
    only at an eligible public-clock edge.  A boundary event has no capture
    cycle: that capture and its setup are already inside the native service.
    """
    logical = case["logical"]
    installed = case["resources"]["installed"]
    native = case["resources"]["native_declared"]
    writes = case["resources"]["write_semantics"]
    _require(case["case_id"] == "02_sram_dcim", "incorrect case identity")
    _require((logical["K"], logical["N"]) == (128, 16), "native dimensions changed")
    _require((logical["input_bits"], logical["weight_bits"], logical["output_bits"])
             == (8, 8, 23) and logical["signed"], "arithmetic contract changed")
    _require(logical["B_S_Byte"] == 128 and logical["B_R_Byte"] == 2048,
             "logical payload mismatch")
    _require(installed["input_register_bits"] == 1024
             and installed["output_register_bits"] == 368
             and installed["operand_hold_bits"] == 0,
             "declared register resources changed")
    _require(installed["adc_count"] == 0 and backend.get("sar_ns") is None,
             "an ADC cannot appear in D6CIM")
    _require(native["installed_HCA_BFA"] == native["active_HCA_BFA"] == 16
             and native["digital_terms_per_round"] == 16,
             "native HCA/BFA organization changed")
    _require(writes["full_matrix_transactions"]["value"] == 128
             and writes["logical_payload_per_transaction"]["value"] == 16
             and writes["data_port_width"]["value"] == 128
             and writes["program_driver_channels"]["value"] == 128
             and writes["update_domains"]["value"] == 1,
             "one-beat native write organization changed")
    for name in ("native_mac_cycle", "sram_write_cycle"):
        _require(math.isfinite(p[name]) and p[name] > 0, "invalid " + name)
    _require(math.isfinite(backend["actual_period_ns"])
             and backend["actual_period_ns"] > 0 and backend["dff_cycle"] == 1,
             "invalid executed public clock / DFF result")

    streaming = [{"id": "input_capture", "kind": "digital", "cycles": 1,
                  "provider": DIGITAL, "resources": ["input_register_bits"],
                  "context": {"bits": 1024, "held_until": {"stage_id": "native_mac", "round": 63},
                              "includes": "whole-vector capture and schedule admission"}}]
    for group in range(8):
        for bit in range(8):
            round_number = group * 8 + bit
            streaming.append({
                "id": "native_mac", "kind": "physical", "ns": p["native_mac_cycle"],
                "provider": NATIVE,
                "resources": ["input_register_bits", "native_HCA_BFA_16",
                              "native_static_weight_connection", "native_accumulators"],
                "context": {"round": round_number, "row_group": group,
                            "input_bit": bit, "terms": 16, "output_lanes": 16,
                            "sign_coefficient": -128 if bit == 7 else 1 << bit,
                            "local_clock_id": "native_d6cim_mac",
                            "public_consumer_between_native_rounds": False,
                            "includes": "static SRAM/NOR read, HCA reduction, BFA sign/shift/accumulation"}})
    streaming.append({"id": "output_commit", "kind": "digital", "cycles": 1,
                      "provider": DIGITAL, "resources": ["output_register_bits"],
                      "context": {"bits": 368, "lanes": 16,
                                  "consumer": "declared 16 x 23-bit output register bank",
                                  "native_result_held_until_commit": True}})

    resident = []
    for transaction in range(128):
        resident.append({
            "id": "sram_write_accept", "kind": "boundary", "margin_ns": 0,
            "provider": "public_clock_boundary_included_native_capture",
            "resources": ["encoded_interface_bits", "external_update_domains"],
            "context": {"transaction": transaction, "consumer": "128-bit native write port",
                        "included_capture": True, "setup_owner": "complete native memory cycle",
                        "no_additional_capture_or_handshake_tick": True}})
        resident.append({
            "id": "sram_write", "kind": "physical", "ns": p["sram_write_cycle"],
            "provider": NATIVE,
            "resources": ["encoded_interface_bits", "write_semantics.program_driver_channels",
                          "external_update_domains"],
            "context": {"transaction": transaction, "logical_payload_Byte": 16,
                        "physical_bits": 128, "local_clock_id": "native_sram_memory",
                        "includes": "command/address/data capture, decode, BL/WL drive, cell flip, recovery"}})
    resident.append({
        "id": "matrix_ready", "kind": "boundary", "margin_ns": 0,
        "provider": "public_clock_boundary_included_native_capture",
        "resources": ["external_update_domains"],
        "context": {"consumer": "next eligible public compute/update admission",
                    "setup_owner": "complete native memory cycle",
                    "publication_tick": "included in complete native memory endpoint"}})

    samples = nominal_checks()
    streaming[0].setdefault("context", {}).update({
        "accumulator_initialization": "synchronous clear all existing output containers during input_capture; clear mux/control path included in backend",
        "new_register_or_cycle": False})
    return {
        "streaming": streaming, "resident": resident,
        "snapshot": {
            "adapter": "native_D6CIM_128x16_INT8", "adc": None,
            "native_mac_cycle_ns": p["native_mac_cycle"],
            "native_write_cycle_ns": p["sram_write_cycle"],
            "actual_public_period_ns": backend["actual_period_ns"],
            "native_complete_MAC_rounds": 64, "static_row_group_activations": 8,
            "input_bit_rounds_per_group": 8, "terms_per_round": 16, "output_lanes": 16,
            "resident_transactions": 128, "resident_transaction_payload_Byte": 16,
            "resident_transaction_native_latency_ns": p["sram_write_cycle"],
            "register_resources": {"input_bits": 1024, "output_bits": 368,
                                   "additional_operand_hold_bits": 0},
            "native_MAC_train_boundary": "one vector admission; 64 autonomous complete local rounds; one public output consumer",
            "write_port_boundary_assumption": "128-bit external port accepts only on lv_core edges; one included native capture per transaction; no extra input bank or overlap",
            "native_boundary_setup_margin_ns": 0,
            "setup_ownership": "native write setup/recovery are included; public output setup/clock-to-Q are owned by the qualified digital cycle",
            "arithmetic_scope": "nominal bit-serial two's-complement check; native HCA/BFA transistor timing remains the sourced complete-cycle budget",
            "nominal_arithmetic_samples": samples,
            "source_refs": [
                {"source_id": "inputs", "json_pointer": "/raw_evidence/" + str(i)}
                for i in (0, 1, 2, 3, 4, 6, 8, 9)
            ] + [{"source_id": "inputs", "json_pointer": "/cycle_semantics"},
                 {"source_id": "inputs", "json_pointer": "/dcim_overrides"},
                 {"source_id": "case", "json_pointer": "/device/primitives"},
                 {"source_id": "case", "json_pointer": "/service_schedules"}],
        },
        "checks": {
            "native_64_MAC_rounds": len([e for e in streaming if e["id"] == "native_mac"]) == 64,
            "all_input_bit_terms_covered": 64 * 16 * 16 == 8 * 128 * 16,
            "full_matrix_128_transactions": len([e for e in resident if e["id"] == "sram_write"]) == 128,
            "logical_payload_not_encoded_occupancy": 128 * 16 == logical["B_R_Byte"],
            "native_read_sign_accumulate_not_added": {e["id"] for e in streaming} == {"input_capture", "native_mac", "output_commit"},
            "native_write_capture_not_added": not any(e["kind"] == "digital" for e in resident),
            "no_ADC": installed["adc_count"] == 0 and backend.get("sar_ns") is None,
            "signed_INT8_nominal_matches": all(s["matches_integer_vmm"] for s in samples),
            "positive_extreme_requires_23_bits": samples[1]["outputs"][0] == (1 << 21),
            "no_added_operand_bank": installed["operand_hold_bits"] == 0,
        },
    }

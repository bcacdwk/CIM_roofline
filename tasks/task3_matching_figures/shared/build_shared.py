#!/usr/bin/env python3
"""Adapt accepted read-only sources; emit only files beside this script."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from style import CASE_ORDER, COLORS, LABELS, MARKERS, U_VALUES

PATHS = {
    "hardware_central": "tasks/task1_table_I_NVM/analysis/data/ten_case_results.json",
    "hardware_table": "tasks/task1_table_I_NVM/analysis/11_summary_figures/data/table_scenarios.json",
    "hardware_plot": "tasks/task1_table_I_NVM/analysis/11_summary_figures/data/rho_tau_loglog_circles_points.csv",
    "hardware_method": "tasks/task1_table_I_NVM/analysis/shared_baseline/README.md",
    "table_IIa": "tasks/task2_table_II_workloads/table_IIa/data/results.json",
    "table_IIa_config": "tasks/task2_table_II_workloads/table_IIa/data/config.json",
    "workload_conventions": "tasks/task2_table_II_workloads/table_IIb/04_crosscheck/data/conventions.json",
    "workload_models": "tasks/task2_table_II_workloads/table_IIb/04_crosscheck/data/model_inputs.json",
    "workload_results": "tasks/task2_table_II_workloads/table_IIb/04_crosscheck/data/results.json",
}


def read(name):
    return json.loads((ROOT / PATHS[name]).read_text())


def close(a, b):
    assert math.isclose(a, b, rel_tol=2e-12, abs_tol=1e-12), (a, b)


def fraction_value(obj):
    return obj["numerator"] / obj["denominator"] if isinstance(obj, dict) else obj


def resolve_pointer(ref):
    relative, pointer = ref.split("#", 1)
    path = ROOT / "tasks/task1_table_I_NVM/analysis" / relative
    value = json.loads(path.read_text())
    for token in pointer.strip("/").split("/"):
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def write_json(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_csv(name, rows, fields):
    with (HERE / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    central, table = read("hardware_central"), read("hardware_table")
    central_rows = {(r["case_id"], r["scenario_profile"]): r for r in central["results"]
                    if r["scenario_profile"] in ("short", "reference", "long")
                    and r["workload_mapping_eligibility"]
                    and r["scenario_type"] in ("paired_conditional", "recommended_reference")}
    assert len(table) == 30
    hardware = []
    for t in table:
        c = central_rows[t["case_id"], t["profile"]]
        native = resolve_pointer(t["source_mapping"])
        for key, central_key in (("rho_MB_per_s", "rho"), ("tau_MB_per_s", "tau"),
                                 ("RI_star", "RI_star"), ("U_star", "U_star"),
                                 ("T_R_ns", "T_R_ns"), ("delta_S_ns", "delta_S_ns")):
            close(t[key], c[central_key])
        for key in ("K", "N", "T_R_ns", "delta_S_ns", "U_star", "RI_star"):
            close(t[key], native[key])
        assert c["b_S"] == c["b_R"] == 1
        assert t["workload_mapping_eligibility"] is True
        assert t["B_S_Byte"] == t["K"]
        assert t["B_R_Byte"] == t["K"] * t["N"]
        close(t["rho_MB_per_s"], 1e3 * t["K"] / t["delta_S_ns"])
        close(t["tau_MB_per_s"], 1e3 * t["K"] * t["N"] / t["T_R_ns"])
        close(t["RI_star"], t["rho_MB_per_s"] / t["tau_MB_per_s"])
        close(t["U_star"], t["N"] * t["RI_star"])
        close(t["U_star"], t["T_R_ns"] / t["delta_S_ns"])
        h = dict(t)
        h.update(label=LABELS[t["case_id"]], color=COLORS[t["case_id"]],
                 marker=MARKERS[t["case_id"]], b_S=1, b_R=1,
                 sigma_MB_per_s=t["N"] * t["rho_MB_per_s"],
                 central_source=PATHS["hardware_central"],
                 central_scenario_id=c["scenario_id"],
                 native_configuration=c["native_configuration"],
                 full_load_equivalent_per_s=1e9 / t["T_R_ns"],
                 full_vector_per_s=1e9 / t["delta_S_ns"])
        close(h["sigma_MB_per_s"] / h["tau_MB_per_s"], h["U_star"])
        hardware.append(h)
    assert {h["case_id"] for h in hardware} == set(CASE_ORDER)

    iia = read("table_IIa")
    selected = []
    all_iia = []
    for i, c in enumerate(iia["cases"]):
        if c["kind"] != "finite":
            continue
        r = c["result"]
        assert r["Q_S"] == c["U"] * c["K"]
        assert r["Q_R"] == c["N"] * c["K"]
        close(fraction_value(r["RI"]), c["U"] / c["N"])
        row = {"case_id": c["case_id"], "workload": "single_matrix_GEMM", "U": c["U"],
               "N": c["N"], "K": c["K"], "Q_S_Byte": r["Q_S"], "Q_R_Byte": r["Q_R"],
               "RI_exact": r["RI"], "RI": fraction_value(r["RI"]),
               "source": PATHS["table_IIa"] + f"#/cases/{i}",
               "label": f"GEMM W[{c['N']},{c['K']}], U={c['U']}",
               "mapping_scope": "exact for same native K,N; otherwise transferable U reference only"}
        all_iia.append(row)
        if c["N"] == c["K"] == 128 and c["U"] in U_VALUES:
            selected.append(row)
    assert [c["U"] for c in selected] == list(U_VALUES)

    # Keep the accepted projection family available for demand-only comparison.
    # Its model dimensions are never used to rename native service coordinates.
    projection = []
    workload = read("workload_results")
    models = {m["model_id"]: m for m in read("workload_models")["models"]}
    for i, c in enumerate(workload["cases"]):
        if c["workload"] != "qkv_projection" or c["kind"] != "finite":
            continue
        p, r = c["parameters"], c["result"]
        assert r["Q_R"] == p["D"] * p["N_proj"]
        assert r["Q_S"] == c["U"] * p["D"]
        close(fraction_value(r["RI"]), c["U"] / p["N_proj"])
        projection.append({"case_id": c["case_id"], "model_id": c["model_id"],
                           "model_label": models[c["model_id"]]["display_name"],
                           "workload": c["workload"], "U": c["U"],
                           "N": p["N_proj"], "K": p["D"],
                           "Q_S_Byte": r["Q_S"], "Q_R_Byte": r["Q_R"],
                           "RI_exact": r["RI"], "RI": fraction_value(r["RI"]),
                           "shared_input_bytes_removed": r["shared_input_bytes_removed"],
                           "source": PATHS["workload_results"] + f"#/cases/{i}",
                           "mapping_scope": "operator-stage demand only; no native hardware mapping"})

    mapping_models = ("qwen35_2b", "mimo_v25_pro")
    mapping_hardware = [r for r in hardware if r["K"] == r["N"] == 128]
    tile_mappings = []
    mapped_workloads = []
    for model_id in mapping_models:
        cases = [r for r in projection if r["model_id"] == model_id]
        N_proj, D = cases[0]["N"], cases[0]["K"]
        assert N_proj % 128 == D % 128 == 0
        m_N, m_K = N_proj // 128, D // 128
        scenarios = []
        for h in mapping_hardware:
            effective_rho = h["rho_MB_per_s"] / m_N
            effective_ridge = effective_rho / h["tau_MB_per_s"]
            close(effective_ridge, h["U_star"] / N_proj)
            scenarios.append({"case_id": h["case_id"], "profile": h["profile"],
                              "rho_effective_MB_per_s": effective_rho,
                              "tau_effective_MB_per_s": h["tau_MB_per_s"],
                              "RI_star_effective": effective_ridge,
                              "U_star": h["U_star"],
                              "T_R_all_tiles_ns": m_N * m_K * h["T_R_ns"],
                              "streaming_ns_per_model_vector": m_N * m_K * h["delta_S_ns"],
                              "hardware_source": h["source_mapping"]})
        tile_mappings.append({"model_id": model_id, "model_label": cases[0]["model_label"],
                              "D": D, "N_proj": N_proj, "native_K": 128, "native_N": 128,
                              "m_K": m_K, "m_N": m_N, "tile_count": m_K * m_N,
                              "padding_elements": 0, "model_Q_R_Byte": D * N_proj,
                              "schedule": "one 128x128 native engine; each tile loaded once and serves all U vectors before next tile",
                              "scenarios": scenarios})
        for c in cases:
            r = dict(c)
            r.update(mapping_id=f"{model_id}/native128_sequential_tiles",
                     m_K=m_K, m_N=m_N, tile_count=m_K*m_N,
                     native_accumulated_Q_S_Byte=m_N*c["Q_S_Byte"],
                     native_accumulated_Q_R_Byte=c["Q_R_Byte"],
                     mapping_scope="explicit sequential 128x128-tile component-service bound")
            assert r["native_accumulated_Q_S_Byte"] == m_K*m_N*c["U"]*128
            assert r["native_accumulated_Q_R_Byte"] == m_K*m_N*128*128
            for h in mapping_hardware:
                # Derive service time independently from the unique-demand/effective-rate view.
                t_s_native = m_K*m_N*c["U"]*h["delta_S_ns"]
                t_r_native = m_K*m_N*h["T_R_ns"]
                close(t_s_native, 1e3*c["Q_S_Byte"]/(h["rho_MB_per_s"]/m_N))
                close(t_r_native, 1e3*c["Q_R_Byte"]/h["tau_MB_per_s"])
                close(t_r_native/t_s_native, h["U_star"]/c["U"])
            mapped_workloads.append(r)

    sources = [{"id": key, "path": rel,
                "sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()}
               for key, rel in PATHS.items()]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    data = {
        "schema_version": "task3-service-interface-1",
        "checkpoint_requested": "100c233a2dbdb74ca3894aa96ee39c358e9ebe41",
        "actual_head": head,
        "units": {"payload": "Byte", "rho_tau_sigma": "decimal MB/s = 10^6 Byte/s",
                  "service_time": "ns", "U": "input vectors per complete weight load, including first use",
                  "quantity_suffixes": {"1K": 1024, "1M": 1048576}},
        "boundary": "Each hardware record retains its full native matrix and complete vector service. A/C/D/E compare a required reuse count against that native service; only equal-shape cases establish direct Table II(a) demand matching.",
        "formulas": {"sigma": "N*rho (INT8 equal width); full-matrix-equivalent streaming capacity",
                     "U_star": "sigma/tau = N*RI_star = T_R/delta_S",
                     "balance_capability": "sigma = U*tau; above resident-bound, below streaming-bound",
                     "balance_demand_same_shape": "Q_S = RI_star*Q_R; above streaming-bound, below resident-bound",
                     "normalized_bound": "min(1,U/U_star)",
                     "input_rate_bound": "min(rho,(U/N)*tau) [MB/s]",
                     "analytic_improvement": "min(a*rho,b*(U/N)*tau); a,b multiply streaming,resident capacities"},
        "reference_scope": "Two-route resource ceiling; not achieved throughput, single-job latency, or model/device deployment feasibility. Resource overlap is not guaranteed.",
        "exclusions": ["FFN multi-stage aggregate", "attention KV append or prefill incremental writes",
                       "arbitrary points sampled from scenario circles", "infinity assigned a finite log coordinate"],
        "hardware": hardware,
        "selected_workloads": selected,
        "table_IIa_finite": all_iia,
        "projection_demand_only": projection,
        "qkv_tile_mappings": tile_mappings,
        "qkv_mapped_workloads": mapped_workloads,
        "same_shape_hardware_128": [h["case_id"] for h in hardware
                                    if h["profile"] == "reference" and h["N"] == h["K"] == 128],
        "sources": sources,
    }
    write_json("data.json", data)
    write_csv("hardware.csv", hardware, ["case_id", "label", "profile", "K", "N", "rho_MB_per_s", "tau_MB_per_s",
                                          "sigma_MB_per_s", "RI_star", "U_star", "B_S_Byte", "B_R_Byte",
                                          "delta_S_ns", "T_R_ns", "source_mapping", "source_result"])
    write_csv("selected_workloads.csv", selected, ["case_id", "workload", "U", "K", "N", "Q_S_Byte", "Q_R_Byte", "RI", "source", "mapping_scope"])
    write_json("source_index.json", {"actual_head": head, "sources": sources})
    # This is a compact cross-figure check set, not a device x workload classification table.
    checks = []
    for case, U in (("06_mram", 128), ("05_rram", 1024), ("03_nor_2d", 131072)):
        h = next(r for r in hardware if r["case_id"] == case and r["profile"] == "reference")
        checks.append({"case_id": case, "profile": "reference", "U": U, "U_star": h["U_star"],
                       "U_over_U_star": U / h["U_star"],
                       "normalized_bound": min(1, U / h["U_star"]),
                       "bottleneck": "resident-bound" if U < h["U_star"] else "streaming-bound"})
    write_json("validation.json", {"status": "PASS", "hardware_rows_checked": len(hardware),
                                   "table_IIa_finite_checked": len(all_iia), "qkv_finite_checked": len(projection),
                                   "source_paths_and_native_pointers_checked": True,
                                   "qkv_mapping_models": len(tile_mappings),
                                   "qkv_mapping_cases": len(mapped_workloads),
                                   "qkv_mapping_hardware_scenarios": len(mapping_hardware),
                                   "qkv_native_and_effective_route_times_agree": True,
                                   "identities": ["rho=1000*K/delta_S", "tau=1000*K*N/T_R", "U*=N*rho/tau=T_R/delta_S"],
                                   "cross_figure_spot_checks": checks})
    print(f"PASS: 30 paired hardware records, {len(selected)} selected reuse states, {len(all_iia)} II(a) and {len(projection)} QKV demand records; HEAD={head}")


if __name__ == "__main__":
    main()

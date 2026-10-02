#!/usr/bin/env python3
"""Independent native-row/prefix count plus archived operator regression."""
import argparse
import csv
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[1]
TASK = HERE.parents[1]
COMMON = HERE.parent / "04_crosscheck"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def value(x):
    if isinstance(x, dict):
        assert set(x) == {"numerator", "denominator"}
        assert isinstance(x["numerator"], int) and isinstance(x["denominator"], int)
        assert x["denominator"] > 1
        result = Fraction(x["numerator"], x["denominator"])
        assert result.numerator == x["numerator"] and result.denominator == x["denominator"]
        return result
    assert type(x) is int
    return Fraction(x)


def exact(x):
    x = Fraction(x)
    return x.numerator if x.denominator == 1 else {"numerator": x.numerator, "denominator": x.denominator}


def native_dimensions(model):
    raw = read(TASK / model["local_material"]["raw_config"])
    raw = raw.get("text_config", raw)
    layer = model["selected_layer"]
    assert 0 <= layer < raw["num_hidden_layers"]
    if "layer_types" in raw:
        assert raw["layer_types"][layer] == "full_attention"
    if "hybrid_layer_pattern" in raw:
        assert raw["hybrid_layer_pattern"][layer] == 0
        assert raw["add_full_attention_sink_bias"] is False
        assert str(raw["attention_value_scale"]) == "0.612"
    assert raw.get("sliding_window") is None or model["model_id"] == "mimo_v25_pro"
    hq = raw["num_attention_heads"]
    hkv = raw["num_key_value_heads"]
    dq = raw["head_dim"]
    dv = raw.get("v_head_dim") or dq
    assert hq % hkv == 0
    return {"H_q": hq, "H_kv": hkv, "d_QK": dq, "d_V": dv, "g": hq // hkv}


def prefix_count(p, length, prefill):
    """Count native row widths and causal prefix lengths, without a closed triangular formula.

    Each entry width comes from a native vector. Sum per valid query position and
    per appended KV row. This creates neither a square matrix nor element events.
    """
    query_width = sum(len(range(p["d_QK"])) for _ in range(p["H_q"]))
    key_row_width = sum(len(range(p["d_QK"])) for _ in range(p["H_kv"]))
    value_row_width = sum(len(range(p["d_V"])) for _ in range(p["H_kv"]))
    query_positions = range(1, length + 1) if prefill else range(length, length + 1)
    qk_s = av_s = key_write = value_write = 0
    for position in query_positions:
        qk_s += query_width
        av_s += len(range(1, position + 1)) * len(range(p["H_q"]))
        key_write += key_row_width
        value_write += value_row_width
    initial_positions = range(0) if prefill else range(length - 1)
    initial_key = sum(key_row_width for _ in initial_positions)
    initial_value = sum(value_row_width for _ in initial_positions)
    final_key = sum(key_row_width for _ in range(length))
    final_value = sum(value_row_width for _ in range(length))
    return {
        "QK": {"Q_S": qk_s, "Q_R": key_write, "RI": exact(Fraction(qk_s, key_write)),
               "resident_bytes_initial": initial_key, "resident_bytes_final": final_key},
        "AV": {"Q_S": av_s, "Q_R": value_write, "RI": exact(Fraction(av_s, value_write)),
               "resident_bytes_initial": initial_value, "resident_bytes_final": final_value},
    }


def explicit_identities(p, length, prefill):
    """Small fixtures only: actual semantic identities for inputs and state elements."""
    positions = range(1, length + 1) if prefill else [length]
    query_ids = {(h, t, d) for h in range(p["H_q"]) for t in positions for d in range(p["d_QK"])}
    coefficient_ids = {(h, t, j) for h in range(p["H_q"]) for t in positions for j in range(1, t + 1)}
    parts = {}
    for name, width, input_ids in [("QK", p["d_QK"], query_ids), ("AV", p["d_V"], coefficient_ids)]:
        new = {(h, t, d) for h in range(p["H_kv"]) for t in positions for d in range(width)}
        final = {(h, t, d) for h in range(p["H_kv"]) for t in range(1, length + 1) for d in range(width)}
        initial = final - new
        parts[name] = {"Q_S": len(input_ids), "Q_R": len(new), "RI": exact(Fraction(len(input_ids), len(new))),
                       "resident_bytes_initial": len(initial), "resident_bytes_final": len(final)}
    return parts


def no_forbidden(value_to_check, forbidden):
    if isinstance(value_to_check, dict):
        assert not set(value_to_check).intersection(forbidden)
        for x in value_to_check.values():
            no_forbidden(x, forbidden)
    elif isinstance(value_to_check, list):
        for x in value_to_check:
            no_forbidden(x, forbidden)
    else:
        assert not isinstance(value_to_check, float), "binary float in results"


def check():
    conventions = read(COMMON / "data/conventions.json")
    fixed_models = read(COMMON / "data/model_inputs.json")["models"]
    fixed_by_id = {m["model_id"]: m for m in fixed_models}
    original_models = {m["id"]: m for m in read(TASK / "data/models.json")["models"]}
    registry = {s["local_path"]: s for s in read(TASK / "data/sources.json")}
    config = read(HERE / "data/config.json")
    results = read(HERE / "data/results.json")
    assert set(config) == set(conventions["config_root_keys"])
    assert set(results) == set(conventions["results_root_keys"])
    assert config["reference_id"] == results["reference_id"] == conventions["reference_id"]
    assert config["boundary"] == results["boundary"] == "operator_stage"
    assert config["element_bytes"] == 1
    assert results["model_order"] == config["model_order"] == conventions["model_order"]
    assert results["workload_ids"] == ["attention_prefill", "attention_decode"]
    assert [m["model_id"] for m in config["models"]] == config["model_order"]
    assert config["sweeps"] == {w: conventions["sweeps"][w] for w in results["workload_ids"]}
    for w in results["workload_ids"]:
        assert set(config["window_rules"][w]) == set(conventions["window_keys"])
        assert all(isinstance(v, str) for v in config["window_rules"][w].values())
    native = {}
    for model in config["models"]:
        assert set(model) == set(conventions["config_model_keys"])
        fixed = fixed_by_id[model["model_id"]]
        original = original_models[model["model_id"]]
        native[model["model_id"]] = native_dimensions(fixed)
        assert model["parameters"] == native[model["model_id"]]
        assert model["model_revision"] == fixed["model_revision"] == original["identity"]["revision"]
        assert model["selected_layer"] == fixed["selected_layer"] == original["backbone"]["selected_layer_index_zero_based"]
        assert model["selected_layer"] in original["backbone"]["full_gqa_layer_indices_zero_based"]
        assert model["source_paths"] == [fixed["local_material"][k] for k in ("structure_card", "raw_config", "raw_model_card", "implementation")]
    assert native["mimo_v25_pro"]["d_QK"] == 192 and native["mimo_v25_pro"]["d_V"] == 128
    ling_card = (TASK / fixed_by_id["ling_1t"]["local_material"]["raw_model_card"]).read_text()
    for text in ('"factor": 4.0', '"original_max_position_embeddings": 32768', '"type": "yarn"', '--max-model-len'):
        assert text in ling_card
    expected_ids = [f"{m}/{w}/{length}" for m in conventions["model_order"]
                    for w in results["workload_ids"] for length in config["sweeps"][w]["L"]]
    assert [c["case_id"] for c in results["cases"]] == expected_ids
    assert len(expected_ids) == len(set(expected_ids)) == 36
    no_forbidden(results, conventions["forbidden_result_fields"])
    case_checks = []
    for case in results["cases"]:
        assert set(case) == set(conventions["case_keys"])
        assert case["kind"] == "finite" and case["U"] is None
        fixed = fixed_by_id[case["model_id"]]
        assert case["model_revision"] == fixed["model_revision"]
        assert case["selected_layer"] == fixed["selected_layer"]
        assert case["parameters"] == native[case["model_id"]]
        assert case["window"] == config["window_rules"][case["workload"]]
        assert set(case["result"]) == set(conventions["demand_keys"] + conventions["result_additional_keys"])
        assert [c["id"] for c in case["components"]] == ["QK", "AV"]
        prefill = case["workload"] == "attention_prefill"
        counted = prefix_count(native[case["model_id"]], case["L"], prefill)
        for component in case["components"]:
            assert set(component) == set(conventions["component_keys"])
            expected = counted[component["id"]]
            for field in conventions["demand_keys"]:
                assert value(component[field]) == value(expected[field]), (case["case_id"], component["id"], field)
            p = native[case["model_id"]]
            assert component["shape_N_K"] == ([case["L"], p["d_QK"]] if component["id"] == "QK" else [p["d_V"], case["L"]])
            assert component["state_copies"] == p["H_kv"]
            assert component["resident_bytes_final"] - component["resident_bytes_initial"] == component["Q_R"]
        total = case["result"]
        for field in ("Q_S", "Q_R", "resident_bytes_initial", "resident_bytes_final"):
            assert total[field] == sum(c[field] for c in counted.values()), (case["case_id"], field)
        assert total["shared_input_bytes_removed"] == 0
        assert value(total["RI"]) == Fraction(total["Q_S"], total["Q_R"])
        assert total["resident_bytes_final"] - total["resident_bytes_initial"] == total["Q_R"]
        case_checks.append({"case_id": case["case_id"], "status": "PASS", "demand_fields": 15,
                            "component_shapes_and_copies": "PASS", "state_delta_equals_write": "PASS"})
    identity_checks = []
    for hq, hkv, dq, dv, length in [(2, 1, 3, 2, 1), (2, 1, 3, 2, 2), (2, 1, 3, 2, 5), (4, 2, 5, 3, 4)]:
        p = {"H_q": hq, "H_kv": hkv, "d_QK": dq, "d_V": dv, "g": hq // hkv}
        for prefill in (True, False):
            assert prefix_count(p, length, prefill) == explicit_identities(p, length, prefill)
            identity_checks.append({"parameters": p, "L": length, "mode": "prefill" if prefill else "decode", "status": "PASS"})
    for p in native.values():
        assert prefix_count(p, 1, True) == prefix_count(p, 1, False)

    archive_path = TASK / "../archived/task2_table_IIb_previous/03_attention/data/results.json"
    archive = {c["case_id"]: c for c in read(archive_path)["cases"]}
    migration = []
    # Recheck all historical lengths independently; only 1K overlaps the new main sweep.
    current_by_id = {c['case_id']: c for c in results['cases']}
    for old in archive.values():
        parts = prefix_count(native[old['model_id']], old['L'], '/attention_prefill/' in old['case_id'])
        s = sum(p['Q_S'] for p in parts.values()); r = sum(p['Q_R'] for p in parts.values())
        old_r = old['result']
        for field, expected in {'Q_S': s, 'Q_R': r, 'RI': Fraction(s, r)}.items():
            assert value(old_r['operator'][field]) == expected
        for name, part in parts.items():
            old_c = old_r['parts'][name]
            for field in ('Q_S', 'Q_R', 'RI'):
                assert value(part[field]) == value(old_c['operator'][field])
            assert part['resident_bytes_initial'] == old_c['initial_layout']['valid_resident_bytes']
            assert part['resident_bytes_final'] == old_c['layout']['valid_resident_bytes']
        if old['case_id'] in current_by_id:
            current = current_by_id[old['case_id']]
            assert current['model_revision'] == old['model_revision'] and current['selected_layer'] == old['selected_layer']
            for field in ('Q_S', 'Q_R', 'RI'):
                assert value(current['result'][field]) == value(old_r['operator'][field])
        migration.append({'case_id': old['case_id'], 'status': 'PASS',
                          'current_sweep_overlap': old['case_id'] in current_by_id,
                          'scope': 'historical regression only; not an added main-table case'})
    assert sum(x['current_sweep_overlap'] for x in migration) == 12

    source_checks = []
    for source in config["sources"]:
        assert set(source) == {"path", "sha256", "locator"}
        digest = hashlib.sha256((TASK / source["path"]).read_bytes()).hexdigest()
        assert digest == source["sha256"], source["path"]
        if source["path"] in registry:
            assert digest == registry[source["path"]]["sha256"]
        source_checks.append({"path": source["path"], "sha256": digest, "status": "PASS"})
    with (HERE / "data/results.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == conventions["csv_columns"]
        rows = list(reader)
    assert len(rows) == 108
    for case, triplet_start in zip(results["cases"], range(0, len(rows), 3)):
        for row, demand, component in zip(rows[triplet_start:triplet_start + 3], [case["result"], *case["components"]], ["total", "QK", "AV"]):
            assert row["case_id"] == case["case_id"] and row["component"] == component
            assert int(row["Q_S_Byte"]) == demand["Q_S"] and int(row["Q_R_Byte"]) == demand["Q_R"]
            assert Fraction(row["RI_exact"]) == value(demand["RI"])
            assert int(row["resident_initial_Byte"]) == demand["resident_bytes_initial"]
            assert int(row["resident_final_Byte"]) == demand["resident_bytes_final"]
            assert row["U"] == "" and int(row["L"]) == case["L"]
    report = {
        "schema_version": conventions["schema_version"], "reference_id": conventions["reference_id"],
        "status": "PASS", "case_counts": {"finite": 36, "limit": 0},
        "independent_checks": {
            "method": "Read original configs; accumulate native query widths, causal prefix coefficient lengths, and per-KV-head appended row widths. No production counting imports.",
            "cases": case_checks, "small_explicit_identity_checks": identity_checks,
            "L1_prefill_equals_decode": "PASS for all six native head structures",
            "schema_and_order": "PASS", "csv_rows": 108,
            "complexity": "O(L+H_q+H_kv) work, constant working memory; explicit element identities only for four tiny synthetic fixtures.",
        },
        "legacy_comparison": {"source": "../archived/task2_table_IIb_previous/03_attention/data/results.json",
                              "status": "PASS", "operator_cases": migration,
                              "scope": "Each total and QK/AV Q_S, Q_R, RI, initial/final effective capacity; aggregate shared overlap; version and layer identity."},
        "source_checks": source_checks,
        "notes": ["36 finite cases: 18 Prefill and 18 Decode; no limit cells.",
                  "Every demand is an integer or reduced exact fraction. QK and AV are distinct matrix-stage inputs.",
                  "Native MiMo dimensions 192/128, Value scale 0.612, and no global sink are preserved; Ling 64K retains the previously fixed official extended-context configuration.",
                  "Independent counting uses valid causal ranges, without specifying an execution order. PDF inspection is recorded separately."],
    }
    assert set(report) == set(conventions["checks_root_keys"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = check()
    target = HERE / "data/checks.json"
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.emit:
        target.write_text(text, encoding="utf-8")
    elif not target.exists() or target.read_text(encoding="utf-8") != text:
        raise SystemExit("STALE: data/checks.json; run check.py --emit explicitly")
    print("PASS: 36 independent cases, 36 historical regressions (12 current overlaps), 8 identity fixtures, source hashes and CSV")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Independent raw-config/identity audit; does not import the generator or old counting code."""
import argparse
import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
TASK = HERE.parents[1]
CROSS = HERE.parent / "04_crosscheck"
LEGACY = TASK.parent / "archived/task2_table_IIb_previous/01_qkv_projection/data/results.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio(a, b):
    value = Fraction(a, b)
    if value.denominator == 1:
        return value.numerator
    return {"numerator": value.numerator, "denominator": value.denominator}


def raw_parameters(original):
    raw = load(TASK / original["local_material"]["raw_config"])
    raw = raw.get("text_config", raw)
    layer = original["backbone"]["selected_layer_index_zero_based"]
    if "layer_types" in raw:
        assert raw["layer_types"][layer] == "full_attention"
    if "hybrid_layer_pattern" in raw:
        assert raw["hybrid_layer_pattern"][layer] == 0
    d, hq, hkv, dq = (raw[key] for key in ["hidden_size", "num_attention_heads", "num_key_value_heads", "head_dim"])
    dv = raw.get("v_head_dim") or dq
    dg = hq * dq if raw.get("attn_output_gate", False) else 0
    widths = {"Q": hq*dq}
    if dg:
        widths["G"] = dg
    widths.update({"K": hkv*dq, "V": hkv*dv})
    # Weight identity: each semantic projection j has N_j distinct rows, each containing D distinct entries.
    # Keep intervals instead of materializing every payload element of large matrices.
    weight_rows = {(j, row): range(d) for j, n in widths.items() for row in range(n)}
    component_writes = {j: sum(len(columns) for (name, _), columns in weight_rows.items() if name == j) for j in widths}
    assert len(weight_rows) == sum(widths.values())
    parameters = {"D": d, "H_q": hq, "H_kv": hkv, "d_QK": dq, "d_V": dv, "D_g": dg,
                  "N_Q": widths["Q"], "N_G": dg, "N_K": widths["K"], "N_V": widths["V"],
                  "N_proj": len(weight_rows)}
    return parameters, widths, component_writes


def check_exact_tree(value, forbidden):
    assert not isinstance(value, float), "binary floating value in exact results"
    if isinstance(value, dict):
        assert not set(value).intersection(forbidden)
        if "numerator" in value:
            assert set(value) == {"numerator", "denominator"}
            assert type(value["numerator"]) is int and type(value["denominator"]) is int
            f = Fraction(value["numerator"], value["denominator"])
            assert f.numerator == value["numerator"] and f.denominator == value["denominator"] and f.denominator > 1
        for item in value.values():
            check_exact_tree(item, forbidden)
    elif isinstance(value, list):
        for item in value:
            check_exact_tree(item, forbidden)


def csv_scalar(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        return f'{value["numerator"]}/{value["denominator"]}'
    return str(value)


def audit():
    contract = load(CROSS / "data/conventions.json")
    config = load(HERE / "data/config.json")
    data = load(HERE / "data/results.json")
    original_models = {m["id"]: m for m in load(TASK / "data/models.json")["models"]}
    fixed_models = {m["model_id"]: m for m in load(CROSS / "data/model_inputs.json")["models"]}
    registry = {s["local_path"]: s for s in load(TASK / "data/sources.json")}
    assert set(config) == set(contract["config_root_keys"])
    assert set(data) == set(contract["results_root_keys"])
    assert config["reference_id"] == data["reference_id"] == contract["reference_id"]
    assert config["boundary"] == data["boundary"] == "operator_stage"
    assert config["element_bytes"] == 1
    assert config["model_order"] == data["model_order"] == contract["model_order"]
    assert data["workload_ids"] == ["qkv_projection"]
    assert isinstance(config["models"], list)
    assert [m["model_id"] for m in config["models"]] == contract["model_order"]
    assert config["sweeps"] == {"qkv_projection": {"U": [1, 1024, 131072, 1048576, "infinity"]}}
    assert set(config["window_rules"]) == {"qkv_projection"}
    assert set(config["window_rules"]["qkv_projection"]) == set(contract["window_keys"])
    assert all(isinstance(x, str) for x in config["window_rules"]["qkv_projection"].values())
    check_exact_tree(data, contract["forbidden_result_fields"])
    expected_ids = [f"{mid}/qkv_projection/{b}" for mid in contract["model_order"] for b in [1, 1024, 131072, 1048576, "infinity"]]
    assert [c["case_id"] for c in data["cases"]] == expected_ids
    cases_by_id = {c["case_id"]: c for c in data["cases"]}
    checks = []
    for model in config["models"]:
        assert set(model) == set(contract["config_model_keys"])
        original = original_models[model["model_id"]]
        fixed = fixed_models[model["model_id"]]
        parameters, widths, writes = raw_parameters(original)
        assert model["parameters"] == parameters
        assert model["model_revision"] == original["identity"]["revision"] == fixed["model_revision"]
        assert model["selected_layer"] == original["backbone"]["selected_layer_index_zero_based"] == fixed["selected_layer"]
        for key in ["D", "H_q", "H_kv", "d_QK", "d_V", "D_g"]:
            assert parameters[key] == fixed[key]
        for j, key in [("Q", "q_logical"), ("G", "q_output_gate_logical"), ("K", "k"), ("V", "v")]:
            if j in widths:
                assert [widths[j], parameters["D"]] == original["attention"]["weight_shapes_N_K"][key] == fixed["qkv_shapes_N_K"][key]
        for b in [1, 1024, 131072, 1048576, "infinity"]:
            case = cases_by_id[f'{model["model_id"]}/qkv_projection/{b}']
            assert set(case) == set(contract["case_keys"])
            assert case["parameters"] == parameters
            assert case["model_revision"] == model["model_revision"] and case["selected_layer"] == model["selected_layer"]
            assert case["workload"] == "qkv_projection" and case["L"] is None and case["U"] == b
            assert case["window"] == config["window_rules"]["qkv_projection"]
            assert case["kind"] == ("limit" if b == "infinity" else "finite")
            assert [p["id"] for p in case["components"]] == list(widths)
            total_write = sum(writes.values())
            if b == "infinity":
                assert parameters["D"] > 0 and total_write > 0
                input_bytes = removed = "infinity"
                intensity = "infinity"
            else:
                # Independent branch requests share the same (stage, vector) identity.
                # Union source identities for one use; repeats have disjoint use indices.
                # Count those intervals without a million-entry identity dictionary.
                source_rows = {("X", 0): range(parameters["D"]) for j in widths}
                per_use = sum(len(columns) for columns in source_rows.values())
                input_bytes = sum(per_use for _ in range(b))
                requested = sum(len(range(parameters["D"])) for j in widths) * b
                removed = requested - input_bytes
                intensity = ratio(input_bytes, total_write)
            expect = {"Q_S": input_bytes, "Q_R": total_write, "RI": intensity,
                      "resident_bytes_initial": 0, "resident_bytes_final": total_write,
                      "shared_input_bytes_removed": removed}
            assert case["result"] == expect, case["case_id"]
            for part in case["components"]:
                assert set(part) == set(contract["component_keys"])
                j = part["id"]
                assert part["shape_N_K"] == [widths[j], parameters["D"]]
                assert part["state_copies"] == 1 and part["input_role"] == "shared_projection_input_X"
                assert {k: part[k] for k in contract["demand_keys"]} == {
                    "Q_S": input_bytes, "Q_R": writes[j],
                    "RI": "infinity" if b == "infinity" else ratio(input_bytes, writes[j]),
                    "resident_bytes_initial": 0, "resident_bytes_final": writes[j]}
            checks.append({"case_id": case["case_id"], "status": "PASS",
                           "method": "positive input-row slope and fixed nonzero weight-row sum" if b == "infinity" else "raw-config projection weight-row identities and union of shared input-row identities",
                           "expected_result": expect})
    # Explicit element identities on a small, non-aligned example establish the interval-counting convention.
    tiny_widths, tiny_d, tiny_b = {"Q": 5, "G": 5, "K": 2, "V": 3}, 3, 4
    tiny_inputs = [("X", b, d) for j in tiny_widths for b in range(tiny_b) for d in range(tiny_d)]
    tiny_writes = {(j, n, d) for j, nmax in tiny_widths.items() for n in range(nmax) for d in range(tiny_d)}
    assert len(set(tiny_inputs)) == 12 and len(tiny_writes) == 45 and len(tiny_inputs)-len(set(tiny_inputs)) == 36
    checks.append({"case_id": "identity_enumeration_small", "status": "PASS", "method": "explicit element tuples",
                   "Q_S": 12, "Q_R": 45, "RI": {"numerator": 4, "denominator": 15}, "shared_input_bytes_removed": 36})
    # Every CSV entry is checked against an already independently verified result or component.
    with (HERE / "data/results.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == contract["csv_columns"]
        rows = list(reader)
    expected_rows = []
    for case in data["cases"]:
        for part in [{"id": "total", **case["result"]}] + case["components"]:
            row = {k: csv_scalar(case[k]) for k in ["case_id", "model_id", "model_revision", "selected_layer", "workload", "kind", "U", "L"]}
            row.update({"component": part["id"], "N": csv_scalar(part.get("shape_N_K", ["", ""])[0]),
                        "K": csv_scalar(part.get("shape_N_K", ["", ""])[1]), "state_copies": csv_scalar(part.get("state_copies", ""))})
            for column, key in [("Q_S_Byte", "Q_S"), ("Q_R_Byte", "Q_R"), ("RI_exact", "RI"),
                                ("resident_initial_Byte", "resident_bytes_initial"), ("resident_final_Byte", "resident_bytes_final"),
                                ("shared_input_removed_Byte", "shared_input_bytes_removed")]:
                row[column] = csv_scalar(part.get(key, ""))
            expected_rows.append(row)
    assert rows == expected_rows and len(rows) == 130
    checks.append({"case_id": "csv_exact_records", "status": "PASS", "rows": 130})
    source_checks = []
    for source in config["sources"]:
        assert set(source) == {"path", "sha256", "locator"}
        actual = sha(TASK / source["path"])
        assert actual == source["sha256"], source["path"]
        if source["path"] in registry:
            assert actual == registry[source["path"]]["sha256"]
        source_checks.append({"path": source["path"], "sha256": actual, "status": "PASS",
                              "official_registry_match": source["path"] in registry})
    legacy = []
    for old in load(LEGACY)["cases"]:
        new = cases_by_id[f'{old["model_id"]}/qkv_projection/1']
        old_result = old["result"]
        assert new["result"]["Q_S"] == old_result["operator"]["Q_S"]
        assert old_result["operator"]["Q_R"] == 0 and old_result["operator"]["RI"] == "infinity"
        assert new["result"]["Q_R"] == old_result["capacity"]["valid_resident_bytes"]
        assert old["model_revision"] == new["model_revision"] and old["selected_layer"] == new["selected_layer"]
        for component in new["components"]:
            prior = old_result["parts"][component["id"]]
            assert component["Q_S"] == prior["operator"]["Q_S"]
            assert component["Q_R"] == prior["layout"]["valid_resident_bytes"]
        legacy.append({"model_id": old["model_id"], "status": "PASS", "U1_input_matches_prior_operator": True,
                       "new_write_equals_native_weight_elements_and_prior_valid_capacity": True,
                       "prior_Q_R": 0, "prior_RI": "infinity", "new_Q_R": new["result"]["Q_R"],
                       "new_RI": new["result"]["RI"], "finite_RI_equality_required": False})
    counts = {"finite": sum(c["kind"] == "finite" for c in data["cases"]),
              "limit": sum(c["kind"] == "limit" for c in data["cases"])}
    assert counts == contract["expected_counts"]["qkv_projection"]
    result = {"schema_version": contract["schema_version"], "reference_id": contract["reference_id"],
              "status": "PASS", "case_counts": counts, "independent_checks": checks,
              "legacy_comparison": {"path": str(LEGACY.relative_to(TASK.parent)), "sha256": sha(LEGACY),
                                    "window_change": "用户确认从预驻留窗口改为一次完整装载；旧零写入和新有限写入不得要求 RI 相等。", "models": legacy},
              "source_checks": source_checks,
              "notes": ["主生成器与独立检查均未导入旧计数 API；未执行原始模型实现。",
                        "实际矩阵按带投影名的权重行身份累计；共享输入按 X 行身份取并集；小例显式枚举元素身份。",
                        "极限检查仅验证正输入斜率与固定正写入量；不执行无穷减无穷。",
                        "本轮由主 Agent 修改并复核；最新显示与扫描修订待用户审阅。"]}
    assert set(result) == set(contract["checks_root_keys"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    value = audit()
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path = HERE / "data/checks.json"
    if args.emit:
        path.write_text(text, encoding="utf-8")
    elif not path.exists() or path.read_text(encoding="utf-8") != text:
        raise SystemExit("STALE: data/checks.json; use --emit after reviewing the difference")
    print("PASS: raw-source dimensions, 30 cases, exact CSV, shared-input identities and explicit window migration")


if __name__ == "__main__":
    main()

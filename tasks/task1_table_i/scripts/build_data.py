#!/usr/bin/env python3
"""Rebuild Table I from curated primary-source extractions (standard library only).

No network, no source PDF dependency, no writes outside the task directory.
Raw facts: data/extractions.json. Configuration/recipes: data/implementations.json.
"""
from pathlib import Path
import ast
import copy
import csv
import json
import math
import operator
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def save(path, data):
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


# Original units remain in extractions. Only these exact conversions affect recipes.
UNITS = {
    "ns": (1e-9, "second"), "us": (1e-6, "second"),
    "ms": (1e-3, "second"), "s": (1, "second"),
    "minute": (60, "second"), "MHz": (1e6, "1/second"),
    "MS/s": (1e6, "sample/second"), "Kibit": (1024 / 8, "Byte"),
    "GOPS": (1e9, "OP/second"), "TOPS": (1e12, "OP/second"),
    "us/cell": (1e-6, "second/cell"), "uS": (1e-6, "siemens"),
    "pF": (1e-12, "farad"), "fF": (1e-15, "farad"),
    "nm": (1e-9, "metre"), "um2": (1e-12, "metre^2"),
}


def evaluate(expression, env):
    """Arithmetic only; reject calls, indexing and attribute access."""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow}
    def walk(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            value = env[node.id]
            if value is None:
                raise ValueError(f"Unknown operand: {node.id}")
            return value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
        raise ValueError(f"Unsupported arithmetic: {expression}")
    result = walk(ast.parse(expression, mode="eval").body)
    if not math.isfinite(result):
        raise ValueError("Nonfinite result")
    return result


def capability(recipe, env, unknown):
    if recipe is None:
        assert unknown
        return dict(value=None, unit="Byte/s", interval=None, nature="unknown",
                    result_origin=None, derivation_kind=None,
                    unknown_reason=unknown, use_as_strict_upper_bound=False)
    result = copy.deepcopy(recipe)
    result["value"] = evaluate(recipe["formula"], env)
    result.update(interval=None, unknown_reason=None)
    return result


def tex_escape(text):
    for a, b in [("−", "-"), ("–", "--"), ("×", "$\\times$"),
                 ("&", r"\&"), ("%", r"\%"), ("_", r"\_")]:
        text = text.replace(a, b)
    return text


def display(value):
    if value is None:
        return "—"
    # Two significant digits; originals remain unrounded in JSON.
    return format(value, ".2g")


def render_row_text(template, values):
    """Resolve numeric display tokens from source facts and computed geometry."""
    def substitute(match):
        value = values[match.group(1)]
        assert value is not None, f"Unknown display operand: {match.group(1)}"
        return format(value, ".12g")
    return re.sub(r"\[\[([A-Za-z_][A-Za-z_0-9]*)\]\]", substitute, template)


def main():
    evidence = {x["evidence_id"]: x for x in read("data/extractions.json")}
    sources = {x["source_id"]: x for x in read("sources/manifest.json")}
    normalized_facts = []
    for ev in evidence.values():
        for key, raw in ev["values"].items():
            factor, unit = UNITS.get(raw["unit"], (1, raw["unit"]))
            normalized_facts.append(dict(evidence_id=ev["evidence_id"], key=key,
                original=raw, conversion_factor=factor, value=raw["value"] * factor,
                unit=unit, source_ids=ev["source_ids"], location=ev["location"],
                result_origin=raw["result_origin"], derivation_kind=raw["derivation_kind"]))
    facts = {(x["evidence_id"], x["key"]): x for x in normalized_facts}
    records = []
    for config in read("data/implementations.json"):
        r = copy.deepcopy(config)
        env, steps = {}, []
        for name, pointer in config["parameters"].items():
            fact = facts[(pointer["evidence_id"], pointer["key"])]
            env[name] = fact["value"]
            steps.append(dict(symbol=name, value=env[name], unit=fact["unit"],
                              source_pointer=pointer))
        for fmt_key, symbol in [("streaming_format", "b_S"), ("resident_format", "b_R")]:
            bits = config[fmt_key]["bits"]
            env[symbol] = None if bits is None else bits / 8
            r[symbol] = env[symbol]
            r[symbol + "_unit"] = "Byte/element"
            r[symbol + "_unknown_reason"] = config[fmt_key]["unknown_reason"] if bits is None else None
            steps.append(dict(symbol=symbol, formula="logical_format_bits / 8",
                              value=env[symbol], unit="Byte/element", format=config[fmt_key]["name"]))
        for name, expr in config["geometry_plan"].items():
            value = evaluate(expr, env) if expr is not None else None
            if value is not None:
                assert value > 0 and int(value) == value
                value = int(value)
            r[name] = env[name] = value
            steps.append(dict(symbol=name, formula=expr, value=value))
        for name, expr in config["intermediate_plan"].items():
            env[name] = evaluate(expr, env)
            steps.append(dict(symbol=name, formula=expr, value=env[name]))
        for key in ("rho", "tau"):
            r[key] = capability(config.get(key + "_recipe"), env, config["unknown_reasons"][key])
        pair = r.get("pair_compatibility", {"compatible": False,
                   "basis": "At least one capability or compatible logical format is missing."})
        r["pair_compatibility"] = pair
        if r["rho"]["value"] is not None and r["tau"]["value"] is not None:
            assert pair["compatible"]
            r["ridge"] = dict(value=r["rho"]["value"] / r["tau"]["value"],
                interval=None, unit="Byte_streaming/Byte_resident", nature="paired_point",
                result_origin=r["rho"]["result_origin"], derivation_kind="converted",
                formula="rho / tau", unknown_reason=None)
        else:
            r["ridge"] = dict(value=None, interval=None, unit="Byte_streaming/Byte_resident",
                nature="unknown", result_origin=None, derivation_kind=None,
                unknown_reason="Compatible rho and tau pair not available.")
        if "native_storage_write_recipe" in config:
            r["native_storage_write_bandwidth"] = capability(config["native_storage_write_recipe"], env, None)
            r["native_storage_write_bandwidth"]["not_a_CIM_tau"] = True
        if "logical_resident_capacity_Byte" in env:
            r["service_unit"]["capacity_Byte"] = env["logical_resident_capacity_Byte"]
            r["service_unit"]["capacity_unknown_reason"] = None
        elif "logical_weight_count" in env:
            r["service_unit"]["capacity_logical_elements"] = int(env["logical_weight_count"])
            r["service_unit"]["capacity_unknown_reason"] = "Analog b_R not defined; capacity in logical elements is available."
        elif r["logical_n_in"] is not None and r["logical_n_out"] is not None and r["b_R"] is not None:
            r["service_unit"]["capacity_Byte"] = r["logical_n_in"] * r["logical_n_out"] * r["b_R"]
            r["service_unit"]["capacity_unknown_reason"] = None
            r["service_unit"]["capacity_scope"] = "Active logical matrix at the chosen service boundary; parent physical capacity is separate."
        else:
            r["service_unit"]["capacity_unknown_reason"] = "A complete CIM service matrix has not been specified; physical storage is described separately."
        r["intermediate_values"] = env
        r["calculation_steps"] = steps
        r["main_table"] = False
        records.append(r)
    by_id = {x["record_id"]: x for x in records}
    selected = []
    for sel in read("data/main_selection.json"):
        r = by_id[sel["record_id"]]
        r["main_table"] = True
        row = copy.deepcopy(sel)
        text_values = dict(n_out=r["logical_n_out"], n_in=r["logical_n_in"],
                           s_bits=r["streaming_format"]["bits"], r_bits=r["resident_format"]["bits"])
        for name, pointer in sel.get("display_bindings", {}).items():
            if "formula" in pointer:
                text_values[name] = evaluate(pointer["formula"], text_values)
            else:
                fact = facts[(pointer["evidence_id"], pointer["key"])]
                text_values[name] = fact["original"]["value"]
                assert fact["original"]["unit"] == pointer["original_unit"]
        row["display_values"] = text_values
        for field in ["configuration_tex", "evidence_condition_tex"]:
            row[field] = render_row_text(sel[field], text_values)
        row["source_ids"] = r["source_ids"]
        row["evidence_ids"] = r["evidence_ids"]
        for key in ["rho", "tau"]:
            value = r[key]["value"]
            row[key + "_GB_per_s"] = None if value is None else value / 1e9
            row[key + "_display"] = display(row[key + "_GB_per_s"])
        row["ridge"] = r["ridge"]["value"]
        row["ridge_display"] = display(row["ridge"])
        selected.append(row)
    scenarios = read("data/reference_scenarios.json")
    for scenario in scenarios:
        r = by_id[scenario["based_on_record_id"]]
        env = r["intermediate_values"]
        scenario["rho_Byte_per_s"] = r["rho"]["value"]
        scenario["tau_Byte_per_s"] = env["write_bus_bits"] / 8 * env["f"]
        scenario["ridge"] = scenario["rho_Byte_per_s"] / scenario["tau_Byte_per_s"]
    coverage = []
    for medium in ["SRAM", "DRAM", "eDRAM / gain-cell", "3D NAND", "2D NOR Flash", "RRAM", "MRAM", "PCM", "FeRAM", "3D FeNOR / vertical FeFET"]:
        group = [r for r in records if r["technology"] == medium]
        coverage.append(dict(technology=medium, covered=True,
            record_ids=[r["record_id"] for r in group],
            main_record_ids=[r["record_id"] for r in group if r["main_table"]],
            gaps=[dict(record_id=r["record_id"], rho=r["unknown_reasons"]["rho"],
                       tau=r["unknown_reasons"]["tau"], next_match=r["matching_conditions"]) for r in group]))
    save("data/normalized_extractions.json", normalized_facts)
    save("data/hardware_records.json", records)
    save("data/main_table.json", selected)
    save("data/coverage.json", coverage)
    save("data/reference_scenarios_evaluated.json", scenarios)
    save("data/task3_hardware_export.json", dict(schema_version="1.0", baseline_commit="6817194a3be1ba18ad2c3eb9273bb25a0fa470c2",
        matrix_orientation="n_out x n_in", base_units=["Byte", "second", "OP"],
        source_manifest="../sources/manifest.json", records=records,
        reference_scenarios=scenarios, caution="Native formats and boundaries must be matched. Unknowns are not zeros. Reference scenarios are not chip measurements."))
    with (ROOT / "data/main_table.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["row_id", "record_id", "technology", "rho_GB_per_s", "tau_GB_per_s", "ridge", "rho_display", "tau_display", "ridge_display", "source_ids"])
        writer.writeheader()
        for row in selected:
            writer.writerow({"row_id":row["row_id"], "record_id":row["record_id"],
                "technology":row["technology_display"], **{key:row[key] for key in ["rho_GB_per_s", "tau_GB_per_s", "ridge", "rho_display", "tau_display", "ridge_display"]},
                "source_ids":";".join(row["source_ids"])})
    lines = ["% GENERATED by scripts/build_data.py; edit JSON inputs, not this file.",
        "% Requires amsmath, booktabs, array, tabularx and cite in the parent preamble.",
        r"\ifdefined\TOneTableBox\else\newsavebox{\TOneTableBox}\fi",
        r"\begin{table*}[!t]", r"\centering",
        r"\caption{Literature-grounded streaming and resident-write capabilities of representative CIM implementations}",
        r"\label{tab:t1_capabilities}",
        r"\begingroup", r"\setlength{\tabcolsep}{3pt}", r"\renewcommand{\arraystretch}{1.10}",
        r"\sbox{\TOneTableBox}{\begin{minipage}{\textwidth}\fontsize{8.5}{10.2}\selectfont",
        r"\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{31mm}>{\raggedright\arraybackslash}p{40mm}rrr>{\raggedright\arraybackslash}X@{}}",
        r"\toprule",
        r"Technology / implementation & Mode; logical $n_{\rm out}\!\times n_{\rm in}$; input/weight & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & Evidence / key condition \\",
        r" & & \multicolumn{2}{c}{[GB/s]} & & \\", r"\midrule"]
    for row in selected:
        values = [r"\textemdash" if row[key] == "—" else "$" + row[key] + "$" for key in ["rho_display", "tau_display", "ridge_display"]]
        lines.append(tex_escape(row["technology_display"]) + r"~\cite{" + ",".join(row["source_ids"]) + "} & " +
            row["configuration_tex"] + " & " + " & ".join(values) + " & " + row["evidence_condition_tex"].replace("−", "-") + r" \\")
    lines += [r"\bottomrule", r"\end{tabularx}", r"\par\vspace{5pt}",
        r"\textit{Scope:} Native local service boundaries; one core/group unless specified. Packed logical input bytes are counted once per complete stated-precision evaluation; physical bit slices and complementary cells are not extra payload. Analog outputs retain the reported quantization/error contract. $\mathrm{RI}^{*}=\rho/\tau$ only for a compatible pair; GB/s is decimal. These configurations are not normalized for process, area, capacity or power.",
        r"\par\vspace{2pt}\textit{Evidence:} First code: M, measured chip; D, measured device; S, simulation. Second code: D, directly reported parameter; C, converted capability. PCM timing is RTL-derived on a measured-chip architecture. \textemdash\ means insufficient evidence for this service boundary, not impossibility. AAP is a DRAM row-operation primitive; RAW means read-after-write. FeNOR switching pulses and RAW delays do not specify CIM throughput. Full conditions, write/verify evidence and unavailable timing are retained in the supporting records.",
        r"\end{minipage}}",
        r"\typeout{T1_BODY_WIDTH_PT=\the\wd\TOneTableBox}",
        r"\typeout{T1_BODY_HEIGHT_PT=\the\ht\TOneTableBox}",
        r"\typeout{T1_BODY_DEPTH_PT=\the\dp\TOneTableBox}",
        r"\usebox{\TOneTableBox}", r"\endgroup", r"\end{table*}", ""]
    (ROOT / "tex/table_i.tex").write_text("\n".join(lines))
    bib = []
    for s in sources.values():
        # Full author metadata remains in the manifest; compact IEEE bibliography.
        authors = s["authors"][:3] + (["others"] if len(s["authors"]) > 3 else [])
        title = tex_escape(s["title"]).replace("10^11", r"$10^{11}$").replace("10^12", r"$10^{12}$")
        title = title.replace("/mm2", r"/mm$^2$")
        title = title.replace("±", r"$\pm$")
        lines = ["@misc{"+s["source_id"]+",", "  author = {"+" and ".join(authors)+"},",
                 "  title = {{"+title+"}},", "  howpublished = {"+tex_escape(s["venue"])+"},",
                 "  year = {"+str(s["year"])+"},"]
        if s["source_id"] == "t1_pcm64":
            lines.append("  note = {Numerical evidence: arXiv:2212.02872, Dec. 7, 2022 version},")
        if s["doi"]:
            lines.append("  doi = {"+s["doi"]+"},")
            lines.append("  url = {https://doi.org/"+s["doi"]+"},")
        else:
            lines.append("  url = {"+s["official_url"]+"},")
        lines.append("}")
        bib.append("\n".join(lines))
    (ROOT / "tex/table_i.bib").write_text("\n\n".join(bib)+"\n")
    stats = dict(main_rows=len(selected), hardware_records=len(records), sources=len(sources),
        local_full_text_sources=sum(s["local_file"] is not None for s in sources.values()),
        main_numeric_rho=sum(x["rho_GB_per_s"] is not None for x in selected),
        main_numeric_tau=sum(x["tau_GB_per_s"] is not None for x in selected),
        main_numeric_ridge=sum(x["ridge"] is not None for x in selected),
        primary_evidence_entries=len(evidence), normalized_facts=len(normalized_facts))
    save("output/data_build_summary.json", stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

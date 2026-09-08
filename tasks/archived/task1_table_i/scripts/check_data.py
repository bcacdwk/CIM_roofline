#!/usr/bin/env python3
"""Consistency checks plus independent arithmetic controls for the research table."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import hashlib
import json
import math
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(p): return json.loads((ROOT / p).read_text())


def close(a, b): return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15)


def main():
    files = ["data/hardware_records.json", "data/main_table.json", "tex/table_i.tex", "tex/table_i.bib", "data/task3_hardware_export.json"]
    before = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    subprocess.run([sys.executable, str(ROOT/"scripts/build_data.py")], check=True, stdout=subprocess.DEVNULL)
    assert before == {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}, "Generated data was stale"
    checks = ["Raw JSON -> normalized records -> table/Task3 export reproducible byte-for-byte"]
    records = {r["record_id"]:r for r in read("data/hardware_records.json")}
    sources = {s["source_id"]:s for s in read("sources/manifest.json")}
    evs = {e["evidence_id"]:e for e in read("data/extractions.json")}
    selected = read("data/main_table.json")
    assert len(records) == len(read("data/hardware_records.json"))
    assert len(selected) in range(11,14)
    assert all(r.startswith("hw_") for r in records)
    assert all(s.startswith("t1_") for s in sources)
    for r in records.values():
        assert set(r["source_ids"]) <= sources.keys()
        assert r["boundary_kind"] and r["boundary_description"] and r["matching_conditions"]
        for e in r["evidence_ids"]:
            assert e in evs and evs[e]["location"]
        for key, fmt in [("b_S", "streaming_format"), ("b_R", "resident_format")]:
            if r[key] is None:
                assert r[key + "_unknown_reason"]
            else:
                assert r[key] > 0 and close(8*r[key], r[fmt]["bits"])
            assert r[fmt]["name"]
        if r["logical_n_in"] is None or r["logical_n_out"] is None:
            assert r["geometry_unknown_reason"]
        for key in ["rho", "tau", "ridge"]:
            cap = r[key]
            if cap["value"] is None:
                assert cap["unknown_reason"] and cap["nature"] == "unknown"
            else:
                assert cap["value"] > 0 and math.isfinite(cap["value"])
                assert cap["result_origin"] and cap["derivation_kind"]
        if r["ridge"]["value"] is not None:
            assert r["pair_compatibility"]["compatible"]
            assert r["rho"]["value"] is not None and r["tau"]["value"] is not None
            assert close(r["ridge"]["value"], r["rho"]["value"]/r["tau"]["value"])
        if r["rho"]["value"] is not None:
            assert r["logical_n_in"] and r["logical_n_out"] and r["b_S"]
        if r["tau"]["value"] is not None:
            assert r["b_R"] and r["write_service"]["completion_condition"]
        for key in ["rho", "tau", "ridge"]:
            interval = r[key].get("interval")
            if interval is not None:
                assert 0 < interval[0] <= interval[1]
        if r["ridge"]["interval"] is not None:
            a,b=r["rho"]["interval"],r["tau"]["interval"]
            assert close(r["ridge"]["interval"][0],a[0]/b[1])
            assert close(r["ridge"]["interval"][1],a[1]/b[0])
    checks.append("IDs, references, orthogonal evidence labels, formats, null reasons, dimensions, positive units and compatible ridge pairs")
    # Unit controls use exact rational arithmetic, independent of build_data.UNITS.
    facts = {(f["evidence_id"],f["key"]):f for f in read("data/normalized_extractions.json")}
    assert close(facts[("ev_gaincell","capacity")]["value"],32*1024/8)
    assert close(facts[("ev_d6","frequency")]["value"],360*1_000_000)
    assert close(facts[("ev_neurram","latency")]["value"],float(Fraction(39,10_000_000)))
    assert close(facts[("ev_neurram","wait_before_inference")]["value"],1800)
    assert facts[("ev_neurram","verify_min")]["value"] <= facts[("ev_neurram","verify_max")]["value"]
    assert facts[("ev_edram","simulated_clock")]["result_origin"] == "simulation"
    assert facts[("ev_neurram_projection","projected_program_time")]["result_origin"] == "reference_scenario"
    assert records["hw_pcm_hermes64_4phase"]["rho"]["result_origin"] == "simulation"
    assert records["hw_rram_neurram2022_4b"]["b_R"] is None
    assert records["hw_feram_cy15b101n_storage"]["tau"]["value"] is None
    assert records["hw_feram_cy15b101n_storage"]["native_storage_write_bandwidth"]["not_a_CIM_tau"]
    for row in selected:
        r=records[row["record_id"]]
        assert r["evidence_ids"] and r["main_table"]
        assert "[[" not in row["configuration_tex"] + row["evidence_condition_tex"]
        if r["rho"]["value"] is not None:
            expected = "$" + str(r["logical_n_out"]) + r"\times" + str(r["logical_n_in"]) + "$"
            assert expected in row["configuration_tex"], "Displayed geometry disagrees with hardware geometry"
        for binding in row.get("display_bindings", {}).values():
            if "evidence_id" in binding:
                assert binding["evidence_id"] in r["evidence_ids"]
                raw = evs[binding["evidence_id"]]["values"][binding["key"]]
                assert raw["unit"] == binding["original_unit"]
        for key in ["rho","tau"]:
            v=row[key+"_GB_per_s"]
            if v is not None:
                assert close(v*1_000_000_000,r[key]["value"])
            else: assert row[key+"_display"] == "—"
    checks.append("bit/Byte, Ki-bit/Byte, ns/us/minute/second, MHz and decimal GB/s; storage and projected values are not CIM measurements")
    # Physical/logic controls independent of expression evaluation.
    assert records["hw_sram_dcim_d6cim2023_u8"]["service_unit"]["capacity_Byte"] == 128*128/8 == 16*128
    assert records["hw_sram_acim_jia2022_4b"]["service_unit"]["capacity_Byte"] == 64*1152*.5 == 1152*256/8
    assert records["hw_mram_jung2022_binary"]["service_unit"]["capacity_Byte"] == 512
    assert records["hw_rram_neurram2022_4b"]["intermediate_values"]["logical_weight_count"] == 65536/2
    assert records["hw_nand_shim2021_int8"]["intermediate_values"]["physical_cells_per_logical_weight"] == 36
    assert records["hw_fenor_zhou2026"]["physical_organization"]["dimensions"]["shown_pattern_cells"] == 4*16*16
    assert all(records["hw_fenor_zhou"+str(y)]["rho"]["value"] is None for y in [2025,2026])
    checks.append("Spatial slices, differential pairs, NAND duplication and fabricated-vs-validated FeFET cell counts")
    # Independent manual controls entered as physical counts and full schedule costs.
    d6_ops_per_second = Fraction(128*16*2*360_000_000,64)
    manual_d6 = float(d6_ops_per_second/Fraction(2*16,1))
    full_mram_write_seconds = Fraction(64*2,11_100_000)
    manual_mram_tau = float(Fraction(64*64,8)/full_mram_write_seconds)
    manual_mram_rho = float(Fraction(64,8)*11_100_000)
    manual_jia_chip_ops = 16*1152*64*2*20_000_000/4
    assert close(manual_d6,records["hw_sram_dcim_d6cim2023_u8"]["rho"]["value"])
    assert close(manual_mram_tau,records["hw_mram_jung2022_binary"]["tau"]["value"])
    assert close(manual_mram_rho,records["hw_mram_jung2022_binary"]["rho"]["value"])
    assert close(manual_mram_rho/manual_mram_tau,2)
    assert abs(manual_jia_chip_ops/1e12-11.8) < .05 # source rounds peak to 11.8 TOPS
    checks.append("Independent D6CIM OP/kappa calculation, MRAM full-array refill calculation and Jia 16-core TOPS cross-check")
    # A conservative ratio envelope is monotone in opposite directions.
    # Synthetic arithmetic guard only; it is NOT an observed hardware interval.
    a,b=(2,4),(5,10)
    assert (a[0]/b[1],a[1]/b[0]) == (.2,.8)
    checks.append("Interval direction checked; no hardware capability interval or confidence interval manufactured")
    cover=read("data/coverage.json")
    assert len(cover)==10 and all(c["main_record_ids"] for c in cover)
    sram_modes={records[row["record_id"]]["mode"] for row in selected if records[row["record_id"]]["technology"]=="SRAM"}
    assert sram_modes=={"ACIM","DCIM"}
    tex=(ROOT/"tex/table_i.tex").read_text();bib=(ROOT/"tex/table_i.bib").read_text()
    keys={x for group in re.findall(r"\\cite\{([^}]+)\}",tex) for x in group.split(",")}
    assert all("{"+key+"," in bib for key in keys)
    assert r"\documentclass" not in tex
    checks.append("All ten technology groups covered, SRAM modes separated, and every main citation present")
    local_verified=[];missing_local=[]
    for s in sources.values():
        if s["local_file"]:
            p=ROOT/s["local_file"]
            if not p.exists():
                missing_local.append(s["source_id"]);continue # public checkout intentionally omits PDFs
            assert p.read_bytes().startswith(b"%PDF")
            assert hashlib.sha256(p.read_bytes()).hexdigest()==s["sha256"]
            local_verified.append(s["source_id"])
    for copy in read("sources/repository_copies.json"):
        original=ROOT.parents[1]/copy["original_path"]
        if original.exists():assert hashlib.sha256(original.read_bytes()).hexdigest()==copy["sha256"]
    checks.append("Available local PDF signatures/hashes and original repository copies verified; missing ignored PDFs explicitly reported")
    report=dict(status="PASS",check_groups=checks,main_rows=len(selected),hardware_records=len(records),
        local_source_hashes_verified=local_verified,local_sources_absent=missing_local,
        evidence_origin_counts=dict(Counter(e["result_origin"] for e in evs.values())),
        individual_fact_origin_counts=dict(Counter(f["result_origin"] for f in read("data/normalized_extractions.json"))),
        manual_controls=dict(d6_rho_Byte_per_s=manual_d6,mram_rho_Byte_per_s=manual_mram_rho,
            mram_tau_Byte_per_s=manual_mram_tau,mram_full_refill_second=float(full_mram_write_seconds),
            mram_ridge=2,jia_chip_TOPS=manual_jia_chip_ops/1e12),
        limitations=["Schema and arithmetic checks cannot prove truth of literature facts; source reading remains required.",
            "No empirical interval data is supplied; unknown throughput does not imply a ridge."])
    (ROOT/"output/check_results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"PASS: {len(checks)} check groups, {len(selected)} rows, {len(local_verified)} PDF hashes; absent ignored PDFs: {len(missing_local)}")


if __name__ == "__main__":main()

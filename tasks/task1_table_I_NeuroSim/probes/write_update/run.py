#!/usr/bin/env python3
"""Compile unmodified locked native functions in a fresh local probe directory."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

LOCKS = {
    "2DTrainingV2.1": "f80a4345f70dcb1ddfd003d3ddcfbd067b55a79a",
    "MLPInferenceV3.0": "6098feabaf17b8209a8edbef4a9c963b5f015132",
    "2DInferenceV1.4": "8a88abf85844c0e1ba17cc771ea535fff6040456",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=os.environ.get("NEUROSIM_ROOT", str(Path.home()/"neurosim")))
    p.add_argument("--out", required=True)
    p.add_argument("--cxx", required=True)
    a = p.parse_args()
    root, out = Path(a.root).resolve(), Path(a.out).resolve()
    if root not in out.parents or any(s in str(root).lower() for s in ("onedrive", "icloud", "cloudstorage")):
        raise SystemExit("--out must be inside the nonsynchronized local root")
    if out.exists() and any(out.iterdir()):
        raise SystemExit("--out must be fresh (will not overwrite existing evidence)")
    out.mkdir(parents=True, exist_ok=True)
    (out/"tmp").mkdir()
    os.environ["TMPDIR"] = str(out/"tmp")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    commands, assertions, manifest = [], [], []
    here = Path(__file__).resolve().parent
    worktrees = json.loads((root/"worktrees.json").read_text())
    for name in ("run.py", "training_probe.cpp", "mlp_probe.cpp", "sram_driver_probe.cpp"):
        src, dest = here/name, out/name
        shutil.copy2(src, dest)
        manifest.append({"path": name, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "kind": "canonical_probe_copy"})

    def run(cmd, label):
        result = subprocess.run([str(x) for x in cmd], cwd=out, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out/(label+".log")).write_text(result.stdout)
        commands.append({"argv": [str(x) for x in cmd], "cwd": str(out), "returncode": result.returncode, "log": label+".log"})
        (out/"commands.json").write_text(json.dumps(commands, indent=2)+"\n")
        if result.returncode:
            raise RuntimeError("failed: "+label+"; see local log")
        if "ERROR" in result.stdout or "Error:" in result.stdout:
            raise RuntimeError("upstream emitted error: "+label)
        return result.stdout

    for branch, sha in LOCKS.items():
        head = run(["git", "-C", worktrees[branch], "rev-parse", "HEAD"], "head-"+branch).strip()
        assert head == sha, (branch, head)

    t = Path(worktrees["2DTrainingV2.1"])/"Training_pytorch/NeuroSIM"
    m = Path(worktrees["MLPInferenceV3.0"])
    v = Path(worktrees["2DInferenceV1.4"])/"Inference_pytorch/NeuroSIM"
    for branch, src, dest, extensions in [
        ("2DTrainingV2.1", t, out/"training-src", (".cpp", ".h")),
        ("MLPInferenceV3.0", m, out/"mlp-src", (".cpp", ".h")),
        ("2DInferenceV1.4", v, out/"v14-src", (".cpp", ".h"))]:
        dest.mkdir()
        if branch == "2DTrainingV2.1":
            names = sorted(src.iterdir())
        elif branch == "MLPInferenceV3.0":
            names = [src/n for n in ("Cell.cpp", "Cell.h", "Array.h", "formula.cpp", "formula.h")]
        else:
            names = [src/n for n in ("Param.cpp", "Param.h", "SRAMWriteDriver.cpp", "SRAMWriteDriver.h", "FunctionUnit.cpp", "FunctionUnit.h", "Technology.cpp", "Technology.h", "formula.cpp", "formula.h", "constant.h", "InputParameter.h", "MemCell.h", "typedef.h")]
        for f in names:
            if f.is_file() and f.suffix in extensions and f.name != "main.cpp":
                shutil.copy2(f, dest/f.name)
                manifest.append({"branch": branch, "sha": LOCKS[branch], "path": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "kind": "unmodified_upstream_build_copy"})
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    base = [a.cxx, "-std=c++11", "-O2", "-fopenmp"]
    run(base+["-I", out/"training-src", out/"training_probe.cpp"]+sorted((out/"training-src").glob("*.cpp"))+["-o", out/"training_probe"], "compile-training")
    run(base+["-I", out/"mlp-src", out/"mlp_probe.cpp", out/"mlp-src/Cell.cpp", out/"mlp-src/formula.cpp", "-o", out/"mlp_probe"], "compile-mlp")
    run(base+["-I", out/"v14-src", out/"sram_driver_probe.cpp"]+sorted((out/"v14-src").glob("*.cpp"))+["-o", out/"sram_driver_probe"], "compile-sram-driver")
    def check(name, actual, expected):
        ok = math.isclose(actual, expected, rel_tol=2e-12, abs_tol=1e-25)
        assertions.append({"name": name, "actual": actual, "expected": expected, "status": "PASS" if ok else "FAIL"})
    # Hand-counted pulses and observed source semantics, independent constants.
    # These regression observations do NOT claim physical correctness. Separate
    # hand-derived transaction references below expose the known mismatches.
    expected = {
        "unchanged": (0, 0, 0.0, 0.0),
        "set": (2, 2, 0.25, 0.25),
        "reset": (2, 2, 0.25, 0.25),
        "mixed": (5, 5, 0.125, 0.25),
        "two_set_rows": (3, 3, 0.125, 0.5),
        "all_set": (4, 4, 0.5, 0.5),
    }
    rows=[]
    for name, (total, avg, ac, ar) in expected.items():
        for width in (1, 4):
            raw=run([out/"training_probe", name, str(width)], "training-"+name+"-"+str(width))
            row=json.loads(next(x for x in raw.splitlines() if x.startswith("{")))
            rows.append(row)
            for field, val in [("pulse_total", total), ("pulse_average", avg), ("activity_col", ac), ("activity_row", ar)]:
                check(name+"-"+str(width)+"-"+field, row[field], val)
            check(name+"-"+str(width)+"-array-pulse-time", row["write_latency_array_s"], total*50e-9)
            assert math.isfinite(row["write_latency_total_s"])
            if total:
                assert row["write_latency_total_s"] >= row["write_latency_array_s"] > 0
    narrow=next(r for r in rows if r["case"]=="all_set" and r["parallelism"]==1)
    wide=next(r for r in rows if r["case"]=="all_set" and r["parallelism"]==4)
    assertions.append({"name": "limited-parallelism-changes-periphery-not-array-pulses", "status": "PASS" if narrow["write_latency_total_s"] > wide["write_latency_total_s"] and narrow["write_latency_array_s"] == wide["write_latency_array_s"] else "FAIL", "narrow_s": narrow["write_latency_total_s"], "wide_s": wide["write_latency_total_s"]})
    raw=run([out/"mlp_probe"], "mlp")
    mlp=json.loads(next(x for x in raw.splitlines() if x.startswith("{")))
    check("DigitalNVM.Read-low-VG", mlp["read0_A"], 0.5/24000)
    check("DigitalNVM.Read-high-VG", mlp["read1_A"], 0.5/8000)
    check("DigitalNVM.Read-reset-VG", mlp["read0_after_reset_A"], 0.5/24000)
    check("DigitalNVM.Write-configured-pulse", mlp["write_pulse_LTP_s"], 10e-9)
    check("DigitalNVM.Write-energy", mlp["set_energy_J"], (1/24000+1/8000)/2*10e-9+2e-15)
    check("DigitalNVM.unchanged-retains-energy-field", mlp["unchanged_energy_field_J"], mlp["set_energy_J"])
    raw=run([out/"sram_driver_probe"], "sram-driver")
    sram=json.loads(next(x for x in raw.splitlines() if x.startswith("{")))
    assert math.isfinite(sram["single_write_s"]) and sram["single_write_s"] > 0
    assert sram["cap_inv_input_F"] > 0 and sram["cap_inv_output_F"] > 0
    check("SRAMWriteDriver.numWrite-owned-here", sram["two_writes_s"], 2*sram["single_write_s"])
    check("SRAMWriteDriver.lane-count-not-single-op-latency", sram["width8_single_write_s"], sram["single_write_s"])
    independent_reference = {
      "input_domain": {"old_codes": [[4,4,4,4],[4,4,4,4]], "conductance_per_code_S": 2**-20, "max_codes":9,"min_codes":1,"levels_LTP_LTD":8},
      "mixed": {"new_codes":[[6,1,4,4],[4,4,4,4]], "SET_pulses":2,"RESET_pulses":3,"SET_active_rows":1,"RESET_active_rows":1,"SET_active_cells":1,"RESET_active_cells":1,"phase_mean_activity_col":0.25,"phase_mean_activity_row":0.5,"native_activity_col":0.125,"native_activity_row":0.25,"assessment":"MISMATCH: native else-if omits RESET activity on a mixed row"},
      "two_set_rows": {"new_codes":[[6,5,4,4],[5,4,4,4]],"SET_active_cells":3,"SET_active_rows":2,"mean_active_columns":1.5,"ceiling_mean_active_columns":2,"native_ceiling_result":1,"assessment":"MISMATCH: int/int occurs before ceil"},
      "all_set": {"new_codes":[[6,6,6,6],[6,6,6,6]],"pulse_slots_if_one_cell_per_operation":16,"pulse_slots_if_four_cells_per_operation":4,"native_pulse_total_both_widths":4,"assessment":"MISMATCH at width 1: estimator assumes row-parallel pulses, width only changes later peripheral counts"},
      "interpretation":"PASS means reproducing locked implementation and exposing limits, not approving it as a complete resident-load scheduler. The 128x128 latency probe uses synthetic aggregate activity and is distinct from the 2x4 estimator transaction."
    }
    summary={"status":"PASS" if all(x["status"]=="PASS" for x in assertions) else "FAIL", "probe_kind":"mechanism_only_not_case_simulation", "locked_sha":LOCKS, "training":rows, "mlp":mlp, "sram_driver":sram, "independent_transaction_reference":independent_reference,
      "v1_4_write":{"value":None,"status":"NOT_IMPLEMENTED_IN_SUBARRAY_AGGREGATOR","source_evidence":"SubArray.cpp:896,962-966,1267-1269"},
      "findings":["Mixed SET/RESET row: RESET row/column activity omitted by upstream else-if, though its pulses remain in total.","ceil(integer/integer) truncates selected-column average before ceil.","Finite write width affects peripheral repeated operation count but not array pulse sum; full-cover batching must be outside this estimator.","DigitalNVM.Read returns V*G; no MTJ switching or complementary IBMD dynamics. Unchanged Write leaves previous energy field stale."],
      "assertions":assertions}
    (out/"summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status":summary["status"],"assertions":len(assertions),"out":str(out)},ensure_ascii=False))
    return 0 if summary["status"]=="PASS" else 1

if __name__ == "__main__":
    sys.exit(main())

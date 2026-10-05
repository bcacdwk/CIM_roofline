#!/usr/bin/env python3
"""Independent Task III interface + A/C/D audit.

No author builders or shared computational functions are imported. Expected
values come from accepted Task I native mappings/CSV and Task II result files.
Writes only review/independent_ACD.json.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
T3 = HERE.parent
ROOT = T3.parent.parent
T1 = ROOT / "tasks/task1_table_I_NVM"
T2 = ROOT / "tasks/task2_table_II_workloads"


def read_json(p):
    return json.loads(p.read_text())


def read_csv(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pointer(base, ref):
    name, ptr = ref.split("#", 1)
    x = read_json(base/name)
    for k in ptr.strip("/").split("/"):
        k = k.replace("~1", "/").replace("~0", "~")
        x = x[int(k)] if isinstance(x, list) else x[k]
    return x


def close(a,b):
    assert math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=1e-14), (a,b)


def status(u,t):
    if math.isclose(u,t,rel_tol=1e-10): return "balanced"
    return "resident-bound" if u<t else "streaming-bound"


def main():
    s=read_json(T3/"shared/data.json")
    src_rows=read_csv(T1/"analysis/11_summary_figures/data/rho_tau_loglog_circles_points.csv")
    original={(r["case_id"],r["profile"]):r for r in src_rows}
    hw={(r["case_id"],r["profile"]):r for r in s["hardware"]}
    assert set(original)==set(hw) and len(hw)==30
    counts={"native_scenarios":0,"source_hashes":0,"shared_tableIIa_cases":0,
            "shared_qkv_workload_states":0,"shared_qkv_mapped_scenarios":0,
            "A_points":0,"A_circles":0,"C_thresholds":0,
            "AC_classifications":0,"D_scan_points":0,"D_curve_points":0,
            "threshold_neighbors":0}
    for src in s["sources"]:
        assert hashlib.sha256((ROOT/src["path"]).read_bytes()).hexdigest()==src["sha256"]
        counts["source_hashes"]+=1
    truth={}
    for key,row in hw.items():
        old=original[key]
        raw=pointer(T1/"analysis",row["source_mapping"])
        n,k=raw["N"],raw["K"]
        delta,load=raw["delta_S_ns"],raw["T_R_ns"]
        rho=raw["B_S_Byte"]*1000/delta
        tau=raw["B_R_Byte"]*1000/load
        ustar=load/delta
        for name,a,b in [("rho",rho,row["rho_MB_per_s"]),("tau",tau,row["tau_MB_per_s"]),
                         ("Ustar",ustar,row["U_star"]),("sigma",n*rho,row["sigma_MB_per_s"]),
                         ("nativeRI",rho/tau,row["RI_star"]),
                         ("acceptedrho",rho,old["rho"]),("acceptedtau",tau,old["tau"]),
                         ("acceptedU",ustar,old["U_star"])]: close(a,b)
        assert (n,k)==(row["N"],row["K"])
        assert raw["B_S_Byte"]==k and raw["B_R_Byte"]==n*k
        truth[key]={"N":n,"K":k,"rho":rho,"tau":tau,"U_star":ustar,"sigma":n*rho,
                    "delta":delta,"load":load}
        counts["native_scenarios"]+=1
        for f in [1-1e-6,1,1+1e-6]:
            u=f*ustar
            st=status(u,ustar)
            a=status(u*tau,n*rho)  # demand capacity vs native streaming-equivalent capacity
            c="resident-bound" if f<1 else ("balanced" if f==1 else "streaming-bound")
            assert st==a==c
            close(min(1,u/ustar), min(rho,tau*u/n)/rho)
            counts["threshold_neighbors"]+=1
    ii=read_json(T2/"table_IIa/data/results.json")
    ii_lookup={r["case_id"]:r for r in ii["cases"]}
    for row in s["table_IIa_finite"]:
        src=ii_lookup[row["case_id"]]
        assert src["result"]["Q_S"]==row["Q_S_Byte"]==row["U"]*row["K"]
        assert src["result"]["Q_R"]==row["Q_R_Byte"]==row["N"]*row["K"]
        close(row["RI"],row["U"]/row["N"])
        counts["shared_tableIIa_cases"]+=1
    qkv=read_json(T2/"table_IIb/04_crosscheck/data/results.json")
    qkvlookup={r["case_id"]:r for r in qkv["cases"]}
    maps={m["model_id"]:m for m in s["qkv_tile_mappings"]}
    for w in s["qkv_mapped_workloads"]:
        src=qkvlookup[w["case_id"]]
        d,n=src["parameters"]["D"],src["parameters"]["N_proj"]
        m=maps[w["model_id"]]
        assert d%128==0 and n%128==0
        assert m["m_K"]==d//128 and m["m_N"]==n//128
        assert m["tile_count"]==d*n//(128**2)
        assert w["Q_S_Byte"]==src["result"]["Q_S"]==w["U"]*d
        assert w["Q_R_Byte"]==src["result"]["Q_R"]==d*n
        assert w["native_accumulated_Q_S_Byte"]==w["U"]*128*m["tile_count"]
        assert w["native_accumulated_Q_R_Byte"]==d*n
        counts["shared_qkv_workload_states"]+=1
    for m in maps.values():
        for row in m["scenarios"]:
            t=truth[(row["case_id"],row["profile"])]
            assert t["N"]==t["K"]==128
            close(row["rho_effective_MB_per_s"],t["rho"]/m["m_N"])
            close(row["tau_effective_MB_per_s"],t["tau"])
            close(row["RI_star_effective"],t["U_star"]/m["N_proj"])
            close(row["T_R_all_tiles_ns"],m["tile_count"]*t["load"])
            close(row["streaming_ns_per_model_vector"],m["tile_count"]*t["delta"])
            counts["shared_qkv_mapped_scenarios"]+=1
    a=read_json(T3/"01_hardware_overlay/plotted_data.json")
    ap={(r["case_id"],r["profile"]):r for r in a["points"]}
    assert set(ap)==set(truth)
    assert a["demand_U"]==[1,128,1024,131072]
    for key,p in ap.items():
        t=truth[key]
        close(p["x_tau_MB_per_s"],t["tau"])
        close(p["y_sigma_MB_per_s"],t["sigma"])
        close(p["U_star"],t["U_star"])
        assert p["at_U128"]==status(128,t["U_star"])
        counts["A_points"]+=1
    for circle in a["circles"]:
        cid=circle["case_id"]
        pair=[]
        for profile in ["short","long","reference"]:
            t=truth[(cid,profile)]
            pair.append([math.log10(t["tau"]),math.log10(t["sigma"])])
        c=circle["center_log10"]; r=circle["radius_decades"]
        ds=[math.dist(c,p) for p in pair]
        close(ds[0],r);close(ds[1],r);assert ds[2]<=r+1e-12
        mid=[(x+y)/2 for x,y in zip(pair[0],pair[1])]
        chord=[x-y for x,y in zip(pair[1],pair[0])]
        denom=sum(x*x for x in chord)
        scale=sum((p-mm)*ch for p,mm,ch in zip(pair[2],mid,chord))/denom
        expected=[p-scale*ch for p,ch in zip(pair[2],chord)]
        close(c[0],expected[0]);close(c[1],expected[1])
        counts["A_circles"]+=1
    c=read_csv(T3/"03_reuse_threshold/data/plotted_thresholds.csv")
    assert len(c)==30
    c_lookup={(r["case_id"],r["profile"]):r for r in c}
    for key,row in c_lookup.items():
        t=truth[key]
        close(row["U_star"],t["U_star"])
        for u in [1,128,1024,131072]:
            assert row[f"at_U_{u}"]==status(u,t["U_star"])
            if u==128: assert row[f"at_U_{u}"]==ap[key]["at_U128"]
            counts["AC_classifications"]+=1
        counts["C_thresholds"]+=1
    d=read_csv(T3/"04_normalized_response/data/scan_points.csv")
    for row in d:
        t=truth[(row["case_id"],row["profile"])]
        u=float(row["U"])
        y=min(t["rho"],t["tau"]*u/t["N"])/t["rho"]
        close(row["P_bound_over_rho"],y)
        close(row["P_bound_MB_per_s"],y*t["rho"])
        assert row["classification"]==status(u,t["U_star"])
        assert int(u)==ii_lookup[row["scan_case_id"]]["U"]
        if int(u) in [1,128,1024,131072]:
            assert row["classification"]==c_lookup[(row["case_id"],row["profile"])][f"at_U_{int(u)}"]
        counts["D_scan_points"]+=1
    curves=read_csv(T3/"04_normalized_response/data/curve_points.csv")
    knees=set()
    for row in curves:
        t=truth[(row["case_id"],"reference")]
        u=float(row["U"])
        close(row["P_bound_over_rho"],min(1,u*t["delta"]/t["load"]))
        if math.isclose(u,t["U_star"],rel_tol=1e-12):knees.add(row["case_id"])
        counts["D_curve_points"]+=1
    assert len(knees)==3
    import pypdfium2 as pdfium
    figures={"A":T3/"01_hardware_overlay/figure.pdf",
             "C":T3/"03_reuse_threshold/output/figure.pdf",
             "D":T3/"04_normalized_response/output/figure.pdf"}
    sizes={}
    for label,path in figures.items():
        doc=pdfium.PdfDocument(str(path))
        page=doc[0]
        sizes[label]=[float(page.get_width())/72,float(page.get_height())/72]
        assert math.isclose(sizes[label][0],7.16,rel_tol=1e-7)
    result={"status":"PASS", "reviewer_role":"B/E author independently reviews interface and A/C/D; no claim of independent self-review",
            "independent_expectations":"Original Task I native mapping JSON + accepted Task I points CSV; original Task II JSON; no author/shared computational functions imported",
            "counts":counts,"pdf_size_in":sizes,
            "focused_cases":{"MRAM_U128_typical_ratio":128/truth[("06_mram","reference")]["U_star"],
                             "MRAM_U128_profiles":{p:status(128,truth[("06_mram",p)]["U_star"]) for p in ["short","reference","long"]},
                             "NOR_U128K_profiles":{p:status(131072,truth[("03_nor_2d",p)]["U_star"]) for p in ["short","reference","long"]}},
            "visual_review":{"A":"actual PNG viewed: native sigma axis, paired circles and four U lines, readable labels",
                             "C":"actual PNG viewed: categorical marker offsets only; no Ustar shift; paired crossing clear",
                             "D":"actual PNG viewed: all six finite U states; near-threshold MRAM is explained in caption; normalized label clear"},
            "findings":[],"scope":"Native full-load reference; only 128x128 shapes are direct II(a) matches. QKV serial complete-tile resource mapping verified separately; no append/FFN inference."}
    (HERE/"independent_ACD.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"PASS","counts":counts,"pdf_size_in":sizes},ensure_ascii=False))


if __name__=="__main__":main()

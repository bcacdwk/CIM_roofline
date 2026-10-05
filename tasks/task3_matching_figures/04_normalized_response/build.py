#!/usr/bin/env python3
"""Candidate D: normalized native-service upper bounds, exact shared U*."""
import sys
sys.dont_write_bytecode=True
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent / "shared"))
from interface import load_data, normalized_bound, classify
from style import apply_style, save_figure, COLORS, LABELS, MARKERS, INK, MUTED, GRID, DOUBLE_COLUMN_IN

CASES=("06_mram","04_nand_3d","03_nor_2d")


def main():
    data=load_data()
    hw={r["case_id"]:r for r in data["hardware"] if r["profile"]=="reference"}
    scan=[r for r in data["table_IIa_finite"] if r["N"]==128 and r["K"]==128]
    scan=sorted(scan,key=lambda r:r["U"])
    apply_style(8)
    fig,axes=plt.subplots(1,3,figsize=(DOUBLE_COLUMN_IN,2.60),sharex=True,sharey=True)
    fig.subplots_adjust(left=.081,right=.985,bottom=.255,top=.735,wspace=.12)
    fig.text(.025,.965,"D  |  How reuse approaches each streaming ceiling",fontsize=10,weight="semibold",va="top")
    fig.text(.081,.855,r"Typical paired scenarios:  $P_{\rm bound}/\rho = \min(1, U/U^*)$",fontsize=8)
    fig.text(.081,.797,r"Filled: Table II(a) U scan  ·  Open: balance $U^*$",fontsize=7.5,color=MUTED)
    records=[]
    curves=[]
    for i,(ax,cid) in enumerate(zip(axes,CASES)):
        row=hw[cid]
        threshold=row["U_star"]
        us=np.unique(np.r_[np.logspace(0,np.log10(1048576),350), threshold, [r["U"] for r in scan]])
        response=np.minimum(1,us/threshold)
        color=COLORS[cid]
        ax.set_xscale("log")
        ax.set_xlim(.8,1400000)
        ax.set_ylim(-.045,1.14)
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        ax.grid(axis="y",color=GRID,lw=.6)
        ax.axhline(1,color="#b6c1ca",lw=.65,ls=(0,(2,2)),zorder=1)
        ax.axvline(threshold,color=color,ls=(0,(3,2)),lw=.8,alpha=.7,zorder=1)
        ax.plot(us,response,color=color,lw=1.8,zorder=3)
        ax.scatter([r["U"] for r in scan],[normalized_bound(r["U"],threshold) for r in scan],
                   color=color,marker=MARKERS[cid],s=25,edgecolors="white",linewidths=.5,zorder=5)
        ax.scatter([threshold],[1],s=24,marker=MARKERS[cid],facecolors="white",edgecolors=color,linewidths=.9,zorder=6)
        ax.text(.025,.98,LABELS[cid],transform=ax.transAxes,color=color,fontsize=8.2,weight="semibold",va="top")
        ax.text(.97 if i == 0 else .025, .62 if i == 0 else .73,f"$U^*$ = {threshold:,.1f}" if threshold<1000 else f"$U^*$ = {threshold:,.0f}",
                transform=ax.transAxes,ha="right" if i == 0 else "left",fontsize=7.7,color=color)
        ax.text(.97 if i == 0 else .025, .45 if i == 0 else .59,rf"$\rho$ = {row['rho_MB_per_s']:.2f} MB/s",transform=ax.transAxes,
                ha="right" if i == 0 else "left",fontsize=7.0,color=MUTED)
        ax.set_xticks([1,128,1024,131072,1048576])
        ax.set_xticklabels(["1","128","1K","128K","1M"],fontsize=6.8)
        ax.tick_params(axis="x",which="minor",length=0)
        ax.set_yticks([0,.5,1]); ax.set_yticklabels(["0","0.5","1.0"])
        for r in scan:
            records.append({"case_id":cid,"profile":"reference","K_native":row["K"],"N_native":row["N"],
                            "U_star":threshold,"U":r["U"],"P_bound_over_rho":normalized_bound(r["U"],threshold),
                            "P_bound_MB_per_s":row["rho_MB_per_s"]*normalized_bound(r["U"],threshold),
                            "classification":classify(r["U"],threshold),"scan_case_id":r["case_id"],
                            "scan_source":r["source"],"hardware_source":row["source_result"]})
        for u,y in zip(us,response): curves.append({"case_id":cid,"U":u,"P_bound_over_rho":y})
    axes[0].set_ylabel(r"Reference upper bound $P_{\rm bound}/\rho$",labelpad=7)
    fig.text(.525,.102,"Reuse U (vectors / full native load)",ha="center",fontsize=8)
    fig.text(.525,.027,"Equal normalized plateaus have different absolute streaming ceilings.",ha="center",fontsize=7.5,color=MUTED)
    save_figure(fig,HERE/"output"/"figure")
    plt.close(fig)
    (HERE/"data").mkdir(exist_ok=True)
    for name,rs in [("scan_points.csv",records),("curve_points.csv",curves)]:
        with (HERE/"data"/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
    checks={"interface":"../shared/data.json","formula":"min(1, U/U_star)","figure_inches":[DOUBLE_COLUMN_IN,2.60],
            "native_service_scope":data["boundary"],"scan_values":[r["U"] for r in scan],
            "selected_hardware":list(CASES),"threshold_checks":[]}
    for cid in CASES:
        row=hw[cid]; t=row["U_star"]
        checks["threshold_checks"].append({"case_id":cid,"U_star":t,"at_0.999_Ustar":normalized_bound(.999*t,t),
               "at_Ustar":normalized_bound(t,t),"at_1.001_Ustar":normalized_bound(1.001*t,t),
               "classifications":[classify(v*t,t) for v in [.999,1,1.001]]})
    (HERE/"data"/"validation.json").write_text(json.dumps(checks,indent=2)+"\n")

if __name__=="__main__":
    main()

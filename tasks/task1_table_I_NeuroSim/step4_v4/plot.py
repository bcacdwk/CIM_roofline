#!/usr/bin/env python3
"""Render the nine Step 4 V4 model points from RUN/summary.json only.

Usage: /opt/anaconda3/bin/python plot.py /absolute/local/run
Outputs PNG, SVG and auditable source/geometry records under RUN/figures.
No model calculation, parameter change, coordinate scaling, or interpolation
of additional model scenarios is performed here. Circle paths are geometric
illustrations in log10 coordinate space, not additional model data.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import textwrap

sys.dont_write_bytecode = True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import numpy as np

CASES = ("ns_sram_acim", "ns_sram_dcim", "ns_rram_1t1r")
SCENARIOS = ("optimistic", "reference", "pessimistic")
TEMPERATURES = dict(zip(SCENARIOS, (300, 350, 400)))
STYLES = {
    "ns_sram_acim": dict(name="SRAM ACIM", code="A", color="#3176A7",
        note="Analog transfer and 256-row read stability unverified. Nominal 9-bit code is not ENOB."),
    "ns_sram_dcim": dict(name="SRAM DCIM", code="D", color="#C46B27",
        note="Exact nominal digital mapping. Native SRAM/clock timing abstraction; no SPICE signoff."),
    "ns_rram_1t1r": dict(name="1T1R RRAM", code="R", color="#38866B",
        note="Segmented, approximate Q4 output. Stiff read rail and successful bounded program-verify assumed; no ENOB claim."),
}
MARKERS = {"optimistic": "^", "reference": "o", "pessimistic": "s"}
SIZES = {"optimistic": 49, "reference": 119, "pessimistic": 43}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.labelsize": 11, "axes.titlesize": 14,
    "svg.fonttype": "none", "savefig.facecolor": "white",
    "axes.unicode_minus": True,
})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def three_sig(value):
    exponent = math.floor(math.log10(abs(value))) if value else 0
    return format(value, ".2e") if exponent >= 3 or exponent < -3 else format(value, f".{max(0, 2-exponent)}f")


def load_summary(run):
    source = run / "summary.json"
    raw = source.read_bytes()
    summary = json.loads(raw)
    rows = summary["case_results"]
    require(len(rows) == 9, "Expected exactly nine actual points (three cases × three scenarios).")
    require({r["case_id"] for r in rows} == set(CASES), "Unexpected or missing case IDs.")
    keys = [(r["case_id"], r["scenario"]) for r in rows]
    require(len(set(keys)) == 9, "Duplicated case/scenario pair.")
    require(set(keys) == set(itertools.product(CASES, SCENARIOS)), "Incomplete paired scenarios.")
    require(len({r["paired_id"] for r in rows}) == 9, "Duplicate paired_id.")
    groups = {c: {r["scenario"]: r for r in rows if r["case_id"] == c} for c in CASES}
    definition = summary["scenario_definition"]
    require(all(definition["scenarios"][s]["temperature_K"] == TEMPERATURES[s] for s in SCENARIOS),
            "Declared scenario temperatures differ from the actual paired points.")
    fixed_fields = ("backend", "backend_sha", "technode_nm", "roadmap", "K", "N", "input_bits", "weight_bits",
                    "physical_rows", "physical_cols", "B_S_Byte", "B_R_Byte", "banks", "adc_count",
                    "output_bits", "fractional_output_bits")
    fixed_checks = []
    for case, group in groups.items():
        checked = []
        for key in fixed_fields:
            if any(key in r for r in group.values()):
                require(all(key in r for r in group.values()), f"Inconsistent fixed-field presence: {case} {key}")
                require(all(r[key] == group["reference"][key] for r in group.values()),
                        f"Architecture field changes across the paired scenarios: {case} {key}")
                checked.append(key)
        fixed_checks.append({"case_id": case, "fixed_architecture_fields_checked": checked, "passed": True})
    checks = []
    for r in rows:
        for key in ("delta_S_ns", "T_R_ns", "rho_MB_per_s", "tau_MB_per_s", "RI_star", "U_star"):
            require(isinstance(r[key], (int, float)) and math.isfinite(r[key]) and r[key] > 0,
                    f"Invalid positive finite {key}: {r['paired_id']}")
        require(r["temperature_K"] == TEMPERATURES[r["scenario"]], "Scenario temperature mismatch.")
        require(bool(r["status"]) and bool(r["qualification"]), "Missing model qualification.")
        require(str(r["status"]).startswith("conditional"), "All V4 points must retain conditional status.")
        require(math.isclose(r["RI_star"], r["rho_MB_per_s"] / r["tau_MB_per_s"], rel_tol=2e-10),
                f"RI* mismatch: {r['paired_id']}")
        require(math.isclose(r["U_star"], r["T_R_ns"] / r["delta_S_ns"], rel_tol=2e-10),
                f"U* mismatch: {r['paired_id']}")
        if "B_S_Byte" in r and "B_R_Byte" in r:
            require(math.isclose(r["rho_MB_per_s"], 1000*r["B_S_Byte"]/r["delta_S_ns"], rel_tol=2e-10),
                    f"Streaming payload/service mismatch: {r['paired_id']}")
            require(math.isclose(r["tau_MB_per_s"], 1000*r["B_R_Byte"]/r["T_R_ns"], rel_tol=2e-10),
                    f"Resident payload/service mismatch: {r['paired_id']}")
        checks.append({"paired_id": r["paired_id"], "numeric_identity_checks": "pass"})
    ordered = [groups[c][s] for c in CASES for s in SCENARIOS]
    return summary, ordered, groups, {
        "source_summary": str(source), "source_summary_sha256": hashlib.sha256(raw).hexdigest(),
        "nine_unique_actual_records": True, "point_identity_checks": checks,
        "fixed_architecture_checks": fixed_checks,
        "source_coordinates_modified": False, "synthetic_model_points": 0,
    }


def xy_log(row):
    return np.log10([row["tau_MB_per_s"], row["rho_MB_per_s"]])


def minimal_circle(points):
    """Exact finite candidate search for at most three log-space points."""
    candidates = [(p.copy(), 0.0) for p in points]
    for a, b in itertools.combinations(points, 2):
        c = (a + b)/2
        candidates.append((c, float(np.linalg.norm(a-c))))
    a, b, p = points
    mat = 2*np.vstack((b-a, p-a))
    if abs(float(np.linalg.det(mat))) > 1e-15:
        c = np.linalg.solve(mat, np.array([b@b-a@a, p@p-a@a]))
        candidates.append((c, float(np.linalg.norm(a-c))))
    valid = [(c, r) for c, r in candidates if all(np.linalg.norm(v-c) <= r+1e-11 for v in points)]
    require(bool(valid), "Failed to construct enclosing geometry.")
    return min(valid, key=lambda cr: cr[1])


def circle_for(case, group):
    a, b, p = [xy_log(group[s]) for s in ("optimistic", "pessimistic", "reference")]
    mid, chord = (a+b)/2, b-a
    chord2 = float(chord@chord)
    reason = None
    if chord2 <= 1e-24:
        original = {"defined": False, "center_log10": None, "radius_decades": None,
                    "reference_inside": None, "reason": "coincident_or_numerically_degenerate_endpoints"}
        reason = original["reason"]
    else:
        c = p - float((p-mid)@chord)/chord2*chord
        r = float(np.linalg.norm(a-c))
        offset = float(np.linalg.norm(p-c))
        original = {"defined": True, "center_log10": c.tolist(), "radius_decades": r,
                    "reference_distance_decades": offset, "reference_inside": bool(offset <= r+1e-11),
                    "endpoint_radius_error_decades": abs(float(np.linalg.norm(b-c))-r),
                    "perpendicular_bisector_dot_residual": float((c-mid)@chord),
                    "projection_cross_residual": float(np.linalg.det(np.vstack((p-c, chord))))}
        require(original["endpoint_radius_error_decades"] < 1e-10, "Unequal original endpoint radii.")
        require(abs(original["perpendicular_bisector_dot_residual"]) < 1e-10, "Bisector check failed.")
        require(abs(original["projection_cross_residual"]) < 1e-10, "Projection check failed.")
        if not original["reference_inside"]:
            reason = "reference_outside_projected_center_circle"
    if reason:
        c, r = minimal_circle([a, b, p])
        rule = "minimum_enclosing_point" if r <= 1e-12 else "minimum_enclosing_circle"
    else:
        rule = "reference_projection_onto_endpoint_perpendicular_bisector"
    distances = {s: float(np.linalg.norm(xy_log(group[s])-c)) for s in SCENARIOS}
    require(all(d <= r+1e-10 for d in distances.values()), "Displayed geometry does not contain all points.")
    return {"case_id": case, "coordinate_space": "log10(tau_MB_per_s), log10(rho_MB_per_s)",
            "original": original, "fallback_reason": reason, "display_rule": rule,
            "center_log10": c.tolist(), "radius_decades": r,
            "point_distances_decades": distances, "reference_inside": distances["reference"] <= r+1e-10,
            "all_points_inside": True,
            "endpoints_on_circumference": all(abs(distances[s]-r) <= 1e-10 for s in ("optimistic", "pessimistic")),
            "points_log10": {s: xy_log(group[s]).tolist() for s in SCENARIOS},
            "paired_points": [{"paired_id": group[s]["paired_id"], "scenario": s,
                               "log10_tau": float(xy_log(group[s])[0]),
                               "log10_rho": float(xy_log(group[s])[1])} for s in SCENARIOS],
            "interpretation": "Finite paired scenario illustration only; not confidence bounds or a feasible region."}


def overlaps(a, b, padding=0):
    return not (a.x1+padding <= b.x0 or b.x1+padding <= a.x0 or
                a.y1+padding <= b.y0 or b.y1+padding <= a.y0)


def contains(outer, inner, tol=0.2):
    return (inner.x0 >= outer.x0-tol and inner.y0 >= outer.y0-tol and
            inner.x1 <= outer.x1+tol and inner.y1 <= outer.y1+tol)


def text_checks(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inactive_tick_labels = set()
    for ax in fig.axes:
        for axis, limits in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
            for tick in axis.get_major_ticks()+axis.get_minor_ticks():
                # LogLocator owns labels beyond the view interval that Axis.draw
                # does not render. Do not confuse these with clipped visible text.
                if not ax.axison or not min(limits) <= tick.get_loc() <= max(limits):
                    inactive_tick_labels.update((id(tick.label1), id(tick.label2)))
    entries = []
    for item in fig.findobj(match=Text):
        if id(item) not in inactive_tick_labels and item.get_visible() and item.get_text().strip():
            box = Text.get_window_extent(item, renderer)
            if box.width > 0 and box.height > 0:
                entries.append((item.get_text(), box))
    clipped = [t for t, b in entries if not contains(fig.bbox, b)]
    collisions = [[ta, tb] for i, (ta, ba) in enumerate(entries)
                  for tb, bb in entries[i+1:] if overlaps(ba, bb, -0.25)]
    require(not clipped, f"Text outside figure: {clipped}")
    require(not collisions, f"Text overlaps: {collisions}")
    return {"all_text_visible": True, "text_collision_count": 0, "checked_text_count": len(entries),
            "text_bounds_px": [{"text": t, "bounds": list(b.bounds)} for t, b in entries]}


def place_case_labels(fig, ax, rows, groups):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    point_boxes = []
    for row in rows:
        x, y = ax.transData.transform((row["tau_MB_per_s"], row["rho_MB_per_s"]))
        radius = math.sqrt(SIZES[row["scenario"]])*fig.dpi/72*0.7+3
        point_box = Bbox.from_extents(x-radius, y-radius, x+radius, y+radius)
        require(contains(ax.bbox, point_box, 0), f"Point marker exceeds axes: {row['paired_id']}")
        point_boxes.append(point_box)
    labels, boxes = [], []
    offsets = [(16, 22), (-16, 24), (16, -27), (-16, -27), (36, 0), (-36, 0),
               (25, 42), (-25, 42), (25, -45), (-25, -45), (60, 16), (-60, 16)]
    for case in CASES:
        row, style = groups[case]["reference"], STYLES[case]
        for dx, dy in offsets:
            ha = "left" if dx >= 0 else "right"
            label = ax.annotate(style["name"], (row["tau_MB_per_s"], row["rho_MB_per_s"]),
                xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                fontsize=10.5, fontweight="semibold", color=style["color"], zorder=8,
                bbox=dict(facecolor="white", alpha=.93, edgecolor="none", pad=2),
                arrowprops=dict(arrowstyle="-", lw=.65, color=style["color"], alpha=.6,
                                shrinkA=4, shrinkB=8))
            # Annotation extents include the connector; assess the text separately.
            label.update_positions(renderer)
            box = Text.get_window_extent(label, renderer).expanded(1.03, 1.08)
            if contains(ax.bbox, box, 0) and not any(overlaps(box, b, 4) for b in point_boxes+boxes):
                labels.append(label)
                boxes.append(box)
                break
            label.remove()
        else:
            raise ValueError(f"No collision-free placement for {case}.")
    return {"case_labels_within_axes": True, "case_label_to_point_collisions": 0,
            "all_point_markers_fully_visible": True,
            "case_label_count": len(labels)}


def bounds_for(rows, specs):
    coords = [xy_log(row) for row in rows]
    for spec in specs:
        c, r = np.array(spec["center_log10"]), spec["radius_decades"]
        coords.extend((c-r, c+r))
    values = np.array(coords)
    lo, hi = values.min(axis=0), values.max(axis=0)
    padding = np.maximum(.30, .13*(hi-lo))
    return lo-padding, hi+padding


def draw_plot(out, rows, groups, specs, with_circles):
    fig = plt.figure(figsize=(12.8, 8.7), dpi=180, facecolor="white")
    ax = fig.add_axes([.075, .205, .59, .68])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_aspect("equal", adjustable="box")
    lo, hi = bounds_for(rows, specs)  # Identical limits across the paired figures.
    ax.set_xlim(10**lo[0], 10**hi[0])
    ax.set_ylim(10**lo[1], 10**hi[1])
    ax.set_xlabel(r"Resident update capability $\tau$ (MB/s)", labelpad=9)
    ax.set_ylabel(r"Streaming input capability $\rho$ (MB/s)", labelpad=9)
    ax.grid(which="major", color="#DEE3E7", linewidth=.75, zorder=0)
    ax.grid(which="minor", color="#EEF1F3", linewidth=.4, zorder=0)
    ax.tick_params(which="both", direction="out", labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#A8B1B9")
        spine.set_linewidth(.7)
    diag_lo, diag_hi = max(lo), min(hi)
    if diag_hi > diag_lo:
        ax.plot(10**np.array([diag_lo, diag_hi]), 10**np.array([diag_lo, diag_hi]),
                color="#9DA5AC", lw=.85, ls=(0, (4, 4)), zorder=1)
    for spec in specs:
        case, c, radius = spec["case_id"], np.array(spec["center_log10"]), spec["radius_decades"]
        if with_circles and radius > 1e-12:
            theta = np.linspace(0, 2*np.pi, 721)
            arc = c[:, None] + radius*np.array([np.cos(theta), np.sin(theta)])
            xx, yy = 10**arc
            ax.fill(xx, yy, color=STYLES[case]["color"], alpha=.10, zorder=2)
            ax.plot(xx, yy, color=STYLES[case]["color"], lw=1.15, ls=(0, (4, 3)), alpha=.85, zorder=3)
        group, style = groups[case], STYLES[case]
        ax.plot([group[s]["tau_MB_per_s"] for s in SCENARIOS],
                [group[s]["rho_MB_per_s"] for s in SCENARIOS], color=style["color"],
                alpha=.8, linewidth=1.25, zorder=4)
        for s in SCENARIOS:
            row = group[s]
            ax.scatter(row["tau_MB_per_s"], row["rho_MB_per_s"], s=SIZES[s], marker=MARKERS[s],
                       facecolor=style["color"], edgecolor="white", linewidth=.9, zorder=6 if s == "reference" else 5)
    title = "Paired thermal design scenarios" + (" · log-space circles" if with_circles else "")
    fig.text(.075, .952, title, fontsize=18, fontweight="semibold", color="#1E303F", va="top")
    fig.text(.075, .912, "Three architectures · nine conditional model points · fixed architecture within each case",
             fontsize=10.7, color="#566674", va="top")
    fig.text(.715, .862, "SCENARIO KEY", fontsize=10, fontweight="bold", color="#566674", va="top")
    legend_handles = [Line2D([], [], ls="none", marker=MARKERS[s], color="#50616D",
                            markeredgecolor="white", markersize=10 if s == "reference" else 7,
                            label=f"{TEMPERATURES[s]} K  " + ("warm reference" if s == "reference" else s)) for s in SCENARIOS]
    legend_handles.append(Line2D([], [], color="#9DA5AC", lw=.9, ls="--", label=r"$RI^{*}=\rho/\tau=1$"))
    fig.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(.704, .832), frameon=False,
               handlelength=1.7, labelspacing=.65, fontsize=10, borderpad=0)
    yy = .636
    for case in CASES:
        style = STYLES[case]
        fig.text(.715, yy, style["name"], fontsize=11, fontweight="bold", color=style["color"], va="top")
        note = textwrap.fill(style["note"], width=34)
        fig.text(.715, yy-.031, note, fontsize=9.5, color="#44515D", linespacing=1.35, va="top")
        yy -= .031 + (note.count("\n")+1)*.020 + .030
    fig.text(.075, .118, "300 / 350 / 400 K are finite engineering design scenarios; 350 K is a warm reference, not a statistical median.",
             fontsize=10, color="#44515D", va="top")
    fig.text(.075, .086, "Native automatic sizing is retained; these are not fixed-chip PVT or statistical bounds. Decimal MB/s = 10⁶ Byte/s.",
             fontsize=10, color="#44515D", va="top")
    foot = ("Circles illustrate only the three paired scenarios; they are not confidence intervals or regions of feasible combinations."
            if with_circles else "Connecting lines identify paired scenarios within each case; points retain the source summary coordinates.")
    fig.text(.075, .054, foot, fontsize=10, color="#44515D", va="top")
    label_report = place_case_labels(fig, ax, rows, groups)
    fig.canvas.draw()
    unit = ax.transData.transform([[1, 1], [10, 1], [1, 10]])
    dx = float(np.linalg.norm(unit[1]-unit[0]))
    dy = float(np.linalg.norm(unit[2]-unit[0]))
    require(math.isclose(dx, dy, rel_tol=1e-10), "Unequal screen length per log decade.")
    visibility = []
    for spec in specs:
        c, r = np.array(spec["center_log10"]), spec["radius_decades"]
        visible = bool(np.all(c-r >= lo) and np.all(c+r <= hi))
        require(visible, "A full circle lies outside axis limits.")
        display = ax.transData.transform(10**np.array([c-r, c+r]))
        circle_box = Bbox.from_extents(*display[0], *display[1])
        require(contains(ax.bbox, circle_box, 0), "Circle display bounds exceed axes.")
        require(math.isclose(circle_box.width, circle_box.height, rel_tol=1e-10, abs_tol=1e-9),
                "Log-space circle is not circular on screen.")
        visibility.append({"case_id": spec["case_id"], "full_circle_visible": visible,
                           "display_circle_bounds_px": list(circle_box.bounds), "display_circular": True,
                           "point_enclosure": spec["all_points_inside"]})
    for row in rows:
        point = xy_log(row)
        require(bool(np.all(point > lo) and np.all(point < hi)), "Point outside plot limits.")
    report = {"x_axis": "tau_MB_per_s", "y_axis": "rho_MB_per_s", "units": "decimal MB/s",
              "x_limits_log10": [float(lo[0]), float(hi[0])], "y_limits_log10": [float(lo[1]), float(hi[1])],
              "x_limits_data": list(ax.get_xlim()), "y_limits_data": list(ax.get_ylim()),
              "axes_display_bounds_px": list(ax.bbox.bounds), "figure_dpi": fig.dpi,
              "figure_size_inches": list(fig.get_size_inches()),
              "pixels_per_x_decade": dx, "pixels_per_y_decade": dy, "equal_decade_screen_length": True,
              "RI_1_line_angle_degrees": math.degrees(math.atan2(dy, dx)), "all_points_visible": True,
              "circle_visibility": visibility, **label_report, **text_checks(fig)}
    stem = "rho_tau_circles" if with_circles else "rho_tau_pairs"
    for extension in ("png", "svg"):
        fig.savefig(out/f"{stem}.{extension}", dpi=180)
    plt.close(fig)
    return report


def draw_table(out, rows):
    fig = plt.figure(figsize=(14.4, 8.6), dpi=180, facecolor="white")
    fig.text(.055, .951, "Three-case paired scenario table", fontsize=18, fontweight="semibold", color="#1E303F", va="top")
    fig.text(.055, .908, "Conditional model estimates · values shown to three significant digits · full precision in plot_points.csv / .json",
             fontsize=10.5, color="#566674", va="top")
    ax = fig.add_axes([.055, .370, .89, .483])
    ax.axis("off")
    columns = ["Architecture", "Scenario", "T (K)", r"$\Delta_S$ (ns)", r"$T_R$ (ns)",
               r"$\rho$ (MB/s)", r"$\tau$ (MB/s)", r"$RI^{*}$", r"$U^{*}$"]
    fields = ("delta_S_ns", "T_R_ns", "rho_MB_per_s", "tau_MB_per_s", "RI_star", "U_star")
    body = [[STYLES[r["case_id"]]["name"], ("Warm reference" if r["scenario"] == "reference" else r["scenario"].capitalize()),
             str(r["temperature_K"]), *[three_sig(r[k]) for k in fields]] for r in rows]
    table = ax.table(cellText=body, colLabels=columns, cellLoc="center", colLoc="center", bbox=[0, 0, 1, 1],
                     colWidths=[.16, .155, .065, .105, .115, .11, .11, .085, .095])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_linewidth(1.4)
        if r == 0:
            cell.set_facecolor("#233D50")
            cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        else:
            row = rows[r-1]
            cell.set_facecolor("#E9F0F4" if row["scenario"] == "reference" else ("#F4F7F8" if (r-1)//3 % 2 == 0 else "#F8F6F2"))
            if c == 0:
                cell.get_text().set_color(STYLES[row["case_id"]]["color"])
                cell.get_text().set_fontweight("semibold")
            if row["scenario"] == "reference":
                cell.get_text().set_fontweight("semibold")
    yy = .319
    for case in CASES:
        style = STYLES[case]
        note = textwrap.fill(style["name"] + ": " + style["note"], width=145)
        fig.text(.055, yy, note, fontsize=10, color="#44515D", linespacing=1.25, va="top")
        yy -= .025*(note.count("\n")+1)+.014
    fig.text(.055, .126, "300 / 350 / 400 K: finite fixed-architecture design scenarios with native automatic sizing. The 350 K warm reference is not a median.",
             fontsize=10, color="#44515D", va="top")
    fig.text(.055, .091, r"Decimal MB/s = 10⁶ Byte/s. $RI^{*}=\rho/\tau$; $U^{*}=T_R/\Delta_S$. Qualifications and source fields are preserved in the machine-readable exports.",
             fontsize=10, color="#44515D", va="top")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    cell_checks = []
    for (r, c), cell in table.get_celld().items():
        fits = contains(cell.get_window_extent(renderer), cell.get_text().get_window_extent(renderer), 0)
        require(fits, f"Table text exceeds cell at {r},{c}.")
        cell_checks.append({"row": r, "column": c, "text_fits": True})
    report = {"display_significant_digits": 3, "all_cell_text_fits": True,
              "checked_cell_count": len(cell_checks), **text_checks(fig)}
    for extension in ("png", "svg"):
        fig.savefig(out/f"scenario_table.{extension}", dpi=180)
    plt.close(fig)
    return report


def main():
    require(len(sys.argv) == 2, "Usage: plot.py LOCAL_RUN_DIRECTORY")
    run = Path(sys.argv[1]).expanduser().resolve(strict=True)
    require(run.is_dir(), "Argument must be a local run directory.")
    summary, rows, groups, provenance = load_summary(run)
    out = run/"figures"
    out.mkdir(exist_ok=True)
    specs = [circle_for(c, groups[c]) for c in CASES]
    record = {"schema": "step4-v4-plot-points.1", **provenance,
              "display_significant_digits": 3, "machine_precision": "unrounded source JSON numbers",
              "scenario_definition": summary["scenario_definition"], "case_results": rows}
    (out/"plot_points.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with (out/"plot_points.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})
    geometry = {"schema": "step4-v4-plot-geometry.1", **provenance,
                "renderer": {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             "matplotlib_version": matplotlib.__version__, "numpy_version": np.__version__},
                "circle_specs": specs, "scenario_definition": summary["scenario_definition"],
                "circle_rule": "c = p - dot(p-m,d)/dot(d,d) * d; m=(a+b)/2, d=b-a; r=norm(a-c).",
                "fallback_rule": "If endpoints are degenerate or reference is outside, use the minimum enclosing circle or point; retain original geometry and reason.",
                "interpretation": "Finite paired scenario illustration; not confidence bounds or a feasible region.",
                "figures": {"rho_tau_pairs": draw_plot(out, rows, groups, specs, False),
                            "rho_tau_circles": draw_plot(out, rows, groups, specs, True),
                            "scenario_table": draw_table(out, rows)},
                "visual_QA": "Programmatic geometry/text checks passed; human or image-view QA is a separate recorded step."}
    geometry["artifacts"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())
                              if p.suffix in (".png", ".svg", ".csv", ".json") and p.name != "geometry.json"}
    (out/"geometry.json").write_text(json.dumps(geometry, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
    print(f"PASS: nine unchanged model points; equal log-decade scales; full circles; collision-free labels. Outputs: {out}")


if __name__ == "__main__":
    main()

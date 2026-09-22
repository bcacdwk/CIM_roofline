#!/usr/bin/env python3
"""Final ten-point log-log plot: equal scales, complete frame, names and RI below."""
from __future__ import annotations

import csv
import json
import math
import sys

sys.dont_write_bytecode = True

from build_figures import COLORS, DATA, LABELS, MUTED, OUT, fmt, plt
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullLocator
import numpy as np

XLIMITS = (.0011, 6000)
YLIMITS = (.04, 60)
INCHES_PER_DECADE = 2.6
MARKER_AREA = 320
STEM = "rho_tau_loglog"


def render_final(groups, source_report):
    """Return the figure for the combined review PDF; write final plot and data."""
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    rows = [group["reference"] for group in groups]
    assert len(rows) == 10 and all(row["recommended"] for row in rows)
    sx, sy = [math.log10(high / low) for low, high in (XLIMITS, YLIMITS)]
    width, height = sx * INCHES_PER_DECADE, sy * INCHES_PER_DECADE
    left, bottom, right, top = 1.05, .78, .4, .9
    fw, fh = width + left + right, height + bottom + top
    fig = plt.figure(figsize=(fw, fh), facecolor="white")
    ax = fig.add_axes([left / fw, bottom / fh, width / fw, height / fh])
    ax.set(xscale="log", yscale="log", xlim=XLIMITS, ylim=YLIMITS)
    ax.set_aspect("equal", adjustable="box")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#82909c")
        spine.set_linewidth(1.1)
    ax.set_xlabel(r"Resident throughput $\tau$ [MB/s]", fontsize=14, labelpad=12)
    ax.set_ylabel(r"Streaming throughput $\rho$ [MB/s]", fontsize=14, labelpad=12)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(LogLocator(base=10, numticks=9))
        axis.set_major_formatter(LogFormatterMathtext(base=10))
        axis.set_minor_locator(NullLocator())
    ax.tick_params(labelsize=12.5, length=4.5, pad=6)
    ax.grid(color="#e3e9ee", lw=.8, zorder=0)
    xx = np.geomspace(*XLIMITS, 1000)
    ax.fill_between(xx, np.clip(xx, *YLIMITS), YLIMITS[1], color="#fbf8f3", zorder=0)
    ax.fill_between(xx, YLIMITS[0], np.clip(xx, *YLIMITS), color="#f3f8fb", zorder=0)
    for ratio in (.01, 1, 100):
        yy = ratio * xx
        inside = (yy >= YLIMITS[0]) & (yy <= YLIMITS[1])
        ax.plot(xx[inside], yy[inside], color="#28465e" if ratio == 1 else "#718594",
                lw=3.0 if ratio == 1 else 1.65,
                ls=(0, (7, 4)) if ratio == 1 else (0, (4, 4)), zorder=2)
    ax.text(.09, .85, r"$\rho>\tau$" + "\nRI > 1", transform=ax.transAxes,
            fontsize=15, color="#876337", va="center", ha="left", linespacing=1.5)
    ax.text(.91, .16, r"$\rho<\tau$" + "\nRI < 1", transform=ax.transAxes,
            fontsize=15, color="#426e8b", va="center", ha="right", linespacing=1.5)
    guide_texts = [
        ax.text(10, 15, r"$\rho=\tau$  (RI = 1)", rotation=45, rotation_mode="anchor",
                fontsize=16.5, weight="bold", color="#28465e",
                bbox=dict(facecolor="#fbf8f3", edgecolor="none", pad=2.0)),
        ax.text(.012, 1.7, r"$\mathrm{RI}=10^{2}$", rotation=45, rotation_mode="anchor",
                fontsize=13.2, weight="bold", color="#637b8d",
                bbox=dict(facecolor="#fbf8f3", edgecolor="none", pad=1.2)),
        ax.text(8, .11, r"$\mathrm{RI}=10^{-2}$", rotation=45, rotation_mode="anchor",
                fontsize=13.2, weight="bold", color="#637b8d",
                bbox=dict(facecolor="#f3f8fb", edgecolor="none", pad=1.2)),
    ]

    points, annotations, labels_by_case = [], [], []
    for i, row in enumerate(rows):
        points.append(ax.scatter(row["tau"], row["rho"], s=MARKER_AREA, c=COLORS[i],
                                 edgecolors="white", linewidths=1.25, zorder=6))
        anchor, dy = (row["tau"], row["rho"]), -13
        if i in (0, 1):
            # Both SRAM points have the same tau; stack their complete labels
            # under the pair in the same top/bottom order, without moving dots.
            anchor = (row["tau"], min(rows[0]["rho"], rows[1]["rho"]))
            dy = -13 if i == 1 else -57
        name = ax.annotate(LABELS[i], anchor, xytext=(0, dy), textcoords="offset points",
                           ha="center", va="top", fontsize=12.6, color=COLORS[i],
                           weight="semibold", zorder=8,
                           bbox=dict(facecolor="white", edgecolor="none", alpha=.94, pad=.3))
        ratio = ax.annotate(f"RI = {fmt(row['RI_star'])}", anchor, xytext=(0, dy - 17),
                            textcoords="offset points", ha="center", va="top",
                            fontsize=11.3, color=COLORS[i], zorder=8,
                            bbox=dict(facecolor="white", edgecolor="none", alpha=.94, pad=.25))
        annotations.extend([name, ratio])
        labels_by_case.append((name, ratio))

    fig.text(left / fw, (bottom + height + .48) / fh,
             "Typical streaming and resident throughput", fontsize=22, weight="bold")
    fig.text(left / fw, (bottom + height + .18) / fh,
             "Ten CIM reference designs  ·  RI = ρ/τ",
             fontsize=12, color=MUTED)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = ax.get_window_extent()
    assert math.isclose(bounds.width / sx, bounds.height / sy, rel_tol=1e-8)
    p0, p1 = ax.transData.transform([[.1, .1], [1, 1]])
    angle = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    assert math.isclose(angle, 45, abs_tol=1e-8)
    dot_radius = (math.sqrt(MARKER_AREA) + 1.25) / 2 * fig.dpi / 72
    for point, row, (name, ratio) in zip(points, rows, labels_by_case):
        np.testing.assert_array_equal(point.get_offsets().data[0], [row["tau"], row["rho"]])
        xy = ax.transData.transform((row["tau"], row["rho"]))
        assert bounds.contains(xy[0] - dot_radius, xy[1] - dot_radius)
        assert bounds.contains(xy[0] + dot_radius, xy[1] + dot_radius)
        assert name.get_window_extent(renderer).y1 < xy[1] - dot_radius
        assert ratio.get_window_extent(renderer).y1 < name.get_window_extent(renderer).y0
        assert math.isclose(row["RI_star"], row["rho"] / row["tau"], rel_tol=1e-12)
    for i, label in enumerate(annotations):
        assert label.arrow_patch is None
        box = label.get_window_extent(renderer)
        assert bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1), label.get_text()
        for other in annotations[i + 1:]:
            assert not box.overlaps(other.get_window_extent(renderer)), (label.get_text(), other.get_text())
        for row in rows:
            xy = ax.transData.transform((row["tau"], row["rho"]))
            distance = math.hypot(xy[0] - np.clip(xy[0], box.x0, box.x1),
                                  xy[1] - np.clip(xy[1], box.y0, box.y1))
            assert distance > dot_radius, f"Label covers point: {label.get_text()} / {row['case_id']}"
    for label in guide_texts:
        box = label.get_window_extent(renderer)
        assert bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1), label.get_text()
    assert all(spine.get_visible() for spine in ax.spines.values())

    for extension in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{STEM}.{extension}", dpi=220, bbox_inches="tight", pad_inches=.14)
    with (DATA / f"{STEM}_points.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["case_id", "technology", "rho", "tau", "RI_star", "source_result"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in rows)
    report = {
        "all_passed": True, "point_count": 10, "selection": "recommended reference only",
        "x": {"metric": "tau", "label": "Resident throughput", "scale": "log10", "limits": XLIMITS},
        "y": {"metric": "rho", "label": "Streaming throughput", "scale": "log10", "limits": YLIMITS},
        "title": "Typical streaming and resident throughput", "footer_notes": False,
        "plot_width_over_height": sx / sy, "inches_per_decade": INCHES_PER_DECADE,
        "equality_line_angle_degrees": angle, "same_scale_per_decade_verified": True,
        "all_ten_points_and_labels_contained": True, "unmodified_coordinates_verified": True,
        "label_content": "Technology name, then RI = rho/tau on the next line; RI denotes RI_star",
        "no_label_leaders_verified": True, "labels_below_points_verified": True,
        "no_overlapping_labels_or_label_dot_collisions": True, "all_four_spines_visible": True,
        "marker_area_points_squared": MARKER_AREA,
        "guide_lines": {"1": {"linewidth": 3.0, "label_size": 16.5},
                        "0.01": {"linewidth": 1.65, "label_size": 13.2},
                        "100": {"linewidth": 1.65, "label_size": 13.2}},
        "source_checks_passed": source_report["all_passed"],
        "source_sha256": source_report["sha256"]["data/ten_case_results.json"],
    }
    (DATA / f"{STEM}_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: final log-log plot; all ten points and RI labels; equal scale and 45 degrees; four-sided frame; collision-free labels.")
    return fig


if __name__ == "__main__":
    # One command reproduces both final deliverables and their combined PDF.
    from build_figures import main
    main()

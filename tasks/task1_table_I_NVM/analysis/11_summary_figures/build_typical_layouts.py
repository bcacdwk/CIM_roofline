#!/usr/bin/env python3
"""Compare four rectangular log-log layouts with equal display scale per decade."""
from __future__ import annotations

import json
import math
import sys

sys.dont_write_bytecode = True

from build_figures import COLORS, DATA, LABELS, MUTED, OUT, load_and_validate, plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullLocator
import numpy as np

VARIANTS = [
    {"id": "A", "name": "More vertical context", "zh": "保留较多空白", "x": (1e-3, 1e4), "y": (1e-2, 1e3)},
    {"id": "B", "name": "Whole-decade crop", "zh": "整十倍边界", "x": (1e-3, 1e4), "y": (1e-2, 1e2)},
    {"id": "C", "name": "Compact crop", "zh": "紧凑裁剪", "x": (1e-3, 6000), "y": (.03, 80)},
    {"id": "D", "name": "Close to the edges", "zh": "贴边裁剪", "x": (.0011, 6000), "y": (.04, 60)},
]
INCHES_PER_DECADE = 2.0
MARKER_AREA = 200


def spans(variant):
    return [math.log10(high / low) for low, high in (variant["x"], variant["y"])]


def populate(ax, rows, variant, scale=1):
    xlimits, ylimits = variant["x"], variant["y"]
    ax.set(xscale="log", yscale="log", xlim=xlimits, ylim=ylimits)
    ax.set_aspect("equal", adjustable="box")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlabel(r"Resident update capacity $\tau$ [MB/s]", fontsize=13 * scale, labelpad=10 * scale)
    ax.set_ylabel(r"Input evaluation capacity $\rho$ [MB/s]", fontsize=13 * scale, labelpad=10 * scale)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(LogLocator(base=10, numticks=9))
        axis.set_major_formatter(LogFormatterMathtext(base=10))
        axis.set_minor_locator(NullLocator())
    ax.tick_params(labelsize=11.5 * scale, length=4 * scale, pad=5 * scale)
    ax.grid(color="#e3e9ee", lw=.75 * scale, zorder=0)
    xx = np.geomspace(*xlimits, 900)
    ax.fill_between(xx, np.clip(xx, *ylimits), ylimits[1], color="#fbf8f3", zorder=0)
    ax.fill_between(xx, ylimits[0], np.clip(xx, *ylimits), color="#f3f8fb", zorder=0)
    for ratio in (.01, 1, 100):
        yy = ratio * xx
        inside = (yy >= ylimits[0]) & (yy <= ylimits[1])
        ax.plot(xx[inside], yy[inside], color="#4b657b" if ratio == 1 else "#c5cfd8",
                lw=(1.6 if ratio == 1 else .9) * scale,
                ls=(0, (5, 4)) if ratio == 1 else (0, (3, 5)), zorder=2)
    ax.text(.09, .85, r"$\rho>\tau$" + "\n" + r"$\mathrm{RI}^{*}>1$",
            transform=ax.transAxes, fontsize=13 * scale, color="#947041",
            va="center", ha="left", linespacing=1.5)
    ax.text(.91, .16, r"$\rho<\tau$" + "\n" + r"$\mathrm{RI}^{*}<1$",
            transform=ax.transAxes, fontsize=13 * scale, color="#4a7795",
            va="center", ha="right", linespacing=1.5)
    ax.text(12, 18, r"$\rho=\tau$  ($\mathrm{RI}^{*}=1$)", rotation=45,
            rotation_mode="anchor", color="#4b657b", fontsize=10.3 * scale,
            bbox=dict(facecolor="#fbf8f3", edgecolor="none", pad=1.3 * scale))
    ax.text(.012, 1.7, r"$\mathrm{RI}^{*}=10^{2}$", rotation=45,
            rotation_mode="anchor", fontsize=9.3 * scale, color="#98a6b2")
    ax.text(8, .11, r"$\mathrm{RI}^{*}=10^{-2}$", rotation=45,
            rotation_mode="anchor", fontsize=9.3 * scale, color="#98a6b2")

    points, names = [], []
    for i, row in enumerate(rows):
        points.append(ax.scatter(row["tau"], row["rho"], s=MARKER_AREA * scale**2,
                                 c=COLORS[i], edgecolors="white", linewidths=1.15 * scale,
                                 zorder=6))
        anchor, dy = (row["tau"], row["rho"]), -13
        if i in (0, 1):
            anchor = (row["tau"], min(rows[0]["rho"], rows[1]["rho"]))
            dy = -13 if i == 1 else -32
        names.append(ax.annotate(LABELS[i], anchor, xytext=(0, dy * scale),
                                 textcoords="offset points", ha="center", va="top",
                                 fontsize=12.2 * scale, color=COLORS[i], weight="medium",
                                 bbox=dict(facecolor="white", edgecolor="none", alpha=.92, pad=.18 * scale),
                                 zorder=8))
    return points, names


def check_layout(fig, ax, rows, variant, artists, names, scale=1):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = ax.get_window_extent()
    sx, sy = spans(variant)
    assert math.isclose(bounds.width / sx, bounds.height / sy, rel_tol=1e-8)
    p0, p1 = ax.transData.transform([[.1, .1], [1, 1]])
    angle = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    assert math.isclose(angle, 45, abs_tol=1e-8)
    dot_radius = (math.sqrt(MARKER_AREA) + 1.15) * scale / 2 * fig.dpi / 72
    for point, row, name in zip(artists, rows, names):
        np.testing.assert_array_equal(point.get_offsets().data[0], [row["tau"], row["rho"]])
        assert variant["x"][0] <= row["tau"] <= variant["x"][1]
        assert variant["y"][0] <= row["rho"] <= variant["y"][1]
        assert name.arrow_patch is None
        text_box = name.get_window_extent(renderer)
        xy = ax.transData.transform((row["tau"], row["rho"]))
        assert bounds.contains(xy[0] - dot_radius, xy[1] - dot_radius)
        assert bounds.contains(xy[0] + dot_radius, xy[1] + dot_radius)
        assert text_box.y1 < xy[1] - dot_radius
        assert bounds.contains(text_box.x0, text_box.y0) and bounds.contains(text_box.x1, text_box.y1), name.get_text()
    for i, name in enumerate(names):
        box = name.get_window_extent(renderer)
        for other in names[i + 1:]:
            assert not box.overlaps(other.get_window_extent(renderer)), (name.get_text(), other.get_text())
        # Verify no technology name covers another technology's dot.
        for row in rows:
            xy = ax.transData.transform((row["tau"], row["rho"]))
            nearest_x = np.clip(xy[0], box.x0, box.x1)
            nearest_y = np.clip(xy[1], box.y0, box.y1)
            assert math.hypot(xy[0] - nearest_x, xy[1] - nearest_y) > dot_radius, name.get_text()
    data_sx = math.log10(max(row["tau"] for row in rows) / min(row["tau"] for row in rows))
    data_sy = math.log10(max(row["rho"] for row in rows) / min(row["rho"] for row in rows))
    return {
        **variant, "x_decades": sx, "y_decades": sy, "plot_width_over_height": sx / sy,
        "equality_line_angle_degrees": angle, "same_scale_per_decade_verified": True,
        "all_ten_points_and_labels_contained": True, "unmodified_coordinates_verified": True,
        "no_label_leaders_verified": True, "labels_below_points_verified": True,
        "no_overlapping_names_or_name_dot_collisions": True,
        "data_span_fraction_x": data_sx / sx, "data_span_fraction_y": data_sy / sy,
        "data_bounding_box_area_fraction": data_sx * data_sy / (sx * sy),
    }


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    _, groups, source_report = load_and_validate()
    rows = [g["reference"] for g in groups]
    assert len(rows) == 10 and len({r["case_id"] for r in rows}) == 10
    figures, reports = [], []
    for variant in VARIANTS:
        sx, sy = spans(variant)
        width, height = sx * INCHES_PER_DECADE, sy * INCHES_PER_DECADE
        left, bottom, right, top = 1.0, 1.0, .35, .88
        fw, fh = width + left + right, height + bottom + top
        fig = plt.figure(figsize=(fw, fh), facecolor="white")
        ax = fig.add_axes([left / fw, bottom / fh, width / fw, height / fh])
        artists, names = populate(ax, rows, variant)
        fig.text(left / fw, (bottom + height + .48) / fh,
                 f"{variant['id']}   {variant['name']}", fontsize=20, weight="bold")
        fig.text(left / fw, (bottom + height + .19) / fh,
                 "Ten typical CIM designs  ·  identical scale per decade  ·  ρ = τ at 45°",
                 fontsize=11, color=MUTED)
        fig.text(left / fw, .16 / fh,
                 "Paired reference estimates in MB/s. Gain-cell includes refresh; 3D FeFET denotes the 2026 vertical AND design.",
                 fontsize=10, color=MUTED)
        report = check_layout(fig, ax, rows, variant, artists, names)
        reports.append(report)
        stem = f"rho_tau_equal_scale_{variant['id']}"
        for extension in ("png", "pdf", "svg"):
            fig.savefig(OUT / f"{stem}.{extension}", dpi=200, bbox_inches="tight", pad_inches=.14)
        figures.append(fig)

    with PdfPages(OUT / "rho_tau_equal_scale_variants.pdf") as pdf:
        for fig in figures:
            pdf.savefig(fig, bbox_inches="tight", pad_inches=.14)
    for fig in figures:
        plt.close(fig)

    # Comparison uses the same physical length per decade in all four panels.
    # Thus changes in occupied area reflect cropping rather than different scaling.
    overview = plt.figure(figsize=(21.8, 14), facecolor="white")
    panel_scale = .64
    panel_decade_inches = INCHES_PER_DECADE * panel_scale
    row_tops = [12.65, 5.55]
    column_lefts = [1.0, 11.9]
    for i, variant in enumerate(VARIANTS):
        sx, sy = spans(variant)
        w, h = sx * panel_decade_inches, sy * panel_decade_inches
        left, top = column_lefts[i % 2], row_tops[i // 2]
        ax = overview.add_axes([left / 21.8, (top - h) / 14, w / 21.8, h / 14])
        artists, names = populate(ax, rows, variant, scale=panel_scale)
        overview.text(left / 21.8, (top + .21) / 14,
                      f"{variant['id']}   {variant['name']}   ({sx / sy:.2f}:1)",
                      fontsize=13, weight="bold")
        check_layout(overview, ax, rows, variant, artists, names, scale=panel_scale)
    overview.text(.046, .972, "ρ–τ layout comparison | same points, same log scale, 45° equality line", fontsize=20, weight="bold")
    overview.text(.046, .025, "A → D trims the empty margins. Cropping changes framing; it does not change any capacity ratio or move a point.",
                  fontsize=12, color=MUTED)
    for extension in ("png", "pdf"):
        overview.savefig(OUT / f"rho_tau_equal_scale_comparison.{extension}", dpi=160,
                         bbox_inches="tight", pad_inches=.14)
    plt.close(overview)

    report = {"all_passed": True, "point_count": 10, "inches_per_decade": INCHES_PER_DECADE,
              "marker_area_points_squared": MARKER_AREA,
              "source_checks_passed": source_report["all_passed"],
              "source_sha256": source_report["sha256"]["data/ten_case_results.json"],
              "variants": reports,
              "interpretation": "All points retain their exact rho/tau values. Equal log scales preserve the same perpendicular distance to the equality line at a fixed inches/decade. Different limits remove empty margins only."}
    (DATA / "rho_tau_equal_scale_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: four layouts and comparison; 10 unchanged points each; equal log scales; 45-degree lines; labels below and collision-free.")
    for r in reports:
        print(f"{r['id']}: aspect {r['plot_width_over_height']:.3f}; data spans {r['data_span_fraction_x']:.1%} x {r['data_span_fraction_y']:.1%} of axes")


if __name__ == "__main__":
    main()

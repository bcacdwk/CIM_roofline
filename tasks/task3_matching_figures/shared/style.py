"""Task III common paper style; no writes outside Task III.

Hardware hues retain Task I. A symbol identifies a medium consistently;
scenario size/fill may distinguish short/reference/long without recoloring it.
"""
from pathlib import Path

CASE_ORDER = ["01_sram_acim", "02_sram_dcim", "03_nor_2d", "04_nand_3d",
              "05_rram", "06_mram", "07_pcm", "08_feram_hfo2",
              "09_gain_cell_edram", "10_fenor_3d"]
_COLORS = ["#2d63ad", "#6e52a2", "#a37622", "#68737d", "#c54e55",
           "#178276", "#ca6b2b", "#338fa5", "#7b8736", "#ad5390"]
_LABELS = ["SRAM ACIM", "SRAM DCIM", "2D NOR", "3D NAND", "RRAM", "MRAM",
           "PCM", "HfO2 FeRAM", "Gain-cell eDRAM", "3D FeFET"]
_MARKERS = ["o", "s", "^", "v", "D", "P", "X", "h", "p", "*"]
COLORS = dict(zip(CASE_ORDER, _COLORS))
LABELS = dict(zip(CASE_ORDER, _LABELS))
MARKERS = dict(zip(CASE_ORDER, _MARKERS))
INK, MUTED, GRID = "#182838", "#657382", "#e5eaf0"
PROFILES = ("short", "reference", "long")
PROFILE_LABELS = {"short": "Optimistic", "reference": "Typical", "long": "Pessimistic"}
U_VALUES = (1, 128, 1024, 131072)
U_LABELS = {1: "1", 128: "128", 1024: "1K", 16384: "16K", 131072: "128K", 1048576: "1M"}
# U references are neutral: color is reserved for hardware identity.
U_LINESTYLES = {1: (0, (1, 2)), 128: (0, (4, 2)), 1024: "-", 131072: (0, (5, 2, 1, 2))}
SINGLE_COLUMN_IN = 3.5
DOUBLE_COLUMN_IN = 7.16


def apply_style(font_size=8):
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": font_size,
        "axes.titlesize": font_size + 1, "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 0.5, "ytick.labelsize": font_size - 0.5,
        "legend.fontsize": font_size - 0.5, "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": "#82909c", "axes.linewidth": 0.6,
        "mathtext.fontset": "dejavusans", "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "savefig.facecolor": "white",
        "savefig.dpi": 240, "axes.titleweight": "semibold",
    })


def save_figure(fig, stem):
    """Save at its explicitly assigned paper dimensions (no bbox resizing)."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(stem.with_suffix("." + suffix), dpi=240)


def format_u(value):
    return U_LABELS.get(value, f"{value:g}")

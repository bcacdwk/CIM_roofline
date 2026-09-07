#!/usr/bin/env python3
"""Task 0 algebra and illustrative numbers; no device or simulator validation.

Run with Python 3 and the standard library. Source-reference checks below are
structural only; they cannot prove that all TeX statements follow conventions.
"""

from fractions import Fraction as F
from math import inf
from pathlib import Path
import re


def roofline(qs, qr, rho, tau):
    """Return (RI, input-throughput upper bound), branching before division."""
    if qs <= 0 or qr < 0 or rho <= 0 or tau < 0:
        raise ValueError("Invalid demand or capability")
    if qr == 0:
        return inf, rho
    if tau == 0:
        raise ValueError("Dynamic residency requires write support")
    ri = F(qs) / F(qr)
    return ri, min(rho, tau * ri)


def rectangle(n_in, n_out, u, bs, br):
    qs = u * n_in * bs
    qr = n_out * n_in * br
    m = 2 * u * n_out * n_in
    return qs, qr, m


def check_sram():
    interval = F(10, 10**9)
    qs, qr, m = rectangle(128, 128, 1, F(1), F(1))
    macs = m // 2
    rho = qs / interval
    assert qs == 128 and qr == 16384
    assert qs * 8 == 1024 and macs == 16384 and m == 32768
    assert rho == 12800000000 and rho / 10**9 == F("12.8")
    assert m / interval / 10**12 == F("3.2768")
    assert m / qs == 256
    # Static state was loaded before W. No write capability is needed here.
    assert roofline(qs, 0, rho, 0) == (inf, rho)
    assert roofline(qs, 0, rho, 1)[1] * (m / qs) == m / interval


def check_rectangles():
    # Rectangular, non-square cases and unequal / sub-byte precisions matter:
    # square-only, equal-precision checks could conceal swapped dimensions.
    cases = [(96, 64, 7, F(1, 2), F(2)),
             (32, 128, 512, F(2), F(1, 2)),
             (128, 128, 128, F(1), F(1))]
    assert rectangle(*cases[0]) == (336, 12288, 86016)
    assert F(336, 12288) == F(7, 256)
    for n_in, n_out, u, bs, br in cases:
        qs, qr, m = rectangle(n_in, n_out, u, bs, br)
        ks, kr = m / qs, m / qr
        assert ks == 2 * n_out / bs and kr == 2 * u / br
        assert qs / qr == u * bs / (n_out * br) == kr / ks
        # Arbitrary exact rates exercise both branches; not SRAM measurements.
        for rho, tau in [(F(1000), F(1)), (F(1000), F(100000))]:
            ri, upper = roofline(qs, qr, rho, tau)
            t_lower = max(qs / rho, qr / tau)
            assert upper == qs / t_lower
            assert ks * upper == min(ks * rho, kr * tau) == m / t_lower
            # A slower execution still obeys the unit-conversion identity.
            actual_t = 3 * t_lower
            assert m / actual_t == ks * (qs / actual_t)
            assert qs / actual_t <= upper
            for copies in (2, 5, 11):
                assert roofline(copies * qs, copies * qr, rho, tau) == (ri, upper)
                assert max(copies * qs / rho, copies * qr / tau) == copies * t_lower
            # Fixed input workload and rates: more resident demand cannot help.
            bounds = [roofline(qs, k * qr, rho, tau)[1] for k in (0, 1, 2, 4, 32)]
            assert all(a >= b for a, b in zip(bounds, bounds[1:]))
    assert roofline(*rectangle(128, 128, 128, F(1), F(1))[:2], 1000, 10)[0] == 1


def check_source_links():
    root = Path(__file__).resolve().parents[1]
    source = (root / "CIM_Roofline_Paper/cim_roofline.tex").read_text()
    # Current document is self-contained. Ignore comments, not the bibliography.
    source = re.sub(r"(?m)(?<!\\)%.*$", "", source)
    labels = re.findall(r"\\label\{([^}]+)\}", source)
    refs = re.findall(r"\\(?:eqref|ref|pageref)\{([^}]+)\}", source)
    assert len(labels) == len(set(labels)), "Duplicate labels"
    assert set(refs) <= set(labels), f"Dangling refs: {set(refs) - set(labels)}"
    keys = set(re.findall(r"\\bibitem\{([^}]+)\}", source))
    cites = {key.strip() for group in re.findall(r"\\cite\{([^}]+)\}", source)
             for key in group.split(",")}
    assert cites <= keys, f"Missing bibliography entries: {cites - keys}"
    assert not re.search(r"\\(?:input|include)\b", source), "Recheck compilation scope"
    assert not {"sec:pd_fusion", "sec:channel_decomposition", "tab:hw_calibration",
                "tab:wl_calibration", "tab:regime_matrix"} & set(labels)
    assert {"eq:RI", "eq:cim_roofline", "eq:cim_time_bound", "eq:rect_work",
            "eq:rect_resident", "eq:tops_demystify", "tab:comparison"} <= set(labels)
    print(f"PASS source structure: {len(labels)} labels, {len(refs)} references, "
          f"{len(cites)} cited keys; legacy sections excluded")


if __name__ == "__main__":
    check_sram()
    print("PASS 128x128: 128 Byte, 16384 MAC, 32768 OP, 12.8 GB/s, 3.2768 TOPS")
    check_rectangles()
    print("PASS rectangular/precision relations, static branch, monotonicity, "
          "complete repetition, and OP-throughput identities")
    check_source_links()
    print("Scope: algebra, illustrative numbers and source links only; "
          "not measured validation or proof of every TeX statement.")

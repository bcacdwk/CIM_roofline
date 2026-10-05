"""Read-only figure interface for the frozen Task III adapter output."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_data():
    return json.loads((HERE / "data.json").read_text())


def hardware(case_id=None, profile=None):
    rows = load_data()["hardware"]
    return [r for r in rows if (case_id is None or r["case_id"] == case_id)
            and (profile is None or r["profile"] == profile)]


def get_hardware(case_id, profile="reference"):
    return hardware(case_id, profile)[0]


def selected_workloads():
    return load_data()["selected_workloads"]


def qkv_mapping(model_id):
    return next(r for r in load_data()["qkv_tile_mappings"] if r["model_id"] == model_id)


def mapped_hardware(model_id, case_id, profile="reference"):
    return next(r for r in qkv_mapping(model_id)["scenarios"]
                if r["case_id"] == case_id and r["profile"] == profile)


def mapped_workloads(model_id=None):
    return [r for r in load_data()["qkv_mapped_workloads"]
            if model_id is None or r["model_id"] == model_id]


def classify(U, U_star, rel_tol=1e-10):
    """Compare actual points only; never classify a point sampled from a circle."""
    if math.isclose(U, U_star, rel_tol=rel_tol):
        return "balanced"
    return "resident-bound" if U < U_star else "streaming-bound"


def normalized_bound(U, U_star):
    """P_bound/rho for the matched full-load service; no latency claim."""
    return min(1.0, U / U_star)


def bound_MB_per_s(row, U, streaming_factor=1.0, resident_factor=1.0):
    """Ideal two-route ceiling in native input MB/s; positive analytic factors."""
    if min(U, streaming_factor, resident_factor) <= 0:
        raise ValueError("Reuse and capability factors must be positive")
    return min(streaming_factor * row["rho_MB_per_s"],
               resident_factor * row["tau_MB_per_s"] * U / row["N"])


def native_demand(row, U):
    """One complete native matrix and U full vectors, INT8 equal width."""
    return {"Q_S_Byte": U * row["K"], "Q_R_Byte": row["K"] * row["N"],
            "RI": U / row["N"], "U": U, "N": row["N"], "K": row["K"]}

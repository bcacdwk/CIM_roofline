"""Exact workload demands. No hardware rates. Stdlib only; all bytes use Fraction.

Events are grouped index families, not samples: elements and repetitions are exact.
The independent enumerator in test_counts.py does not call these formula helpers.
"""
from fractions import Fraction as F
from math import prod


def ceildiv(a, b):
    assert a >= 0 and b > 0
    return (a + b - 1) // b


def rational(x):
    x = F(x)
    return {"numerator": x.numerator, "denominator": x.denominator}


def unpack(x):
    return F(x["numerator"], x["denominator"])


def ratio(s, r):
    if r:
        return {"status": "finite", **rational(F(s) / r)}
    return {"status": "infinite" if s > 0 else "undefined_zero_over_zero"}


def event(kind, role, shape, fmt, repetitions, elements=None, **details):
    n = prod(shape) * repetitions if elements is None else elements
    return {"event_type": kind, "tensor_role": role, "logical_shape": shape,
            "format": fmt["name"], "bytes_per_element": rational(fmt["bytes"]),
            "repetitions": repetitions, "total_elements": n,
            "payload_Byte": rational(n * F(fmt["bytes"])), **details}


def finish(events, M):
    s = sum((unpack(e["payload_Byte"]) for e in events if e["event_type"] == "stream_input"), F(0))
    r = sum((unpack(e["payload_Byte"]) for e in events if e["event_type"] == "resident_write"), F(0))
    return {"Q_S_Byte": rational(s), "Q_R_Byte": rational(r), "M_OP": M, "RI": ratio(s, r)}


def tile_classes(n, width):
    full, rem = divmod(n, width)
    return ([(width, full)] if full else []) + ([(rem, 1)] if rem else [])


def gemm(n_out, n_in, U, stream, resident, loads=1, tile=None,
         stream_role="X", resident_role="W", replicas=1, epoch_vectors=None):
    assert min(n_out, n_in, U, replicas) > 0 and loads >= 0
    if epoch_vectors is not None:
        assert len(epoch_vectors) == loads and sum(epoch_vectors) == U and min(epoch_vectors) > 0
    r, c = tile or (n_out, n_in)
    assert r > 0 and c > 0
    events = []
    for nr, mr in tile_classes(n_out, r):
        for nc, mc in tile_classes(n_in, c):
            mult = mr * mc
            common = {"service_boundary": "tile_port" if tile else "logical_operator",
                      "resident_copies": replicas, "tile_shape_multiplicity": mult,
                      "index_family": "output blocks then input blocks; valid elements only"}
            events.append(event("resident_write", resident_role, [nr, nc], resident,
                                mult * loads * replicas, state_change="absent/evicted -> resident" if loads else "pre-resident -> unchanged",
                                reason="each actual full placement, including each maintained replica", **common))
            events.append(event("stream_input", stream_role, [nc], stream, mult * U,
                                state_change="no resident change", reason="each output tile receives its input segment; vectors partitioned across replicas", **common))
    full = n_out * n_in * F(resident["bytes"]) * replicas
    min_live = full if loads == 0 or tile is None else min(n_out, r) * min(n_in, c) * F(resident["bytes"]) * replicas
    return {"kind": "gemm", "logical_n_out": n_out, "logical_n_in": n_in,
            "input_vector_count": U, "resident_tensor": resident_role, "streaming_tensor": stream_role,
            "parameters": {"loads": loads, "replicas": replicas, "epoch_vectors": epoch_vectors,
                           "r": r if tile else None, "c": c if tile else None},
            "initial_state": "matrix already resident" if loads == 0 else "matrix absent; each later epoch evicts preceding placement",
            "end_state": "matrix unchanged" if loads == 0 else "last placement remains (only final tile if sequential scratch mapping)",
            "capacity": {"full_resident_Byte": rational(full), "minimum_live_resident_Byte": rational(min_live),
                         "allocated_logical_slots_if_all_tiles_kept": ceildiv(n_out, r) * ceildiv(n_in, c) * r * c * replicas,
                         "partial_sum_requirement": "complete dot product across input tiles; up to U*n_out accumulator elements; external workspace excluded from resident payload"},
            "events": events, "exact": finish(events, 2 * U * n_out * n_in)}


def sum_ceil_prefix(n, r):
    """Sum ceil(t/r), t=1..n, by complete blocks."""
    k, rem = divmod(n, r)
    return r * k * (k + 1) // 2 + rem * (k + 1)


def attention(B, Hq, Hkv, d, C, N, query, kv, probability, tile=None, replicas=1, value_kv=None):
    """C = initial history, N new tokens, t_j=C+j AFTER each append.
    K resident shape t_j x d. V resident shape d x t_j. All KV kept.
    Copies serve disjoint query-head work; total Q and A inputs unchanged.
    """
    assert min(B, Hq, Hkv, d, N, replicas) > 0 and C >= 0 and Hq % Hkv == 0
    assert replicas <= Hq // Hkv
    value_kv = value_kv or kv
    Lf = C + N
    T = N * C + N * (N + 1) // 2
    rr = tile[0] if tile else None
    cc = tile[1] if tile else None
    q_repeats = sum_ceil_prefix(Lf, rr) - sum_ceil_prefix(C, rr) if tile else N
    a_repeats = ceildiv(d, rr) if tile else 1
    components = []
    for role, shape, sfmt, selements, vector_count in [
        ("K", ["C+j", d], query, B * Hq * d * q_repeats, B * Hq * N),
        ("V_transposed", [d, "C+j"], probability, B * Hq * T * a_repeats, B * Hq * N)]:
        is_k = role == "K"
        resident_format = kv if is_k else value_kv
        events = [event("resident_write", role, [N, d] if is_k else [d, N], resident_format, B * Hkv * replicas,
                        service_boundary="tile_port" if tile else "logical_operator", resident_copies=replicas,
                        state_change=f"{C} -> {Lf} KV entries per request/head", reason="append only; no old prefix rewritten",
                        index_family="b,kv_head,copy,new_token,dimension; K tile=(token//r,dimension//c), V tile=(dimension//r,token//c)"),
                  event("stream_input", "query" if is_k else "attention_probability", [d] if is_k else ["C+j"], sfmt,
                        B * Hq * q_repeats if is_k else B * Hq * N * a_repeats, elements=selements,
                        service_boundary="tile_port" if tile else "logical_operator", resident_copies=replicas,
                        state_change="read currently visible prefix", reason="query service" if is_k else "one second-matmul input service; first-matmul output not counted separately",
                        index_family="b,hq,j=1..N; hkv=floor(hq/(Hq/Hkv)); visible k=0..C+j-1",
                        reception_rule="d*ceil((C+j)/r) per query" if is_k and tile else "(C+j)*ceil(d/r) per query" if tile else "one valid vector per query")]
        nr, nc = (Lf, d) if is_k else (d, Lf)
        cap = B * Hkv * replicas * Lf * d * F(resident_format["bytes"])
        components.append({"kind": "attention_qk" if is_k else "attention_av", "resident_tensor": role,
                           "streaming_tensor": "query" if is_k else "attention_probability",
                           "logical_n_out": shape[0], "logical_n_in": shape[1], "shape_series": {"j": [1, N], "C": C},
                           "input_vector_count": vector_count,
                           "resident_group_count": B * Hkv,
                           "vectors_per_current_prefix_shared_group": Hq // Hkv,
                           "vectors_per_group_over_window": N * (Hq // Hkv),
                           "replica_assignment": "query heads partitioned over maintained copies; group totals do not multiply by copies",
                           "port_vector_segments": B * Hq * q_repeats * ceildiv(d, cc) if tile and is_k else B * Hq * a_repeats * (sum_ceil_prefix(Lf, cc) - sum_ceil_prefix(C, cc)) if tile else vector_count,
                           "capacity": {"full_resident_Byte": rational(cap), "minimum_live_resident_Byte": rational(cap),
                                        "allocated_logical_slots_if_all_tiles_kept": B * Hkv * replicas * (ceildiv(nr, rr) * ceildiv(nc, cc) * rr * cc if tile else nr * nc),
                                        "partial_sum_requirement": "reduce input-column tiles; softmax receives complete QK scores; AV output completes all visible coefficients"},
                           "events": events, "exact": finish(events, 2 * B * Hq * d * T)})
    events = [e for component in components for e in component["events"]]
    return {"kind": "attention", "parameters": {"B": B, "H_q": Hq, "H_kv": Hkv, "d": d, "C_before_append": C, "N_new": N,
                                                  "L_visible_final": Lf, "causal_pairs_per_head": T, "kv_replicas": replicas, "r": rr, "c": cc},
            "initial_state": f"{C} K and V entries per request/KV head in each maintained layout/copy",
            "end_state": f"{Lf} entries; only {N} entries appended; all tiles retained",
            "components": components, "events": events,
            "capacity": {"full_resident_Byte": rational(B * Hkv * replicas * Lf * d * (F(kv["bytes"])+F(value_kv["bytes"]))),
                         "minimum_live_resident_Byte": rational(B * Hkv * replicas * Lf * d * (F(kv["bytes"])+F(value_kv["bytes"])))},
            "exact": finish(events, 4 * B * Hq * d * T)}


def training(n_out, n_in, U, A, formats, tile=None):
    assert A >= 1
    f = gemm(n_out, n_in, U, formats["input"], formats["weight"], 0, tile)
    dx = gemm(n_in, n_out, U, formats["gradient"], formats["weight"], 0, tile, "dY", "W_transposed")
    dw = gemm(n_in, U, n_out, formats["gradient"], formats["activation"], 1, tile, "dY_transposed", "X_transposed")
    alt = gemm(n_out, U, n_in, formats["activation"], formats["gradient"], 1, tile, "X_transposed", "dY_transposed")
    events = []
    for name, rec in [("forward", f), ("dX", dx), ("dW", dw)]:
        for e in rec["events"]:
            events.append({**e, "component": name, "microbatch_occurrences": A,
                           "repetitions": e["repetitions"] * A, "total_elements": e["total_elements"] * A,
                           "payload_Byte": rational(unpack(e["payload_Byte"]) * A)})
    for name in ["W", "W_transposed"]:
        events.append(event("resident_write", name, [n_out, n_in] if name == "W" else [n_in, n_out], formats["weight"], 1,
                            component="end_update", service_boundary="tile_port" if tile else "logical_operator", resident_copies=1,
                            state_change="old parameters -> new parameters", reason="one actual update per maintained weight layout after A microbatches"))
    cap = 2 * n_out * n_in * F(formats["weight"]["bytes"]) + n_in * U * F(formats["activation"]["bytes"])
    return {"kind": "linear_training_cycle", "parameters": {"n_out": n_out, "n_in": n_in, "U": U, "A": A, "weight_layouts": 2},
            "initial_state": "W and W_transposed hold current parameters; temporary activation region reusable; gradient accumulator reset outside CIM",
            "end_state": "both weight layouts updated once; temporary X can be discarded; next cycle begins without another initial load",
            "components": {"forward": f, "dX": dx, "dW": dw}, "alternative_dW": alt,
            "capacity": {"full_resident_Byte": rational(cap), "minimum_live_resident_Byte": rational(2 * n_out * n_in * F(formats["weight"]["bytes"]) + unpack(dw["capacity"]["minimum_live_resident_Byte"])),
                         "external_accumulator": "n_out*n_in gradient elements; chosen accumulator precision is outside this operand payload scope"},
            "events": events, "exact": finish(events, 6 * A * U * n_out * n_in)}

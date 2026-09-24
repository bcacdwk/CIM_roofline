"""Exact matrix-stage demand templates. No model loading or hardware-time prediction."""
from fractions import Fraction


def ceildiv(n, size):
    if n < 0 or size <= 0:
        raise ValueError('nonnegative extent and positive tile size required')
    return (n + size - 1) // size


def exact(value):
    return Fraction(str(value))


def demand(qs, qr, calls=None):
    qs, qr = exact(qs), exact(qr)
    if qs < 0 or qr < 0 or (calls is not None and calls < 0):
        raise ValueError('negative demand')
    ratio = qs / qr if qr else ('infinity' if qs else 'undefined_empty')
    return {'Q_S': qs, 'Q_R': qr, 'RI': ratio, 'tile_evaluations': calls}


def widths(n, size):
    return [min(size, n-start) for start in range(0, n, size)]


def matvec(n, k, uses=1, loads=0, b_s=1, b_r=1, tile_n=128, tile_k=128):
    """loads counts complete logical writes per tile, independent of uses."""
    if min(n,k,uses) <= 0 or loads < 0:
        raise ValueError('positive matrix and uses; nonnegative load count required')
    tn, tk = ceildiv(n,tile_n), ceildiv(k,tile_k)
    qr = loads*n*k*exact(b_r)
    return {'operator': demand(uses*k*exact(b_s),qr),
            'ports': demand(uses*tn*k*exact(b_s),qr,uses*tn*tk),
            'tile_layout': {'output_block_sizes':widths(n,tile_n), 'input_block_sizes':widths(k,tile_k),
                            'resident_tiles':tn*tk, 'load_events':loads*tn*tk}}


def _sum_demands(parts, boundary, overlap=0):
    return demand(sum(p[boundary]['Q_S'] for p in parts)-overlap,
                  sum(p[boundary]['Q_R'] for p in parts),
                  sum(p[boundary]['tile_evaluations'] for p in parts) if boundary == 'ports' else None)


def qkv(D, Hq, Hkv, dqk, dv, gate_width=0, b_x=1, b_w=1, tile_n=128, tile_k=128):
    """Canonical semantic banks Q, optional G, K, V, even for packed checkpoint tensors."""
    if Hq % Hkv:
        raise ValueError('GQA group size must be integral')
    dims={'Q':Hq*dqk,'K':Hkv*dqk,'V':Hkv*dv}
    if gate_width:
        dims={'Q':dims['Q'],'G':gate_width,'K':dims['K'],'V':dims['V']}
    parts={name:matvec(n,D,b_s=b_x,b_r=b_w,tile_n=tile_n,tile_k=tile_k) for name,n in dims.items()}
    overlap=(len(parts)-1)*D*exact(b_x)
    return {'parts':parts,'operator':_sum_demands(parts.values(),'operator',overlap),
            'operator_shared_input_overlap_removed':overlap,
            'ports':_sum_demands(parts.values(),'ports')}


def ffn(D, F, B, b_x=1, b_z=1, b_gate=1, b_up=1, b_down=1, tile_n=128, tile_k=128):
    """One dense FFN or one routed expert; one weight load per residency."""
    parts={
        'gate':matvec(F,D,B,1,b_x,b_gate,tile_n,tile_k),
        'up':matvec(F,D,B,1,b_x,b_up,tile_n,tile_k),
        'down':matvec(D,F,B,1,b_z,b_down,tile_n,tile_k)}
    overlap=B*D*exact(b_x)
    return {'parts':parts,'operator':_sum_demands(parts.values(),'operator',overlap),
            'operator_shared_input_overlap_removed':overlap,
            'ports':_sum_demands(parts.values(),'ports')}


def sum_ceil_prefix(L, tile_size):
    """Exact sum_{i=1}^L ceil(i/tile_size), including L=0 for telescoping tests."""
    m,r=divmod(L,tile_size)
    return tile_size*m*(m+1)//2+(m+1)*r


def attention(Hq, Hkv, dqk, dv, L, mode, b_q=1, b_p=1, b_k=1, b_v=1, tile_n=128, tile_k=128):
    if Hkv <= 0 or Hq < Hkv or Hq % Hkv or min(dqk,dv) <= 0:
        raise ValueError('invalid native attention dimensions')
    if mode not in ('prefill','decode') or L < (1 if mode=='decode' else 0):
        raise ValueError('invalid mode or visible length')
    if mode=='prefill':
        queries=L; pair_sum=L*(L+1)//2; cn=sum_ceil_prefix(L,tile_n); ck=sum_ceil_prefix(L,tile_k); appended=L
    else:
        queries=1; pair_sum=L; cn=ceildiv(L,tile_n); ck=ceildiv(L,tile_k); appended=1
    k_writes=appended*Hkv*dqk*exact(b_k)
    v_writes=appended*Hkv*dv*exact(b_v)
    qk={'operator':demand(Hq*queries*dqk*exact(b_q),k_writes),
        'ports':demand(Hq*dqk*cn*exact(b_q),k_writes,Hq*ceildiv(dqk,tile_k)*cn)}
    av={'operator':demand(Hq*pair_sum*exact(b_p),v_writes),
        'ports':demand(Hq*ceildiv(dv,tile_n)*pair_sum*exact(b_p),v_writes,Hq*ceildiv(dv,tile_n)*ck)}
    return {'parts':{'QK':qk,'AV':av},'operator':_sum_demands([qk,av],'operator'),
            'ports':_sum_demands([qk,av],'ports'),
            'appended_tokens':appended,'kv_copies_per_head':1,
            'group_size':Hq//Hkv,'prefix_sum_i':pair_sum,'prefix_sum_ceil_output':cn,
            'prefix_sum_ceil_input':ck,
            'active_layout_at_L':{'K_matrix_N_K':[L,dqk],'V_matrix_N_K':[dv,L]},
            'append_shape_per_kv_head':{'K':[1,dqk],'V':[dv,1]}}


def encode(value):
    """JSON-safe exact rationals; no nonstandard Infinity literal or binary-float rounding."""
    if isinstance(value,Fraction):
        return value.numerator if value.denominator==1 else {'numerator':value.numerator,'denominator':value.denominator}
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [encode(v) for v in value]
    return value

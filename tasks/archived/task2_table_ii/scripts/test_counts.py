"""Independent small-index enumerations, numerical gradients, and invariants."""
import json
import unittest
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from counts import gemm, attention, training, unpack, finish

BF = {"name": "BF16", "bytes": "2"}
I8 = {"name": "INT8", "bytes": "1"}
I4 = {"name": "INT4", "bytes": "1/2"}
FORMATS = {k: BF for k in ["input", "weight", "gradient", "activation"]}


def enumerate_gemm(m, n, u, loads, tile, bs, br):
    """Receivers keyed by output block, input block, vector, element.
    Each resident element keyed by load and (output,input); no closed formula.
    """
    r, c = tile or (m, n)
    writes, streams, macs = [], [], []
    for i0 in range(0, m, r):
        for k0 in range(0, n, c):
            for epoch in range(loads):
                for i in range(i0, min(m, i0 + r)):
                    for k in range(k0, min(n, k0 + c)):
                        writes.append((epoch, i, k))
            for v in range(u):
                for k in range(k0, min(n, k0 + c)):
                    streams.append((i0, k0, v, k))
                    for i in range(i0, min(m, i0 + r)):
                        macs.append((v, i, k))
    assert len(set(writes)) == len(writes)
    assert len(set(macs)) == len(macs)
    return F(len(streams)) * bs, F(len(writes)) * br, 2 * len(macs), {"write_indices": writes, "stream_indices": streams, "mac_indices": macs}


def enumerate_attention(B, Hq, Hkv, d, C, N, tile=None, copies=1, rectangle=False):
    """Explicit requests, head ownership, KV append indices and receiving ports.
    rectangle=True computes all final-length entries and supplies masked zeros to AV.
    """
    writes = {"K": [], "V": []}
    streams = {"K": [], "V": []}
    macs = {"K": [], "V": []}
    useful = 0
    for b in range(B):
        for j in range(N):
            t = C + j + 1
            for h in range(Hkv):
                for copy in range(copies):
                    for z in range(d):
                        writes["K"].append((b, h, copy, t-1, z))
                        writes["V"].append((b, h, copy, z, t-1))
            for h in range(Hq):
                owner = h // (Hq // Hkv)
                length = C + N if rectangle else t
                kr, kc = tile or (length, d)
                vr, vc = tile or (d, length)
                for o in range(0, length, kr):
                    for k0 in range(0, d, kc):
                        for z in range(k0, min(d, k0+kc)):
                            streams["K"].append((b,h,j,o,k0,z))
                            for p in range(o, min(length, o+kr)):
                                macs["K"].append((b,h,owner,j,p,z))
                                if p < t:
                                    useful += 2
                for o in range(0, d, vr):
                    for k0 in range(0, length, vc):
                        for p in range(k0, min(length, k0+vc)):
                            streams["V"].append((b,h,j,o,k0,p))
                            for z in range(o, min(d, o+vr)):
                                macs["V"].append((b,h,owner,j,p,z))
                                if p < t:
                                    useful += 2
    return {role: (2*len(streams[role]), 2*len(writes[role]), 2*len(macs[role])) for role in writes}, useful


class CountsTests(unittest.TestCase):
    def assert_counts(self, rec, values):
        self.assertEqual((unpack(rec["exact"]["Q_S_Byte"]), unpack(rec["exact"]["Q_R_Byte"]), rec["exact"]["M_OP"]), values[:3])

    def test_rectangular_precision_half_byte(self):
        for m,n,u in [(5,7,3),(1,3,1),(7,2,4)]:
            for tile in [None,(3,4),(2,9)]:
                for loads in [0,1,3]:
                    for bs,br in [(BF,BF),(I8,I4),(I4,BF)]:
                        self.assert_counts(gemm(m,n,u,bs,br,loads,tile), enumerate_gemm(m,n,u,loads,tile,F(bs["bytes"]),F(br["bytes"])))
        x=gemm(1,3,1,I8,I4)
        self.assertEqual(unpack(x["exact"]["Q_R_Byte"]),F(3,2))

    def test_static_and_reload_epochs(self):
        self.assertEqual(gemm(5,7,4,BF,BF,0)["exact"]["RI"],{"status":"infinite"})
        a=gemm(5,7,4,BF,BF,1,epoch_vectors=[4])
        b=gemm(5,7,4,BF,BF,2,epoch_vectors=[2,2])
        self.assertEqual(unpack(b["exact"]["Q_R_Byte"]),2*unpack(a["exact"]["Q_R_Byte"]))
        self.assertEqual(b["exact"]["Q_S_Byte"],a["exact"]["Q_S_Byte"])
        with self.assertRaises(AssertionError): gemm(5,7,4,BF,BF,2,epoch_vectors=[4,4])

    def test_receivers_not_column_repeat_factor(self):
        a=enumerate_gemm(5,7,3,1,(3,4),F(1),F(1))[3]
        cnt=Counter((v,k) for _,_,v,k in a["stream_indices"])
        self.assertEqual(set(cnt.values()),{2})
        self.assertEqual(len(a["write_indices"]),35)
        padded_slots=2*2*3*4
        self.assertGreater(padded_slots,len(a["write_indices"]))

    def test_full_mode_repeat(self):
        a=gemm(5,7,3,BF,BF,1,(3,4))
        b=gemm(5,7,12,BF,BF,4,(3,4))
        for key in ["Q_S_Byte","Q_R_Byte"]:
            self.assertEqual(unpack(b["exact"][key]),4*unpack(a["exact"][key]))
        self.assertEqual(b["exact"]["RI"],a["exact"]["RI"])

    def test_batch_weights_shared_kv_private(self):
        a,b=[gemm(5,7,B,BF,BF) for B in [1,8]]
        self.assertEqual(a["exact"]["Q_R_Byte"],b["exact"]["Q_R_Byte"])
        aa,bb=[attention(B,6,2,3,4,1,BF,BF,BF) for B in [1,8]]
        for k in ["Q_S_Byte","Q_R_Byte"]: self.assertEqual(unpack(bb["exact"][k]),8*unpack(aa["exact"][k]))

    def test_attention_explicit_gqa_and_boundaries(self):
        for B in [1,2]:
            for C,N in [(0,1),(0,5),(4,1),(2,4)]:
                for tile in [None,(2,2),(4,2),(2,4)]:
                    rec=attention(B,6,2,3,C,N,BF,BF,BF,tile)
                    expected,_=enumerate_attention(B,6,2,3,C,N,tile)
                    for sub,role in zip(rec["components"],["K","V"]): self.assert_counts(sub,expected[role])
                    self.assert_counts(rec,tuple(sum(expected[k][i] for k in expected) for i in range(3)))

    def test_decode_append_before_after(self):
        for visible in [1,2,5]:
            rec=attention(1,6,2,3,visible-1,1,BF,BF,BF)
            self.assertEqual(rec["parameters"]["L_visible_final"],visible)
            self.assertEqual(rec["parameters"]["causal_pairs_per_head"],visible)
            self.assertEqual(rec["exact"]["M_OP"],4*6*3*visible)

    def test_incremental_from_empty_equals_prefill(self):
        for tile in [None,(2,2),(4,2)]:
            for L in [1,5,8]:
                inc=[enumerate_attention(2,6,2,3,j,1,tile)[0] for j in range(L)]
                expected=tuple(sum(rec[k][i] for rec in inc for k in rec) for i in range(3))
                self.assert_counts(attention(2,6,2,3,0,L,BF,BF,BF,tile),expected)

    def test_masked_rectangle_and_payload_scope(self):
        p,pu=enumerate_attention(1,6,2,3,0,5)
        z,zu=enumerate_attention(1,6,2,3,0,5,rectangle=True)
        self.assertEqual(pu,zu)
        self.assertGreater(z["V"][0],p["V"][0])
        self.assertGreater(sum(x[2] for x in z.values()),zu)
        a=attention(1,6,2,3,0,5,BF,BF,BF)
        self.assertEqual(len([e for e in a["events"] if e["event_type"]=="stream_input"]),2)
        self.assertEqual({e["tensor_role"] for e in a["events"] if e["event_type"]=="stream_input"},{"query","attention_probability"})

    def test_replication_changes_writes_and_capacity(self):
        a,b=[attention(1,6,2,3,2,4,BF,BF,BF,(2,2),k) for k in [1,3]]
        self.assertEqual(a["exact"]["Q_S_Byte"],b["exact"]["Q_S_Byte"])
        self.assertEqual(unpack(b["exact"]["Q_R_Byte"]),3*unpack(a["exact"]["Q_R_Byte"]))
        self.assertEqual(unpack(b["capacity"]["full_resident_Byte"]),3*unpack(a["capacity"]["full_resident_Byte"]))

    def test_attention_independent_operand_precisions(self):
        ref,_=enumerate_attention(1,6,2,3,2,4,(2,2))
        rec=attention(1,6,2,3,2,4,I8,I4,BF,(2,2),value_kv=I8)
        self.assert_counts(rec["components"][0],(F(ref["K"][0],2),F(ref["K"][1],4),ref["K"][2]))
        self.assert_counts(rec["components"][1],(ref["V"][0],F(ref["V"][1],2),ref["V"][2]))

    def test_training_shapes_and_accumulation(self):
        for tile in [None,(3,2)]:
            for A in [1,4,16]:
                rec=training(5,7,3,A,FORMATS,tile)
                for name,m,n,u,loads in [("forward",5,7,3,0),("dX",7,5,3,0),("dW",7,3,5,1)]:
                    self.assert_counts(rec["components"][name],enumerate_gemm(m,n,u,loads,tile,F(2),F(2)))
                end=[e for e in rec["events"] if e["component"]=="end_update"]
                self.assertEqual(len(end),2)
                self.assertEqual(sum(e["repetitions"] for e in end),2)
                self.assertEqual(unpack(rec["exact"]["Q_R_Byte"]),A*7*3*2+2*5*7*2)
                self.assertEqual(rec["exact"]["M_OP"],6*A*5*7*3)
                self.assert_counts(rec["alternative_dW"],enumerate_gemm(5,3,7,1,tile,F(2),F(2)))

    def test_training_cycle_explicit_write_indices(self):
        for A in [1,16]:
            writes=[]
            # Every microbatch creates a new temporary X layout; neither weight
            # layout is initially written within this repeating cycle.
            for micro in range(A):
                for n in range(7):
                    for u in range(3): writes.append(("X_T",micro,n,u))
            # One end-of-cycle parameter update, in each maintained orientation.
            for m in range(5):
                for n in range(7):
                    writes.extend([("W",A,m,n),("W_T",A,n,m)])
            self.assertEqual(len(writes),len(set(writes)))
            cycle=training(5,7,3,A,FORMATS,(3,2))
            self.assertEqual(unpack(cycle["exact"]["Q_R_Byte"]),2*len(writes))
            self.assertEqual(sum(k[0]=="W" for k in writes),35)
        one=training(5,7,3,1,FORMATS); accumulated=training(5,7,3,16,FORMATS)
        self.assertEqual(16*one["exact"]["M_OP"],accumulated["exact"]["M_OP"])
        self.assertGreater(16*unpack(one["exact"]["Q_R_Byte"]),unpack(accumulated["exact"]["Q_R_Byte"]))

    def test_matrix_gradients_finite_difference(self):
        rng=np.random.default_rng(20260907)
        X=rng.normal(size=(3,7)); W=rng.normal(size=(5,7)); G=rng.normal(size=(3,5))
        Y=X@W.T; dx=G@W; dw=G.T@X
        self.assertEqual(Y.shape,(3,5)); self.assertEqual(dx.shape,X.shape); self.assertEqual(dw.shape,W.shape)
        np.testing.assert_allclose(X.T@G,dw.T)
        eps=1e-6
        for A,grad in [(X,dx),(W,dw)]:
            for idx in np.ndindex(A.shape):
                old=A[idx]; A[idx]=old+eps; plus=np.sum((X@W.T)*G)
                A[idx]=old-eps; minus=np.sum((X@W.T)*G); A[idx]=old
                self.assertAlmostEqual((plus-minus)/(2*eps),grad[idx],places=7)

    def test_reject_invalid_shapes(self):
        with self.assertRaises(AssertionError): attention(1,5,2,3,0,1,BF,BF,BF)
        with self.assertRaises(AssertionError): attention(1,6,2,3,-1,1,BF,BF,BF)
        with self.assertRaises(AssertionError): gemm(5,7,3,BF,BF,tile=(0,2))


if __name__ == "__main__":
    unittest.main(verbosity=2)

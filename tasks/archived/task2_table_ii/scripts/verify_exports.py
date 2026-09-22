"""Audit generated artifacts, source code shapes, exact events and independent traces."""
import ast
import hashlib
import json
import re
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from counts import finish, unpack
from generate import display_payload, display_fraction
from test_counts import enumerate_gemm, enumerate_attention

ROOT=Path(__file__).resolve().parents[1]


def read(path): return json.loads((ROOT/path).read_text())


def source_shapes(config):
    """Read official AST constructors without importing Transformers or loading weights."""
    tree=ast.parse((ROOT/"sources/official/modeling_qwen2.py").read_text())
    vals={"hidden_size":config["hidden_size"],"intermediate_size":config["intermediate_size"],
          "num_heads":config["num_attention_heads"],"num_key_value_heads":config["num_key_value_heads"],
          "head_dim":config["hidden_size"]//config["num_attention_heads"],"vocab_size":config["vocab_size"]}
    def evaluate(node):
        if isinstance(node,ast.Attribute): return vals[node.attr]
        if isinstance(node,ast.Constant): return node.value
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult): return evaluate(node.left)*evaluate(node.right)
        raise ValueError(ast.dump(node))
    found={}
    for cls in tree.body:
        if not isinstance(cls,ast.ClassDef) or cls.name not in ["Qwen2MLP","Qwen2Attention","Qwen2ForCausalLM"]: continue
        for node in ast.walk(cls):
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=="Linear":
                name=node.targets[0].attr
                bias=next((evaluate(k.value) for k in node.value.keywords if k.arg=="bias"),True)
                found[name.removesuffix("_proj")]=(evaluate(node.value.args[1]),evaluate(node.value.args[0]),bias)
    return found


def main():
    export=read("data/task3_demands.json"); recs=export["records"]; by={r["wl_id"]:r for r in recs}
    assert len(recs)==len(by)
    maps=read("configs/mappings.json")["mapping_ids"]
    manifest=read("sources/manifest.json"); sources={s["source_id"]:s for s in manifest}
    for s in manifest:
        p=ROOT/s["local_path"]
        if p.exists(): assert hashlib.sha256(p.read_bytes()).hexdigest()==s["sha256"],s["source_id"]
        else: assert "local-only" in p.parts,s["source_id"]
    for r in recs:
        assert r["wl_id"].startswith("wl_") and r["mapping_id"] in maps
        assert all(s in sources for s in r["source_ids"])
        for key in ["model","operator","stage","window","initial_state","end_state","boundary_kind","logical_n_out","logical_n_in","input_vector_count","formats","capacity"]: assert key in r,(r["wl_id"],key)
        assert r["exact"]==finish(r["events"],r["exact"]["M_OP"]),r["wl_id"]
        for e in r["events"]:
            assert e["total_elements"]*unpack(e["bytes_per_element"])==unpack(e["payload_Byte"])
        children=r.get("component_ids")
        if children:
            mult=r["parameters"]["A"] if r["kind"]=="linear_training_cycle" else 1
            assert r["exact"]["M_OP"]==mult*sum(by[k]["exact"]["M_OP"] for k in children)
            assert unpack(r["exact"]["Q_S_Byte"])==mult*sum(unpack(by[k]["exact"]["Q_S_Byte"]) for k in children)
            wr=mult*sum(unpack(by[k]["exact"]["Q_R_Byte"]) for k in children)
            if mult>=1 and r["kind"]=="linear_training_cycle": wr+=sum(unpack(e["payload_Byte"]) for e in r["events"] if e.get("component")=="end_update")
            assert unpack(r["exact"]["Q_R_Byte"])==wr
    # Parse original implementation, compare against every declared matrix shape.
    original=read("data/official_models.json"); catalog=read("data/operator_catalog.json"); parameter_checks={}
    for model,meta in original.items():
        shapes=source_shapes(meta["original_config"])
        for op in catalog:
            if op["model"]==meta["repo"]: assert shapes[op["operator"]]==(op["logical_n_out"],op["logical_n_in"],op["bias"])
        cc=meta["original_config"]; h=cc["hidden_size"]; layers=cc["num_hidden_layers"]
        # Catalog counts matrices including LM head; add embedding lookup and RMSNorm vectors.
        total=sum((o["matrix_elements"]+o["bias_elements"])*o["instances_in_model"] for o in catalog if o["model"]==meta["repo"])+cc["vocab_size"]*h+(2*layers+1)*h
        api=read(f"sources/official/qwen{model.removesuffix('b')}_repo.json")
        assert total==api["safetensors"]["total"]
        parameter_checks[model]={"from_shapes_and_norms":total,"official_repo_metadata":api["safetensors"]["total"]}
    rows=read("data/table_rows.json")
    tex=(ROOT/"tex/table_ii.tex").read_text(); bib=(ROOT/"tex/table_ii.bib").read_text()
    assert len(rows)==10
    for row in rows:
        assert row["short_id"] in tex
        for d in row["display"]:
            ex=by[d["wl_id"]]["exact"]
            assert d["exact"]==ex and d["Q_R"]==display_payload(ex["Q_R_Byte"]) and d["Q_S"]==display_payload(ex["Q_S_Byte"]) and d["RI_tex"]==display_fraction(ex["RI"])
    cites=set(k for group in re.findall(r"\\cite\{([^}]+)\}",tex) for k in group.split(","))
    keys=set(re.findall(r"@\w+\{([^,]+),",bib)); assert cites<=keys and all(k.startswith("t2_") for k in keys)
    assert cites<=set(sources)
    trace=enumerate_gemm(5,7,3,1,(3,4),F(1),F(1,2))
    att,useful=enumerate_attention(2,6,2,3,0,5,(2,2))
    rectangle,ru=enumerate_attention(2,6,2,3,0,5,(2,2),rectangle=True)
    independent={"gemm":{"shape":{"n_out":5,"n_in":7,"U":3,"r":3,"c":4},"Q_S_Byte":str(trace[0]),"Q_R_Byte":str(trace[1]),"M_OP":trace[2],**trace[3]},
                 "attention":{"B":2,"H_q":6,"H_kv":2,"d":3,"C":0,"N":5,"r":2,"c":2,"prefix_components_S_R_M":att,"useful_OP":useful,"rectangle_components_S_R_executedOP":rectangle,"rectangle_useful_OP":ru}}
    (ROOT/"data/independent_enumeration.json").write_text(json.dumps(independent,indent=2)+"\n")
    summary={"record_count":len(recs),"shape_count":len(catalog),"table_rows":len(rows),"resolved_citation_keys":sorted(cites),"source_hash_checks":"passed (missing ignored fulltexts allowed)","official_AST_shapes":"all passed","parameter_total_checks":parameter_checks,"event_sums":"all passed","component_aggregation":"all passed","display_generation":"all passed"}
    (ROOT/"output/export_audit.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()

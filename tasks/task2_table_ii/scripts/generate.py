"""Parse pinned model configs, instantiate demands, select and render Table II."""
import argparse
import csv
import hashlib
import json
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
from counts import gemm, attention, training, rational, unpack, finish

ROOT = Path(__file__).resolve().parents[1]


def save(path, obj):
    (ROOT / path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def display_fraction(q):
    if q.get("status") == "infinite": return r"\infty"
    x=unpack(q)
    den=x.denominator
    for prime in [2,5]:
        while den % prime == 0: den //= prime
    dec=format(Decimal(x.numerator)/Decimal(x.denominator),"f")
    if den == 1 and len(dec) <= 6:
        return dec
    return rf"\frac{{{x.numerator}}}{{{x.denominator}}}"


def display_payload(q):
    x=unpack(q)/1048576
    value=Decimal(x.numerator)/Decimal(x.denominator)
    rounded=value.quantize(Decimal("0.0001"),rounding=ROUND_HALF_UP)
    s=format(rounded,"f").rstrip("0").rstrip(".")
    return {"text":s or "0", "unit":"MiB", "rounded":F(rounded)!=x, "exact_MiB":rational(x)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--tile",nargs=2,type=int,metavar=("R","C")); args=ap.parse_args()
    cfg=json.loads((ROOT/"configs/scenarios.json").read_text()); fmt=cfg["formats"]
    tiles=[None]+([tuple(args.tile)] if args.tile else [(v["r"],v["c"]) for v in cfg["tile_examples"]])
    models={}; catalog=[]; records=[]
    for key, meta in cfg["models"].items():
        raw=json.loads((ROOT/"configs"/meta["config"]).read_text())
        h=raw["hidden_size"]; f=raw["intermediate_size"]; hq=raw["num_attention_heads"]; hk=raw["num_key_value_heads"]
        assert h%hq==0 and hq%hk==0 and raw["hidden_act"]=="silu" and not raw["tie_word_embeddings"] and not raw["use_sliding_window"]
        d=raw.get("head_dim",h//hq); kv=hk*d
        models[key]={**meta, **{k:raw[k] for k in ["hidden_size","intermediate_size","num_hidden_layers","num_attention_heads","num_key_value_heads","vocab_size","hidden_act","tie_word_embeddings","torch_dtype","use_sliding_window","attention_dropout","transformers_version"]},
                     "head_dim":d,"head_dim_rule":"hidden_size // num_attention_heads", "mlp":"down(silu(gate(x))*up(x))", "attention_semantics":"full causal including current; no padding in selected windows", "implementation_version":"transformers v4.45.2 / 53fad641cfdb5105e2470bcf3ef17ea8e25cc300"}
        for op,m,n,bias in [("q",hq*d,h,True),("k",kv,h,True),("v",kv,h,True),("o",h,hq*d,False),("gate",f,h,False),("up",f,h,False),("down",h,f,False),("lm_head",raw["vocab_size"],h,False)]:
            catalog.append({"wl_id":f"wl_{key}_{op}_shape", "model":meta["repo"],"revision":meta["revision"],"operator":op,"logical_n_out":m,"logical_n_in":n,
                            "matrix_elements":m*n,"bias":bias,"bias_elements":m if bias else 0,"instances_in_model":1 if op=="lm_head" else raw["num_hidden_layers"],
                            "scope":"matrix multiply only; bias is external vector addition", "source_ids":[f"t2_qwen{key}_config","t2_transformers"],"derivation_id":"D1"})
    save("data/model_summary.json",models); save("data/operator_catalog.json",catalog)

    def register(rec, base, model, op, stage, mapping, tile, window):
        rec=deepcopy(rec)
        suffix="lo" if tile is None else f"tp_r{tile[0]}_c{tile[1]}"
        rid=base+"_"+suffix
        def add(node,rid,nodeop):
            node["wl_id"]=rid; node["model"]={k:models[model][k] for k in ["repo","revision"]}
            node["operator"]=nodeop; node["stage"]=stage; node["window"]=window
            node["mapping_id"]=mapping+("_LO" if tile is None else "_TP")
            node["boundary_kind"]="logical_operator" if tile is None else "tile_port"
            node["boundary_description"]="one full logical matrix service; input shared internally across outputs" if tile is None else "sum of receiving tile ports; output-block recipients count separately; input columns segmented"
            node["formats"]=fmt
            node["source_ids"]=[f"t2_qwen{model}_config","t2_transformers","t2_isaac"]+(["t2_attention","t2_gqa"] if "attention" in node["kind"] else ["t2_pytorch","t2_pytorch_derivatives","t2_pytorch_backward"] if stage=="training" else [])
            node["derivation_id"]="D3" if "attention" in node["kind"] else "D4" if stage=="training" else "D2"
            node["pairing_conditions"]=["match exact format names, logical input/write boundary and required complete output", "no hardware rate is exported", "account for necessary reductions, conversion, internal bit steps and write granularity in service capability", "match retained capacity and actual placement/replay schedule"]
            node.setdefault("initial_state",rec.get("initial_state","see containing cycle"))
            node.setdefault("end_state",rec.get("end_state","see containing cycle"))
            children=node.pop("components",None)
            if children:
                children=children.items() if isinstance(children,dict) else [("qk" if c["kind"]=="attention_qk" else "av",c) for c in children]
                node["component_ids"]=[]
                for name,child in children:
                    cid=rid+"_"+name.lower(); add(child,cid,name); node["component_ids"].append(cid)
                node["aggregation_semantics"]="demand summary only; do not add again to components; no common rho asserted"
                node["logical_n_out"]="component-specific"; node["logical_n_in"]="component-specific"; node["input_vector_count"]="component-specific"
                node["resident_tensor"]="see components"; node["streaming_tensor"]="see components"
            if "alternative_dW" in node:
                alt=node.pop("alternative_dW"); aid=rid+"_dw_alternative"; add(alt,aid,"dW_alternative"); node["alternative_component_ids"]=[aid]
            for i,e in enumerate(node["events"]):
                e["event_id"]=rid+f"_event_{i:02d}"
                e["boundary_id"]=rid+"/"+e.get("component",e["tensor_role"])
            records.append(node)
        add(rec,rid,op)

    for model,m in models.items():
        cat=[v for v in catalog if v["model"]==m["repo"]]
        for tile in tiles:
            for op in cat:
                nout,nin=op["logical_n_out"],op["logical_n_in"]; name=op["operator"]
                for B in cfg["inference_batch"]:
                    for loads,state in [(0,"static"),(1,"load")]:
                        rec=gemm(nout,nin,B,fmt["input"],fmt["weight"],loads,tile)
                        register(rec,f"wl_{model}_{name}_decode_b{B}_{state}",model,name,"decode","G0" if loads==0 else "G1",tile,{"B":B,"tokens_per_request":1,"U":B,"model_weight_shared_across_batch":True})
                    for L in cfg["prefill_tokens"]:
                        rec=gemm(nout,nin,B*L,fmt["input"],fmt["weight"],1,tile)
                        register(rec,f"wl_{model}_{name}_prefill_b{B}_l{L}_load",model,name,"prefill","G1",tile,{"B":B,"N_new":L,"U":B*L,"lm_head_policy":"all processed tokens if this operator is selected"})
            rp=cfg["reload_policy"]; epochs=rp["epoch_vectors"]
            register(gemm(m["intermediate_size"],m["hidden_size"],sum(epochs),fmt["input"],fmt["weight"],len(epochs),tile,epoch_vectors=epochs),f"wl_{model}_gate_reload_b1_l{sum(epochs)}_e{len(epochs)}",model,"gate","prefill","G2",tile,{"B":1,"U":sum(epochs),"epoch_vectors":epochs,"eviction_cause":rp["cause"]})
            for B in cfg["inference_batch"]:
                for stage,vals in [("prefill",cfg["prefill_tokens"]),("decode",cfg["decode_visible_after_append"])]:
                    for L in vals:
                        C,N=(0,L) if stage=="prefill" else (L-1,1)
                        rec=attention(B,m["num_attention_heads"],m["num_key_value_heads"],m["head_dim"],C,N,fmt["input"],fmt["kv"],fmt["probability"],tile,cfg["kv_replicas"])
                        register(rec,f"wl_{model}_attn_{stage}_b{B}_{'l' if stage=='prefill' else 'v'}{L}",model,"QK+AV",stage,"A1",tile,{"B":B,"C_before_append":C,"N_new":N,"L_visible_final":L,"layer_instances":1})
            train=cfg["training"]; U=train["microbatch"]*train["tokens"]
            for A in train["accumulations"]:
                register(training(m["intermediate_size"],m["hidden_size"],U,A,fmt,tile),f"wl_{model}_train_gate_u{U}_a{A}",model,"gate_training_cycle","training","T1",tile,{"microbatch_B":train["microbatch"],"tokens":train["tokens"],"U_per_microbatch":U,"A":A,"parameter_updates":1,"component_counts":"each child GEMM is one microbatch; parent events multiply by A"})
    # Precision and service-boundary sensitivities remain separate records.
    m=models["7b"]; n=m["hidden_size"]; kout=m["num_key_value_heads"]*m["head_dim"]
    for wformat in [{"name":"INT8","bytes":"1"},{"name":"INT4","bytes":"1/2"}]:
        rec=gemm(kout,n,8,{"name":"INT8","bytes":"1"},wformat)
        register(rec,f"wl_7b_k_decode_b8_int8_{wformat['name'].lower()}","7b","k","decode","G1",None,{"B":8,"U":8,"precision_comparison_only":True})
        records[-1]["formats"]={**fmt,"input":{"name":"INT8","bytes":"1"},"weight":wformat}
    for name,nout,parts in [("qkv",n+2*kout,["q","k","v"]),("gate_up",2*m["intermediate_size"],["gate","up"])]:
        register(gemm(nout,n,8,fmt["input"],fmt["weight"]),f"wl_7b_{name}_fused_u8","7b",name,"decode","F1",None,{"B":8,"U":8,"fused_components":parts,"one_shared_input_boundary":True})
    for tile in tiles:
        rec=attention(1,m["num_attention_heads"],m["num_key_value_heads"],m["head_dim"],2047,1,fmt["input"],fmt["kv"],fmt["probability"],tile,7)
        register(rec,"wl_7b_attn_decode_b1_v2048_copy7","7b","QK+AV","decode","A1",tile,{"B":1,"C_before_append":2047,"N_new":1,"L_visible_final":2048,"kv_replicas":7})
    ids=[r["wl_id"] for r in records]; assert len(ids)==len(set(ids))
    outname="demands_custom_tile.json" if args.tile else "demands.json"
    export={"schema_version":"t2.1","baseline_commit":cfg["baseline_commit"],"units":{"payload":"Byte","work":"OP","MAC_to_OP":2},
            "fraction_encoding":"{numerator: integer, denominator: positive integer}; RI also carries status", "mapping_file":"configs/mappings.json",
            "aggregate_rule":"select parent summary OR listed component records; never both; cycle children are per microbatch",
            "format_rule":"format names required for compatibility; BF16 != INT16 even though bytes match", "records":records}
    save("data/"+outname,export)
    if args.tile: return
    save("data/task3_demands.json",export)
    select_table(records,models)
    with (ROOT/"data/exact_counts.csv").open("w",newline="") as f:
        writer=csv.writer(f); writer.writerow(["wl_id","boundary_kind","Q_R_Byte","Q_S_Byte","M_OP","RI_state","RI_exact"])
        for r in records:
            ex=r["exact"]; writer.writerow([r["wl_id"],r["boundary_kind"],str(unpack(ex["Q_R_Byte"])),str(unpack(ex["Q_S_Byte"])),ex["M_OP"],ex["RI"]["status"],str(unpack(ex["RI"])) if ex["RI"]["status"]=="finite" else ""])
    print(f"Generated {len(catalog)} operator shapes and {len(records)} workload records.")


def select_table(records,models):
    by={r["wl_id"]:r for r in records}
    config=json.loads((ROOT/"configs/scenarios.json").read_text())
    n=models["7b"]["hidden_size"]; m=models["7b"]["intermediate_size"]
    k=models["7b"]["num_key_value_heads"]*models["7b"]["head_dim"]
    b1,b8=config["inference_batch"]; L=config["prefill_tokens"][0]; Lv=config["decode_visible_after_append"][-1]
    U=config["training"]["microbatch"]*config["training"]["tokens"]
    a1,a16=config["training"]["accumulations"]; ep=config["reload_policy"]["epoch_vectors"]
    specs=[
        ("S1","K projection",["wl_7b_k_decode_b1_static_lo"],"G0: pre-resident; decode"),
        ("S2","K projection",["wl_7b_k_decode_b1_load_lo"],"G1: load once; decode"),
        ("S3","K, 7B / 14B",["wl_7b_k_decode_b8_load_lo","wl_14b_k_decode_b8_load_lo"],"G1: load once; decode"),
        ("S4","MLP gate",["wl_7b_gate_prefill_b1_l2048_load_lo"],"G1: load once; prefill"),
        ("S5","MLP gate",["wl_7b_gate_reload_b1_l2048_e4_lo"],f"G2: {len(ep)} placement epochs"),
        ("S6","Causal prefill",["wl_7b_attn_prefill_b1_l2048_lo"],"A1: empty KV; append prefixes"),
        ("S7","KV-append decode",["wl_7b_attn_decode_b8_v8192_lo"],"A1: keep history; append one"),
        ("S8",r"Gate input grad. $dX$",["wl_7b_train_gate_u2048_a1_lo_dx"],r"T1: pre-resident $W^\top$"),
        ("S9",r"Gate weight grad. $dW$",["wl_7b_train_gate_u2048_a1_lo_dw"],r"T1: load $X^\top$ once"),
        ("S10","Gate update cycle",["wl_7b_train_gate_u2048_a1_lo","wl_7b_train_gate_u2048_a16_lo"],"T1: two weight layouts updated")]
    rows=[]; tex=[]
    for short,label,ids,window in specs:
        # Payloads and displayed dimensions come from the same config/records.
        chosen=[by[i] for i in ids]; display=[]
        for r in chosen:
            ex=r["exact"]; display.append({"wl_id":r["wl_id"],"Q_R":display_payload(ex["Q_R_Byte"]),"Q_S":display_payload(ex["Q_S_Byte"]),"RI_tex":display_fraction(ex["RI"]),"exact":ex})
        qr=" / ".join(v["Q_R"]["text"] for v in display); qs=" / ".join(v["Q_S"]["text"] for v in display)
        ri=r"\;/\;".join(v["RI_tex"] for v in display)
        dims={
            "S1":rf"$U={b1}$; $W_K:{k}\times{n}$", "S2":rf"$B=U={b1}$",
            "S3":rf"$B=U={b8}$; shared $W_K$", "S4":rf"$U={b1*L}$; $W_g:{m}\times{n}$",
            "S5":rf"$U={sum(ep)}$; ${ep[0]}$ vectors/epoch", "S6":rf"$B={b1}$, $C=0$, $N={L}$",
            "S7":rf"$B={b8}$, $N=1$, $L_v={Lv}$", "S8":rf"$dY:{U}\times{m}$",
            "S9":rf"$X^\top:{n}\times{U}$", "S10":rf"$U={U}$; $A={a1}\,/\,{a16}$"}[short]
        tex.append(f"{short} {label} & {window} & {dims} & {qr} & {qs} & ${ri}$ " + r"\\")
        rows.append({"short_id":short,"workload_ids":ids,"label_tex":label,"window_tex":window,"dimensions_tex":dims,"display":display})
    save("data/table_rows.json",rows)
    header=r"""% Generated by scripts/generate.py; do not edit numbers here.
\begin{table*}[t]
\caption{Windowed operand demands of representative LLM workloads under explicit CIM mappings}
\label{tab:t2_windowed_demands}
\centering
\small
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.20}
\begin{tabularx}{\textwidth}{@{}p{0.185\textwidth}p{0.235\textwidth}Xrrr@{}}
\toprule
Workload / operator & Window and residency mapping & Key dimensions / parameters & $Q_R$ & $Q_S$ & $\mathrm{RI}$ \\
 & & & (MiB) & (MiB) & \\
\midrule
"""
    tail=r"""
\bottomrule
\end{tabularx}
\vspace{3pt}
\begin{minipage}{\textwidth}
\footnotesize
All rows use \texttt{logical\_operator} boundaries and @FORMAT@ (@BYTES@ Byte/element). One projection or one attention layer is counted;
7B is used except for the paired 7B/14B values in S3. Model dimensions follow fixed official configurations and implementation\cite{t2_qwen7b_config,t2_qwen14b_config,t2_transformers,t2_qwen_report}.
G0/G1/G2: independent weight-stationary projections; $Q_S=Un_{\rm in}b_S$, $Q_R=E n_{\rm out}n_{\rm in}b_R$, with $E=0,1,@E@$ respectively.
A1: $H_q=@HQ@$,$H_{kv}=@HKV@$,$d=@D@$; one shared KV copy per group, separate K and V layouts. $L_v=C+N$ is the final visible length, including the current token.
For $T=NC+N(N+1)/2$, $Q_S=BH_q(Nd b_Q+T b_A)$ and $Q_R=BH_{kv}Nd(b_K+b_V)$; QK and AV are separate services\cite{t2_attention,t2_gqa}.
T1: forward, $dX=dY W$, $dW=dY^\top X$; temporary resident $X^\top$ is replaced each microbatch, and pre-resident $W,W^\top$ are each updated once per cycle\cite{t2_pytorch}. S8--S9 are per microbatch; S10 gives cycle totals for $A=@A1@/@A16@$.
S6--S7 and S10 are demand sums with retained components, without a common service-rate claim.
The parameterized tile-port export uses arbitrary $(r,c)$ and counts each receiving output tile; ISAAC supports the underlying resident-MVM and partitioned-input concept\cite{t2_isaac}, while these schedules are our reference choices.
Payloads are rounded to 4 decimal places where needed (1 MiB=$2^{20}$ Byte); RI fractions are exact. Softmax, RoPE, bias and other non-matrix work are outside scope.
An AV input does not require external materialization of the entire attention matrix; these demands are not FlashAttention HBM traffic\cite{t2_flashattention}.
\end{minipage}
\end{table*}
"""
    tail=tail.replace("@HQ@",str(models["7b"]["num_attention_heads"])).replace("@HKV@",str(models["7b"]["num_key_value_heads"])).replace("@D@",str(models["7b"]["head_dim"]))
    assert all(v==config["formats"]["input"] for v in config["formats"].values()),"Main-table uniform-format note requires one shared format; asymmetric examples remain separate data."
    tail=tail.replace("@FORMAT@",config["formats"]["input"]["name"]).replace("@BYTES@",config["formats"]["input"]["bytes"]).replace("@E@",str(len(ep))).replace("@A1@",str(a1)).replace("@A16@",str(a16))
    (ROOT/"tex/table_ii.tex").write_text(header+"\n".join(tex)+tail)
    deriv=["# 主表逐行代入（脚本生成）","","所有 payload 单位 Byte；精确 RI 取该行 Q_S/Q_R。"]
    for row in rows:
        deriv.extend(["",f"## {row['short_id']}"])
        for rid in row["workload_ids"]:
            r=by[rid]; ex=r["exact"]
            deriv.extend([f"- `{rid}`；映射 `{r['mapping_id']}`。",f"- 窗口：`{json.dumps(r['window'],ensure_ascii=False)}`。",
                          f"- Q_R = {unpack(ex['Q_R_Byte'])}；Q_S = {unpack(ex['Q_S_Byte'])}；M = {ex['M_OP']} OP；RI = {str(unpack(ex['RI'])) if ex['RI']['status']=='finite' else '∞'}。",
                          "- 写入／输入事件："])
            for e in r["events"]:
                if e["total_elements"]:
                    deriv.append(f"  - {e.get('component','')}/{e['tensor_role']}：{e['event_type']}，形状 {e['logical_shape']}，次数 {e['repetitions']}，{e['total_elements']} 元素 × {unpack(e['bytes_per_element'])} Byte = {unpack(e['payload_Byte'])} Byte。")
            deriv.append(f"- 完整 resident 容量：{unpack(r['capacity']['full_resident_Byte'])} Byte；详见该记录的 capacity 和 components。")
    (ROOT/"data/table_substitutions.zh.md").write_text("\n".join(deriv)+"\n")


if __name__=="__main__": main()

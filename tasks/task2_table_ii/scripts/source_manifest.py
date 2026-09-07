"""Create attributed source manifest and checksums from the downloaded originals."""
import csv
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TF="53fad641cfdb5105e2470bcf3ef17ea8e25cc300"
PT="ee1b6804381c57161c477caa380a840a84167676"


def main():
    sources=[]
    def add(sid,title,author,version,url,path,locator,support,license,doi=None):
        p=ROOT/path
        sources.append(dict(source_id=sid,title=title,author_or_publisher=author,version=version,doi=doi,url=url,access_date="2026-09-07",local_path=path,locator=locator,supports=support,redistribution=license,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    cfg=json.loads((ROOT/"configs/scenarios.json").read_text())
    for model,meta in cfg["models"].items():
        size=model.upper(); repo=meta["repo"]; rev=meta["revision"]
        add(f"t2_qwen{model}_config",repo+" config.json","Qwen Team",rev,f"https://huggingface.co/{repo}/resolve/{rev}/config.json",f"configs/qwen{size}_config.json","all JSON keys; dimensions and tie_word_embeddings/use_sliding_window", "exact tensor dimension parameters, serialized dtype, config metadata version", "Apache-2.0; corresponding LICENSE retained")
        add(f"t2_qwen{model}_card",repo+" model card","Qwen Team",rev,f"https://huggingface.co/{repo}/resolve/{rev}/README.md",f"sources/official/qwen{size}_README.md","Introduction feature list, lines 23-31; Requirements", "base causal model; RoPE, SwiGLU, RMSNorm, QKV bias and GQA; official implementation routing", "Apache-2.0; corresponding LICENSE retained")
        add(f"t2_qwen{model}_metadata",repo+" repository API snapshot","Qwen / Hugging Face",rev+"; captured API response on 2026-09-07",f"https://huggingface.co/api/models/{repo}",f"sources/official/qwen{model.removesuffix('b')}_repo.json","sha and safetensors.total fields", "actual model commit and independent total parameter count; download/like counters are not used", "repository metadata snapshot; dynamic counters prevent byte-identical live re-fetch")
        sources[-1]["fetch_policy"]="frozen_snapshot_keep_local"
    add("t2_transformers","Transformers Qwen2 modeling_qwen2.py","Hugging Face contributors","v4.45.2; "+TF,f"https://raw.githubusercontent.com/huggingface/transformers/{TF}/src/transformers/models/qwen2/modeling_qwen2.py","sources/official/modeling_qwen2.py","lines 100-116 causal mask; 265-276 MLP; 280-289 repeat_kv; 309-327 projections; 349-380 reshape/cache/matmuls/softmax; 1089 LM head", "head_dim=h/Hq; exact bias and matrix roles; current-token mask; GQA repeats are software semantics, not required CIM copies", "Apache-2.0; transformers_LICENSE retained")
    add("t2_transformers_config","Transformers Qwen2 configuration_qwen2.py","Hugging Face contributors","v4.45.2; "+TF,f"https://raw.githubusercontent.com/huggingface/transformers/{TF}/src/transformers/models/qwen2/configuration_qwen2.py","sources/official/configuration_qwen2.py","Qwen2Config.__init__, use_sliding_window and sliding_window assignment", "config interpretation; serialized transformers_version is not a hardware or execution-backend declaration", "Apache-2.0; transformers_LICENSE retained")
    add("t2_pytorch","PyTorch Linear.cpp","PyTorch contributors","v2.4.1; "+PT,f"https://raw.githubusercontent.com/pytorch/pytorch/{PT}/aten/src/ATen/native/Linear.cpp","sources/official/pytorch_Linear.cpp","linear(): lines 73-123, especially 96 and 111", "forward input @ weight.T plus optional bias", "BSD-style; pytorch_LICENSE retained")
    add("t2_pytorch_derivatives","PyTorch derivatives.yaml","PyTorch contributors","v2.4.1; "+PT,f"https://raw.githubusercontent.com/pytorch/pytorch/{PT}/tools/autograd/derivatives.yaml","sources/official/pytorch_derivatives.yaml","addmm lines 256-260; mm lines 1172-1175", "links matrix-input gradients to mm_mat1_backward/mm_mat2_backward", "BSD-style; pytorch_LICENSE retained")
    add("t2_pytorch_backward","PyTorch FunctionsManual.cpp","PyTorch contributors","v2.4.1; "+PT,f"https://raw.githubusercontent.com/pytorch/pytorch/{PT}/torch/csrc/autograd/FunctionsManual.cpp","sources/official/pytorch_FunctionsManual.cpp","lines 1415-1451 (fallback lines 1431, 1450)", "matrix gradient identities; applying chain rule to W.T gives dX=dY W, dW=dY.T X", "BSD-style; pytorch_LICENSE retained")
    for args in [
        ("t2_qwen_report","Qwen2.5 Technical Report","Qwen Team","arXiv:2412.15115v1","https://arxiv.org/pdf/2412.15115v1","qwen25","PDF pp. 2-3, Sec. 2 and Table 1","dense decoder, GQA heads/layers, SwiGLU, untied embeddings; config supplies padded vocabulary matrix size"),
        ("t2_attention","Attention Is All You Need","Vaswani et al.","arXiv:1706.03762v7","https://arxiv.org/pdf/1706.03762v7","attention","PDF pp. 3-5, Secs. 3.2.1-3.2.3, Eq. (1)","QK and probability-times-V operations; causal visibility includes current position"),
        ("t2_gqa","GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints","Ainslie et al.; Google Research","arXiv:2305.13245v3 / EMNLP 2023","https://arxiv.org/pdf/2305.13245v3","gqa","PDF p. 2, Sec. 2.2 and Fig. 2","one K/V head shared per query-head group; no compulsory Hq-fold KV state"),
        ("t2_isaac","ISAAC: A Convolutional Neural Network Accelerator with In-Situ Analog Arithmetic in Crossbars","Shafiee et al.; University of Utah and HPE","ISCA 2016 author manuscript","https://svivek.com/research/publications/isca16.pdf","isaac","PDF p. 3 Fig. 1 and Sec. III; pp. 6-7 Sec. VI execution example","resident weights, streamed inputs, row/column partitioning, repeated recipients, partial-sum completion; not BF16/Qwen hardware evidence"),
        ("t2_flashattention","FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness","Dao, Fu, Ermon, Rudra and Re","arXiv:2205.14135v2","https://arxiv.org/pdf/2205.14135v2","flashattention","PDF pp. 4-6 Sec. 3, Algorithm 1 (p. 5), Theorem 2","blocked online softmax and fusion avoid full external attention-matrix materialization; its HBM IO scope differs from these CIM inputs")]:
        sid,title,author,ver,url,name,loc,support=args
        add(sid,title,author,ver,url,f"sources/local-only/{name}.pdf",loc,support,"local-only by default; not redistributed in commit", "10.18653/v1/2023.emnlp-main.298" if name=="gqa" else None)
    (ROOT/"sources/manifest.json").write_text(json.dumps(sources,ensure_ascii=False,indent=2)+"\n")
    with (ROOT/"sources/manifest.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(sources[0])+["fetch_policy"]); w.writeheader(); w.writerows(sources)
    lines=["# 来源清单", "", "访问日期：2026-09-07。所有 URL 固定版本；论文全文默认 local-only。自己的推导见 SUPPORT.zh.md。", ""]
    for s in sources:
        lines.extend([f"## {s['source_id']}","",f"- [{s['title']}]({s['url']})；{s['author_or_publisher']}；{s['version']}。",f"- 本地：`{s['local_path']}`；定位：{s['locator']}。",f"- 支持：{s['supports']}。",f"- 提交策略：{s['redistribution']}；SHA-256：`{s['sha256']}`。",""])
    (ROOT/"sources/README.md").write_text("\n".join(lines))
    # Save original config structures in data as well, keeping exact downloaded bytes in configs.
    original={key:{**meta,"original_config":json.loads((ROOT/"configs"/meta["config"]).read_text())} for key,meta in cfg["models"].items()}
    (ROOT/"data/official_models.json").write_text(json.dumps(original,indent=2)+"\n")


if __name__=="__main__": main()

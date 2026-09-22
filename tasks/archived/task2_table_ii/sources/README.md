# 来源清单

访问日期：2026-09-07。所有 URL 固定版本；论文全文默认 local-only。自己的推导见 SUPPORT.zh.md。

## t2_qwen7b_config

- [Qwen/Qwen2.5-7B config.json](https://huggingface.co/Qwen/Qwen2.5-7B/resolve/d149729398750b98c0af14eb82c78cfe92750796/config.json)；Qwen Team；d149729398750b98c0af14eb82c78cfe92750796。
- 本地：`configs/qwen7B_config.json`；定位：all JSON keys; dimensions and tie_word_embeddings/use_sliding_window。
- 支持：exact tensor dimension parameters, serialized dtype, config metadata version。
- 提交策略：Apache-2.0; corresponding LICENSE retained；SHA-256：`267ce68584c5f24c3b267d934db2de68dd21d1ca677fb78ed809eb60067f7642`。

## t2_qwen7b_card

- [Qwen/Qwen2.5-7B model card](https://huggingface.co/Qwen/Qwen2.5-7B/resolve/d149729398750b98c0af14eb82c78cfe92750796/README.md)；Qwen Team；d149729398750b98c0af14eb82c78cfe92750796。
- 本地：`sources/official/qwen7B_README.md`；定位：Introduction feature list, lines 23-31; Requirements。
- 支持：base causal model; RoPE, SwiGLU, RMSNorm, QKV bias and GQA; official implementation routing。
- 提交策略：Apache-2.0; corresponding LICENSE retained；SHA-256：`8a23291de92bddc940674a5b7088b8443bde94a1df7f1911703d2cd6554c7328`。

## t2_qwen7b_metadata

- [Qwen/Qwen2.5-7B repository API snapshot](https://huggingface.co/api/models/Qwen/Qwen2.5-7B)；Qwen / Hugging Face；d149729398750b98c0af14eb82c78cfe92750796; captured API response on 2026-09-07。
- 本地：`sources/official/qwen7_repo.json`；定位：sha and safetensors.total fields。
- 支持：actual model commit and independent total parameter count; download/like counters are not used。
- 提交策略：repository metadata snapshot; dynamic counters prevent byte-identical live re-fetch；SHA-256：`0fba918b3aaecd1d0f3aeb25074715d6972c624c67ea3a5c8333e95738222ce2`。

## t2_qwen14b_config

- [Qwen/Qwen2.5-14B config.json](https://huggingface.co/Qwen/Qwen2.5-14B/resolve/97e1e76335b7017d8f67c08a19d103c0504298c9/config.json)；Qwen Team；97e1e76335b7017d8f67c08a19d103c0504298c9。
- 本地：`configs/qwen14B_config.json`；定位：all JSON keys; dimensions and tie_word_embeddings/use_sliding_window。
- 支持：exact tensor dimension parameters, serialized dtype, config metadata version。
- 提交策略：Apache-2.0; corresponding LICENSE retained；SHA-256：`fdb89460be9a6383451437cdf632a3e087522efa682265461f33507e7069f026`。

## t2_qwen14b_card

- [Qwen/Qwen2.5-14B model card](https://huggingface.co/Qwen/Qwen2.5-14B/resolve/97e1e76335b7017d8f67c08a19d103c0504298c9/README.md)；Qwen Team；97e1e76335b7017d8f67c08a19d103c0504298c9。
- 本地：`sources/official/qwen14B_README.md`；定位：Introduction feature list, lines 23-31; Requirements。
- 支持：base causal model; RoPE, SwiGLU, RMSNorm, QKV bias and GQA; official implementation routing。
- 提交策略：Apache-2.0; corresponding LICENSE retained；SHA-256：`e408f4734c24731ef86d48993c7747147cc578b1fbe50dec4bfdbae7e83147ec`。

## t2_qwen14b_metadata

- [Qwen/Qwen2.5-14B repository API snapshot](https://huggingface.co/api/models/Qwen/Qwen2.5-14B)；Qwen / Hugging Face；97e1e76335b7017d8f67c08a19d103c0504298c9; captured API response on 2026-09-07。
- 本地：`sources/official/qwen14_repo.json`；定位：sha and safetensors.total fields。
- 支持：actual model commit and independent total parameter count; download/like counters are not used。
- 提交策略：repository metadata snapshot; dynamic counters prevent byte-identical live re-fetch；SHA-256：`72a532801944b331c2a4e7494277ee8284cdcce9867cb7fc0d8385e716c7e4ac`。

## t2_transformers

- [Transformers Qwen2 modeling_qwen2.py](https://raw.githubusercontent.com/huggingface/transformers/53fad641cfdb5105e2470bcf3ef17ea8e25cc300/src/transformers/models/qwen2/modeling_qwen2.py)；Hugging Face contributors；v4.45.2; 53fad641cfdb5105e2470bcf3ef17ea8e25cc300。
- 本地：`sources/official/modeling_qwen2.py`；定位：lines 100-116 causal mask; 265-276 MLP; 280-289 repeat_kv; 309-327 projections; 349-380 reshape/cache/matmuls/softmax; 1089 LM head。
- 支持：head_dim=h/Hq; exact bias and matrix roles; current-token mask; GQA repeats are software semantics, not required CIM copies。
- 提交策略：Apache-2.0; transformers_LICENSE retained；SHA-256：`c0f712cc217640b9dd3d168ed000a5dc92079fc850385e5604a150c134d70fec`。

## t2_transformers_config

- [Transformers Qwen2 configuration_qwen2.py](https://raw.githubusercontent.com/huggingface/transformers/53fad641cfdb5105e2470bcf3ef17ea8e25cc300/src/transformers/models/qwen2/configuration_qwen2.py)；Hugging Face contributors；v4.45.2; 53fad641cfdb5105e2470bcf3ef17ea8e25cc300。
- 本地：`sources/official/configuration_qwen2.py`；定位：Qwen2Config.__init__, use_sliding_window and sliding_window assignment。
- 支持：config interpretation; serialized transformers_version is not a hardware or execution-backend declaration。
- 提交策略：Apache-2.0; transformers_LICENSE retained；SHA-256：`a4da735ab575c3f73a50e5f493e355d1ab271ff3f27fab384294f6cd992ea03f`。

## t2_pytorch

- [PyTorch Linear.cpp](https://raw.githubusercontent.com/pytorch/pytorch/ee1b6804381c57161c477caa380a840a84167676/aten/src/ATen/native/Linear.cpp)；PyTorch contributors；v2.4.1; ee1b6804381c57161c477caa380a840a84167676。
- 本地：`sources/official/pytorch_Linear.cpp`；定位：linear(): lines 73-123, especially 96 and 111。
- 支持：forward input @ weight.T plus optional bias。
- 提交策略：BSD-style; pytorch_LICENSE retained；SHA-256：`3264a545db3f6da93dad03e4f65364b980572e936485117e2376b2a7bafa0895`。

## t2_pytorch_derivatives

- [PyTorch derivatives.yaml](https://raw.githubusercontent.com/pytorch/pytorch/ee1b6804381c57161c477caa380a840a84167676/tools/autograd/derivatives.yaml)；PyTorch contributors；v2.4.1; ee1b6804381c57161c477caa380a840a84167676。
- 本地：`sources/official/pytorch_derivatives.yaml`；定位：addmm lines 256-260; mm lines 1172-1175。
- 支持：links matrix-input gradients to mm_mat1_backward/mm_mat2_backward。
- 提交策略：BSD-style; pytorch_LICENSE retained；SHA-256：`9b9c2ddabf4ca49d3483c0ebff179886dc21ae1db46abd493c72073c6bacc972`。

## t2_pytorch_backward

- [PyTorch FunctionsManual.cpp](https://raw.githubusercontent.com/pytorch/pytorch/ee1b6804381c57161c477caa380a840a84167676/torch/csrc/autograd/FunctionsManual.cpp)；PyTorch contributors；v2.4.1; ee1b6804381c57161c477caa380a840a84167676。
- 本地：`sources/official/pytorch_FunctionsManual.cpp`；定位：lines 1415-1451 (fallback lines 1431, 1450)。
- 支持：matrix gradient identities; applying chain rule to W.T gives dX=dY W, dW=dY.T X。
- 提交策略：BSD-style; pytorch_LICENSE retained；SHA-256：`f7c074589357d685a4910110de79072cd1daa044f5d5d598110099ee04b6010e`。

## t2_qwen_report

- [Qwen2.5 Technical Report](https://arxiv.org/pdf/2412.15115v1)；Qwen Team；arXiv:2412.15115v1。
- 本地：`sources/local-only/qwen25.pdf`；定位：PDF pp. 2-3, Sec. 2 and Table 1。
- 支持：dense decoder, GQA heads/layers, SwiGLU, untied embeddings; config supplies padded vocabulary matrix size。
- 提交策略：local-only by default; not redistributed in commit；SHA-256：`367bbeef22d21b6a11efbb114d8d4e72cdf3ebb5662c55d59bf2fa10e8c3da6c`。

## t2_attention

- [Attention Is All You Need](https://arxiv.org/pdf/1706.03762v7)；Vaswani et al.；arXiv:1706.03762v7。
- 本地：`sources/local-only/attention.pdf`；定位：PDF pp. 3-5, Secs. 3.2.1-3.2.3, Eq. (1)。
- 支持：QK and probability-times-V operations; causal visibility includes current position。
- 提交策略：local-only by default; not redistributed in commit；SHA-256：`bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`。

## t2_gqa

- [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/pdf/2305.13245v3)；Ainslie et al.; Google Research；arXiv:2305.13245v3 / EMNLP 2023。
- 本地：`sources/local-only/gqa.pdf`；定位：PDF p. 2, Sec. 2.2 and Fig. 2。
- 支持：one K/V head shared per query-head group; no compulsory Hq-fold KV state。
- 提交策略：local-only by default; not redistributed in commit；SHA-256：`ba9094fe73db9bf515d47ae8b2d502fee9d8a6c7b1327e197ddb160f4c63b94a`。

## t2_isaac

- [ISAAC: A Convolutional Neural Network Accelerator with In-Situ Analog Arithmetic in Crossbars](https://svivek.com/research/publications/isca16.pdf)；Shafiee et al.; University of Utah and HPE；ISCA 2016 author manuscript。
- 本地：`sources/local-only/isaac.pdf`；定位：PDF p. 3 Fig. 1 and Sec. III; pp. 6-7 Sec. VI execution example。
- 支持：resident weights, streamed inputs, row/column partitioning, repeated recipients, partial-sum completion; not BF16/Qwen hardware evidence。
- 提交策略：local-only by default; not redistributed in commit；SHA-256：`4508a420654e4720adcd33a739891377938946e9f8adc0c0e1f1f7f7f190f796`。

## t2_flashattention

- [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/pdf/2205.14135v2)；Dao, Fu, Ermon, Rudra and Re；arXiv:2205.14135v2。
- 本地：`sources/local-only/flashattention.pdf`；定位：PDF pp. 4-6 Sec. 3, Algorithm 1 (p. 5), Theorem 2。
- 支持：blocked online softmax and fusion avoid full external attention-matrix materialization; its HBM IO scope differs from these CIM inputs。
- 提交策略：local-only by default; not redistributed in commit；SHA-256：`ca7f9fda10b90fc05dd291a3accc85e9c1a4a860b99b31928dab03ed3fcb14e4`。

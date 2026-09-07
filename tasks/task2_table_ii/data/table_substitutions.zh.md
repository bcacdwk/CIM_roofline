# 主表逐行代入（脚本生成）

所有 payload 单位 Byte；精确 RI 取该行 Q_S/Q_R。

## S1
- `wl_7b_k_decode_b1_static_lo`；映射 `G0_LO`。
- 窗口：`{"B": 1, "tokens_per_request": 1, "U": 1, "model_weight_shared_across_batch": true}`。
- Q_R = 0；Q_S = 7168；M = 3670016 OP；RI = ∞。
- 写入／输入事件：
  - /X：stream_input，形状 [3584]，次数 1，3584 元素 × 2 Byte = 7168 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。

## S2
- `wl_7b_k_decode_b1_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 1, "tokens_per_request": 1, "U": 1, "model_weight_shared_across_batch": true}`。
- Q_R = 3670016；Q_S = 7168；M = 3670016 OP；RI = 1/512。
- 写入／输入事件：
  - /W：resident_write，形状 [512, 3584]，次数 1，1835008 元素 × 2 Byte = 3670016 Byte。
  - /X：stream_input，形状 [3584]，次数 1，3584 元素 × 2 Byte = 7168 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。

## S3
- `wl_7b_k_decode_b8_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 8, "tokens_per_request": 1, "U": 8, "model_weight_shared_across_batch": true}`。
- Q_R = 3670016；Q_S = 57344；M = 29360128 OP；RI = 1/64。
- 写入／输入事件：
  - /W：resident_write，形状 [512, 3584]，次数 1，1835008 元素 × 2 Byte = 3670016 Byte。
  - /X：stream_input，形状 [3584]，次数 8，28672 元素 × 2 Byte = 57344 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。
- `wl_14b_k_decode_b8_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 8, "tokens_per_request": 1, "U": 8, "model_weight_shared_across_batch": true}`。
- Q_R = 10485760；Q_S = 81920；M = 83886080 OP；RI = 1/128。
- 写入／输入事件：
  - /W：resident_write，形状 [1024, 5120]，次数 1，5242880 元素 × 2 Byte = 10485760 Byte。
  - /X：stream_input，形状 [5120]，次数 8，40960 元素 × 2 Byte = 81920 Byte。
- 完整 resident 容量：10485760 Byte；详见该记录的 capacity 和 components。

## S4
- `wl_7b_gate_prefill_b1_l2048_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 1, "N_new": 2048, "U": 2048, "lm_head_policy": "all processed tokens if this operator is selected"}`。
- Q_R = 135790592；Q_S = 14680064；M = 278099132416 OP；RI = 4/37。
- 写入／输入事件：
  - /W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - /X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

## S5
- `wl_7b_gate_reload_b1_l2048_e4_lo`；映射 `G2_LO`。
- 窗口：`{"B": 1, "U": 2048, "epoch_vectors": [512, 512, 512, 512], "eviction_cause": "evict this operator between token chunks to schedule other operators in a shared resident region"}`。
- Q_R = 543162368；Q_S = 14680064；M = 278099132416 OP；RI = 1/37。
- 写入／输入事件：
  - /W：resident_write，形状 [18944, 3584]，次数 4，271581184 元素 × 2 Byte = 543162368 Byte。
  - /X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

## S6
- `wl_7b_attn_prefill_b1_l2048_lo`；映射 `A1_LO`。
- 窗口：`{"B": 1, "C_before_append": 0, "N_new": 2048, "L_visible_final": 2048, "layer_instances": 1}`。
- Q_R = 4194304；Q_S = 132177920；M = 30079451136 OP；RI = 16135/512。
- 写入／输入事件：
  - /K：resident_write，形状 [2048, 128]，次数 4，1048576 元素 × 2 Byte = 2097152 Byte。
  - /query：stream_input，形状 [128]，次数 57344，7340032 元素 × 2 Byte = 14680064 Byte。
  - /V_transposed：resident_write，形状 [128, 2048]，次数 4，1048576 元素 × 2 Byte = 2097152 Byte。
  - /attention_probability：stream_input，形状 ['C+j']，次数 57344，58748928 元素 × 2 Byte = 117497856 Byte。
- 完整 resident 容量：4194304 Byte；详见该记录的 capacity 和 components。

## S7
- `wl_7b_attn_decode_b8_v8192_lo`；映射 `A1_LO`。
- 窗口：`{"B": 8, "C_before_append": 8191, "N_new": 1, "L_visible_final": 8192, "layer_instances": 1}`。
- Q_R = 16384；Q_S = 3727360；M = 939524096 OP；RI = 455/2。
- 写入／输入事件：
  - /K：resident_write，形状 [1, 128]，次数 32，4096 元素 × 2 Byte = 8192 Byte。
  - /query：stream_input，形状 [128]，次数 224，28672 元素 × 2 Byte = 57344 Byte。
  - /V_transposed：resident_write，形状 [128, 1]，次数 32，4096 元素 × 2 Byte = 8192 Byte。
  - /attention_probability：stream_input，形状 ['C+j']，次数 224，1835008 元素 × 2 Byte = 3670016 Byte。
- 完整 resident 容量：134217728 Byte；详见该记录的 capacity 和 components。

## S8
- `wl_7b_train_gate_u2048_a1_lo_dx`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 0；Q_S = 77594624；M = 278099132416 OP；RI = ∞。
- 写入／输入事件：
  - /dY：stream_input，形状 [18944]，次数 2048，38797312 元素 × 2 Byte = 77594624 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

## S9
- `wl_7b_train_gate_u2048_a1_lo_dw`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 14680064；Q_S = 77594624；M = 278099132416 OP；RI = 37/7。
- 写入／输入事件：
  - /X_transposed：resident_write，形状 [3584, 2048]，次数 1，7340032 元素 × 2 Byte = 14680064 Byte。
  - /dY_transposed：stream_input，形状 [2048]，次数 18944，38797312 元素 × 2 Byte = 77594624 Byte。
- 完整 resident 容量：14680064 Byte；详见该记录的 capacity 和 components。

## S10
- `wl_7b_train_gate_u2048_a1_lo`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 286261248；Q_S = 169869312；M = 834297397248 OP；RI = 54/91。
- 写入／输入事件：
  - forward/X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
  - dX/dY：stream_input，形状 [18944]，次数 2048，38797312 元素 × 2 Byte = 77594624 Byte。
  - dW/X_transposed：resident_write，形状 [3584, 2048]，次数 1，7340032 元素 × 2 Byte = 14680064 Byte。
  - dW/dY_transposed：stream_input，形状 [2048]，次数 18944，38797312 元素 × 2 Byte = 77594624 Byte。
  - end_update/W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - end_update/W_transposed：resident_write，形状 [3584, 18944]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
- 完整 resident 容量：286261248 Byte；详见该记录的 capacity 和 components。
- `wl_7b_train_gate_u2048_a16_lo`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 16, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 506462208；Q_S = 2717908992；M = 13348758355968 OP；RI = 864/161。
- 写入／输入事件：
  - forward/X：stream_input，形状 [3584]，次数 32768，117440512 元素 × 2 Byte = 234881024 Byte。
  - dX/dY：stream_input，形状 [18944]，次数 32768，620756992 元素 × 2 Byte = 1241513984 Byte。
  - dW/X_transposed：resident_write，形状 [3584, 2048]，次数 16，117440512 元素 × 2 Byte = 234881024 Byte。
  - dW/dY_transposed：stream_input，形状 [2048]，次数 303104，620756992 元素 × 2 Byte = 1241513984 Byte。
  - end_update/W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - end_update/W_transposed：resident_write，形状 [3584, 18944]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
- 完整 resident 容量：286261248 Byte；详见该记录的 capacity 和 components。

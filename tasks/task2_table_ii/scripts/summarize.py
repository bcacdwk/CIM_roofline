"""Generate support comparisons and inject exact main-row substitutions."""
import json
from pathlib import Path
from counts import unpack
ROOT=Path(__file__).resolve().parents[1]


def main():
    records=json.loads((ROOT/"data/demands.json").read_text())["records"]
    by={r["wl_id"]:r for r in records}
    picks=[
        "wl_7b_attn_prefill_b1_l2048_lo","wl_7b_attn_prefill_b1_l8192_lo",
        "wl_14b_attn_prefill_b1_l2048_lo","wl_14b_attn_prefill_b1_l8192_lo",
        "wl_7b_attn_decode_b1_v2048_lo","wl_7b_attn_decode_b1_v8192_lo",
        "wl_14b_attn_decode_b1_v2048_lo","wl_14b_attn_decode_b1_v8192_lo",
        "wl_7b_attn_prefill_b1_l2048_tp_r128_c128","wl_7b_attn_prefill_b1_l2048_tp_r192_c160",
        "wl_7b_attn_decode_b1_v8192_tp_r128_c128","wl_7b_attn_decode_b1_v8192_tp_r192_c160",
        "wl_7b_gate_prefill_b1_l2048_load_lo","wl_7b_gate_prefill_b1_l2048_load_tp_r128_c128","wl_7b_gate_prefill_b1_l2048_load_tp_r192_c160",
        "wl_7b_k_decode_b8_int8_int8_lo","wl_7b_k_decode_b8_int8_int4_lo",
        "wl_7b_qkv_fused_u8_lo","wl_7b_gate_up_fused_u8_lo",
        "wl_7b_attn_decode_b1_v2048_copy7_lo",
        "wl_7b_train_gate_u2048_a1_lo_dw","wl_7b_train_gate_u2048_a1_lo_dw_alternative",
        "wl_7b_train_gate_u2048_a1_lo","wl_7b_train_gate_u2048_a16_lo"]
    lines=["# 参数和边界对照（脚本生成）","","下表的值均为精确值。每条记录及其事件可从 demands.json / task3_demands.json 查到。", "", "| wl_id | Q_R (Byte) | Q_S (Byte) | M (OP) | RI | 全 resident 容量 (Byte) |", "|---|---:|---:|---:|---:|---:|"]
    subset=[]
    for k in picks:
        r=by[k]; e=r["exact"]; ri=str(unpack(e["RI"])) if e["RI"]["status"]=="finite" else "∞"
        lines.append(f"| `{k}` | {unpack(e['Q_R_Byte'])} | {unpack(e['Q_S_Byte'])} | {e['M_OP']} | {ri} | {unpack(r['capacity']['full_resident_Byte'])} |")
        subset.append({"wl_id":k,"exact":e,"capacity":r["capacity"]})
    lines.extend(["","## 读数规则","","- K 输出轴是 token，V 转置输出轴是 d，因此 tile 变化对 QK 和 AV 输入影响不同。","- INT8 输入固定时，INT4 权重对照只将 resident bytes 减半，RI 倍增。","- 7 份 KV copy 保留原有 query 总工作，写入与容量同时乘 7。","- dW alternative 的输出是 dW 转置，归置后的数学梯度相同；其临时 resident 和 streaming 角色交换。","- cycle 行是完整周期，dW 行是一 microbatch 的分项；不能同时相加。"])
    (ROOT/"data/parameter_comparisons.md").write_text("\n".join(lines)+"\n")
    (ROOT/"data/parameter_comparisons.json").write_text(json.dumps(subset,indent=2)+"\n")
    support=ROOT/"SUPPORT.zh.md"
    text=support.read_text(); start="<!-- BEGIN GENERATED SUBSTITUTIONS -->"; end="<!-- END GENERATED SUBSTITUTIONS -->"
    substitutions=(ROOT/"data/table_substitutions.zh.md").read_text().split("\n",3)[-1]
    substitutions=substitutions.replace("## S","### S")
    text=text.split(start)[0]+start+"\n"+substitutions+"\n"+end+text.split(end)[1]
    support.write_text(text)


if __name__=="__main__": main()

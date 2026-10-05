# 候选 B / E 独立复核

审查 Agent 未参与 B/E 的绘图实现。原 Task I、Task II、B/E 目录与 shared 均只读；复核脚本和报告只写本 review 目录。

**PASS：B/E 数值、最终实际图面与 caption 的独立复核全部通过。**

- [独立复核脚本](independent_BE_check.py) · [机器可读结果](independent_BE_check.json)
- 复现：从仓库根执行 `PYTHONDONTWRITEBYTECODE=1 python tasks/task3_matching_figures/review/independent_BE_check.py`。
- 不调用 `shared/interface.py`、`build_shared.py` 或候选构图函数作为期望值。只用 shared 中的来源定位符回到已认可 Task I 原始 `mapping_interface`，直接读取 `T_R_ns`、`delta_S_ns`、K/N、字节数；Task II 直接读现行模型输入与各 Q/G/K/V component。

## B：数据与计量连接

8 个需求点、6 条模型专属有效硬件射线、24 个模型—硬件状态全部复算通过。

1. 对 Task II QKV component 逐项加和输出维与 resident 字节，输入加和后扣除原 `shared_input_bytes_removed`，得到 `Q_S=UD`、`Q_R=DN_proj`。Qwen gate 包含在 N_proj=5120 中；MiMo N_proj=27136。没有重复计算共享逻辑输入。
2. 两模型 D、N_proj 均完整整除 128，无 padding。Qwen 为 m_K=16、m_N=40、M=640；MiMo 为 48、212、10176。原生累计输入是 `M U 128=m_N Q_S`，每个 tile 只完整装载一次，总 resident 字节仍等于逻辑 Q_R。
3. 用直接累计时间 `T_S=M U Delta_S`、`T_R,total=M T_R` 独立恢复 `rho_eff=Q_S/T_S`、`tau_eff=Q_R/T_R,total`；导出的有效射线与 B 数据逐值相符。射线上方意味着 streaming 组件累计时间更大，下方意味着 resident 组件时间更大；与 A 的能力平面上下侧相反，但同一 U 的瓶颈标签相同。
4. 绝对 Byte 差异正确：MiMo/Qwen 的 Q_R=15.9 倍，同 U 的 Q_S=3 倍；Qwen/MiMo 的有效射线斜率=5.3 倍。两模型经明确分块映射后仍保留各硬件原生 U*。

每条模型—硬件射线在 0.999 U*、U*、1.001 U* 检查，18 个邻域判定均为 resident / balanced / streaming。已读 B caption 与 README，它们明确限定到组件服务上界，保留 input replay，并把跨 tile 归约、切换等开销置于参考之外；未把组件时间之最大值冒充完整顺序墙钟时间。实际 PNG 已看，点的位置、Byte 标签、两模型射线转换与上下侧说明一致。

## E：解析改进收益

直接把“能力提高 f 倍”改写成对应组件服务时间除以 f，独立计算上界收益：

```text
T_S = U Delta_S; T_R = full native load service time
G_stream(f) = max(T_S,T_R) / max(T_S/f,T_R)
G_resident(f) = max(T_S,T_R) / max(T_S,T_R/f)
```

3 个真实参考状态、1548 个曲线数值、2 倍改进点及瓶颈通路的饱和倍率全部通过。

| 原生参考工况 | 直接 T_S / T_R (ns) | 初始瓶颈 | 仅 streaming ×2 的收益 | 仅 resident ×2 的收益 | 改瓶颈通路的收益上限 |
|---|---:|---|---:|---:|---:|
| RRAM, U=128 | 656640 / 1911760 | resident | 1.000000× | 2.000000× | 2.911427875× |
| MRAM, U=128 | 103680 / 107520 | resident | 1.000000× | 1.037037037× | 1.037037037× |
| MRAM, U=1K | 829440 / 107520 | streaming | 2.000000× | 1.000000× | 7.714285714× |

MRAM U=128 的“接近平衡”是数值事实：P_bound/rho=0.964285714；resident 仍是瓶颈，但单独提高 resident 能力的剩余上界增益只有 3.7037%。另对 RRAM/MRAM 的 U* 邻域做了 6 个检查，判定与参考响应均连续一致。这里的收益只对应解析两通路上界，不代表相同工程投入、功耗/面积收益或实测加速。

## 跨图与本轮修改记录

对 B/E 与 A/C/D 导出数据中的相同硬件、相同 U 做了 23 项直接比较（候选不包含某 U 时不造点），瓶颈标签全部一致，尤其 MRAM U=128 仍为 resident-bound。用于比较的临界值再次由原始 T_R/Delta_S 得到，未用某张图的圆或区间代替真实情景。

E 第一版 PNG 发现两处具体布局问题，已回报 supervisor 交作者修改：x 轴标题与线型图例重叠，各面板 2× 数值行与底部说明重叠。已亲自复看 E 最终 7.16 × 4.15 in PNG：x 轴标题、逐面板 2× 读数、公共图例、底部说明四层明确分离，未见重叠；“Gain cap”与图意一致。已读最终 caption/README，原生 W[N,K]、固定另一通路、解析收益范围及非等成本含义齐全。E 图面审查通过。B 最后将最右侧 1 GiB 刻度向纸内收齐；已亲自复看合并 PDF 的 144 dpi `rendered/candidate_B.png`，刻度完整、无裁边，图面通过。B/E 未发现需要修改共同公式或已认可上游数据的问题。

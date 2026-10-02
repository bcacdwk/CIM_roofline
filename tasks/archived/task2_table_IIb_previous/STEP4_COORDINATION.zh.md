# Step 4 协调记录与共同接口

2026-09-25。当前起点 HEAD / Step 3 审阅提交：`e472a0d864b8fb9afb14b0c306217a0e5653e122`；初始工作区干净。Step 1/2/3 均已通过，旧稿状态作为历史保留。

## 所有权与调度

| 责任 | 独占写入目录 | 交付工况 |
|---|---|---:|
| Agent A | `table_IIb/01_qkv_projection/` | 6 |
| Agent B | `table_IIb/02_ffn_moe/` | 18 |
| Agent C | `table_IIb/03_attention/` | 36 |
| Agent D | `table_IIb/04_crosscheck/` | 60 条独立复核与统一汇总 |
| 主 Agent | 本文件、README、study_plan.json、STEP4_REVIEW.zh.md | 协调、亲自审阅与状态 |

并发上限是主 Agent 加三个子 Agent。A/B/C 同时启动；首个计算任务交付释放名额后启动 D，D 可以在其余任务完成前准备复核，正式验收只读取明确交付的版本。主 Agent 不接管三类计算代码/详细推导。

所有 Agent 禁止 Git 暂存、提交、推送、重置、切换分支。目录之外只读；共享方法、models.json、原始证据、pilot、Table II(a)、Task I 与主论文不改。疑似共享方法问题立即向主 Agent 报告，不各自更换计量规则。

Python 运行设 `PYTHONDONTWRITEBYTECODE=1` 或在跨目录导入前禁用 bytecode；既有回归只调用默认只读检查，不执行会覆盖历史 PDF 的 shared/pilot 构建脚本。

## 固定共同接口（step4-delivery-v1）

以 `data/study_plan.json` 的六模型顺序、四行标识、B/L 为准。共享参考为 `WS128-INT8-semantic-banks-v1`：128×128、各角色 INT8/1 Byte、ports 主边界、operator 对照、独立语义矩阵、每 KV head 一份状态、逐前缀组织。

每个计算目录提供 `data/results.json`，根对象包含 `schema_version`、`cases`。每条沿用 pilot：

```text
case_id = model_id/row/one_token      (QKV)
        = model_id/ffn_or_moe/B       (B 为十进制整数)
        = model_id/attention_prefill/L 或 model_id/attention_decode/L
model_id, row, model_revision, selected_layer, shared_reference_id
B 或 L（QKV 可保留 L:null，与 pilot 一致）
result:
  ports / operator: Q_S, Q_R, RI, tile_evaluations
  parts: Q[,G],K,V 或 gate,up,down 或 QK,AV
    每分项含 ports/operator 同字段与 layout
  capacity: valid_resident_bytes, allocated_tile_bytes, resident_tiles
```

整数原样存储；非整数分数为 `{numerator, denominator}`，无穷用 `infinity` 字符串。`tile_evaluations` 是 ports 的实际调用整数，operator 可为 null。RI 必须分别从对应边界字节求比，不能混用；operator 分项是独立入口，聚合共享输入扣除量另存 `operator_shared_input_overlap_removed`。

`layout` 至少保存矩阵 N×K、copies、有效/分配容量与 resident tile 数；沿用 pilot 键名为宜。Attention 保留 initial_KV_tokens、final_KV_tokens、initial_valid_resident_bytes、append_shape_per_kv_head，以及分项 append 切片/次数和有效尾块。最终容量是 `capacity.valid_resident_bytes`，累计写入始终是 Q_R。更多局部字段可自由增加。

计算主流程可以调用共享 API；独立检查必须从原始配置或真实 tile/不同求和组织形成预期值。重叠工况重新生成，与 pilot 按语义字段对照，不复制 pilot 结果作为正式数据。

`study_plan.json` 的阶段状态由主 Agent 收尾更新；数值复现应校验其实际科学输入子集（模型序、行、B/L、参考），不因阶段状态变化制造结果过期。不变的模型/共享定义/原始实现仍可校验完整文件哈希。

## 每个计算目录的最低交付

- 中文独立 TeX/PDF、六模型概览、简短 README。
- 精确 `data/results.json`（可另有 CSV），使用的配置、revision、来源定位和必要哈希。
- 主计算与独立检查入口；局部 build/tmp 和局部忽略规则。
- PDF 编译、页面渲染并逐页查看，保存 QA 记录。沿用本机 XeLaTeX/latexmk、`/opt/anaconda3/bin/python` 与 pypdfium2 可用环境；按 PDF 技能办理。
- 全部完成后最后写 `DELIVERY.json`，含 `status: ready_for_review`、递增 `delivery_revision`、`case_count`、results/PDF/TeX/README/checks 的路径与 SHA-256、复算命令。修订开始先撤销 ready，修订完更新交付版本与哈希，再通知主 Agent。

Agent D 只验收已收到 READY 通知且 DELIVERY 哈希一致的最终版本。D 自行维护独立检查、统一 JSON/CSV、双边界四行六模型 Markdown 预览与复核报告。统一记录保留原目录、results 文件哈希和 case_id/数组位置等追踪信息。发现问题交回责任 Agent 修改，D 不编辑上游结果。

## 交付与迭代日志

1. 共同接口固定后，实际并行启动 `/root/qkv`、`/root/ffn`、`/root/attention`，分别承担 A/B/C；三者均处于运行状态。用户中途指示“继续”后，主 Agent 确认三个任务仍在运行，未重复启动。
2. 主 Agent 预审固定配置与实现：核对 Qwen3.5 是 Dense、Hy3 原生 Q 输出宽为 8192、Ling 融合 QKV 与 128K 的官方 YaRN/运行端条件；将容易混淆的 Dense/专家宽度和结构差异发送给责任 Agent。
3. A 首次 READY（revision 1）后，实际启动 `/root/crosscheck` 承担 D。D 收到 A、B、C 的正式交付通知，并按各目录 DELIVERY 的路径基准和哈希读取；未把在写中间文件作为最终数据。
4. 主 Agent 亲读 A/B/C 三份 TeX 与六模型概览，也检查了主计算和独立检查的组织方式。A/B 初稿有通式、数据与比较，但缺少一条连续数字代入链，要求各补 Qwen3.6 代表工况；A 同时把本地容量符号从 M 改为 C_R，避免与理论约定的有用 OP 符号相混。修订只涉及文稿/QA/交付版本，不改变科学数据或共享版本。
5. A 已交 revision 2，主 Agent 已逐页查看最终 4 页 PNG，完整代入与所有表格可读；数据哈希与 revision 1 相同。C revision 1 的 8 页稿件已亲读并逐页查看，MiMo cache update 的本地第 309 行及 Ling 官方扩展条件再次核对，未发现需要返工的问题。
6. B 已交 revision 2，新增 Qwen3.6 单专家 B=8 的矩阵、tile、分项字节、调用与双边界 RI 代入；主 Agent 重新查看最终 4 页，数据和检查文件哈希不变。主 Agent 亲自运行 A/B/C 的 generate/check 默认只读入口，全部通过。
7. D 独立复核 60 汇总/146 分项与 22 个 pilot 既有工况，全部精确一致；5 项只读回归及受保护基线检查通过。主 Agent 亲读其程序、完整报告和统一预览；要求将“每 head”明确为“每 KV head 一份 K/V”，并在 README 链接稳定后刷新回归日志的链接计数。没有修改科学结果。
8. 最终交付版本 **A2/B2/C1/D1**。D 的 DELIVERY SHA-256 为 `a8b0f5c90dd5fd4e242d73113dd85aa4fcbec94240898985329973ad59b325ff`；统一 results SHA-256 为 `c31af181f16bba59b12690d00f4ac16cd022941acd036630b405bd20aaea2612`。上游 52 个清单项及 D 本地 11 个清单项均已核验。

**内部验收完成；Step 4 完成待用户审阅。** 用户尚未审阅通过 Step 4；Step 5 未启动。完整结果、检查与条件见 [STEP4_REVIEW.zh.md](STEP4_REVIEW.zh.md)。

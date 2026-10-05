# 共同接口与 A/C/D 独立复核

**结论：通过，本轮没有发现需要追加修改的数值或口径问题。** 复核人负责 B/E 绘图，但未编写共同适配器或 A/C/D；这里不把自己的 B/E 自查称为独立审查。已阅读共同方法、A/C/D 脚本和英文 caption，并亲自查看三张实际 PNG。状态仅为内部审阅，不代替用户选图。

## 独立数据链

[复核脚本](independent_ACD.py) 未导入共享计算函数或绘图作者的生成器。预期值直接读取 Task I 的 30 条原生 `mapping_interface`、已认可圆图 points CSV，以及 Task II 现行整数需求结果；输出为 [机器报告](independent_ACD.json)。

| 检查 | 数量／结果 |
|---|---|
| 原始来源 SHA-256 | 9 个，全相符 |
| Task I 原生时延／Byte → rho、tau、U*、sigma | 30 情景，全相符 |
| Task II(a) 有限整数需求 | 30 状态，全相符 |
| 两 QKV 原始逻辑需求 → serial full-tile 映射 | 8 状态、24 个硬件情景，全相符 |
| A 坐标与真实成对情景 | 30 点，无拼接端点 |
| A 有限情景圆 | 10 个；两端在圆上、典型在圆内、中心规则一致 |
| C 阈值与跨图分类 | 30 阈值、120 分类，全相符 |
| D 扫描与解析曲线 | 18 点、1068 曲线值，全相符，3 个精确折点均在曲线中 |
| 所有原生 U* 邻域 | 90 项，即 0.999999、1、1.000001 倍阈值 |

A 的横轴是 tau、纵轴是 sigma=N·rho；不是将 Task II 算子 RI 与未转换的原生 RI* 比较。A 上方 resident-bound 与 C 中 U<U* 一致。D 的 min(1,U/U*) 也与原生 `min(rho,tau U/N)/rho` 独立复算一致。圆没有进入分类公式。

QKV 的共享扣除保留逻辑入口计数，额外重放只进入 native 组件输入；两模型各自的 m_N 使 rho_eff=rho/m_N，而 tau_eff=tau。用总 tile 数乘原生服务时间，能复算每个映射情景的两路累计时间。该方法支持组件资源上界与瓶颈比较；未认证跨 tile 归约或实际完整部署，也没有延伸到 FFN/Attention append。

## 关键跨界复核

- MRAM、U=128：short/reference/long 分别 resident/resident/streaming。reference 的 U/U*=0.9642857143，因此 D 近平台的 U=128 点仍为 resident-bound；C 注释正确，A 对该真实点的判定相同。
- 2D NOR、U=128K：short/reference 为 streaming-bound，long 为 resident-bound。有限情景圆或区间不能替代这一逐情景判定。
- 典型 MRAM、NAND、NOR 的 D 精确折点均使用原生 T_R/Δ_S，未从显示四舍五入值反推，也未从圆内采样。

## 实际图面与 caption 审查

- **A，7.16 × 4.35 in。** 实际 PNG 中十类介质、真实成对点和四条 U 参照可辨识。纵轴写明 sigma=N·rho，突出 U=128 的上下方说明只对该参照，不用一层固定底色指代所有工作负载。caption 明确有限情景圆语义、不同原生形状仅转移复用要求、MB/s 十进制单位。
- **C，7.16 × 4.05 in。** 对数 U* 坐标、典型值列和真实三情景区间清楚。小幅纵向偏移只分开分类行内标记，数值坐标 U* 未变；说明与 caption 已交代。相对 A 新增“至少需多少复用”的直接阅读价值，绝对能力信息较少。
- **D，7.16 × 2.60 in。** 三小面板共享归一化纵轴，给出原生 rho，避免同平台等吞吐的误读。MRAM U=128 点与折点很近是原始数据的真实结果；caption 明确 96.43% 与仍 resident-bound，未移动点。六个有限扫描状态保留，平台上的状态也没有删去。相对 A 新增复用收益和饱和过程，牺牲其他七类介质与情景范围。

PDF MediaBox 尺寸由独立读取验证，与声明目标一致。阅读必须以双栏宽为准；本轮没有把可读性建立在大画布后缩到单栏的做法上。没有综合产品排名或“streaming-bound 即性能最优”的结论。

## 运行

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/review/independent_ACD.py
```

该脚本只写自己的审查 JSON，不运行原任务或作者生成器。图像目视审查是本轮人工检查记录，不由数值脚本自动宣称完成。

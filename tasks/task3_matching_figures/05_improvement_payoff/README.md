# 候选 E：瓶颈决定能力改进的上界收益

**目标双栏：7.16 × 4.15 in，字号 7.1–11 pt。** 英文图面、PNG 240 dpi、PDF/SVG 矢量文件。已完成第一轮 supervisor 审阅与版面修改，待用户选图与审阅。

- [PNG](output/figure.png) · [PDF](output/figure.pdf) · [SVG](output/figure.svg)
- [英文 caption](caption.en.md) · [完整绘图数据](plotted_data.json) · [数值验证](validation.json)
- 只读输入：[共同数据](../shared/data.json)、[共同计量说明](../shared/README.zh.md)。

## 问题、工况与读法

在一个明确的硬件原生完整装载／向量服务边界，应该优先改善 streaming 还是 resident 更新能力？改善到什么程度后另一条通路会限制收益？

三个面板是：典型 RRAM W[64,128]、U=128；典型 MRAM W[32,256]、U=128；相同 MRAM、U=1K。W 的形状为 [N,K]，不是 [K,N]。两个 U 均来自现行 Task II 的复用扫描要求，移植的是复用次数；这里用各硬件原生矩阵的完整服务，不声称把 W[128,128] 直接部署到不同原生形状上。

RRAM 的状态明显 resident-bound，MRAM 的 U=128 状态仅稍微 resident-bound，MRAM 的 U=1K 为 streaming-bound。选点形成“明确单侧受限—接近平衡—同硬件随需求改变瓶颈”的对照，没有改变任何真实硬件点。颜色仍区分介质（RRAM 红、MRAM 绿），实线只提高 rho、虚线只提高 tau；同一能力倍数 f=2 的实心/空心介质符号标注对应增益。

共同 x 轴 f 从 1 到 16，对数显示；共同 y 轴为相对原始两路参考上界的增益，1 表示上界不变。MRAM U=128 的 1.037× 上限保留真实位置，未通过独立放大纵轴夸大收益。文字和引线使接近重合的曲线仍能理解。

## 公式与结论范围

原始参考上界：P_0=min(rho,tau·U/N)。两种解析情景分别为：

```text
streaming-only gain = min(f·rho, tau·U/N) / P_0
resident-only gain  = min(rho, f·tau·U/N) / P_0
```

没有引入新器件数据或成本模型。f 不代表相同面积、能耗或工程投入。min 是理想两通路资源上界；真实串行服务、资源共享或额外开销可使实现性能更低。“改善非瓶颈通路没有收益”只指本上界，不泛指实测完整任务时间。

1. RRAM U=128：只提高 rho，上界保持 1；tau 提高 2× 带来 2× 上界，最终在 2.9114× 处受 streaming 限制。
2. MRAM U=128：U*=132.7407，仅略高于 128。tau 提高到 1.0370× 就遇到另一条通路；继续提高单条通路几乎无益，说明平衡附近需要协同改变两路能力才能获得大幅上界增长。
3. MRAM U=1K：当前瓶颈转为 streaming；rho 提高 2× 带来 2× 上界，最终 7.7143× 饱和。相同硬件的优先改善方向随 U 改变。

相对候选 A，本图把硬件—需求平衡翻译成解析改进决策；相对 D，本图固定 U 改变能力，而 D 固定能力改变复用。E 适合设计启示重点，代价是需要解释解析倍数并避免等成本最优的误读。

## 复现与审查

从仓库根运行：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/05_improvement_payoff/build.py
```

仅共享接口读数；每条曲线使用闭式上界、显式加入精确折点和 f=2。`plotted_data.json` 保存完整原生记录、native Q_R/Q_S、所有曲线数值与 f=2 结果；`validation.json` 逐点核对闭式限幅关系。样本量是曲线绘图采样，不是新的硬件测量。

自查已查看实际 PNG；第一版发现底部 x 轴标题、图例和数值说明挤压，已调整为 4.15 in 高、逐面板两行 2× 读数及独立公共图例。没有移动真实工况或放大近平衡增益。需按双栏宽使用。

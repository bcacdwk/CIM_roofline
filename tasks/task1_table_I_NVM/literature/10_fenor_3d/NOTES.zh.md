# 10 — 3D FeNOR／vertical FeFET

保留四篇直接相关的器件/小阵列和栅堆栈研究，包括指定的 Zhou 2025/2026。NOR 与 AND 拓扑、半选/相邻扰动、器件脉冲与宏级模拟分开。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="FENOR-01"></a>
## FENOR-01 — 3D NOR-type FeFETs with Record Endurance of 10^11, Fast Erase of 50 ns, and Immediate Read-After-Write for In-Memory Learning

**核心** · 2025 · Symposium on VLSI Technology and Circuits · [全文](FENOR-01_2025_3DNOR_FeFET.pdf)

**身份与版本：** Yuejia Zhou, Runteng Zhu, Wenpu Luo, Xiaojian Xu, Siyuan Qi, Zhiyuan Ning, Liang Chen, Hanyong Shao, Kechao Tang, Ru Huang。User-supplied 3-page manuscript; no version/date identifier on PDF。

**用途与结构：** 指定 Zhou 2025 文件确认 8×8×3 IGO/HZO NOR-type；PGM/ERS、read-after-write、层间差异及 cell 逻辑有实际测量。

**正文定位：** p.1，Fabrication/Speed/Simulation；pp.2–3，Figs.2–12。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；IGO／HZO；NOR-type；器件偏置分条件。

**使用限制：** NN benchmark 与大阵列延时为模拟；单 cell/小阵列测试不等于全精度 macro 周期。

**证据关系：** 与 FENOR-02/06 同团队；逐篇保留不同结构、栅堆栈和测试条件。

**出版标识：** [DOI](https://doi.org/10.23919/vlsitechnologyandcir65189.2025.11074820)。

<a id="FENOR-02"></a>
## FENOR-02 — 3D Vertical FeFET Array with Record Endurance (>10^12), Fast Writing (±2V, 20 ns), Disturb Immunity, and Kb-scale Verification for High Density 1T RAM

**核心** · 2026 · Symposium on VLSI Technology and Circuits T11.1 · [全文](FENOR-02_2026_Vertical_FeFET_Array.pdf)

**身份与版本：** Yuejia Zhou, Yuancheng Yang, Liang Chen, Mingxiang Yu, Wenpu Luo, Zhiyuan Ning, Weiqin Huang, Xiaojian Xu, Jing Guo, Runteng Zhu, Hanyong Shao, Zhiliang Xia, Zongliang Huo, Kechao Tang, Ru Huang。User-supplied 3-page manuscript; no version/date identifier on PDF。

**用途与结构：** 指定 Zhou 2026 文件实际为 3D-AND FeFET；32×32×4 制造结构与 16×16×4 验证范围分开，写入/半选/相邻扰动方案有直接依据。

**正文定位：** p.1，array/disturb/benchmark；pp.2–3，Figs.7–11。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；IGO／HZO；AND-type vertical FeFET；SL/SS 与 O-rich/O-poor 分条件。

**使用限制：** 20 ns 为偏置和结构限定的 switching；TCAD/SPICE read 与密度预测不当作实测宏；不因简称 FeNOR 忽略 AND 结构。

**证据关系：** 与 FENOR-01/06 同团队；最新结果不替代不同器件条件下的证据。

**出版标识：** [DOI](https://doi.org/10.1109/vlsitechnologyandcir65830.2026.11577291)。

<a id="FENOR-04"></a>
## FENOR-04 — Efficient Large Scale Neural Network Acceleration With 3-D FeNOR-Based Computing-in-Memory Design

**核心** · 2025 · IEEE Transactions on Electron Devices · [全文](FENOR-04_2025_FeNOR_CIM_Design.pdf)

**身份与版本：** Yang Feng, Dong Zhang, Chen Sun, Zijie Zheng, Yue Chen, Qiwen Kong, Gan Liu, Xiaolin Wang, Yuye Kang, Kaizhen Han, Zuopu Zhou, Leming Jiao, Jixuan Wu, Jiezhi Chen, Xiao Gong。完整正式论文/技术资料。

**用途与结构：** ZnO/MFMIS 3D FeNOR 器件、阵列电流逻辑实测，与 4096×4096 网络/外围仿真分开；扩展版补写入偏置与变异条件。

**正文定位：** p.2，版本声明；pp.4–6，Figs.7–14、III–IV。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；ZnO/MFMIS 3D FeNOR；小阵列测量 + 大阵列网络模拟。

**使用限制：** 大阵列 4096×4096 不是流片尺寸；高电压时 charge injection 影响 MW；system energy 不作为实测统一外围。

**证据关系：** 以当前期刊全文作为该工作的唯一资料文件。

**出版标识：** [DOI](https://doi.org/10.1109/ted.2025.3554164)。

<a id="FENOR-06"></a>
## FENOR-06 — Gate Stack Engineering of 3D Oxide Channel FeNOR Memory with High-Speed and Reliabilitity

**核心** · 2026 · 2026 10th IEEE Electron Devices Technology & Manufacturing Conference (EDTM) · [全文](FENOR-06_2026_GateStack_FeNOR.pdf)

**身份与版本：** Yuejia Zhou, Ru Huang, Kechao Tang。完整正式论文/技术资料。

**用途与结构：** 2026 EDTM 对照 MFS/MFIS/MIFS/MIFIS，写速度随栅堆栈与偏置改变，可解释 Zhou 系列与其他 FeNOR 差异。

**正文定位：** pp.1–2，B/C；p.3，Figs.5–10。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；3D oxide-channel FeNOR；不同栅堆栈分条件。

**使用限制：** 与 Zhou 同团队，不能当独立外部验证；耐久与写速测试偏置不同，不能拼接最优点。

**证据关系：** 与 FENOR-01/02 同团队；FENOR-04 提供另一团队/结构的直接交叉。

**出版标识：** [DOI](https://doi.org/10.1109/edtm65772.2026.11498024)。


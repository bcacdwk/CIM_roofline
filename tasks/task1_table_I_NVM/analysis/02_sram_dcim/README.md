# SRAM DCIM 介质试算

当前统一入口：[十例复核](../TEN_CASE_REVIEW.zh.md) · [结果JSON](../data/ten_case_results.json) · [结果CSV](../data/ten_case_results.csv)。PDF首页结果卡与这些导出由统一适配器生成；本例原始未取整结果仍在 `data/results.json`。摘要统一十进制MB/s，情景分类见统一复核。


当前交付为 D6CIM 型、精确 INT8 数字计算与普通 SRAM 更新的独立中文分析。沿用 `shared_baseline` 的共同 28 nm、128×128 INT8 输入/权重、128×24-bit 输出和单更新域；按 R2 保留有原文依据的 16 项归约，每向量 512 个完整 MAC 槽。结果是有条件的参考设计，未称同芯片配对硅测，也未制作最终 Table I。

- [中文分析 PDF](output/sram_dcim.pdf)：6 页，含两路完整服务、成对范围、R0 资源对照和参数证据表。
- [章节 TeX](tex/02_sram_dcim.tex)；[独立入口](tex/sram_dcim.tex)。
- [输入、原始证据、R1–R5 例外及基线哈希](data/inputs.json)；[未取整结果和逐情景阶段覆盖](data/results.json)。
- [紧凑参数证据表](notes/evidence.zh.md)；[方法使用约束与QA记录](notes/method_review.zh.md)。
- [最小计算检查脚本](scripts/check_sram_dcim.py)；[构建入口](scripts/build.sh)。

主情景范围：ρ=24.90–58.03 MB/s，τ=1600–7273 MB/s，成对 RI*=0.007980–0.01556。参考点为 ΔS=2570 ns、ΔR=5 ns、ρ≈49.81 MB/s、τ=3200 MB/s、RI*≈0.01556。B_S=128 Byte，B_R=16 Byte。

D6CIM 原宏的128×128是物理bit阵列，仅128×16个INT8权重；本实例用8个容量分片表示一份矩阵，顺序启用一片。每片安装16个HCA/BFA，总共128条，但同时活动16条；不累加独立macro峰值，无等面积主张。每轮16项而不是R0的32项，是操作次数翻倍的原因。

计算槽4.3/5/10 ns覆盖读出、乘法、归约和累加；4.3 ns由原D6CIM 0.9 V/233 MHz向上取整。普通写2.2/5/10 ns与计算时钟分开，2.2 ns由CMOS-07典型455 MHz完整同步周期支持，5/10 ns为共同节拍预算。该互补写证据为48-bit 8T、1.05 V、28 nm eFlash平台；向128-bit 6T移植需要足够驱动，是主要条件性假设，未验证固定0.9 V/25 °C的写时序。原文1.54 ns read access没有当作write。

写事务在本地memory口同沿接收命令/地址/128-bit数据，到下一可计算周期结束；完整memory周期替代已经覆盖的共同写前端。因此主情景不重复加T_W。若确有额外任务握手，参考ΔR=15 ns、τ≈1067 MB/s、RI*≈0.04669，单列为边界敏感性。R0的32项同钟资源对照也单列，未替换主情景。

复算和编译（仓库根目录执行）：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NVM/analysis/02_sram_dcim/scripts/check_sram_dcim.py
sh tasks/task1_table_I_NVM/analysis/02_sram_dcim/scripts/build.sh
```

默认计算检查只读；`--emit`只刷新本目录的派生JSON、TeX表和证据表。通过 `importlib` 导入共享计算接口，并在导入前设 `sys.dont_write_bytecode=True`。所有服务公式使用共享接口，完整周期替代仅由薄适配层组合共享操作块。`build/`、`tmp/`均忽略；原始PDF只读，未复制或修改文献。

本轮读取的共享JSON SHA256：`6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42`；共享计算脚本 SHA256：`eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3`。原始输入中记录了全部实际读取哈希。主审及最终同基线核对已完成：共享方法TeX最终SHA256为`b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9`，仅修正w_IO排印；JSON与计算脚本均未改变。本例最终8组检查、编译和逐页目视通过，数值与首轮一致。

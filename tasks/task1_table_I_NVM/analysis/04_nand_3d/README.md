# 3D NAND 局部 CIM 试算

本案例固定共同128×128 INT8逻辑任务，以SLC二阈值、BL输入/SL求和实现R0近似ACIM。已完成中文章节、独立编译PDF、逐项证据表、机器输入/结果及导入共享计算接口的检查脚本。它是带明确适配条件的参考设计，不是实测芯片性能或最终Table I。

- [中文PDF](output/nand_3d.pdf)（6页）；[连贯章节TeX](tex/04_nand_3d.tex)；[独立入口](tex/nand_3d.tex)。
- [原始参数、选择、例外与实际哈希](data/inputs.json)；[派生计数、结果及系数](data/results.json)。
- [紧凑证据表](notes/parameter_evidence.md)；[方法问题与复核记录](notes/review.md)。
- [最小检查脚本](scripts/check_nand.py)；[编译脚本](scripts/build.sh)；[渲染脚本](scripts/render_pdf.py)。

所选原生结构来自NAND-04：64块/subarray，每块13824 BL×32 WL×3 SSL。两个subarray的128块共同实现八个权重位平面×16个同时输出；八个WL组完成128输出。每个逻辑bit在一页内复制108次，匹配文献的大电流量级，仍逐输入bit计算。读侧条件范围ρ=2.27–3.36 MB/s（参考2.759 MB/s），完整ΔS=38.140/46.402/56.332 μs；它依赖SL模型时序、负载和新前端适配成功，未证明为硅测保证范围。

resident主事务固定16384 Byte整矩阵、1024数据页；一页物理1728 Byte，但只有16 Byte逻辑位片段。每块仅八个有效数据页；持续同地址全矩阵重写需要128次块erase，并重建每块一或两个校准页。一个校准WL的参考情景为：

```text
ΔR,append (μs) = 563.2 + 1024 P + C_app
ΔR,rewrite(μs) = 633.6 + 1152 P + 128 E + C_rw
τ (MB/s) = 16384 / ΔR(μs)
RI*,rewrite = (4.95 + 9 P + E + C_rw/128) / 46.402
```

P是完整SLC-CIM页program，E是完整块erase，C为整矩阵事务的额外校准时间，均以μs计。现有五篇NAND来源未给出所选两阈值电流细调状态的完整P/E绝对时间，因此数值τ/RI字段为null，保留线性系数和RI*=1对应的预算阈值，未使用MLC/TLC/QLC或共享合成物理时间代填。预擦除append只适用于声明的初始空间和校准状态；新布局/背面图案需要重校准时C_app不为零。

从本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_nand.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改输入后先运行`/opt/anaconda3/bin/python scripts/check_nand.py --emit`刷新本目录派生数据与表格。默认检查不写文件。脚本通过importlib导入共享接口，禁用pycache，未复制/修改共享公式。build与tmp由本目录.gitignore忽略；PDF与数据为当前唯一交付版本。

已核对共享JSON SHA256 `6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42`，共享脚本SHA256 `eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3`。本案例6组检查及共享12组检查通过；XeLaTeX编译、6页渲染目视检查完成，无越界或缺字。最终共享基线核对完成：参数JSON与计算API未变，方法TeX仅修正了 $w_{IO}$ 排印，其最终SHA256为 `b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9`。已按同一最终基线重跑与编译，所有数值保持不变。

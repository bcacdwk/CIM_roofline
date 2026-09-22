# 3D NAND 局部 CIM 参考估算

本案例已完成有限ρ、τ、RI*估算：主情景采用一个逻辑bit对应一个SLC cell（c=1），显式电流积分前端；108次等权复制为唯一组织对照。共同128×128 INT8任务、28 nm外围、原生页/块和单更新域保持不变。原始器件值、工程预算与推导量分开记录，不把参考预算称为SLC实测边界。

- [中文报告PDF](output/nand_3d.pdf)（6页）；[连贯章节](tex/04_nand_3d.tex)；[独立编译入口](tex/nand_3d.tex)。
- [参数及原始量→预算桥接表](notes/parameter_evidence.md)；[当前方法与验证说明](notes/review.md)。
- [机器输入、选择和来源哈希](data/inputs.json)；[有限结果和完整服务计数](data/results.json)；[验证记录](data/validation.json)。
- [计算检查](scripts/check_nand.py)；[编译](scripts/build.sh)；[渲染](scripts/render_pdf.py)。

主情景ρ=75.07–76.55 kB/s。预擦除append的τ=3.199–12.30 kB/s、RI*=6.221–23.47；同地址持续整矩阵重写的τ=1.347–4.571 kB/s、RI*=16.75–55.73。参考点ΔS=1.687682 ms；append/持续重写ΔR分别为2.560644/7.040785 s。范围由三个成对参考预算生成，单位kB为10³ Byte。

读取采用128路虚地积分前端，每路新增16 pF反馈电容、有用输出摆幅0.4 V；按128×2 nA满量程电流推导积分25 μs。原生约16 pF的SL寄生另保留。建立与恢复各分配530–750 ns工程预算；每次求值在R0两拍重构前增加一拍数字校正。c=108在相同前端与参考写预算下ρ=1248.8 kB/s、持续τ≈2.3270 kB/s、RI*=536.66；它还要求每通道27.648 μA充放电能力、1.728 V/μs压摆能力，不能把复制收益视为无资源条件。

写侧采用NAND-01完整操作量级支持的P=1.3/2.5/5 ms、E=15/30/45 ms参考服务预算，保留完整泵建立、program/verify、erase-verify及恢复。它们不迁移商品MLC/TLC终点或保证、不按小页缩时。主事务16384 Byte，对应1024数据页；持续重写还重建256校准页，支付128次块擦。两种写入都通过三次已知码读取和固定数字序列重算校准C。超出截止预算或校准未通过时返回失败，不发布状态、不计成功payload，也不隐含无限重试。

从本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_nand.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改输入后执行`/opt/anaconda3/bin/python scripts/check_nand.py --emit`刷新本案例JSON与表格。默认检查只读；通过importlib导入共享计算接口并禁用pycache。当前8组案例检查通过，XeLaTeX及6页渲染目视检查通过，日志无Underfull/Overfull、缺字或未定义引用。检查证明计数、单位和同步，不能替代前端/程序实现能力论证。

共享JSON、计算API及方法TeX均未改动，SHA256分别为：

```text
JSON  6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42
API   eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3
TeX   b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9
```

本目录仅保留当前有效结果与表格；build/tmp由本地.gitignore忽略。不修改SRAM案例、共享文件或主论文，也不生成最终Table I。

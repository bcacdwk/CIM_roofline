# 本任务区工作约定

当前任务是十个参考配置的 NeuroSim 与器件估计结合的 CIM 评估。当前入口为 `analysis/shared/run_evaluation.py`；表图入口为 `analysis/11_summary_figures/build_figures.py`。先阅读 README 和 METHOD，保护用户已有修改。

- 当前业务名称不使用项目版本号、final 或 latest；真实 NeuroSim 分支、SHA、接口版本与上游版权必须保留。
- 计算只读取当前公共代码、小型共享服务输入，以及各例 input.json 与 scenarios.json；归档与历史比较只能用于审计，不作为生成新结果的模型输入。典型图读取 analysis/data/ten_case_results.json；三情景表和圆图读取 analysis/data/paired_scenario_results.json。
- 保持所选器件身份、逻辑精度、资源、调度和维护政策。三情景只应用各例 scenarios.json 中有据、可配对的服务预算；不重选架构、不修改 NeuroSim 算法，不套用兄弟任务的性能值或 TA/TD。每个情景都用同一更新过的 case 向后端资格检查与适配器传参。
- 构建、源码副本、完整 trace、日志、临时文件、PDF 渲染与失败现场全部留在非同步本地区，默认 $NEUROSIM_ROOT 或 $HOME/neurosim；禁止先在 OneDrive 生成再删除，也不建立通往运行树的 symlink。
- 默认入口为 reference；全三情景显式 --scenario all。只为不变结构编译一次，每情景实际重新执行；--export 拒绝部分案例或单个非 reference 情景覆盖正式权威数据。
- 当前目录仅保留规范代码、输入、必要结果、正式图表与简短来源/验证说明。本轮过程记录只放本地区；整个 archive/ 只读，不向其中新增维护报告或改写历史文件。
- 兄弟 NVM 任务、Table II、论文及其他任务区只读。本轮用户未授权 git add、commit、push 或清理无关修改。
- 多人协作时仅指定的集成维护者执行实际移动/安装；其余候选在各自本地目录，独立审查使用新构建，不复用生产二进制。

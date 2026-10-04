# Step4 V4

三例参考审查、必要修订、九个完整成对热设计情景及圆图。三情景为300／350／400 K；350 K为温热工程参考，非统计中位数。保留平台自动尺寸化，故不是同芯片PVT。全部结论保留明确模型条件。

[中文报告](REPORT.zh.md) · [输入继承账本](provenance/input_ledger.json) · [九点CSV](results/reference-v4-20261005/summary.csv) · [JSON](results/reference-v4-20261005/summary.json) · [成对图](results/reference-v4-20261005/figures/rho_tau_pairs.png) · [圆图](results/reference-v4-20261005/figures/rho_tau_circles.png) · [独立审查](reports/review.json)。

```sh
# 仓库根执行；所有build/完整日志/中间文件只写本地runs/step4-v4。
python3 -B tasks/task1_table_I_NeuroSim/step4_v4/run.py \
  --run-id new-v4-run --diagnostics --plots --no-export
# 单例可选三个情景或一个reference；完整九点图要求all/all。
python3 -B tasks/task1_table_I_NeuroSim/step4_v4/run.py \
  --case ns_sram_dcim --scenario reference --run-id new-v4-dcim --no-export
```

也可复制本包到非同步目录从新位置运行；正式入口不需要旧results／legacy。默认环境根NEUROSIM_ROOT或`$HOME/neurosim`；`--root`、`--cxx`及`--plot-python`可覆盖本机环境。本机g++16、Python标准库、已有`/opt/anaconda3/bin/python`的numpy/matplotlib即可。`--plots`只生成PNG/SVG及机器几何数据；不需要DNN或SPICE。`--export`白名单导出小型交付，已有run-id拒绝覆盖。

权威数值输入是`configs/*/base_parameters`（实际文件为`configs/<case_id>.json`）和`configs/scenarios.json`；自动生成request.h与Param构造器输入，解析后字段及因果检查分别保存。修改参数后必须重新构建，不复用旧二进制。未声明override、不支持的INT8接口和温度会拒绝。

`compare_v3.py`只在V4结果已产生后读取明确给定的历史summary，生成历史对照；它不是评估依赖：

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v4/compare_v3.py \
  /Users/shine/neurosim/runs/step4-v4/new-v4-run \
  tasks/task1_table_I_NeuroSim/step4_v3/results/reference-v3-reviewed-20261004/summary.json
```

主运行`/Users/shine/neurosim/runs/step4-v4/reference-v4-20261005`，独立运行`reviewer-ninepoints-20261005`。规范目录包含代码/输入/补丁/报告、精简结果及独立证据；源码副本、编译、完整trace/log、过程候选只在本地。旧V3等全部保留。不暂存／提交／推送，停止V4等用户与外部审阅。

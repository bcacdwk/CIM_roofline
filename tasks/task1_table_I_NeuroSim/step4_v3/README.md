# Step4 V3

三个新增原生参考：`ns_sram_acim`、`ns_rram_1t1r`、`ns_sram_dcim`。共同256×31 signed INT8；条件性有效的完整streaming/resident服务。

[中文报告与主表](REPORT.zh.md) · [结果JSON](results/reference-v3-reviewed-20261004/summary.json) · [CSV](results/reference-v3-reviewed-20261004/summary.csv) · [独立审查](reports/review.json) · [服务契约](INTERFACE.md) · [来源](provenance/sources.json)。

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v3/run.py --run-id new-run-id --diagnostics --no-export
python3 -B tasks/task1_table_I_NeuroSim/step4_v3/run.py --case ns_rram_1t1r --run-id new-rram-run --no-export
```

入口可用绝对路径，或复制整个本包到本地独立目录运行。仅依赖Python标准库、已有C++编译器和已锁定NeuroSim环境；不读取旧results、legacy replay或pilot。用`--root`/NEUROSIM_ROOT指定本地环境，`--cxx`/NEUROSIM_CXX指定编译器。默认`$HOME/neurosim`，每次新建`runs/step4-v3/<run-id>`，不复用旧二进制。`--export`按白名单导出小型结果。

规范source/config/patch在本包；完整源码、编译、日志、失败现场只在本地。三个case agent已实际启动，独立reviewer未参与V3实现；外部ChatGPT尚未验收。完成后停止V3，不扩Step5或论文，不暂存／提交／推送。

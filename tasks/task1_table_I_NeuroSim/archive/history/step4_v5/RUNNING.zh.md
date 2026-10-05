# V5 运行入口

所有命令可从任意 cwd 使用脚本绝对路径启动，构建/trace 始终写入
`NEUROSIM_ROOT`（默认 `/Users/shine/neurosim`）的 `runs/step4-v5`。以下相对路径
仅为仓库根目录的便捷示例。

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py run --case mram --scenario reference --run-id my-new-run
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py all --cases mram nor2d gc04 --run-id my-new-batch --workers 2
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py diagnostics --run-directory /absolute/local/case-run
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py package --cases mram nor2d --run-id my-compute-package
```

`run` 自动按案例 adapter 的实际入口选择冻结 P1 binary 服务或独立 component
服务。`all` 可省略 `--cases` 选择七例；只对已实现的配置真正构建，不将缺失案例
伪造成三条 null 点。未实现、范围未就绪、执行错误和物理不可行分别保留；一个案例
失败后仍执行其他案例。不同后端允许不同文件集合，但同名共享计算文件在本批必须
哈希一致，同例三个场景的全部案例源码/输入必须一致。GC 按真实长期维护口径验证
U/RI，不把有效间隔当物理单次延迟。

`package` 建立计算文件白名单小包到本地 `packages/`，明确排除 case 内的
candidate_points、reference_snapshot、summary/result、报告、旧结果和 replay。
它仅依赖锁定原上游、必要小型参数/表征、许可与实际计算源码。生成包不代表物理
通过；P5 reviewer 仍需在包中重新构建。每次运行 ID 必须唯一，现存现场不覆盖。

`v5.py export --integration-dir <local batch> --output-dir <new export>` 从真实运行生成
`points.json/points.csv`。单次、raw 与长期有效时间分列；只有精确计算哈希匹配且
accepted/PASS 的 qualification 记录才赋予 plot_eligible。缺记录的数值仍为候选。

图表/历史比较保持独立：`v5.py compare` 转交总览作者的 `compare_v4.py`，
`v5.py plots` 转交 `plot_overview.py`，参数原样传递。两个后处理脚本现已交付，
不会把 V4/旧结果导入正式计算。最终文件见 `results/final-reviewed-20261005`。

最终计算包为 `/Users/shine/neurosim/runs/step4-v5/packages/final-compute-seven-r2-20261005`，
82文件928081B；其中21个配置均已实际新构建。首批18成功，MRAM缺两份规范文档的
打包问题修复后仅补跑3点。最终集合为
`/Users/shine/neurosim/runs/step4-v5/integration/final-seven-complete-20261005`。
所有点与独立fresh run逐项哈希匹配，见 `results/final_review_bindings.json`。

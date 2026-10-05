# Step4 V5 最终交接：完成并停止

更新：2026-10-05。用户授权完成七例与成对范围、独立复核、V4衔接/图表后停止V5；最新D028要求solid数量级估计，不追每处严格闭合或晶体管完美。D032避免对未改计算重复独立构建。禁止git add/commit/push、历史回写/破坏清理、全局升级；supervisor不生产实现。

## 当前状态

七例21个配置均已从compute-only白名单包实际fresh构建运行，21conditional/0最终执行失败。首批18成功，MRAM因包缺两份规范文档在构建前失败；仅补规范文档后另3fresh，失败现场保留，没有重复成功18。21点计算源与最终包/管理区逐项hash一致。

21点已内部accepted（七例各3），NAND最终reviews/p4_nand3d/review.json已PASS并由D037接受。正式21/30表图、43项白名单（2,411,985B）、报告/导航/保护审计及治理全部完成（D038/D039）。三名subagent职责均结束，所有生产/图冻结，停止V5等待用户与外部ChatGPT审阅。

## 当前唯一owner

- root：只写PLAN/TODO/DECISIONS/HANDOFF，裁决/抽查/汇报；不写生产代码或代跑仿真。
- integrator：公共代码/锁/运行/导出唯一维护者；已接管NAND生产（B确认停止写），最终表图/REPORT/根导航/白名单保护审计全部完成，已停止。
- A=`pcm_author`：PCM/NOR/FeRAM生产全部accepted；独立审MRAM/GC/FeNOR/NAND，均未参与对应生产。NAND最终PASS已落，最后文字与最终21点独立hash绑定均完成，已停止。
- B=`mram_author`：MRAM/GC/FeNOR生产完成；NAND前期研究已交integrator，不作为NAND独立reviewer；独立审PCM/NOR/FeRAM。P5总表/图独立检查已PASS（D038），工作完成并冻结，未参与绘图生产。

平台最多3个child线程，额外spawn确实失败；用同owner followup继续，不虚构新reviewer、不交叉写公共文件。最后完成后停止，不进入workload/新器件/论文。

## 路径与保护

管理根：`/Users/shine/Library/CloudStorage/OneDrive-个人/Files/02 Works/202609-ISCAS2027-Roofline/tasks/task1_table_I_NeuroSim/step4_v5`。

运行根：`/Users/shine/neurosim/runs/step4-v5/`。源码副本、编译、trace、原PDF、失败现场、独立包均在该区；管理区只规范代码/输入/小表征/关键输出/报告图。

- HEAD仍V4 `216d3f8af6e58fc75632a526b73d017252b2e969`。根`.DS_Store`与`tasks/.DS_Store`范围外保留，不恢复/不纳建议提交。
- 历史step4/V2/V3/V4/pilots/旧NVM/TableII/论文/旧锁/锁定上游均只读。
- V5依赖：`provenance/dependencies.lock.json`及PORTING；主要实际native为MLP V3 SHA6098feabaf17b8209a8edbef4a9c963b5f015132，原始上游只读，修复/扩展在独立副本与小补丁。UMEM/SKY/外部原语各case source ledger单列。
- P1冻结kernel34b81af48c…；已修真实MUX/写路由/漏容/reference隔离/mask/hold/clear；P2/P3独立端口。最后NAND专用run_nand/nand_native及两个C++隔离，没有修改前六例计算文件。

## 最终运行与计算包

- 包：`packages/final-compute-seven-r2-20261005`，不含旧性能/候选汇总/报告/replay；INTERFACE/PROBE_API为必要规范文档，并非性能依赖。
- 初批：`integration/final-seven-from-compute-package-20261005`。
- MRAM补批：`integration/final-mram-package-completion-20261005`。
- 最终集合：`integration/final-seven-complete-20261005`。
- 管理绑定：`provenance/final_run_manifest.json`、`provenance/final_compute_package.json`；完整21个run/config与hash在此。
- B的`reviews/p5_overview/execution_audit.json`已PASS_execution_snapshot：21唯一config/run、39真实native构建目录、所有计算文件/单位/rho/tau/RI/U/GC口径一致。构建数只是执行证据，不是可信度百分比。正式21/30表与四张PNG/SVG几何/视觉亦已通过`reviews/p5_overview/review.json`，管理区白名单复制已完成，文件/哈希与独立审查一致。

## 七例状态与参考范围摘要

以下是治理摘要，正式机器表/报告由integrator从最终运行生成。单位十进制MB/s；值按opt/ref/pess顺序，GC是含维护长期能力。

|Case|状态/独立review|rho|tau|关键身份/条件|
|---|---|---|---|---|
|PCM|accepted D033；reviews/p1_pcm_hv|.246238193（三点同）|2.561210564 / 2.195677121 / 1.135795261|TiSbTe 1T1R，全HV130访问+原生数字；旧LV身份失败只读保留，端态/材料pulse compliance条件公开|
|MRAM|accepted D027；reviews/p1_mram|.398505604（三点同）|1.904584767 / 1.290241290 / .784283690|1T1MTJ UMEM确定性有限成功500ns/1us/2us写，K64N64；不预测WER|
|NOR|accepted D029；reviews/p2_nor2d|.184704185（三点同）|.078651773 / .078651773 / .009129048|K256N16二元读/数字；16页+1sector完整P/E条件转用，opt/ref真实重合|
|FeNOR|accepted D036；reviews/p2_fenor3d|.536013400（三点同）|6.146458583（三点同）|四层×32横向通路；target128修复后r2，层数不乘吞吐；±50mV有限工程状态包，三点退化只画点|
|FeRAM|accepted D035；reviews/p3_feram|.238975594 / .238633429 / .236937195|37.5146542 / 36.9942197 / 34.5945946|K32N16 HZO1T1C极化、128真实破坏域恢复/写通路；100ns额外保守dwell、完整14/20/50ns原语|
|GC04|accepted D031；reviews/p3_gc04|.199128811（三点同）|9.699634850 / 8.238870016 / 7.526912316|易失硅GC04 K64N16，256SAR/128差码/1.024nF hold/Xsum；400/350/330µs维护政策|
|NAND|accepted D037；reviews/p4_nand3d|.121668185（三点同）|.135528000 / .135528000 / .108815211|K4608N240、32层string延伸、64SL×两AMP混合前端，完整6144页/64erase/校准|

所有点只为有限、明确条件的参考模型，不是硅签核、统计材料界或等面积/等精度排名。多数rho变化被固定数字服务周期遮蔽，不人为放大范围。

主要特殊条件：PCM原材料pulse可在3.983V cell compliance内交付及35mV裕量；普通binaryverify不能认证完整电阻窗口。NOR产品P/E转用不保证目标ESF1。FeRAM恢复全128bit×32行、14ns完整写只一次收费；250mA局部供电/0.5与2.5V驱动条件公开。GC原K64N64和300µs政策真实失败保留，rawΔ116.4µs/TR51.4µs与长期321.4µs/124.289µs间隔分开，保持/温度转用及Q4精度条件保留。

NAND有限模型已真跑seriesEKV/共享SL；被动SL背景反例促成有限A0/GBW/slew TIA+buffer，128AMP静态约10.56W。nominal dense约3%残差、isolated unit量化0、极端pass背景+44/−22%显著披露，有限标定域近似Q4，不是精确INT8/ENOB。参考Δ37.8735ms/TR8.160085s，500ns控制周期/16lane重构/byte装载主导，不称材料速度；P/E完整跨实现原语不重复内部verify/pump。

## 最终交付与下一动作

- 入口：`README.md`、`REPORT.zh.md`、`RUNNING.zh.md`。
- 正式交付：`results/final-reviewed-20261005/`，43项/2,411,985B；21点points.csv/json、30点combined_points.csv/json、旧NVM10条背景、21硬件/阶段snapshot、两套paired/circle PNG/SVG及几何/manifest。
- 十类圆图：`results/final-reviewed-20261005/figures/ten/ten_rho_tau_circles.png`；七例在`figures/v5/`。
- 全部最终独立绑定：`results/final_review_bindings.json`，PASS_FINAL_HASH_BINDING，21/21，0pending。
- 总览独立review：`reviews/p5_overview/review.json`/`REVIEW.zh.md`；白名单`export_manifest.json`与`provenance/preservation.final.json`均PASS。
- 计算包82文件/928,081B；六原上游clean，历史未改；README/STATUS仅追加14行，原前缀保留。两处.DS_Store不纳变更建议；未git add/commit/push。

**无在途作者/reviewer、无待执行生产步骤或未关闭主阻断。** 模型/精度/偏置/外部原语/保持等条件继续有效。下一动作是用户及外部ChatGPT审阅；仅在新指令后处理反馈，不自动扩展新器件、workload或论文。

## 复跑入口

可从任意cwd，用V5绝对脚本路径与每次唯一run-id；大文件仍只到NEUROSIM_ROOT。

```sh
python3 -B '<V5绝对路径>/v5.py' run --case nand3d --scenario reference --run-id new-nand-reference
python3 -B '<V5绝对路径>/v5.py' all --run-id new-seven-batch --workers 2
python3 -B '<V5绝对路径>/v5.py' package --run-id new-compute-package
```

最终compare/plots命令见RUNNING.zh.md/PLOT_PIPELINE.zh.md。建议提交名`task1_neurosim_step4_v5_seven_devices`，不实际提交。外部ChatGPT及用户未验收本轮。

# 公共后端交接：2026-10-05

**最终关闭：** 七例21点已全部完成、独立绑定和表图审查通过，正式入口为
`README.md`、`REPORT.zh.md`、`provenance/final_run_manifest.json`。没有活跃构建，
停止于V5。以下内容是本日较早的生产交接快照，保留其历史状态，不作为最终待办。

Owner：integrator（唯一共享生产维护者）。治理 PLAN/TODO/DECISIONS/HANDOFF 由
supervisor 维护，本文件只记录当前可运行公共组件，不替代阶段验收。

- P1 shared kernel 仍为 `34b81af48cd208bc2bebf5db46f625f3db8baee474e6c94dfcd2fc1659ff7842`，
  原 reviewed 计算集合未修改。MRAM 3点 accepted D027；正式轻量导出
  `results/p1_mram_reviewed`，未回写原 candidate/运行记录。P5 总体最终新构建门仍保留。
- NOR P2 threshold v2+Ioff、原生数字和 component 入口暂冻结，A正在完成三场景。
  已实际构建的正低压 gate/precharge/full-TG reference 界面见 `P2_THRESHOLD_API.md`。
  Ioff 是最后增加的参数回读，案例最终包应绑定其实际 hash。
- GC 专用 `gc_current`、`gc_digital`、事件维护聚合已可运行；N64 的100ns数字候选
  被拒，N16/200ns数字构建通过，minimum164.843ns。nominal code/gate诊断通过
  256MAC/32analog/64Xsum/carrytap8、非零初态 clear 与局部refresh状态保持。
  真实模拟精度、保持和整个调度资格仍由B的case模型/独立review决定。
- FeRAM `case_charge_ports` 不再构造低压 access 作HV实现；native SA/整域hold及
  按真实LV负载的decoder已运行。K32示例总BL250.138fF，SenseAmp200.0696ns含
  1/f=200ns，128bit捕获100ns，LV653fF地址建立8.218ns。`FERAM_COMPONENT_API.md`
  给最小输入。PCM可用同实际外围 `voltage_sense` request别名，无极化/恢复语义。
  最终材料、HV与状态服务由案例给出。

最新用户收敛尺度：后续不逐管完备化、不为小变化重复三点构建；只修会改变数量级、
机制、资源计数或真实可行性的缺陷。额定HV控制可用已有实测I/C和保守负载/电流块。

统一入口 `v5.py` 支持 run/all/diagnostics/package/export；compare/plots 独立
转交总览作者的 `compare_v4.py`/`plot_overview.py`，尚未提供时明确报未就绪。
`integrate.py` 对缺失案例保留一条状态记录，继续其余案例；执行错误不会伪装成
物理blocked，三条null不会算21点。共享文件按实际消费集合校验，允许不同组件的
文件集合不同，但同名共享源码在一批中不能混hash。

`export_points.py` 从真实结果输出配置身份、K/N、精度、native后端SHA、主要资源、
模型类别/条件、全部 single/raw/effective 时间、rho/tau/RI/U、计算hash。只有
qualification中的 accepted/PASS 与准确计算SHA匹配才设 plot_eligible。
GC effective interval不会改名成single latency；源单位为秒与十进制MB/s。

已执行的非仿真交付验证：

- MRAM D027规范表：`/Users/shine/neurosim/runs/step4-v5/integration/p1-mram-sidebound-integration-20261005/table-export-D027`，3数值/3图资格，约38.6KB。
- compute白名单示例包：`/Users/shine/neurosim/runs/step4-v5/packages/compute-package-whitelist-mram-20261005`，32文件279424B，无candidate/reference/旧结果。仅验证构包；按授权不另重跑已接受MRAM，P5再从最终包fresh build。
- 缺失案例集成门：`integration/integration-missing-case-gate-20261005`，NAND缺inputs/adapter时0计算点/1 implementation_not_ready记录；没有伪造3点。

等待作者最终机器点与阶段review到齐后：一次 `v5.py all --run-id <final unique id>`，
生成最终compute包，供分组独立复跑；绑定review后白名单export，交总览作者制图。
当前没有需要接续的活跃公共build进程。管理区未见pyc/o/so/symlink；git仅V5新增、
原root及后来观察到的tasks两处.DS_Store修改，均未add/commit/清理或覆盖。

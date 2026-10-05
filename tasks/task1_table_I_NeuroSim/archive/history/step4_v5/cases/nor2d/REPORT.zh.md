# V5 2D NOR：三点已独立复核并内部验收

实现为 `nor2d_esf1_binary_equiv130nm_k256n16_v1`。ESF1 180nm阈值状态证据连接新的130nm局部二元感测与精确数字归约；它不复刻旧模拟分类器，也不采用旧100/120/130ns完整读access。K256×N16、signed INT8，32768物理位，64个差分SA/参考，8个25bit算术lane；读取一行两组并保持128bit，逐输入位计算。全部4KiB数据正好占一个专用sector和16完整page。

|情景|读gate V|ΔS ms|TR ms|ρ MB/s|τ MB/s|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|---:|
|optimistic|1.3|1.386|52.077656|.184704185|.078651773|2.34837915|37.5740664|
|reference|1.2|1.386|52.077656|.184704185|.078651773|2.34837915|37.5740664|
|pessimistic|1.1|1.386|448.677656|.184704185|.009129048|20.2325783|323.721253|

三点是真正固定资源参数包；前两点使用源产品typ P/E，后者使用max。typ不是ESF1统计中位。门偏置改变电流与模拟发展(约3.108/4.396/5.904µA，119.08/100.31/100.31ns)，但800ns读端口clockslot及200ns数字反馈周期掩盖最终ρ变化；optimistic/reference重合不应被人为分开。

原图NOR-04 Fig3的1.1/1.3V曲线中心用于两参数拟合，1.2V另作非拟合检查，电流差−.154%；读图不等于原始高精度测量。255条未选行逐条计漏电上界，全部128列电气活动计共享SL回流。gate/drain/source的几何C来自明确工程EOT、结耗尽、重叠和导线模型；它们不是原论文实测C，也未从旧access反推。

实际MLP代码承担低rail NAND/INV/EN、译码/MUX、PMOS预充、差分SA、保持和数字归约。case解有限gate边沿、实际reference N/P不同控制边沿、TG后内部节点、BL/感测双节点与共享源边界，替换原native恒定ΔI发展项。原生2/f只按一次预充和一次输出相位计量。关断TG按native Ioff给出内部节点约.600mV上界；不是每次免费设零。

原500fF附加读C在参考gate不利电荷注入界下出现−22.8mV早期反极性，已作为真实新构建反例否定。固定4pF/BL后actualsensedC约4.207pF，三情景早期最差−6.30/−7.35/−8.45mV，均未跨SA20mV且剩余误差10mV的假锁存门；30mV决策裕量在VD≥.8V的规定域取得。10→5ps积分步长使捕获时间只变5–10ps。原生VSA抽象锁存与给定噪声/误差条件不等于晶体管瞬态、STA或硅精度认证。

Resident从任意旧状态开始，真实erase全部4KiB，再用实际256B页缓冲逐页接收/编程。50MHz单bit SPI共33720个含命令/地址/状态的时钟和51个CS事务边界，共677.256µs；P/E本体typ为45ms+16×.4ms、max为400ms+16×3ms。完整引擎原语已包含内部pulse/verify/泵/恢复，不再次收费。该W25Q128JV完整引擎的页/sector/时序转用于ESF1读阵列是显式条件性移植：必须提供对应阈值状态和read-safe端口，产品spec并不保证这个新阵列。SPI输入边界与本地向量输入边界分别标明，不包含外部DRAM传输。

独立于生产阶段求和的作者计数重新枚举32768位、16页、1sector、6930个stream周期；零、极值、混合、抵消、组边界和写失败不提交payload均已检查。资源、阶段、来源及最终代码哈希见`reference_snapshot.json`和`candidate_points.json`，诊断见`diagnostics.json`。B组独立新目录重建三点与主导机制/计数检查已通过，结论为`PASS_conditional_model_scope`；supervisor已按D029内部验收。见[独立审查](../../reviews/p2_nor2d/REVIEW.zh.md)。

最终三个真实运行在 `/Users/shine/neurosim/runs/step4-v5/component-services/case-nor2d-nor2d-final-{optimistic,reference,pessimistic}-r2-20261005`；每个都重新构建了独立frontend/digital源码与二进制。共同计算快照为 `f08958add106ed192955b380b84e0693ea17d085739b6c368d7892cff3010fc8`。复跑：

```sh
python3 -B '<V5绝对路径>/run_components.py' --case nor2d --scenario reference --run-id '<新的唯一ID>'
```

主要限制是工程C/geometry与误差预算、简化MOS偏置模型及跨实现完整P/E条件；原生局部面积不包含完整passive/HV引擎layout，不可作为等面积宏比较。范围是有限读偏置/服务政策包，既非PVT统计角落，也非所有可实现组合。

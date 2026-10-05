# Step4 V2 时序源与生命周期审查（本地实验）

仅写本地 `timing-analysis-20261004`，不修改管理区实现。六例分别由 `backend.build` 从锁定 V1.4 8a88abf...源码逐文件验 blob、复制、编译并执行。`instrumented/backend.cpp` 只新增源到达分类探针与独立 phase→enable 门路径；原全图、门负载、常量处理、资源和算术 fixtures 未改。`source_breakdown.json` 是轻量摘要，完整源及命令在各case目录。

## 实测结论

|案例|V1 全图 ns|真实单拍 ibit ns|单拍 acc data ns|首拍 weight ns|V1 人为重新启动的 input group 全图 ns|新主周期 ns|
|---|---:|---:|---:|---:|---:|---:|
|NOR|9.700952|8.380407|5.187721|6.896093|9.700952|8.5|
|MRAM|10.657027|8.539941|4.689876|7.055627|10.657027|9|
|FeRAM|9.700952|8.380407|5.187721|6.896093|9.700952|8.5|
|FeNOR|9.700952|8.380407|5.187721|6.896093|9.700952|8.5|

所有class的最大值均重现V1原全图至1e-18 s内（C++ assert），每个具体门与实际pin负载仍在。数字四例仍明显慢于5ns，原因是实际每拍变化的ibit 经分发、8:1输入bit mux、32项signed树、shift/sign和23/24bit累加。MRAM24bit accumulator比其他三例23bit更慢，不能将原10.657ns全部解释成真实反馈。

### Frame建立，不加缓存

当前group/output-group在原生binary read开始时已选定，固定到后续8个MAC完成。K×8输入寄存器在整vector期间不变，32×8输入group mux是组合网络，没有增加selected-input缓存。最迟到selected-input位mux输入pin的界：NOR/FeRAM/FeNOR input-data=1.133585ns、input-group-select=2.565756ns；MRAM=1.453776/3.362300ns。output-bank select的既有acc源pin界分别2.873692/1.592553ns。它们都在原生read 120/20/40/5ns内已建立，故首MAC之前group mux已稳定。

不能删除group选择网络或其pin负载，也不能将“整个全图延迟减read时间”作为新时钟：应单独记录并校验frame建立条件（上述source pin界≤本例read窗口），然后对每拍变化ibit、acc-data和首拍weight完整路径保留单拍资格。acc data仍每拍经过既有output-bank mux；只是早稳select不再每拍launch。weight在NOR/FeNOR实际捕获边界、MRAM捕获/隔离周期末、FeRAM完整read的已有捕获之后才有效，首MAC从该捕获起一拍，后续7拍保持。

### PCM／GC两拍资格

|案例|E0→E2 完整data/held selection ns|最慢源|E1→E2 phase enable ns|所需period ns|政策period ns|
|---|---:|---|---:|---:|---:|
|PCM|9.407240|SAR code（threshold 9.073156）|2.059456|4.703620|5|
|GC|10.500415|ibit→popcount→decode→tree→acc|2.059456|5.250207|5.5|

SAR码E0前已完成并保留到E2之后；输入向量、ibit、输出group与旧acc在E0到E2不更新。PCM column calibration threshold须在E0之前稳定且保持至E2，它的存储/数值/建立仍为原生条件，未因两拍升级为验证。GC输入bit/popcount在input-step/86ns overhead/1ns integration之前或期间建立；按Step3V2同一保守政策不借E0之前传播，仍将完整10.500415ns数据图约束在E0→E2。该5.5ns不是最短物理点声明。

E1只改变现有phase状态，既无中间result寄存，也不写accumulator，不启动新SAR/刷新/写回。E2才写现有selected-output accumulator并允许下一batch。专用capture-enable采用已验收pilot同一结构：phase C-Q→4级译码→LANES×OUTPUT_WIDTH有负载分发→capture mux→setup，实际返回2.059456ns，必须单拍；普通controller/io/clear/verify路径同样仍单拍。现有V1“phase2 entire path”标签没有对应的E1晚到数据来源，因此无依据。

## 建议局部实现

1. 将源分类到达作为原门图的诊断/路径输出；只对binary MAC创建 `ibit`、`acc_data`、`weight` 单拍资格，并将early-source的mux电路建立界关联到实际native-read窗口。初/后续phase注释保持明确，不能把未知source默认早稳。
2. PCM/GC完整reconstruct标E0→E2、available_cycles=2；保留独立E1→E2 capture-enable。window声明threshold（PCM）/input-popcount源（GC）与ibit/group/oldacc都稳定，E1只phase、E2唯一写回、无overlap或新bank。不能只把所有返回除二。
3. 所有强制时钟低于上述min的请求均拒绝；stream/resident/GC maintenance/guard交由统一入口重算。本实验只给资格与门图实测，不伪造服务结果。
4. 如需保守对照，V1 full图与周期原样保留；新门图与V1算术完全相同，变化仅source launch资格和真实单拍enable路径。

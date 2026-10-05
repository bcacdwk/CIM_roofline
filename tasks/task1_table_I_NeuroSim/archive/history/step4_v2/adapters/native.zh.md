# Step4 V2 六例服务边界

器件与全部原生完整服务继承[只读V1适配](../../step4/adapters/native.zh.md)。V2仅改消费边界和PCM/GC源保持声明；`numerical_checks`不改变编码或码映射。

|阶段|V2语义|setup归属|
|---|---|---|
|NOR/FeNOR读码保持捕获|纯boundary；一次实际采样，无额外整周期|该捕获边沿|
|MRAM读码捕获+IBMD隔离/reset交接|保留有来源的一完整cycle|末端寄存路径，入口不再加setup|
|MRAM/FeNOR终验capture|纯boundary；之后原compare周期完整保留|该捕获边沿|
|PCM endpoint compare|完整阈值/rail/目标态比较周期|末端路径|
|GC refresh sign_decode|完整解码并捕获周期|末端路径|
|PCM/GC两拍重构|连续E0→E2数据传播，E1只phase|E2末端；E1 enable仍一拍|
|NOR sector command/completion、页/事务装载、普通控制/I/O|原完整周期保留|末端路径|
|page/transaction/matrix ready|实际独立发布为boundary；已有捕获/已对齐marker不重复setup|独立捕获时一次|
|FeRAM破坏读/restore/捕获|完整native服务，不额外捕获|原生服务已包含|

纯捕获由原一tick预算改为接收setup后的最早边沿，是显式预算重解释；没有将source与destination setup混用。源tile在捕获后保持八个位操作；MAC组选择从native read开始保持，ibit与累加反馈每拍可以变化。GC刷新与guard随这些完整事件重新计算，不保留V1 availability。

GC刷新采用不超过原保持限制的整数公共拍固定帧。原保持参数400000ns不变，5.5ns时帧为399998.5ns；逐组物理写回在三帧中执行校验，间隔不超过原限制。H/guard/availability以实际帧重算，避免非整比帧的边沿漂移。

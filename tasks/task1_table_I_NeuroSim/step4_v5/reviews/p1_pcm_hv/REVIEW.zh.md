# PCM 全HV新身份独立复核

结论 **PASS_conditional_model_scope**。本次对新的全HV三情景各做一次新源码/新构建/新运行，按用户最新尺度检查机制、完整服务和主要资源/量级。审查者未修改PCM生产；此前LV只读partial审查保留，不对旧identity追溯改成通过。

独立确认16384个3µm/0.5µm HV访问管、128个data SA/参考、16并行热写通路；不再用低压访问管接4.5V热BL。N/P实际I/C、HV读隔离、128返回clamp与parking、156个levelshift通路可见。3.983V材料端compliance与5V控制是显式端口范围；它不由冷态电阻外推PCM编程电流。

独立重建每方向1024个16bit batch、128行求值/128行readback、256个byte比较组和2048个MAC更新。原热写波形含end/quench；在HVaccess关断后回收BL电荷，return不再穿过PCM，没有再添一段材料冷却。新10ns控制器刻度与200ns数字周期分开；SA的200ns输出相位及约80ps本征项仅计一次。

独立计算reference Δ=519.821877 µs、T_R=932.741877 µs；rho三点均0.246238193 MB/s，tau依次2.561210564/2.195677121/1.135795261 MB/s。3个最终计算快照/组件绑定和独立公式见 `review.json`；脚本没有导入生产聚合器。

结论限定于源TiSbTe可达到所列5..20kΩ/200k..2MΩ工作窗口、0.5/0.2mA完整源等效波形能在该compliance下交付，以及有限35mV感测/初态/20ns aperture条件。二元verify不能测量整个电阻窗口或证明良率。没有新增统计WER、长时漂移、全芯片PDN或晶体管STA结论。

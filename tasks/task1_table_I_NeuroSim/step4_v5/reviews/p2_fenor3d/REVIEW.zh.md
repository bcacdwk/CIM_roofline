# 垂直 AND FeFET 独立轻量审查

结论：**PASS_conditional_model_scope**，绑定修正后计算SHA `81880c5e60e9cb036319b4643cf859694da84f3d04d0f621fd3e2e51758038fc`。修后在新目录重新构建三点，ρ均.536013400MB/s、τ均6.146458583MB/s，Δ238.8µs、TR333.2µs；三点重合是有限state包被20ns固定pulse/200ns时钟掩盖的真实结果。

独立计数为4×32×128=16384cell、每次一活跃层、32条横向通路、2048data SA与2048参考、4096bit层tile。流式8次半层读、128次input row选择、1024个16-lane bitserial MAC，不存在免费32输入归约树。独立1194个200ns周期复现stream；resident 128个完整RESET＋128个masked PROGRAM、256次半层verify(524288物理bit读)、256次tile capture、128次目标行compare，1666周期复现TR，payload始终仅2048B。

R1发现原`program_lanes=16`混淆byte与physical bit，与128bit完整行写不一致。作者已改为128，原生128bit目标保持及整字直连成立；额外8组选mux不再被冒充128路。旧`0c37bc03…`三点只留发现/对照，不被作为PASS。修后资源与时钟均重新运行，速率不变不代表无需改正资源语义。

实际四层selected/unselected电流、共享SL/BL负载、负偏置/半选端口及原生选择/感测/数字边界符合当前模型身份；层数只贡献容量。保留EKV非唯一提取、native Ion/W/L source-follower近似、5mV+2mV感测条件、约39ns有限场暴露和未逐管实现的隔离井/负域8ns控制端口。它不是完整负电压level-shifter、PVT分布、ENOB或长期无扰保证。

审查者未编写FeNOR生产，仅曾提供公开SKY130资料入口/小表并编写PCM/NOR/FeRAM；这项相关参与已披露。所有修复由B作者完成。独立运行在 `component-services/case-fenor3d-reviewer-fenor-{ref,opt,pess}-r2-20261005`，完整hash/资源/来源范围见`review.json`。按最终binding无需再次编译未变代码。

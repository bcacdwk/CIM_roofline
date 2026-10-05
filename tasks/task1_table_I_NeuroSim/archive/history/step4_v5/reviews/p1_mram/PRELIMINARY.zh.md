# MRAM 独立预审（未作最终通过）

审核者此前参与 PCM、NOR、FeRAM 案例生产；没有参与 MRAM 或公共后端生产。当前只读检查，最终三点仍须新源码/构建/运行。

MRAM-R1：`mos_circuit` 的共享 source-return 递归将实际栅压降额后，同时重算 `raccess*(vdd-vth)` 分母，改变了应固定的工艺 β，部分抵消低VDS源退化。作者已确认并将在最终快照前分离 native VDD 与实际 gate；旧结果留存。未因此宣布其余模型或三点通过。

最终复核绑定修后 hash，独立检查 UMEM 方程/极性、数值收敛、两极性完整写、读扰、真实 reference/隔离与共享 source-current 回路、数字状态和批次数。

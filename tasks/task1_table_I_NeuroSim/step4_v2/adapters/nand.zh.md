# Step4 V2 NAND服务边界与条件预算

保留[V1原生NAND适配](../../step4/adapters/nand.zh.md)的双幅值/base4/固定双符号相位、容量、页/参考页、原生WL/BL/SL及P/E服务。公共SAR、编码、formatter、merge、符号与累加路径不变。

仿射周期属于完整操作，入口不再另加destination setup；NAND现有9ns主点未因此改变总时间。校准sample capture、page ready和erase-set ready是纯接收边界，保留一次setup后选边沿，不追加周期。透明模板包装不能改变原生物理完成时刻。

仿射乘法/舍入和校准除法仍未闭合，所有结果保持条件性。有限对照将每轮affine预算及448个校准算术周期分别放大2×/4×，其余两拍发布、工作周期、资源、原生服务和共享SAR均固定。此为时间预算敏感性，不声称构造了新乘除实现。原NAND量化、小信号和组边界误差继续原样输出。

# Step4 V3 独立审查（2026-10-04）

结论：**PASS_WITH_EXPLICIT_CONDITIONS**。最终03版本无剩余阻断项；仅对下述明示模型和服务边界成立。这不是用户验收，也不是外部 ChatGPT 验收。

本reviewer未参与本轮生产实现，未修改管理区或上游代码；仅在`reviewer-20261004-*`独立目录编写审计脚本、报告，并向supervisor反馈问题。本线程新启动，无已知历史实现参与。

主仓库HEAD：`b7795fd5acc8f5f3816d1022111330fc569b6853`。编译器：`g++-16 (Homebrew GCC 16.2.0) 16.2.0`。上游Training V2.1为`f80a4345f70dcb1ddfd003d3ddcfbd067b55a79a`，DCIM V1.0-dev为`38eedf926fc1a712df3627f36bb82b097ba6b9cb`；额外参数/LevelShifter来源MLP V3.0与Inference V1.4均保持锁定HEAD且最终工作树干净。

两次最终完整复跑分别位于`/Users/shine/neurosim/runs/step4-v3/reviewer-20261004-direct03`和`/Users/shine/neurosim/runs/step4-v3/reviewer-20261004-standalone03`，每次均新复制上游源码、应用规范constructor/patch、独立编译三个二进制；没有复用主运行二进制。第二次仅从`/Users/shine/neurosim/runs/step4-v3/reviewer-20261004-package03/step4_v3`中的21个Step4 V3文件启动，该包无旧results/legacy，运行所需外部输入只有锁定worktrees环境与工具链。两次构建输入、上游/补丁后源码、二进制SHA、raw、全部diagnostics和summary完全一致。构建输入manifest SHA256为`78b4be48d25c81bcc396f3cc79d49ae92e0b9830b17465e403c60636fd8108fa`。

独立`check_services.py`没有import生产`run.py/evaluate/numeric.py`，从原生中间返回与审计出的操作次数重建主例及全部diagnostics，共387项断言/次。它并非重新实现晶体管模型，仍使用经源码审查的原生primitive返回。独立`independent_arithmetic.py`另行穷举65,536个signed标量组合、33,153个RRAM(active,ones)理想码组合，并以64棵nibble树重建零、极值、异号、混合、抵消矩阵；三阶段25bit范围足够，理想RRAM最大码928，NOR(~x,Qbar)四种物理极性组合正确。上述算术证据不宣称模拟精度、ENOB或硅测校准。

| 案例 | delta_S ns | T_R ns | rho MB/s | tau MB/s | RI* | U* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ns_sram_acim | 4546.744914584 | 2008.288856282 | 56.304016348 | 3951.622783334 | 0.014248328 | 0.441698159 |
| ns_rram_1t1r | 10841.396652999 | 470779.334776103 | 23.613193779 | 16.857154539 | 1.400781711 | 43.424233043 |
| ns_sram_dcim | 147.879789063 | 2912.094307699 | 1731.135820671 | 2725.186467697 | 0.635235732 | 19.692307692 |

全部主例K=256、N=31、B_S=256 Byte、B_R=7936 Byte，独立核对U*=31RI*。参考列、补码校正和内部pass均只作为硬件/时间开销，不加入逻辑payload。

- SRAM ACIM：同一Training SubArray的WL/access gate与BL drain负载、precharge、8组MUX、32个9bit SAR及32路原生ShiftAdd；每bit先`max(WL,首组MUX)`再7组后续MUX，16个输入位轮次，两次独立operand捕获和三个25bit校正阶段。resident为256次全256bit行写，共65536bit，含本地capture、offset编码、原生写选通/driver/cellflip及最终恢复。活动率诊断不影响时延是该原生SRAM并行抽象的预期行为；access变宽虽降低cellaccess R，却增大MUX选择负载，不能只按Ron猜总量单调性。
- RRAM 1T1R：256x288实际cells，32组各8个weight bit+1个HRS reference；31个logical weight+constant1组。stream固定16个完整bit轮次、每轮9次MUX/32SAR，HRS原生Adder减法和寄存捕获有非零时序。主例用单选HRS最慢列RC包络，不对zero/sparse plane跳时隙。resident每方向2304批，RESET+SET共4608个10ns脉冲、9216次assert/release；全73728cells RESET，dense目标32000cells SET使能但不跳过槽位。32bit入口共2304beat装载并保持288bit row buffer；512行phase验证、4608ADC rounds、147456cellsense，使用同阵列/同MUX/同32SAR，目标选择及64个双向Comparator+OR/status均计入。pulse20ns只增加46.08us，batch16加倍编程槽而不加倍verify，符合因果关系。
- SRAM DCIM：真实Type::DCIM→NOR→AdderTree_DCIM路径，256x256是65536总bit；`numCol/4=64`外围乘四份、64棵256输入4bit树，两棵合成一个unsigned8bit输出，32组中含constant1。NOR输入有256路已计负载/时延的反相器，Qbar来自已有SRAM节点且其NOR输入电容加入写翻转负载。专用AdderTree_DCIM返回秒；同步SubArray为每unsigned8bit共9cycle，DFF/ShiftAdd返回cycle。总stream为1次capture+2*(1次selectorfill+9native+1次直接operandmerge)+3次correction=26cycle；每行256bit四组并写，256beat，每beat1capture+1rounded-busy=512cycle全矩阵。write_groups2使T_R准确翻倍；activity1时延不变，access变更仍改变写analog分量但可能不跨时钟取整边界。

修复前实质问题包括C/D引脚负载、DCIM A/B生命周期、RRAM目标/equality外围、RRAM后续MUX聚合、NOR极性/节点电容和被注释吞掉的控制DFF Area。01版本虽数字自洽仍因物理极性未闭合而FAIL；02版本因面积前置遗漏FAIL。最终03已逐项检查并全新重建，不将旧数值匹配视为验收。

公共边界明确为本地输入/写端口与已装寄存资源；外部DRAM/network/chip transport不计；请求之间不重叠，读写和共享ADC互斥。Training阵列秒与数字clock分开，DCIM秒/cycle只转换一次。C/D广播包含真实多lane负载、布线span和native公式driver；1:1寄存转移使用原生DFF半周期/cycle抽象，未声称CQ随load或完整时钟树验证。

RRAM末次verify定义为**held-read idle**：ADC结束、status捕获、read bias稳定、最后onehot mask由DFF保持即可compute-ready；并不承诺所有WL关闭。下一stream或resident先计原生完整mask安装（DFF+TG/实际RC，旧行清除及新行置位），setup结束后才开始下次compute/program pulse。连续read-bias disturb、静态能耗和无毛刺瞬态未验证，是明确物理条件。

其余条件：SRAM多行读稳定性及ADC nominal码宽不等于ENOB；RRAM增益/offset校准、reference package和首脉冲读验成功均为条件；失败重试不是本结果。1V写/1.1Vaccess rails在acceptance前稳定；LevelShifter为同Technology公式的上游未验证primitive，不是独立高压器件或电源生成验证。理想clock-enable/control sequencing保留上游粒度。三个身份不冒充历史器件或论文MAC时隙。

复跑命令：

```sh
python3 -B "/Users/shine/Library/CloudStorage/OneDrive-个人/Files/02 Works/202609-ISCAS2027-Roofline/tasks/task1_table_I_NeuroSim/step4_v3/run.py" --run-id reviewer-20261004-direct03 --diagnostics --no-export
cd /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-package03
python3 -B step4_v3/run.py --run-id reviewer-20261004-standalone03 --diagnostics --no-export
python3 -B /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-audit/check_services.py /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-direct03
python3 -B /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-audit/check_services.py /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-standalone03
python3 -B /Users/shine/neurosim/runs/step4-v3/reviewer-20261004-audit/independent_arithmetic.py
```

二进制与每个源文件的完整SHA、条件、已关闭问题和最终文字澄清差异见同目录`review.json`。若最终INTERFACE/config只补held-read idle文字，独立03所用所有执行/constructor/diagnostic/result键须与最终配置相同，差异另列；任何计算输入或源码改动均不由本结论自动覆盖。

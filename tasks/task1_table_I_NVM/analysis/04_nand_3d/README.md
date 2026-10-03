# 3D NAND 原生 CIM 参考配置

一个64-block subarray实现 `W[480,4608]` INT8。有效容量2,211,840 Byte，物理容量10,616,832 Byte；两位BL/SSL编码、必要复制和两个参考WL均保留。每次1152项、四组求值，固定25 µA电流前端的名义全密度输入为20.736 µA。64 ADC完成原生SL电流读出，无额外16 pF反馈积分电容。

| 固定配置情景 | ρ (MB/s) | τ (MB/s) | RI* | U* |
|---|---:|---:|---:|---:|
| 乐观 | 16.6 | 1.16 | 14.3 | 6875 |
| 典型 | 13.5 | 1.16 | 11.7 | 5612 |
| 悲观 | 11.1 | 0.564 | 19.6 | 9403 |

MB为十进制。典型完整向量间隔340.6 µs，完整矩阵持续替换1.91128132 s，包含6144次页program、64次块erase、metadata和校准。U*=T_R/Δ_S=480·RI*。每16 KiB平均成本只是比例换算，不是真实小事务延迟。

- [中文正文PDF](output/nand_3d.pdf) · [章节TeX](tex/04_nand_3d.tex) · [独立编译入口](tex/nand_3d.tex)
- [输入、原值与选择](data/inputs.json) · [原生资源、三情景及映射接口](data/results.json) · [验证项](data/validation.json)
- [参数证据](notes/parameter_evidence.md) · [方法与检查说明](notes/review.md)
- [统一方法](../shared_baseline/README.md) · [统一结果入口](../TEN_CASE_REVIEW.zh.md)

读侧由480轮SL建立主导。写侧主要受完整SLC program约束；NAND-06同厂SLC产品300/600 µs及1/3.5 ms作为跨实现完整P/E预算，未称为SGVC实测保证。乐观/典型共用典型P/E，不人为构造更快program。

有符号INT8用偏置码计算并显式校正。480个21-bit权重和metadata在完整装载中生成，30-bit中间累加及校正通道处理偏置编码的最大值，最终输出29 bit。8有效bit ADC保留近似部分和语义，不能称精确14-bit计数。外部审阅重点是前端在原偏置及16 pF原生SL上的建立能力、SGVC绝对P/E预算桥接、offset相减后的量化误差。预擦除一代对照单列，不能用于持续τ。

在本目录复算：

```sh
/opt/anaconda3/bin/python scripts/check_nand.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

`--emit`更新现有结果和生成TeX。计算使用公共逻辑配置、页块、完整装载和映射API；默认检查只读。7组检查包括完整编码/容量/选通、全部65,536个signed INT8标量对、独立典型点算术、两表接口、源PDF哈希与生成同步。渲染contact按当前PDF的实际页数生成，不读取旧页残留。

结果卡`tex/result_card.tex`由`../scripts/export_ten_cases.py --emit`唯一生成，中央脚本默认只读逐字校验；本例检查保留全部模型、数据和正文生成项。统一卡生成后由统一构建重编译并复核PDF。

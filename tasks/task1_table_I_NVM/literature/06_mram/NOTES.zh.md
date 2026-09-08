# 06 — MRAM

电阻求和和 bitcell 数字 CIM 分成不同参考机制；普通存储宏和正式 datasheet 支持读写与更新语义。互补 MTJ、两步写入、读验与位串行不能略去。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="MRAM-01"></a>
## MRAM-01 — A crossbar array of magnetoresistive memory devices for in-memory computing

**核心** · 2022 · Nature 601, 211–216 · [全文](MRAM-01_2022_ResistanceSum_Crossbar.pdf)

**身份与版本：** Seungchul Jung, Hyungwoo Lee, Sungmeen Myung, Hyunsoo Kim, Seung Keun Yoon, Soon-Wan Kwon, Yongmin Ju, Minje Kim, Wooseok Yi, Shinhee Han, Baeseong Kwon, Boyoung Seo, Kilho Lee, Gwan-Hyeob Koh, Kangho Lee, Yoonjong Song, Changkyu Choi, Donhee Ham, Sang Joon Kim。Published article including Methods and Extended Data。

**用途与结构：** 28 nm 电阻串联求和、TDC 读出及互补 MTJ 权重；Methods 明确一行左侧、右侧分两次并行编程，每次一个写时钟。

**正文定位：** pp.6–8，Methods：MTJ write/read、weight update、operating frequency。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；二值互补 MTJ；电阻求和／TDC。

**使用限制：** 互补权重的两次写、read resistance sum 和普通 STT RAM 感测是不同机制；scaling 小节属于分析，不能作为追加实测样本。

**出版标识：** [DOI](https://doi.org/10.1038/s41586-021-04196-6)。

<a id="MRAM-03"></a>
## MRAM-03 — A 1-Mb 28-nm 1T1MTJ STT-MRAM With Single-Cap Offset-Cancelled Sense Amplifier and In Situ Self-Write-Termination

**核心** · 2019 · IEEE Journal of Solid-State Circuits · [全文](MRAM-03_2019_SelfWriteTermination.pdf)

**身份与版本：** Qing Dong, Zhehong Wang, Jongyup Lim, Yiqun Zhang, Mahmut E. Sinangil, Yi-Chun Shih, Yu-Der Chih, Jonathan Chang, David Blaauw, Dennis Sylvester。完整正式论文/技术资料。

**用途与结构：** 28 nm 1T1MTJ 实测 macro，local subarray/SA、预充与 offset cancel、写稳定与自终止信号明确；读写成功率随时间/温度改变。

**正文定位：** pp.3–7，Figs.7–21，read timing／write termination。

**工艺/模式：** 直接的 28 nm 证据（专用 MRAM 外围）；binary 1T1MTJ STT-MRAM。

**使用限制：** 读写指标附 BER 条件；自终止的节能收益不自动证明缩短固定外部写周期。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2018.2872584)。

<a id="MRAM-04"></a>
## MRAM-04 — A 28nm 32Kb embedded 2T2MTJ STT-MRAM macro with 1.3ns read-access time for fast and reliable read applications

**补充** · 2018 · 2018 IEEE International Solid - State Circuits Conference - (ISSCC) · [全文](MRAM-04_2018_2T2MTJ_ReadMacro.pdf)

**身份与版本：** Tzu-Hsien Yang, Kai-Xiang Li, Yen-Ning Chiang, Wei-Yu Lin, Huan-Ting Lin, Meng-Fan Chang。完整正式论文/技术资料。

**用途与结构：** 28 nm 2T2MTJ 实测快速读，包含预充、发展与感测三阶段，可独立核查读侧电路量级。

**正文定位：** p.1，CREVSA；p.2，Figs.30.3.2–6。

**工艺/模式：** 直接的 28 nm 证据（专用 MRAM 外围）；binary 2T2MTJ STT-MRAM。

**使用限制：** 互补物理单元与逻辑 bit 数不同；读 access 不能替代写时间或 CIM 多位求值。

**出版标识：** [DOI](https://doi.org/10.1109/isscc.2018.8310394)。

<a id="MRAM-05"></a>
## MRAM-05 — EMxxxLX/B/HR — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory

**补充** · 2026 · Everspin datasheet, EMxxxLX/B/HR v3.7 · [全文](MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf)

**身份与版本：** Everspin Technologies。Everspin v3.7；修订史 2026-07-23，部分内页仍沿用 ©2025。

**用途与结构：** Everspin EMxxxLX/B/HR v3.7（2026-07-23）正式 datasheet：back-to-back 写、无页跨越限制，读写命令、恢复条件和直接更新语义明确。

**正文定位：** pp.15、41–48，WRITE/ERASE；pp.69–71，AC；pp.81–82，修订史。

**工艺/模式：** 功能与时序定义参考（该文件不证明 28 nm）；binary STT-MRAM；NOR erase 指令可模拟。

**使用限制：** xSPI 是封装接口，不是局部 cell 服务。ERASE 是兼容命令，不能由命令名断言 STT 介质必须先物理擦除；该文件不证明 28 nm。

**文档编号：** EMxxxLX/B/HR v3.7, July 23, 2026。

<a id="MRAM-06"></a>
## MRAM-06 — A lossless and fully parallel spintronic compute-in-memory macro for artificial intelligence chips

**核心** · 2025 · Nature Electronics · [全文](MRAM-06_2025_LosslessParallelSpintronicCIM.pdf)

**身份与版本：** Humiao Li, Zheng Chai, Weirong Dong, Junjie He, Ruijie Peng, Shiheng Li, Zhen Kong, Xihui Yuan, Xianwang Wang, Zhengke Yang, Haoran Lyu, Haofeng Yu, Xue Zhou, Jiamin Li, Feichi Zhou, Yida Li, Zongben Xu, Tai Min, Longyang Lin。完整正式论文/技术资料。

**用途与结构：** 实际 40 nm STT-MRAM 数字 CIM；bitcell 内乘法/数字化，64 bank 各 256×4，输入 MSB-first 位串行、bank 内并行乘加，多精度由累加和 bank 合并实现。写互补 MTJ 分两步，测试按 row 写后读验，错误 row 重写。

**正文定位：** pp.2–5 Figs.2/3；pp.8–9 Methods；p.15 Extended Data Fig.2；已归档 SI Fig.2。

**工艺/模式：** 40 nm STT-MRAM；其他工艺条件保留；binary 互补 2T2MTJ；输入位串行、bank 内并行，4/8/12/16-bit 分模式。

**使用限制：** “Fully parallel”不是任意多位 MVM 一拍完成：4-bit 输入用四拍。数字无损算术也不保证所有电压下存储读无误；p.4 区分低压实测读错误与较高电压无观测错误。不能将最佳能效、时钟及无错条件拼接为同一工作点；未给出完整写验绝对周期。

**出版标识：** [DOI](https://doi.org/10.1038/s41928-025-01479-y)。

**技术补充：** [SI](MRAM-06_2025_LosslessParallelSpintronicCIM_Supplement.pdf)，15 页，已归档。


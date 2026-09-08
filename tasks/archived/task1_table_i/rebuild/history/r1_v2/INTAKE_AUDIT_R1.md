# A/B 到件、身份与重命名核验（R1）

2026-09-08。原清单 55 条主文记录全部齐全；原 18 个 A 包、10 个 B 包及 FENOR-03 关联会议稿都已核对。没有缺主文、登录 HTML 假 PDF 或相同字节的重复文件。

## 来件与版本

- R0 本地主文 26；本轮用户新增主文 29、额外简表 1。30 个来件均按稳定 ID 重命名。
- Everspin 来件为 v3.7，修订史日期 2026-07-23；比原请求 v3.4 更新，已接受替代并修正年份/路径。
- FERAM-04、FENOR-03 的文字层存在字体编码问题，已渲染确认内容正常。仅在忽略的 tmp 中作文字解码辅助；PDF 原字节未修改，不需重下。
- 55 条旧主文的题名、正文与角色已核对；新补 CMOS-07 作者稿也已复核。所有 PDF 签名、页数、哈希与可打开性以 metadata 核验记录为准。
- 目前唯一明确缺失的已有论文技术附件是 PCM-04-SI；新增 MRAM-06 已有 SI，仍缺主文。

## 整理及剔除

整篇无关主文删除 **0**。剔除的是不适合承担的证据角色：FENOR-05 退出 FeNOR 核心；FENOR-03 与 FENOR-04 归并；旧 Everspin brief 退出有效证据。原文件字节保留在 comparisons/versions，便于回溯，不算重复核心来源。

30 个来件的原名→新名及 SHA-256 见 [rename_log_r1.json](metadata/rename_log_r1.json)。后续版本/对照目录整理见 [organization_log_r1.json](metadata/organization_log_r1.json)。原 R0 目录和清单见 history/r0，根目录 Zhou 两篇与此前任务材料均未移动或覆盖。

## 主文逐项到件表

| ID | 来源 | 当前文件 | 页数 | SHA-256 前 12 位 | 正文判断 |
|---|---|---|---:|---|---|
| [CMOS-01](LITERATURE_CATALOG.md#CMOS-01) | R0 已有 | [CMOS-01_undated_IGADACT01C_v002.pdf](literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf) | 2 | `15a58e1af2d7` | 补充 |
| [CMOS-02](LITERATURE_CATALOG.md#CMOS-02) | R0 已有 | [CMOS-02_2021_AsynchronousSAR.pdf](literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf) | 10 | `435ff772b6fa` | 核心 |
| [CMOS-03](LITERATURE_CATALOG.md#CMOS-03) | 用户 A/B | [CMOS-03_2012_SRAM_Assist.pdf](literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf) | 5 | `e6edc7bb5b0f` | 核心 |
| [CMOS-04](LITERATURE_CATALOG.md#CMOS-04) | 用户 A/B | [CMOS-04_2011_DualPort_SRAM.pdf](literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf) | 10 | `ddc324b0eda2` | 补充 |
| [CMOS-05](LITERATURE_CATALOG.md#CMOS-05) | 用户 A/B | [CMOS-05_2025_Interleaved_DAC.pdf](literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf) | 5 | `f61db15b5504` | 补充 |
| [CMOS-06](LITERATURE_CATALOG.md#CMOS-06) | R0 已有 | [CMOS-06_2025_ReconfigurableSAR.pdf](literature/00_cmos_periphery/CMOS-06_2025_ReconfigurableSAR.pdf) | 7 | `049e279cabc2` | 条件保留 |
| [CMOS-07](LITERATURE_CATALOG.md#CMOS-07) | C 轮停止指令前取得 | [CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf](literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf) | 11 | `c63c21e5c4a6` | 核心 |
| [SACIM-01](LITERATURE_CATALOG.md#SACIM-01) | R0 已有 | [SACIM-01_2022_Scalable_IMC.pdf](literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf) | 14 | `26bd395f4187` | 核心 |
| [SACIM-02](LITERATURE_CATALOG.md#SACIM-02) | R0 已有 | [SACIM-02_2025_PICO_RAM.pdf](literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf) | 13 | `4c067d2fc7c0` | 核心 |
| [SACIM-03](LITERATURE_CATALOG.md#SACIM-03) | 用户 A/B | [SACIM-03_2023_Hierarchical_Attenuator.pdf](literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf) | 5 | `4a0318542c1d` | 核心 |
| [SACIM-04](LITERATURE_CATALOG.md#SACIM-04) | 用户 A/B | [SACIM-04_2023_C2C_ChargeDomain.pdf](literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf) | 14 | `5bb8359ab3ee` | 核心 |
| [SDCIM-01](LITERATURE_CATALOG.md#SDCIM-01) | R0 已有 | [SDCIM-01_2023_D6CIM.pdf](literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf) | 4 | `bbb72fb65095` | 核心 |
| [SDCIM-02](LITERATURE_CATALOG.md#SDCIM-02) | 用户 A/B | [SDCIM-02_2023_BitReconfigurable_CIM.pdf](literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf) | 5 | `be80de0fd0ce` | 补充 |
| [SDCIM-03](LITERATURE_CATALOG.md#SDCIM-03) | 用户 A/B | [SDCIM-03_2022_DynamicLogic_INT8.pdf](literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf) | 3 | `c2fa5e30cdcd` | 核心 |
| [NOR-01](LITERATURE_CATALOG.md#NOR-01) | 用户 A/B | [NOR-01_2024_GL_S_MIRRORBIT_Military.pdf](literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf) | 106 | `c09592a765a5` | 核心 |
| [NOR-02](LITERATURE_CATALOG.md#NOR-02) | R0 已有 | [NOR-02_2019_W25Q128JV_RevG.pdf](literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf) | 78 | `5e2f6a77e022` | 核心 |
| [NOR-03](LITERATURE_CATALOG.md#NOR-03) | R0 已有 | [NOR-03_2022_SST26VF064B_RevK.pdf](literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf) | 90 | `25dc401ad06c` | 补充 |
| [NOR-04](LITERATURE_CATALOG.md#NOR-04) | R0 已有 | [NOR-04_2017_EmbeddedNOR_Classifier.pdf](literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf) | 4 | `987806007d22` | 核心 |
| [NOR-05](LITERATURE_CATALOG.md#NOR-05) | R0 已有 | [NOR-05_2016_NOR_ModelBased_Tuning.pdf](literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf) | 2 | `87ea1a0bcb77` | 核心 |
| [NAND-01](LITERATURE_CATALOG.md#NAND-01) | 用户 A/B | [NAND-01_2016_Micron_3DNAND.pdf](literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf) | 2 | `2e982c8755b6` | 核心 |
| [NAND-02](LITERATURE_CATALOG.md#NAND-02) | 用户 A/B | [NAND-02_2026_KIOXIA_6Plane_QLC.pdf](literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf) | 3 | `a0e53038d67b` | 核心 |
| [NAND-03](LITERATURE_CATALOG.md#NAND-03) | 用户 A/B | [NAND-03_2025_SKhynix_321Layer_QLC.pdf](literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf) | 3 | `c021e8c4d41c` | 核心 |
| [NAND-04](LITERATURE_CATALOG.md#NAND-04) | 用户 A/B | [NAND-04_2021_NAND_Codesign.pdf](literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf) | 9 | `6a121029ddc6` | 核心 |
| [NAND-05](LITERATURE_CATALOG.md#NAND-05) | 用户 A/B | [NAND-05_2019_3DNAND_nvCIM.pdf](literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf) | 4 | `61536f260f9b` | 核心 |
| [RRAM-01](LITERATURE_CATALOG.md#RRAM-01) | R0 已有 | [RRAM-01_2022_NeuRRAM.pdf](literature/05_rram/RRAM-01_2022_NeuRRAM.pdf) | 29 | `4e75d89025e0` | 核心 |
| [RRAM-02](LITERATURE_CATALOG.md#RRAM-02) | R0 已有 | [RRAM-02_2025_HybridProgramming.pdf](literature/05_rram/RRAM-02_2025_HybridProgramming.pdf) | 9 | `d55cb5abda2d` | 核心 |
| [RRAM-03](LITERATURE_CATALOG.md#RRAM-03) | R0 已有 | [RRAM-03_2022_Weebit_28nm.pdf](literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf) | 5 | `2ad046df73ff` | 补充 |
| [RRAM-04](LITERATURE_CATALOG.md#RRAM-04) | R0 已有 | [RRAM-04_2016_MB85AS4MT.pdf](literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf) | 28 | `c62ba591e01c` | 补充 |
| [RRAM-05](LITERATURE_CATALOG.md#RRAM-05) | 用户 A/B | [RRAM-05_2023_WeightedHybrid_2T1R.pdf](literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf) | 12 | `2770738ae1d9` | 核心 |
| [MRAM-01](LITERATURE_CATALOG.md#MRAM-01) | R0 已有 | [MRAM-01_2022_ResistanceSum_Crossbar.pdf](literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf) | 17 | `8ae3c42c9e81` | 核心 |
| [MRAM-02](LITERATURE_CATALOG.md#MRAM-02) | 用户 A/B | [MRAM-02_2023_Spintronic_CIM.pdf](literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf) | 13 | `98747f7b6c82` | 补充 |
| [MRAM-03](LITERATURE_CATALOG.md#MRAM-03) | 用户 A/B | [MRAM-03_2019_SelfWriteTermination.pdf](literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf) | 9 | `2bf428be6500` | 核心 |
| [MRAM-04](LITERATURE_CATALOG.md#MRAM-04) | 用户 A/B | [MRAM-04_2018_2T2MTJ_ReadMacro.pdf](literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf) | 3 | `655d6de6b37e` | 补充 |
| [MRAM-05](LITERATURE_CATALOG.md#MRAM-05) | 用户 A/B | [MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf](literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf) | 82 | `3ab6e4c97bf3` | 补充 |
| [PCM-01](LITERATURE_CATALOG.md#PCM-01) | R0 已有 | [PCM-01_2023_PCM64_Core.pdf](literature/07_pcm/PCM-01_2023_PCM64_Core.pdf) | 25 | `81c512921e63` | 核心 |
| [PCM-02](LITERATURE_CATALOG.md#PCM-02) | R0 已有 | [PCM-02_2023_AnalogAI_Speech.pdf](literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf) | 23 | `2bca03f1948f` | 核心 |
| [PCM-03](LITERATURE_CATALOG.md#PCM-03) | 用户 A/B | [PCM-03_2022_Hybrid_SLC_MLC.pdf](literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf) | 3 | `91ae3c12a4d5` | 核心 |
| [PCM-04](LITERATURE_CATALOG.md#PCM-04) | 用户 A/B | [PCM-04_2017_Subnanosecond_Nucleation.pdf](literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf) | 5 | `8d3bafdeb91d` | 条件保留 |
| [PCM-05](LITERATURE_CATALOG.md#PCM-05) | R0 已有 | [PCM-05_2024_PCM_Drift.pdf](literature/07_pcm/PCM-05_2024_PCM_Drift.pdf) | 12 | `05992e1bd332` | 补充 |
| [FERAM-01](LITERATURE_CATALOG.md#FERAM-01) | R0 已有 | [FERAM-01_2023_C2FeRAM.pdf](literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf) | 4 | `1e878eb85396` | 核心 |
| [FERAM-02](LITERATURE_CATALOG.md#FERAM-02) | 用户 A/B | [FERAM-02_2021_UltrathinHZO_1T1C.pdf](literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf) | 4 | `07f1125ad2e5` | 核心 |
| [FERAM-03](LITERATURE_CATALOG.md#FERAM-03) | 用户 A/B | [FERAM-03_2020_SoC_1T1C_HZO.pdf](literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf) | 2 | `3baca7408c4b` | 核心 |
| [FERAM-04](LITERATURE_CATALOG.md#FERAM-04) | 用户 A/B | [FERAM-04_2023_NVDRAM_32Gb.pdf](literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf) | 4 | `5498a6eda09e` | 核心 |
| [FERAM-05](LITERATURE_CATALOG.md#FERAM-05) | R0 已有 | [FERAM-05_2024_Codoped_Hafnia.pdf](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf) | 10 | `213d6a142e41` | 补充 |
| [FERAM-06](LITERATURE_CATALOG.md#FERAM-06) | R0 已有 | [FERAM-06_2025_Ferroelectric_Memristor.pdf](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf) | 13 | `d6df9f0b82c8` | 补充 |
| [GC-01](LITERATURE_CATALOG.md#GC-01) | R0 已有 | [GC-01_2022_GainCell_CIM.pdf](literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf) | 2 | `c5e1c9c42668` | 核心 |
| [GC-02](LITERATURE_CATALOG.md#GC-02) | 用户 A/B | [GC-02_2018_MixedVT_4T_GainCell.pdf](literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf) | 13 | `479cfca9f57b` | 核心 |
| [GC-03](LITERATURE_CATALOG.md#GC-03) | R0 已有 | [GC-03_2024_OxideGainCell.pdf](literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf) | 7 | `053621a099f2` | 核心 |
| [GC-04](LITERATURE_CATALOG.md#GC-04) | 用户 A/B | [GC-04_2024_DynamicCascoded_MLC.pdf](literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf) | 13 | `d4c926b1f4d3` | 核心 |
| [GC-05](LITERATURE_CATALOG.md#GC-05) | 用户 A/B | [GC-05_2025_DualMode_GainCell.pdf](literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf) | 13 | `915155c20987` | 核心 |
| [FENOR-01](LITERATURE_CATALOG.md#FENOR-01) | R0 已有 | [FENOR-01_2025_3DNOR_FeFET.pdf](literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf) | 3 | `1fbb27c7d95d` | 核心 |
| [FENOR-02](LITERATURE_CATALOG.md#FENOR-02) | R0 已有 | [FENOR-02_2026_Vertical_FeFET_Array.pdf](literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf) | 3 | `322482d834c2` | 核心 |
| [FENOR-03](LITERATURE_CATALOG.md#FENOR-03) | 用户 A/B | [FENOR-03_2024_BEOL_Vertical_FeNOR.pdf](literature/10_fenor_3d/versions/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf) | 2 | `7399043f639d` | 版本归并 |
| [FENOR-04](LITERATURE_CATALOG.md#FENOR-04) | 用户 A/B | [FENOR-04_2025_FeNOR_CIM_Design.pdf](literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf) | 8 | `21d033ef6ca6` | 核心 |
| [FENOR-05](LITERATURE_CATALOG.md#FENOR-05) | R0 已有 | [FENOR-05_2023_Vertical_FeNAND.pdf](literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND.pdf) | 10 | `de2c0f051648` | 结构对照 |
| [FENOR-06](LITERATURE_CATALOG.md#FENOR-06) | 用户 A/B | [FENOR-06_2026_GateStack_FeNOR.pdf](literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf) | 3 | `9ee85b57af6e` | 核心 |

HEAD：`5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c`。开始时已有 `.DS_Store`、`tasks/.DS_Store` 修改，未清理。未执行 Git 暂存/提交/推送/回退；用户开放 PDF 的本任务 `.gitignore` 设置保留。

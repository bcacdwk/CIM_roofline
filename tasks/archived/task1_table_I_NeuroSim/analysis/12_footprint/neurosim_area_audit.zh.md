# NeuroSim 面积链审查

只验证相容的普通 SRAM 和常规 CMOS-access 1T1R 面积链，不把探针默认尺寸移植到十类主图，也没有执行时延或吞吐模拟。

锁定上游 [NeuroSim 2DInferenceV1.4](https://github.com/neurosim/NeuroSim/tree/8a88abf85844c0e1ba17cc771ea535fff6040456)，SHA `8a88abf85844c0e1ba17cc771ea535fff6040456`。实际来源以 `NEUROSIM_ROOT` 或 `$HOME/neurosim` 的 `worktrees.json` 解析；本机为 `/Users/shine/neurosim/worktrees/2DInferenceV1.4-8a88abf85844`。复制前逐一比较所有 C++/header 与锁定 Git blob，构建副本、可执行文件、日志及 constructor patch 仅留在独立非同步运行区。规范记录见 [neurosim_probe_results.json](neurosim_probe_results.json)，代码见 [探针](neurosim_area_probe.cpp) 与 [runner](run_neurosim_probes.py)。上游版权、CC BY-NC 4.0 与引用说明沿用 [项目上游说明](../../provenance/upstream-notices.txt)。

## 读到的模型口径

- `Technology.cpp:67`：`tech.featureSize = processNode_nm × 1e-9`。本探针为 22 nm。
- `Param.cpp:164-177`：`featuresize` 由 wireWidth 表给出，22 nm 工艺对应 40 nm，不等于 `tech.featureSize`。`ProcessingUnit.cpp:130` 将其写入 `cell.featureSize`。
- `MemCell.h:51-58` 分开定义原始节点、面积、宽高系数；宽高系数的实际尺度取决于 `SubArray` 分支，不能只读变量名。
- `SubArray.cpp:139-176`：普通 SRAM 及 CMOS-access RRAM 的横向数组几何使用 `tech.featureSize`；SRAM 10×28，1T1R 4×12 的默认系数在这里分别形成 280 与 48 个 `tech.featureSize²`。这些默认值只用于链路探针。
- `SubArray.cpp:178-187`：crosspoint 分支使用 `cell.featureSize`，relax 开启时与 CMOS 外围间距要求取 MAX。它不能替代 WH-2T1R、互补 MTJ 或其他特殊结构。
- `relaxArrayCellWidth/Height` 分别扩大与连接外围匹配的宽/高；SRAM 和 1T1R 的映射不同，不能无视两个开关。本轮两个开关均为 0，未把放宽引起的面积混入原生 cell 主图。
- `SubArray.cpp:158-160,190-192` 的 `param->arrayheight/arraywidthunit` 是辅助量，会使用另一 F，且不一定包含 relax。数组面积必须从最终 `lengthRow × lengthCol` / `areaArray` 读取，不能从这两个辅助量推导。
- `SubArray::CalculateArea`（约 541 行起）：`areaArray=heightArray×widthArray` 是数组几何；`usedArea` 加入已实例化外围模块；`area=height×width` 是该 SubArray 模型的总布局框。后两者不是本轮原生存储单元面积。此总布局框也不能称为完整宏 PPA。

## 实际编译与解析结果

两探针均为 128×128 个二元 cell、22 nm CMOS、300 K、LSTP、conventionalSequential。通过 `ProcessingUnitInitialize` 调用 `SubArray::Initialize` 和 `CalculateArea`，只读 SubArray 面积返回；没有调用 latency 接口。时钟等必需初始化字段只使接口合法，不构成时序评价。

| 诊断 | cell 宽×高系数 | tech / cell F [nm] | lengthRow×lengthCol [µm] | areaArray [µm²] | usedArea [µm²] | area [µm²] | array bit area [µm²/bit] |
|---|---:|---:|---:|---:|---:|---:|---:|
| 普通 SRAM | 28×10 | 22 / 40 | 78.848×28.16 | 2220.35968 | 6554.4224768 | 6735.62731424 | 0.13552 |
| 常规 1T1R | 12×4 | 22 / 40 | 33.792×11.264 | 380.633088 | 8206.277301696 | 8206.277301696 | 0.023232 |

解析检查采用 `rows×cols×width_F×height_F×tech.featureSize²`；与 `areaArray` 相同。m²→µm² 乘 10¹²，再除以 16384 bit；同时核验 `area−usedArea=emptyArea` 和 `area≥usedArea≥areaArray>0`。记录保留完整浮点精度，不以显示四舍五入作验算输入。SRAM 辅助 `param->arrayheight` 为 51.2 µm，1T1R 为 20.48 µm，刻意保留其与真正数组高度不同的结果。

```sh
python3 -B analysis/12_footprint/run_neurosim_probes.py \
  --run-dir "$HOME/neurosim/runs/storage-footprint-my-independent-check"
```

run-dir 必须是新的非同步目录；runner 拒绝覆盖。默认 `g++-16`，可用 `--cxx` 或 `NEUROSIM_CXX` 指定兼容编译器。该命令只生成本地诊断，不导出或改动十类输入、服务结果或论文。

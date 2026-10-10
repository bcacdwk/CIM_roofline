# Fig.4 重绘与重新插图检查（2026-10-10）

本轮执行用户最后限定的“只改图并重新插图，不改 papers 的 tex”。起始实际 HEAD 为 `f98cb74d936f58d1b8eda33bc1a7384e02d00abb`，没有回退、commit、PR 或 push。

## 实际修改

- `../plot_qwen36.py`：复用原数据读取与校验，优化单栏图的字号、顶端两行标签、方向提示及底部留白；增加文本互相避碰、文本对 reference 点/三情景范围的避碰检查。默认只生成 single，`--install-paper` 只复制图片文件。
- `../figures/Qwen36_six_lines_shared_SI_single.{png,svg,pdf}`：3.50×3.08 in，保留原十行结构、六个精确负载位置、十个 reference 点、三原生情景范围和技术颜色。字体 7–8.6 pt，PNG 为 360 dpi，SVG/PDF 保持矢量。
- `papers/figures/critical_reuse_single.{png,svg,pdf}`：与上述文件逐字节相同的论文插图副本。文件名沿用既有 includegraphics 路径，原 `fig:critical-reuse` label 不变。
- `papers/output/paper_1167.pdf`：使用现有 Makefile 重新编译的论文。
- 制图包内 README、`caption.en.md` 与 QA 记录：记录用法、图注建议和此次审查。

六份 CSV 的内容哈希与开始时完全一致。没有 tile 换算、新负载计数或仿真。两个真实 alternative 情景仅通过原 min–max 范围表达，未拼接硬件读写端点。原双栏备选图没有重绘。

## 图面与论文检查

顶端六组标签均为阶段名和 U/L 工况两行，数据横坐标未调整。左下角写明 “Hardware relative to each line: ← streaming | resident →”，其左右关系指硬件相对每一条负载线，不是一条共同分界。数值标签对虚线的局部白底遮盖保留，但不遮盖任何硬件点或情景范围。

最终运行 `make -C papers` 成功，编译日志没有 Overfull/Underfull、未定义引用或 LaTeX Warning。最终输出为 7 页，Fig.4 在第 6 页右栏；aux 中为 `fig:critical-reuse → figure 4, page 6`。已用 pypdfium2 渲染单独图文件及全部 7 页并实际查看，图面无标签重叠、裁切或超出版心；正文原有分节、预留框和分页安排未作调整。

机读校验、已审 PDF 哈希和 TeX 状态见 `paper_validation.json`；逐页图在 `paper/`。由于正文存在持续的并行修改与重新编译，将实际查看过的论文版本保存为 `reviewed_paper_1167.pdf`，避免把随后别的进程输出误记为本次已审文件。现有草稿第 5 页的大幅留白未改动，不属于本轮图形调整范围。

## 不改 TeX 的边界

论文 `figures/critical_reuse.tex` 的图注仍描述旧 U* 图，`sections/implications.tex` 与 `sections/conclusion.tex` 也仍包含相关旧表述。新图注仅写入 `../caption.en.md`，已包含“原生硬件服务比与模型级逻辑需求的参考对照、未作完整部署映射校正、低 SI* 不代表更高绝对速度”。**本轮不声称已经同步修改论文文字。**

开始时 `papers/output/paper_1167.pdf` 已有本地改动，替换前已备份至 `before_20261010/`，同时保留原 Fig.4。工作期间 `papers/sections/model.tex` 被并行更新，且其他进程重新编译过论文；本任务没有写入或回退该文件。最终重新编译和目视检查使用并行更新后的最新 TeX，具体哈希已记录。其余开始时记录的 TeX 未发生内容变化。

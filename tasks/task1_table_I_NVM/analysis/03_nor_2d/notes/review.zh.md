# 本例复核记录

- 正式PDF：`output/nor_2d.pdf`，5页，SHA-256 `5af144cca8af93a9f8a852f4f67241f8277a39ac2833ecd8b3a2e9f9b8c01e24`。
- XeLaTeX/ctex构建通过，最终日志无Overfull和Missing character；pypdfium2渲染当前5页至`tmp/pdfs/final/page-01.png`至`page-05.png`，contact同次生成。所有页逐页目视检查，公式、表格、中文字体、页脚和来源长标题无裁切／重叠。
- 原图核对NOR-01 pp85–86、NOR-02 p5/14/37/39/66；关键AC表已渲染目视。主导read、tPP、tSE和BUSY覆盖均与证据一致。
- 默认check_nor.py通过；显式logical维度、32读／32捕获／256数字轮、单4096-bit tile、64page／4sector、全部16384Byte地址一一覆盖、完整写阶段和U*均检查。组织对照保留32sector擦除和相同有效payload。
- 典型独立算式：DS=32×120+(32+256+2)×5=5290ns；TR=64×(400000+18×5)+4×(45000000+2×5)=205605800ns；RI*=(128/16384)×TR/DS=303.64750708884685，U*=TR/DS=38866.880907372404。
- 主范围固定SA、保持、数字通道和native page资源，读100/120/130ns及完整写typ/max相容配对；没有去掉持续erase或将预擦burst当主tau。

外部审阅重点仍为宽读片负载／判决、32片选择隔离、八片共sector高压域、商品完整时序的本地迁移。内部检查不构成用户验收。

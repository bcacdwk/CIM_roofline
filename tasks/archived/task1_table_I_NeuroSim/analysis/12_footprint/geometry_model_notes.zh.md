# RRAM / HZO FeRAM 条件几何模型说明

这两项是明确尺寸、接触和分层布线假设下的原生二元 unit 估计，不是原芯片版图提取、foundry DRC/LVS、完整宏 PPA 或电气时序认证。原来的六项数值不变。规范输入由唯一集成者安装；研究、源码副本、编译、完整源资料和页面渲染均保留非同步区。

## NeuroSim 的实际角色

实际新编译锁定 2DInferenceV1.4、SHA 8a88abf85844c0e1ba17cc771ea535fff6040456 的原 formula.cpp 与 Technology.cpp，调用 `CalculateGateArea(INV,1,W_N,0,H,geometry_only_Technology)`。PMOS 宽度为零，未构造互补 CMOS 门，也没有初始化电气表；28 nm未被伪装成受支持电气节点，130 nm虽有上游电气表，本模型也不调用。`geometry_scale_um` 与最终 `F_mem_nm` 分开：前者只用于公开 compact 几何，后者只在绝对面积得到后归一化。

bulk 单 NMOS 的原生宽度为 7.6F，高度至少 W+3.6F。原生接口没有独立 L，本薄适配明确加入 `n_finger × (L−F)`；另算真正 gate+接触扩散跨度，再取较大的宽度。源/漏 landing 的金属间隙需要时增大接触到 gate 的间距：`gap_eff=max(gap_rule,(landing_width+metal_gap−L−contact_width)/2)`。该值实际进入 C++ 输入及接触跨度，不是图后修正。主值均 1 finger；所有查询保存原生宽高、长栅修正、接触跨度、最终宽度和输入哈希。

每个参数检查从同一输入树产生独立查询，严格验证 primitive_record 的 SHA、输入哈希和 query 哈希。模型又从该 primitive 输出生成 tile；`geometry_inputs` 中的面积不得脱离模型独立手抄。规范有主条件和一次20%宽松接触/间距检查，以及少量单参数响应；较小0.4um²电容只在本地另身份检查，已从规范输入移除。

## WH-2T1R，m=1

原 RRAM-05 PDF p3 Fig4a/c 给 T1 NMOS W/L=500/150nm，T2 NMOS W/L=100/30nm。电路是 T1: SL—X，gate=WL；RRAM: X—BL；T2: GND—TBL，gate=X。这里只有一条外部 WL，不能把第二个物理 gate 导体误称第二 WL。

采用两块独立 active 区，无 T1/T2 或相邻 cell 源漏共享；四个 diffusion 端、两个 gate 接触、X 局部连线以及 SL/BL/WL/TBL/GND/body tie 均有分配。NeuroSim 常数给 contact1.3F、contact-poly gap0.7F、poly extension1F、field-poly gap1.6F 和 M2 pitch3.2F；0.5F enclosure 与将3.2F分为1.6F金属宽/间距是显式 compact 假设，不是该芯片的保密工艺规则。

模型保留 T1 的150nm长栅，主接触区宽 T1=0.3348um、T2=0.2148um。为满足本模型的44.8nm金属间距，T2 的有效 contact-to-gate gap 为21.4nm（不降低19.6nm原下限）。左右布线 gutter 各109.2nm，WL、local X、TBL、GND/body 各有独立通道。WL/TBL 为水平 M2，SL/BL 为垂直 M3，local X 明确为 M1，从 T1 drain/RRAM bottom electrode 到 T2 gate；RRAM top electrode 在独立上层连 BL。

主重复 tile 为 **0.5532×1.2384=0.68508288um²，b=1**。不把 m=4 图的30.3% overhead 套给 m=1，也不以 2×1T1R 比例代替布局。

RRAM 本体横向尺寸未报告。主分配0.0644um square 是 contact/via landing 派生的**条件性上层器件包络**，不称实测 RRAM 电极。包络中心在 T1 drain；200/400nm另包络检查按drain-centered坐标重新计算：200nm使tile面积增至0.74130624um²（+8.2068%），400nm使tile面积增加27.9826%；两者均不作为统计误差界。任何真实 stack 超出该分配应重算 tile，而不是视为零面积。更宽松规则检查是另一布局条件，不是统计区间或工艺/PVT corner。

## HZO 1T1C CUB，1um² active capacitor

新增 Okuno JEDS DOI10.1109/JEDS.2021.3129279 PDF p2 明确64kbit、130nm CMOS、0.4/0.6/0.8/1.0um² MFM和直接位于晶体管上方的 CUB。主保留1.0um²，1×1um square 为面积保持的显式设计形状，来源没有平面 aspect ratio。11/10nm HZO厚度不作为平面 F。

访问 NMOS 选同为130nm的公开 Sky130 `nfet_g5v0d10v5` 参考，W=1um 是设计选择，L=0.5um 来自该5V class公开尺寸。它不是 Sony 原访问管，也不是 native `nfet_05v0_nvt`。官方 VGS0..5.5V、VDS0..11V、VBS0..−5.5V是模型有效电压域，不升级为可靠性认证。主条件选择 WL=5V、目标 storage node=2.5V、body=0；5V wordline源/泵与level shifter属于未计的宏外围。

contact0.17um、HV poly gap0.28um、HV diffusion gap0.30um和L0.5um由公开规则锚定。0.08um enclosure/electrode margin、0.17um contact-to-gate、0.20um poly extension、metal width/space和gate-contact-to-active均是逐字段声明的兼容工程余量，不声称已通过完整 Sky130/Sony DRC。

下层 NMOS contact-inclusive 区宽1.358um；包括body/gate接触的高度2.45um。上层 MFM 的active为1×1um，电极包络1.16×1.16um。按实际坐标放置：BL源端通孔在电容左侧影子以外；drain直接接下电极；PL接上电极。M1 BL纵向贯通，M2 PL和M3 WL横向贯通，M4 body ground分离。WL gate-contact landing下边界离MFM外缘至少0.08um；当电容/边距改变时，接触位置和包络高度自动重算。不是取max(Aaccess,Acap)，也不是把两个面积相加。

主 tile 为 **2.21×2.45=5.4145um²，b=1**。这种包含逐cell body-contact与独立BL通道的条件设计没有主张是最低可实现面积；它给出可追溯的已声明布局，而非为密度排序压缩单元。

官方 Sky130 原始 IDVD 数据（W20/L0.5um，源=0，body=0或−2.5V）已读取并保留小型选定数据行于 drive_check.json。按宽度线性换成W1的静态背景：VGS5/VDS0.2/VBS0时约83.245uA；VGS2/3、VDS0.1、VBS−2.5时约18.441/30.2845uA。后者明确包含body-bias条件，不能当成所有端点80uA保证。这些仅说明所选访问管量级/电压域，既不模拟铁电翻转也不认证2.5V终点、原文8/14ns或现有服务条件。

## 有限自检与限制

- 每个局部区域和contact landing必须位于tile包络内；源漏pad间距、contact-to-gate间距、FeRAM WL/BL通孔避开电容影子逐variant检查。
- 主geometry和单项参数变化真实进入公式。FeRAM L0.5→0.7um使NMOS宽1.358→1.558um，但还未超过上层电容控制的横向尺寸，因此主tile面积可暂时不变；这不是漏用L。cap或electrode margin增加时tile真实增加。
- `D=1/(Axy/b)`，`alpha=(Axy/b)/(F_mem_nm/1000)^2`；F_mem只作归一化，换F不改变绝对密度。两项均node-normalized估计：RRAM28nm、FeRAM130nm。
- 布线矩形/路径证明所声明几何分配和端口归属可审，不等同foundry规则、寄生、电气功能、LVS、良率或量产证明。只有材料名不能自动生成真实存储密度。

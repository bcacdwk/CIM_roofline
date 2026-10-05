// Mechanism-only comparison. Unmodified locked V1.4 supplies every primitive.
#include <cmath>
#include <iomanip>
#include <iostream>
#include "Param.h"
#include "Adder.h"
#include "AdderTree.h"
#include "DFF.h"
#include "constant.h"
Param *param = nullptr;
int main() {
  param = new Param(); param->synchronous = false;
  InputParameter ip{}; ip.processNode=22; ip.temperature=300;
  ip.deviceRoadmap=LSTP; ip.transistorType=conventional;
  Technology tech; tech.Initialize(22,LSTP,conventional); MemCell cell{};
  for (int fanin : {8,32}) for (int bits : {8,18,23}) {
    int depth=static_cast<int>(std::ceil(std::log2(fanin)));
    DFF dff(ip,tech,cell); dff.Initialize(bits+depth,2e8); dff.CalculateArea(0,0,NONE);
    AdderTree tree(ip,tech,cell); tree.Initialize(fanin,bits,1,2e8);
    tree.CalculateArea(0,1e-4,NONE); tree.CalculateLatency(1,fanin,dff.capTgDrain);
    double repeated_two_bit=0, full_width_sequential=0, first=0, two=0;
    for (int level=0;level<depth;++level) {
      Adder short_path(ip,tech,cell); short_path.Initialize(level ? 2 : bits,1,2e8);
      short_path.CalculateArea(0,1e-4,NONE);
      short_path.CalculateLatency(1e20,dff.capTgDrain,1);
      repeated_two_bit+=short_path.readLatency;
      if (!level) first=short_path.readLatency; else two=short_path.readLatency;
      Adder arbitrary_serial(ip,tech,cell); arbitrary_serial.Initialize(bits+level,1,2e8);
      arbitrary_serial.CalculateArea(0,1e-4,NONE);
      arbitrary_serial.CalculateLatency(1e20,dff.capTgDrain,1);
      full_width_sequential+=arbitrary_serial.readLatency;
    }
    std::cout<<std::setprecision(17)<<fanin<<","<<bits<<","<<depth<<","<<dff.capTgDrain<<","<<tree.readLatency<<","<<first<<","<<two<<","<<repeated_two_bit<<","<<full_width_sequential<<"\n";
  }
}

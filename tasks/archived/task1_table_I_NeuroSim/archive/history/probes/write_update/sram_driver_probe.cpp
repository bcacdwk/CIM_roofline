#include <iomanip>
#include <iostream>
#include "Param.h"
#include "SRAMWriteDriver.h"
Param* param = new Param();
int main() {
    InputParameter input;
    input.temperature=300;
    input.processNode=22;
    input.deviceRoadmap=LSTP;
    input.transistorType=conventional;
    Technology tech;
    tech.Initialize(22, LSTP, conventional);
    MemCell cell;
    SRAMWriteDriver narrow(input,tech,cell), wide(input,tech,cell);
    narrow.Initialize(16,1,1);
    wide.Initialize(16,1,8);
    narrow.CalculateArea(0,0,NONE);
    wide.CalculateArea(0,0,NONE);
    narrow.CalculateLatency(1e20,1e-14,500,1);
    const double single=narrow.writeLatency;
    narrow.CalculateLatency(1e20,1e-14,500,2);
    wide.CalculateLatency(1e20,1e-14,500,1);
    std::cout << std::setprecision(17)
      << "{\"technode_nm\":22,\"temperature_K\":300,\"roadmap\":\"LSTP\",\"cap_load_F\":1e-14,\"res_load_ohm\":500"
      << ",\"single_write_s\":" << single << ",\"two_writes_s\":" << narrow.writeLatency
      << ",\"width8_single_write_s\":" << wide.writeLatency
      << ",\"cap_inv_input_F\":" << narrow.capInvInput << ",\"cap_inv_output_F\":" << narrow.capInvOutput
      << "}" << std::endl;
}

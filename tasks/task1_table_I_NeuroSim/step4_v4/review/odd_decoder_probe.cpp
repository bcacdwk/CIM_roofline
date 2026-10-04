#include <iostream>
#include <iomanip>
#include "Param.h"
#include "Technology.h"
#include "RowDecoder.h"
#include "DFF.h"
#include "formula.h"
#include "constant.h"
Param* param;
int main(){Param p;param=&p;InputParameter ip{};ip.temperature=350;ip.processNode=22;ip.transistorType=conventional;ip.deviceRoadmap=LSTP;Technology t;t.Initialize(22,LSTP,conventional);MemCell c{};DFF word(ip,t,c);word.Initialize(24,1e9);word.CalculateArea(0,0,NONE);RowDecoder dec(ip,t,c);dec.Initialize(REGULAR_ROW,9,false,false);dec.CalculateArea(word.height*512,0,NONE);double sink=24*(word.capTgGateN+word.capTgGateP)+word.width*.2e-15/1e-6;dec.CalculateLatency(1e20,sink,0,1,0);double r=CalculateOnResistance(dec.widthInvN,NMOS,350,t),gm=CalculateTransconductance(dec.widthInvN,NMOS,t);auto inv=[&](double cap){return horowitz(r*(dec.capInvOutput+cap),1/(r*gm),1e20,nullptr);};std::cout<<std::setprecision(17)<<"native_decoder_s="<<dec.readLatency<<"\npaired_address_gate_F="<<2*dec.capNandInput<<"\nodd_address_gate_F="<<256*dec.capNorInput<<"\npaired_INV_s="<<inv(2*dec.capNandInput)<<"\nodd_INV_s="<<inv(256*dec.capNorInput)<<"\n";}

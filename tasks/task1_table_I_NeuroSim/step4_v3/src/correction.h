#ifndef STEP4_V3_CORRECTION_H
#define STEP4_V3_CORRECTION_H
#include <algorithm>
#include <cmath>
#include "Adder.h"
#include "DFF.h"
#include "formula.h"
#include "constant.h"
// Exact signed INT8 offset correction, same physical backend technology.
// Three feed-forward 25-bit registered stages, N lanes:
// S1=A-(C<<7); S2=S1-(B<<8); Y=S2+(D<<15).
// NOT(B) + carry-in=1 is a two's-complement subtract. Native full-adder
// carry path is retained; inversion load is the native NAND input capacitance.
// Four operand banks A,B,C,D are installed, no free CPU arithmetic.
struct OffsetCorrection {
  Adder add1, add2, add3;
  DFF operand, stage1, stage2, output;
  double inverter_s, adder_s, combinational_s, area_m2;
  double broadcast_s, broadcast_wire_m, broadcast_cap_F, operand_cap_F;
  int lanes, bits;
  OffsetCorrection(const InputParameter& i,const Technology& t,const MemCell& c,int n,double hz,double h,double macroWidth,double wireResistancePerM)
    :add1(i,t,c),add2(i,t,c),add3(i,t,c),operand(i,t,c),stage1(i,t,c),stage2(i,t,c),output(i,t,c),lanes(n),bits(25){
#ifdef STEP4_TRAINING
    add1.Initialize(bits,n); add2.Initialize(bits,n); add3.Initialize(bits,n);
#else
    add1.Initialize(bits,n,hz); add2.Initialize(bits,n,hz); add3.Initialize(bits,n,hz);
#endif
    operand.Initialize(bits*(2*n+2),hz); // A/B per output; C/D shared scalar, registered
    stage1.Initialize(bits*n,hz); stage2.Initialize(bits*n,hz); output.Initialize(bits*n,hz);
    operand.CalculateArea(h,0,NONE);stage1.CalculateArea(h,0,NONE);stage2.CalculateArea(h,0,NONE);output.CalculateArea(h,0,NONE);
    add1.CalculateArea(h,0,NONE);add2.CalculateArea(h,0,NONE);add3.CalculateArea(h,0,NONE);
    add1.CalculateLatency(1e20,stage1.capTgDrain,1);
    add2.CalculateLatency(1e20,stage2.capTgDrain,1);
    add3.CalculateLatency(1e20,output.capTgDrain,1);
    double ci,co,hi,wi;
    double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn;
    CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hi,&wi);
    CalculateGateCapacitance(INV,1,wn,wp,hi,t,&ci,&co);
    double r=CalculateOnResistance(wn,NMOS,i.temperature,t);
    double gm=CalculateTransconductance(wn,NMOS,t);
    // Each correction lane gets replicated INV per subtract bit: no high-fanout INV.
    operand_cap_F=2*add1.capNandInput; // each operand drives two pins in a nine-NAND full-adder
    inverter_s=horowitz(r*(co+operand_cap_F),1/(r*gm),1e20,nullptr);
    adder_s=std::max(add1.readLatency,std::max(add2.readLatency,add3.readLatency));
    combinational_s=inverter_s+adder_s;
    area_m2=operand.area+stage1.area+stage2.area+output.area+add1.area+add2.area+add3.area+2*n*bits*hi*wi;
    // C,D are scalar results broadcast to N lanes. Keep their installed operand
    // registers and explicitly drive the replicated lane input pins. Two native
    // formula inverters preserve polarity; span comes from this macro/datapath,
    // not a fixed local-wire budget. This is the only fanout extension.
    const double size=std::ceil(std::sqrt(double(n)));
    double ci2,co2,hi2,wi2;
    CalculateGateArea(INV,1,wn*size,wp*size,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hi2,&wi2);
    CalculateGateCapacitance(INV,1,wn*size,wp*size,hi2,t,&ci2,&co2);
    broadcast_wire_m=std::max(macroWidth,area_m2/h);
    broadcast_cap_F=broadcast_wire_m*0.2e-15/1e-6;
    double rw=broadcast_wire_m*wireResistancePerM;
    double r2=CalculateOnResistance(wn*size,NMOS,i.temperature,t);
    double gm2=CalculateTransconductance(wn*size,NMOS,t);
    double first=horowitz(r*(co+ci2),1/(r*gm),1e20,nullptr);
    const double laneLoad=std::max(ci,2*add3.capNandInput); // C: INV pin, D: positive Adder operand
    double second=horowitz(r2*(co2+n*laneLoad+broadcast_cap_F)+rw*(broadcast_cap_F/2+n*laneLoad),1/(r2*gm2),1e20,nullptr);
    broadcast_s=first+second;
    combinational_s=broadcast_s+inverter_s+adder_s;
    area_m2+=2*bits*(hi*wi+hi2*wi2);

  }
};
#endif

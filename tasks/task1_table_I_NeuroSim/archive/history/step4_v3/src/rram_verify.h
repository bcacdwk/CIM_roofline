#ifndef STEP4_V3_RRAM_VERIFY_H
#define STEP4_V3_RRAM_VERIFY_H
#include "Mux.h"
#include "RowDecoder.h"
#include "Comparator.h"
#include "DFF.h"
// Verification uses the compute ADCs with a one-hot row. Select the expected
// bit from the retained 288-bit row, or zero after RESET. Encode the calibrated
// HRS/LRS codes by wires plus one inversion. Two magnitude comparisons and an
// OR implement mismatch equality without a software comparator.
struct RramVerify {
  Mux targetMux,phaseMux;
  RowDecoder targetSelect,phaseSelect;
  DFF control,status;
  Comparator compare;
  double selector_s,compare_s,or_s,encode_s,combinational_s,area_m2;
  RramVerify(const InputParameter&i,const Technology&t,const MemCell&c,int bits,double hz,double h,double w)
    :targetMux(i,t,c),phaseMux(i,t,c),targetSelect(i,t,c),phaseSelect(i,t,c),control(i,t,c),status(i,t,c),compare(i,t,c) {
    control.Initialize(5,hz);status.Initialize(32,hz);
    control.CalculateArea(h,0,NONE);status.CalculateArea(h,0,NONE);
    targetMux.Initialize(32,9,0,true);phaseMux.Initialize(32,2,0,true);
    targetMux.CalculateArea(0,h,NONE);phaseMux.CalculateArea(0,h,NONE);
    targetSelect.Initialize(REGULAR_ROW,4,true,false);phaseSelect.Initialize(REGULAR_ROW,1,true,false);
    targetSelect.CalculateArea(h,0,NONE);phaseSelect.CalculateArea(h,0,NONE);
    double cw=h*0.2e-15/1e-6;
    targetSelect.CalculateLatency(1e20,32*targetMux.capTgGateN+cw,32*targetMux.capTgGateP+cw,1,0);
    phaseSelect.CalculateLatency(1e20,32*phaseMux.capTgGateN+cw,32*phaseMux.capTgGateP+cw,1,0);
    compare.Initialize(bits,64); // two directions per ADC lane, in parallel
    compare.CalculateUnitArea(NONE);compare.CalculateArea(w);
    double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn;
    double hi,wi,ci,co,hn,wnor,cinor,conor;
    CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hi,&wi);
    CalculateGateCapacitance(INV,1,wn,wp,hi,t,&ci,&co);
    CalculateGateArea(NOR,2,wn,2*wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hn,&wnor);
    CalculateGateCapacitance(NOR,2,wn,2*wp,hn,t,&cinor,&conor);
    compare.CalculateLatency(1e20,cinor,1);
    compare_s=compare.readLatency;
    double rp=2*CalculateOnResistance(2*wp,PMOS,i.temperature,t);
    double rn=CalculateOnResistance(wn,NMOS,i.temperature,t);
    or_s=horowitz(rp*(conor+ci),0,1e20,nullptr)+horowitz(rn*(co+status.capTgDrain),0,1e20,nullptr);
    encode_s=horowitz(rn*(co+2*compare.capInvInput),0,1e20,nullptr);
    targetMux.CalculateLatency(1e20,phaseMux.capTgDrain+8*targetMux.capTgDrain,1);
    phaseMux.CalculateLatency(1e20,ci+2*compare.capInvInput+phaseMux.capTgDrain,1);
    selector_s=targetSelect.readLatency+targetMux.readLatency+phaseSelect.readLatency+phaseMux.readLatency;
    combinational_s=encode_s+compare_s+or_s;
    area_m2=control.area+status.area+compare.area+targetMux.area+phaseMux.area+targetSelect.area+phaseSelect.area+32*(2*hi*wi+hn*wnor);
  }
};
#endif

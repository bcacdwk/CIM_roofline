#ifndef STEP4_V3_RRAM_VERIFY_H
#define STEP4_V3_RRAM_VERIFY_H
#include "Mux.h"
#include "RowDecoder.h"
#include "Comparator.h"
#include "DFF.h"
// Verification uses the compute ADCs with a one-hot row. Select the expected
// bit from the retained 288-bit row, or zero after RESET. Encode the calibrated
// HRS/LRS codes by derived constant/direct/inverted target wires. Two magnitude comparisons and an
// OR implement mismatch equality without a software comparator.
struct RramVerify {
  Mux targetMux,phaseMux,statusReset;
  RowDecoder targetSelect;
  DFF control,status,phaseStatus;
  Comparator compare;
  int direct_code_pins=0,inverted_code_pins=0;
  double clear_s,clear_selector_s,sticky_s,phase_combinational_s,phase_finalize_s;
  double selector_s,phase_selector_s,compare_s,or_s,encode_s,combinational_s,area_m2;
  RramVerify(const InputParameter&i,const Technology&t,const MemCell&c,int bits,double hz,double h,double w,double wireResistancePerM,int expectedHRS,int expectedLRS)
    :targetMux(i,t,c),phaseMux(i,t,c),statusReset(i,t,c),targetSelect(i,t,c),control(i,t,c),status(i,t,c),phaseStatus(i,t,c),compare(i,t,c) {
    control.Initialize(6,hz);status.Initialize(32,hz);phaseStatus.Initialize(1,hz);
    control.CalculateArea(h,0,NONE);status.CalculateArea(h,0,NONE);phaseStatus.CalculateArea(h,0,NONE);
    control.CalculateLatency(1e20,1);status.CalculateLatency(1e20,1);phaseStatus.CalculateLatency(1e20,1);
    targetMux.Initialize(32,9,0,true);phaseMux.Initialize(32,2,0,true);statusReset.Initialize(32,2,0,true);
    targetMux.CalculateArea(0,h,NONE);phaseMux.CalculateArea(0,h,NONE);statusReset.CalculateArea(0,h,NONE);
    targetSelect.Initialize(REGULAR_ROW,4,true,false);
    targetSelect.CalculateArea(h,0,NONE);
    double cw=h*0.2e-15/1e-6;
    targetSelect.muxSelectWireCap=cw;targetSelect.muxSelectWireRes=h*wireResistancePerM;targetSelect.muxSelectFanout=32;
    targetSelect.CalculateLatency(1e20,32*targetMux.capTgGateN,32*targetMux.capTgGateP,1,0);
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
    or_s=horowitz(rp*(conor+ci),0,1e20,nullptr)+horowitz(rn*(co+cinor),0,1e20,nullptr);
    // Sticky lane mismatch preserves every earlier MUX group. A native2:1 mux
    // selects constant0 at phase start; after that status <- status OR mismatch.
    sticky_s=horowitz(rp*(conor+ci),0,1e20,nullptr)+horowitz(rn*(co+statusReset.capTgDrain),0,1e20,nullptr);
    statusReset.CalculateLatency(1e20,status.capTgDrain+statusReset.capTgDrain,1);
    const double orStage=horowitz(rp*(conor+ci),0,1e20,nullptr)+horowitz(rn*(co+cinor),0,1e20,nullptr);
    phase_combinational_s=4*orStage+horowitz(rp*(conor+ci),0,1e20,nullptr)+horowitz(rn*(co+phaseStatus.capTgDrain),0,1e20,nullptr);
    phase_finalize_s=phase_combinational_s+phaseStatus.readLatency;
    // Derive the nominal ADC code wires from the actual requested conductances.
    // Constant bits are rail wires; varying bits use direct or inverted target bits.
    for(int bit=0;bit<bits;++bit){int hbit=(expectedHRS>>bit)&1,lbit=(expectedLRS>>bit)&1;
      direct_code_pins+=(hbit==0&&lbit==1);inverted_code_pins+=(hbit==1&&lbit==0);}
    encode_s=inverted_code_pins?horowitz(rn*(co+2*compare.capInvInput),0,1e20,nullptr):0;
    targetMux.CalculateLatency(1e20,phaseMux.capTgDrain+8*targetMux.capTgDrain,1);
    phaseMux.CalculateLatency(1e20,inverted_code_pins*ci+direct_code_pins*2*compare.capInvInput+phaseMux.capTgDrain,1);
    // A one-bit phase does not need the upstream multi-bit decoder topology.
    // Native two inverter stages create complementary enables for both MUX inputs.
    double hp,wpArea,cpin,cpout;
    CalculateGateArea(INV,1,3*wn,3*wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hp,&wpArea);
    CalculateGateCapacitance(INV,1,3*wn,3*wp,hp,t,&cpin,&cpout);
    double gateLoad=32*(phaseMux.capTgGateN+phaseMux.capTgGateP),rw=h*wireResistancePerM;
    double rphase=CalculateOnResistance(3*wn,NMOS,i.temperature,t);
    double gmphase=CalculateTransconductance(3*wn,NMOS,t);
    double distributed=rw*(cw/2+gateLoad*33/64);
    phase_selector_s=horowitz(rphase*(cpout+cpin+gateLoad+cw)+distributed,1/(rphase*gmphase),1e20,nullptr)
                     +horowitz(rphase*(cpout+gateLoad+cw)+distributed,1/(rphase*gmphase),1e20,nullptr);
    double clearLoad=32*(statusReset.capTgGateN+statusReset.capTgGateP);
    double clearDist=rw*(cw/2+clearLoad*33/64);
    clear_selector_s=horowitz(rphase*(cpout+cpin+clearLoad+cw)+clearDist,1/(rphase*gmphase),1e20,nullptr)
                    +horowitz(rphase*(cpout+clearLoad+cw)+clearDist,1/(rphase*gmphase),1e20,nullptr);
    clear_s=2*(control.readLatency+clear_selector_s)+statusReset.readLatency+status.readLatency;
    selector_s=targetSelect.readLatency+targetMux.readLatency+phase_selector_s+phaseMux.readLatency;
    combinational_s=encode_s+compare_s+or_s+sticky_s+statusReset.readLatency;
    area_m2=control.area+status.area+phaseStatus.area+compare.area+targetMux.area+phaseMux.area+statusReset.area+targetSelect.area+4*hp*wpArea+32*((2+inverted_code_pins)*hi*wi+2*hn*wnor)+31*(hi*wi+hn*wnor);
  }
};
#endif

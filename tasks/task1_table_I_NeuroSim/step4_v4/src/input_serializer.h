#ifndef STEP4_V3_INPUT_SERIALIZER_H
#define STEP4_V3_INPUT_SERIALIZER_H
#include "Mux.h"
#include "RowDecoder.h"
#include "DFF.h"
#include "formula.h"
#include "constant.h"
// Byte register -> bit-plane selection, including the fixed-zero selection
// used after the sign-bit plane of the second unsigned pass. No host serializer.
struct InputSerializer {
  Mux mux;
  RowDecoder decoder;
  DFF address;
  double combinational_s, wire_cap_F, wire_res_ohm, area_m2, polarity_inv_s;
  InputSerializer(const InputParameter& i,const Technology& t,const MemCell& c,
                  int rows,double hz,double height,double wireResistancePerM,double sinkCap,bool complement=false)
      :mux(i,t,c),decoder(i,t,c),address(i,t,c) {
    mux.Initialize(rows,9,0,true);
    mux.CalculateArea(0,height,NONE);
    decoder.Initialize(REGULAR_ROW,4,true,false);
    decoder.CalculateArea(height,0,NONE);
    address.Initialize(5,hz); // four selection bits plus the two-pass bank phase
    address.CalculateArea(height,0,NONE);
    wire_cap_F=height*0.2e-15/1e-6;
    wire_res_ohm=height*wireResistancePerM;
#ifdef STEP4_TRAINING
    decoder.muxSelectWireRes=wire_res_ohm;decoder.muxSelectWireCap=wire_cap_F;decoder.muxSelectFanout=rows;
    decoder.CalculateLatency(1e20,rows*mux.capTgGateN,
                             rows*mux.capTgGateP,1,0);
#else
    decoder.CalculateLatency(1e20,rows*mux.capTgGateN+wire_cap_F,
                             rows*mux.capTgGateP+wire_cap_F,wire_res_ohm,rows,1,0);
#endif
    // Nine TG output diffusion nodes share the selected row signal.
    double muxSink=sinkCap,polarityArea=0;
    polarity_inv_s=0;
    if(complement){
      // DCIM NOR(~x, Qbar) implements x AND stored_weight; Qbar is an
      // existing SRAM node, but the input inversion is explicit hardware.
      double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn,hi,wi,ci,co;
      CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hi,&wi);
      CalculateGateCapacitance(INV,1,wn,wp,hi,t,&ci,&co);
      double r=CalculateOnResistance(wn,NMOS,i.temperature,t);
      double gm=CalculateTransconductance(wn,NMOS,t);
      polarity_inv_s=horowitz(r*(co+sinkCap),1/(r*gm),1e20,nullptr);
      muxSink=ci;polarityArea=rows*hi*wi;
    }
    mux.CalculateLatency(1e20,muxSink+8*mux.capTgDrain,1);
    combinational_s=decoder.readLatency+mux.readLatency+polarity_inv_s;
    area_m2=mux.area+decoder.area+address.area+polarityArea;
  }
};
#endif

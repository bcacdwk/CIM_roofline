// NAND native local port/holding/arithmetic bank; external string/TIA model is separate.
// This file constructs no memory cell array and performs no material read/write model.
#include <iostream>
#include <iomanip>
#include <cmath>
#include <map>
#include <memory>
#include <algorithm>
#include "Adder.h"
#include "Subtractor.h"
#include "DFF.h"
#include "Mux.h"
#include "RowDecoder.h"
#include "formula.h"
#include "constant.h"
#include "request.h"
#include "../Param.h"
Param *param;
static void emit(const char*k,double v){if(!std::isfinite(v)){std::cerr<<"V5_INVALID "<<k;std::exit(2);}std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
struct Select {
 Mux mux;RowDecoder decode;bool present=false,addressed=false;double area=0,delay=0,cin=0;
 Select(InputParameter&i,Technology&t,MemCell&c):mux(i,t,c),decode(i,t,c){}
 void init(int bits,int choices,double load,bool address=true){
  if(choices<=1)return;present=true;
  mux.Initialize(bits,choices,0,true);mux.CalculateArea(0,0,NONE);mux.CalculateLatency(1e20,load,1);
  addressed=address;
  if(address){decode.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(choices)),true);decode.CalculateArea(0,0,NONE);
  decode.CalculateLatency(1e20,mux.capTgGateN*bits,mux.capTgGateP*bits,1,1);}
  area=mux.area+(address?decode.area:0);delay=mux.readLatency+(address?decode.readLatency:0);cin=mux.capTgDrain;
 }
 void load(double load){if(present){mux.CalculateLatency(1e20,load,1);delay=mux.readLatency+(addressed?decode.readLatency:0);}}
};
int main(){
 Param paramValue;param=&paramValue;paramValue.processNode=request::technology_nm;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;Technology t;t.Initialize(ip.processNode,LSTP);MemCell c{};
 int K=request::logical_K,N=request::logical_N,L=request::lanes,B=35,adc=request::adc_count;
 DFF blMaskHold(ip,t,c),input(ip,t,c),staging(ip,t,c),page(ip,t,c),raw(ip,t,c),corrected(ip,t,c),result(ip,t,c),coeff(ip,t,c),work(ip,t,c),control(ip,t,c);
 blMaskHold.Initialize(request::bitlines,request::clock_Hz);input.Initialize(K*9,request::clock_Hz);staging.Initialize(K*9,request::clock_Hz);page.Initialize(L*3,request::clock_Hz);raw.Initialize(adc*request::adc_bits,request::clock_Hz);corrected.Initialize(adc*32,request::clock_Hz);result.Initialize(N*32,request::clock_Hz);coeff.Initialize(adc*request::row_groups*48,request::clock_Hz);work.Initialize(L*B*3,request::clock_Hz);control.Initialize(64,request::clock_Hz);
 double area=0;for(auto*d:{&blMaskHold,&input,&staging,&page,&raw,&corrected,&result,&coeff,&work,&control}){d->CalculateArea(0,0,NONE);d->CalculateLatency(1e20,1);area+=d->area;}
 Adder add(ip,t,c),index(ip,t,c);Subtractor sub(ip,t,c),abs(ip,t,c);add.Initialize(B,L);sub.Initialize(B,L);abs.Initialize(9,L);index.Initialize(16,4);
 for(auto*d:{&add,&index}){d->CalculateArea(0,0,NONE);area+=d->area;}for(auto*d:{&sub,&abs}){d->CalculateArea(0,0,NONE);area+=d->area;}
 double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn,ih,iw,ci,co,nh,nw,nci,nco;
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ih,&iw);CalculateGateCapacitance(INV,1,wn,wp,ih,t,&ci,&co);
 CalculateGateArea(NAND,2,2*wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&nh,&nw);CalculateGateCapacitance(NAND,2,2*wn,wp,nh,t,&nci,&nco);
 auto logic=[&](double load){return horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,t)*(nco+ci),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(co+load),0,1e20,nullptr);};
 auto buffer=[&](double load){double scale=std::max(1.,std::ceil(std::sqrt(load/ci))),h,w,c2,o2;CalculateGateArea(INV,1,wn*scale,wp*scale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h,&w);CalculateGateCapacitance(INV,1,wn*scale,wp*scale,h,t,&c2,&o2);return std::pair<double,double>{horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(co+c2),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn*scale,NMOS,ip.temperature,t)*(o2+load),0,1e20,nullptr),h*w+ih*iw};};
 Select inputRead(ip,t,c),maskKeep(ip,t,c),coeffKeep(ip,t,c),corrKeep(ip,t,c),inputKeep(ip,t,c),stageKeep(ip,t,c),stageRead(ip,t,c),pageKeep(ip,t,c),pageRead(ip,t,c),coeffRead(ip,t,c),adcRead(ip,t,c),resultRead(ip,t,c),workKeep(ip,t,c),outKeep(ip,t,c),mode(ip,t,c),shift(ip,t,c),digit(ip,t,c),signAbs(ip,t,c);
 inputRead.init(L*9,K/L,nci);maskKeep.init(request::bitlines,2,blMaskHold.capTgDrain,false);coeffKeep.init(adc*request::row_groups*48,2,coeff.capTgDrain,false);corrKeep.init(adc*32,2,corrected.capTgDrain,false);inputKeep.init(K*9,2,input.capTgDrain,false);stageKeep.init(K*9,2,staging.capTgDrain,false);stageRead.init(L*9,K/L,nci);
 pageKeep.init(L*3,2,page.capTgDrain,false);pageRead.init(8,L*3/8,request::external_IO_load_F);
 coeffRead.init(L*48,adc*request::row_groups/L,add.capNandInput+sub.capNandInput);adcRead.init(L*request::adc_bits,adc/L,sub.capNandInput);
 resultRead.init(8*32,N/8,add.capNandInput+sub.capNandInput);workKeep.init(L*B*3,2,nci,false);outKeep.init(N*32,2,nci,false);
 mode.init(L*B,4,add.capNandInput+sub.capNandInput);shift.init(L*B,16,mode.cin);digit.init(L*2,4,nci);signAbs.init(L*9,2,stageKeep.cin,false);
 resultRead.decode.CalculateLatency(1e20,(resultRead.mux.capTgGateN+outKeep.mux.capTgGateN)*8*32,(resultRead.mux.capTgGateP+outKeep.mux.capTgGateP)*8*32,1,1);resultRead.delay=resultRead.mux.readLatency+resultRead.decode.readLatency;
 add.CalculateLatency(1e20,workKeep.cin+outKeep.cin+corrKeep.cin+coeffKeep.cin,1);sub.CalculateLatency(1e20,workKeep.cin+outKeep.cin,1);abs.CalculateLatency(1e20,signAbs.cin,1);index.CalculateLatency(1e20,nci,1);
 RowDecoder ingress(ip,t,c);ingress.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(K/L)),true);ingress.CalculateArea(0,0,NONE);ingress.CalculateLatency(1e20,(inputKeep.mux.capTgGateN+stageKeep.mux.capTgGateN)*L*9+maskKeep.mux.capTgGateN*L*3,(inputKeep.mux.capTgGateP+stageKeep.mux.capTgGateP)*L*9+maskKeep.mux.capTgGateP*L*3,1,1);
 double pageCaptureDelay=0,pageCaptureArea=0; // all48packet bits captured together; PE engine owns full page buffer
 // Native selection and RC see real BL and external HV level-shifter input loads.
 RowDecoder wl(ip,t,c);wl.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::wordlines)),false);wl.CalculateArea(0,0,NONE);wl.CalculateLatency(1e20,request::blocks*request::HV_level_input_F,0,1,1);
 Mux bl(ip,t,c);bl.Initialize(request::bitlines,2,request::BL_switch_R_ohm,false);bl.CalculateArea(0,0,NONE);bl.CalculateLatency(1e20,request::BL_cap_F,1);
 auto perBLbuffer=buffer(bl.capTgGateN+bl.capTgGateP);area+=request::bitlines*perBLbuffer.second;double blMask=logic(ci)+perBLbuffer.first;auto digitControl=buffer(request::bitlines*nci),clear=buffer((N*32+L*B*3+64)*nci);
 double cellMaskArea=request::bitlines*3*(nh*nw+ih*iw);double clearGate=logic(result.capTgDrain);
 // 35-bit native Add/Sub used for11bit serial calibration multiplication,
 // 32step restoring calibration division, and signed base4 reconstruction.
 double arith=std::max({coeffRead.delay,adcRead.delay,resultRead.delay,shift.delay})+mode.delay+std::max(add.readLatency,sub.readLatency)+workKeep.delay+clearGate;
 double ingressPath=abs.readLatency+signAbs.delay+ingress.readLatency+stageKeep.delay;
 double format=stageRead.delay+digit.delay+logic(pageKeep.cin)+pageCaptureDelay+pageKeep.delay;
 double maskFormat=inputRead.delay+digit.delay+logic(maskKeep.cin)+ingress.readLatency+maskKeep.delay;
 double critical=std::max({maskFormat,arith,ingressPath,format,pageRead.delay,clear.first+clearGate,index.readLatency+clearGate});
 for(auto*x:{&inputRead,&maskKeep,&coeffKeep,&corrKeep,&inputKeep,&stageKeep,&stageRead,&pageKeep,&pageRead,&coeffRead,&adcRead,&resultRead,&workKeep,&outKeep,&mode,&shift,&digit,&signAbs})area+=x->area;
 area+=ingress.area+pageCaptureArea+wl.area+bl.area+cellMaskArea+digitControl.second+clear.second+(N*32+L*B*3+64)*(nh*nw+ih*iw);
 emit("BL_mask_hold_bits",blMaskHold.numDff);emit("native_input_mask_format_s",maskFormat);emit("input_hold_bits",input.numDff);emit("resident_row_staging_bits",staging.numDff);emit("formatted_page_buffer_bits",page.numDff);emit("ADC_code_hold_bits",raw.numDff);emit("corrected_channel_hold_bits",corrected.numDff);emit("output_hold_bits",result.numDff);emit("calibration_coefficient_bits",coeff.numDff);emit("arithmetic_work_bits",work.numDff);emit("control_bits",control.numDff);
 emit("native_Adder_lanes",L);emit("native_Adder_width",B);emit("native_Adder_s",add.readLatency);emit("native_Subtractor_s",sub.readLatency);emit("native_abs_s",abs.readLatency);emit("native_capture_s",raw.readLatency);emit("native_ingress_comb_s",ingressPath);emit("native_format_comb_s",format);emit("native_page_byte_select_s",pageRead.delay);emit("native_arithmetic_comb_s",arith);
 emit("native_WL_decode_s",wl.readLatency);emit("native_WL_LV_output_load_F",request::blocks*request::HV_level_input_F);emit("native_BL_switch_s",bl.readLatency);emit("native_BL_switch_actual_R_ohm",bl.resTg);emit("native_BL_switch_drain_F",bl.capTgDrain);emit("native_BL_switch_gate_n_F",bl.capTgGateN);emit("native_BL_switch_gate_p_F",bl.capTgGateP);emit("native_BL_switch_width_n_m",bl.widthTgN);emit("native_BL_switch_width_p_m",bl.widthTgP);emit("native_BL_mask_s",blMask+digitControl.first);emit("native_state_clear_s",clear.first+clearGate+raw.readLatency);
 emit("native_vdd_V",t.vdd);emit("native_vth_V",t.vth);emit("digital_critical_comb_s",critical);emit("digital_halfcycle_min_period_s",2*critical);emit("digital_clock_budget_satisfied",1/request::clock_Hz>=2*critical);emit("native_digital_port_area_m2",area);emit("component_only",1);return 0;
}

// GC differential ADC / reconstruction / Xsum and separate maintenance state.
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
 Param p;p.processNode=request::technology_nm;param=&p;InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;
 Technology t;t.Initialize(ip.processNode,LSTP);MemCell c{};
 const int K=request::logical_K,N=request::logical_N,L=request::mac_lanes,B=request::accumulator_bits,A=request::adc_bits,P=request::adc_pair_lanes,X=request::xsum_bits,G=N/L;
 DFF operation(ip,t,c),in(ip,t,c),raw(ip,t,c),diff(ip,t,c),target(ip,t,c),refresh(ip,t,c),result(ip,t,c),xsum(ip,t,c),timer(ip,t,c),rp(ip,t,c),fp(ip,t,c),status(ip,t,c);
 operation.Initialize(11,request::clock_Hz);in.Initialize(K*8,request::clock_Hz);raw.Initialize(2*P*A,request::clock_Hz);diff.Initialize(P*(A+1),request::clock_Hz);target.Initialize(L*8,request::clock_Hz);refresh.Initialize(P,request::clock_Hz);result.Initialize(N*B,request::clock_Hz);xsum.Initialize(X,request::clock_Hz);timer.Initialize(16,request::clock_Hz);rp.Initialize(8,request::clock_Hz);fp.Initialize(8,request::clock_Hz);status.Initialize(2,request::clock_Hz);
 double area=0;for(auto*d:{&operation,&in,&raw,&diff,&target,&refresh,&result,&xsum,&timer,&rp,&fp,&status}){d->CalculateArea(0,0,NONE);d->CalculateLatency(1e20,1);area+=d->area;}
 Adder opIncrement(ip,t,c),shiftIndex(ip,t,c),macAdd(ip,t,c),xadd(ip,t,c),tick(ip,t,c),rinc(ip,t,c),finc(ip,t,c),guard(ip,t,c);
 Subtractor macSub(ip,t,c),difference(ip,t,c),deadline(ip,t,c);
 opIncrement.Initialize(10,1);shiftIndex.Initialize(4,1);macAdd.Initialize(B,L);macSub.Initialize(B,L);difference.Initialize(A+1,P);xadd.Initialize(X,1);tick.Initialize(16,1);rinc.Initialize(8,1);finc.Initialize(8,1);guard.Initialize(16,1);deadline.Initialize(16,1);
 for(auto*a:{&opIncrement,&shiftIndex,&macAdd,&xadd,&tick,&rinc,&finc,&guard}){a->CalculateArea(0,0,NONE);area+=a->area;}
 for(auto*s:{&macSub,&difference,&deadline}){s->CalculateArea(0,0,NONE);area+=s->area;}
 double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn,nh,nw,nci,nco,ih,iw,ici,ico;
 CalculateGateArea(NAND,2,2*wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&nh,&nw);CalculateGateCapacitance(NAND,2,2*wn,wp,nh,t,&nci,&nco);
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ih,&iw);CalculateGateCapacitance(INV,1,wn,wp,ih,t,&ici,&ico);
 auto andDelay=[&](double load){return horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,t)*(nco+ici),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(ico+load),0,1e20,nullptr);};
 auto drive=[&](double load){double scale=std::max(1.,std::ceil(std::sqrt(load/ici))),h,w,ci,co;CalculateGateArea(INV,1,wn*scale,wp*scale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h,&w);CalculateGateCapacitance(INV,1,wn*scale,wp*scale,h,t,&ci,&co);area+=h*w+ih*iw;return horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(ico+ci),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn*scale,NMOS,ip.temperature,t)*(co+load),0,1e20,nullptr);};
 Select opKeep(ip,t,c),ingress(ip,t,c),inputRow(ip,t,c),inputBits(ip,t,c),rowGroup(ip,t,c),rowMode(ip,t,c),plane(ip,t,c),shift(ip,t,c),feedback(ip,t,c),operand(ip,t,c),choice(ip,t,c),keep(ip,t,c),xkeep(ip,t,c),programMode(ip,t,c),rkeep(ip,t,c),fkeep(ip,t,c),tkeep(ip,t,c);
 opKeep.init(11,2,nci,false);ingress.init(K*8,2,in.capTgDrain,false);inputRow.init(8,K,xadd.capNandInput*(X-7));inputBits.init(K,8,nci);rowMode.init(K,2,request::rwl_control_load_per_row_F,false);
 plane.init((A+1)*L,P/L,0);shift.init(B*L,15,macAdd.capNandInput+macSub.capNandInput);int signFanout=0;for(int shiftBit=0;shiftBit<15;shiftBit++)signFanout+=std::max(1,B-A-shiftBit);plane.load(shift.cin*signFanout);
 feedback.init(B*L,G,macAdd.capNandInput+macSub.capNandInput,false);operand.init(B*L,2,macSub.capNandInput+macAdd.capNandInput,false);
 keep.init(N*B,2,nci,false);choice.init(B*L,2,keep.cin*G,false);xkeep.init(X,2,nci,false);
 programMode.init(P,2,request::program_control_cap_F,false);rkeep.init(8,2,nci,false);fkeep.init(8,2,nci,false);tkeep.init(16,2,nci,false);
 opIncrement.CalculateLatency(1e20,opKeep.cin,1);shiftIndex.CalculateLatency(1e20,shift.decode.capInvInput,1);
 difference.CalculateLatency(1e20,diff.capTgDrain,1);macAdd.CalculateLatency(1e20,choice.cin,1);macSub.CalculateLatency(1e20,choice.cin,1);xadd.CalculateLatency(1e20,xkeep.cin,1);
 tick.CalculateLatency(1e20,tkeep.cin,1);rinc.CalculateLatency(1e20,rkeep.cin,1);finc.CalculateLatency(1e20,fkeep.cin,1);guard.CalculateLatency(1e20,deadline.capNandInput,1);deadline.CalculateLatency(1e20,status.capTgDrain,1);
 RowDecoder rowsel(ip,t,c),inputCapture(ip,t,c);double groupDelay=0,groupArea=0;
 if(G>1){RowDecoder group(ip,t,c);group.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(G)),true);group.CalculateArea(0,0,NONE);group.CalculateLatency(1e20,(feedback.mux.capTgGateN+keep.mux.capTgGateN)*B*L,(feedback.mux.capTgGateP+keep.mux.capTgGateP)*B*L,1,1);groupDelay=group.readLatency;groupArea=group.area;}
 rowsel.Initialize(REGULAR_ROW,2,true);rowsel.CalculateArea(0,0,NONE);rowsel.CalculateLatency(1e20,nci*16,0,1,1);
 int beats=K*8/request::input_port_bits;inputCapture.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(beats)),true);inputCapture.CalculateArea(0,0,NONE);inputCapture.CalculateLatency(1e20,ingress.mux.capTgGateN*request::input_port_bits,ingress.mux.capTgGateP*request::input_port_bits,1,1);
 // Results/Xsum clear only at new stream request. Progress/timer have their own
 // local clear controls; refresh never drives stream or resident clear nets.
 double clearGate=andDelay(result.capTgDrain);double streamClear=drive((N*B+X+11)*nci)+clearGate;
 double residentClear=drive(8*nci)+andDelay(rp.capTgDrain),refreshClear=drive((8+16)*nci)+andDelay(fp.capTgDrain);
 double mask=andDelay(rowMode.cin),maskControl=drive(K*(rowMode.mux.capTgGateN+rowMode.mux.capTgGateP));
 double modeControl=drive(P*(programMode.mux.capTgGateN+programMode.mux.capTgGateP));
 double xsumBroadcast=0;for(int bit=0;bit<X;bit++)xsumBroadcast=std::max(xsumBroadcast,drive(operand.cin*L*std::max(1,B-X-4)));
 double signSelect=3*horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,t)*(nco+2*nci),0,1e20,nullptr)+drive((choice.mux.capTgGateN+choice.mux.capTgGateP)*B*L);area+=4*nh*nw;
 double arithmetic=std::max(std::max(plane.delay,shiftIndex.readLatency)+shift.delay+operand.delay,groupDelay+feedback.delay)+std::max(macAdd.readLatency,macSub.readLatency)+std::max(choice.delay,signSelect)+keep.delay+clearGate;
 double correction=std::max(groupDelay+feedback.delay,xsumBroadcast+operand.delay)+macSub.readLatency+choice.delay+keep.delay+clearGate;
 double xsumPath=inputRow.delay+xadd.readLatency+xkeep.delay+clearGate;
 double rwl=std::max(inputBits.delay,rowsel.readLatency)+mask+std::max(rowMode.delay,maskControl);
 double guardPath=guard.readLatency+deadline.readLatency;
 double critical=std::max({opIncrement.readLatency+opKeep.delay+clearGate,arithmetic,correction,xsumPath,difference.readLatency,rwl,guardPath,streamClear,residentClear,refreshClear,inputCapture.readLatency+ingress.delay,tick.readLatency+tkeep.delay+clearGate,rinc.readLatency+rkeep.delay+clearGate,finc.readLatency+fkeep.delay+clearGate,modeControl+programMode.delay});
 for(auto*s:{&opKeep,&ingress,&inputRow,&inputBits,&rowMode,&plane,&shift,&feedback,&operand,&choice,&keep,&xkeep,&programMode,&rkeep,&fkeep,&tkeep})area+=s->area;
 area+=groupArea+rowsel.area+inputCapture.area+(N*B+X+43+K)*(nh*nw+ih*iw);
 emit("input_hold_bits",K*8);emit("ADC_raw_hold_bits",2*P*A);emit("ADC_difference_hold_bits",P*(A+1));emit("ADC_difference_bits",A+1);emit("ADC_difference_lanes",P);emit("ADC_difference_s",difference.readLatency);emit("ADC_capture_s",raw.readLatency);emit("difference_capture_s",diff.readLatency);
 emit("target_hold_bits",L*8);emit("refresh_code_hold_bits",P);emit("result_hold_bits",N*B);emit("Xsum_hold_bits",X);emit("input_ingress_beats",beats);emit("input_ingress_select_s",inputCapture.readLatency+ingress.delay);emit("input_capture_s",in.readLatency);
 emit("Xsum_select_s",inputRow.delay);emit("Xsum_add_s",xadd.readLatency);emit("Xsum_comb_s",xsumPath);emit("Xsum_capture_s",xsum.readLatency);emit("Xsum_cycles",K);
 emit("ADC_plane_select_s",plane.delay);emit("ADC_shift_select_s",shift.delay);emit("ADC_shift_index_add_s",shiftIndex.readLatency);emit("ADC_sign_extension_max_fanout",signFanout);emit("Xsum_broadcast_s",xsumBroadcast);emit("add_sub_sign_logic_s",signSelect);emit("MAC_lanes",L);emit("MAC_comb_s",arithmetic);emit("MAC_capture_s",result.readLatency);emit("final_Xsum_correction_comb_s",correction);
 emit("input_row_mask_s",rwl);emit("input_row_mask_gates",K*2);emit("input_bit_select_s",inputBits.delay);emit("output_group_select_s",groupDelay);emit("program_resident_refresh_select_s",modeControl+programMode.delay);emit("refresh_capture_s",refresh.readLatency);emit("target_capture_s",target.readLatency);
 emit("stream_clear_comb_s",streamClear);emit("resident_progress_clear_comb_s",residentClear);emit("refresh_local_clear_comb_s",refreshClear);emit("operation_completion_carry_tap",(int)std::ceil(std::log2((K/16)*G*64)));emit("operation_index_bits",10);emit("operation_done_bits",1);emit("operation_increment_s",opIncrement.readLatency+opKeep.delay+clearGate);emit("operation_state_capture_s",operation.readLatency);emit("clear_stream_bits",N*B+X+11);emit("clear_resident_bits",8);emit("clear_refresh_bits",24);
 emit("resident_progress_bits",8);emit("refresh_progress_bits",8);emit("refresh_deadline_bits",16);emit("resident_progress_increment_s",rinc.readLatency+rkeep.delay+clearGate);emit("refresh_progress_increment_s",finc.readLatency+fkeep.delay+clearGate);emit("deadline_tick_comb_s",tick.readLatency+tkeep.delay+clearGate);emit("deadline_guard_comb_s",guardPath);emit("maintenance_state_capture_s",timer.readLatency);
 emit("native_digital_area_m2",area);emit("digital_critical_comb_s",critical);emit("digital_halfcycle_min_period_s",2*critical);emit("digital_clock_budget_satisfied",1/request::clock_Hz>=2*critical);emit("component_only",1);return 0;
}

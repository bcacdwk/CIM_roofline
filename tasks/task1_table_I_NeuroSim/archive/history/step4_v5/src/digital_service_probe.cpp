// Shared P2+ digital operator bank, ported from the reviewed P1 gate/hold graph.
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
 Param settings;settings.processNode=request::technology_nm;param=&settings;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;
 Technology tech;tech.Initialize(ip.processNode,LSTP);MemCell cell{};
 const int K=request::logical_K,N=request::logical_N,L=request::mac_lanes,B=request::accumulator_bits;
 const int outputGroups=N/L,heldRows=request::weight_hold_rows,heldOutputs=request::weight_hold_outputs,heldGroups=heldOutputs/L;
 const int heldBits=heldRows*heldOutputs*8;
 DFF input(ip,tech,cell),rowInput(ip,tech,cell),weight(ip,tech,cell),target(ip,tech,cell),result(ip,tech,cell),status(ip,tech,cell),retry(ip,tech,cell);
 input.Initialize(K*8,request::clock_Hz);rowInput.Initialize(8,request::clock_Hz);weight.Initialize(heldBits,request::clock_Hz);
 target.Initialize(N*8,request::clock_Hz);result.Initialize(N*B,request::clock_Hz);status.Initialize(1,request::clock_Hz);retry.Initialize(2,request::clock_Hz);
 for(auto*d:{&input,&rowInput,&weight,&target,&result,&status,&retry}){d->CalculateArea(0,0,NONE);d->CalculateLatency(1e20,1);}
 Adder add(ip,tech,cell),counter(ip,tech,cell);Subtractor sub(ip,tech,cell),compare(ip,tech,cell);
 add.Initialize(B,L);sub.Initialize(B,L);compare.Initialize(8,L);counter.Initialize(2,1);
 add.CalculateArea(0,0,NONE);sub.CalculateArea(0,0,NONE);compare.CalculateArea(0,0,NONE);counter.CalculateArea(0,0,NONE);
 double wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn;
 double hn,wna,cn,cno,hi,wi,ci,cio,hno,wno,cnoin,cnoout;
 CalculateGateArea(NAND,2,2*wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hn,&wna);
 CalculateGateCapacitance(NAND,2,2*wn,wp,hn,tech,&cn,&cno);
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hi,&wi);
 CalculateGateCapacitance(INV,1,wn,wp,hi,tech,&ci,&cio);
 CalculateGateArea(NOR,2,wn,wp*2,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hno,&wno);
 CalculateGateCapacitance(NOR,2,wn,wp*2,hno,tech,&cnoin,&cnoout);
 auto andDelay=[&](double load){return horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,tech)*(cno+ci),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+load),0,1e20,nullptr);};
 auto orDelay=[&](double load){return horowitz(2*CalculateOnResistance(2*wp,PMOS,ip.temperature,tech)*(cnoout+ci),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+load),0,1e20,nullptr);};
 auto drive=[&](double load){double scale=std::max(1.,std::ceil(std::sqrt(load/ci))),h,w,c,o;
   CalculateGateArea(INV,1,wn*scale,wp*scale,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&h,&w);
   CalculateGateCapacitance(INV,1,wn*scale,wp*scale,h,tech,&c,&o);
   return std::pair<double,double>{horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+c),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn*scale,NMOS,ip.temperature,tech)*(o+load),0,1e20,nullptr),hi*wi+h*w};};
 double maskDelay=andDelay(add.capNandInput+sub.capNandInput),clearGate=andDelay(result.capTgDrain);
 Select inputIngress(ip,tech,cell),targetIngress(ip,tech,cell),weightIngress(ip,tech,cell),inputRow(ip,tech,cell),inputBit(ip,tech,cell);
 Select weightGroups(ip,tech,cell),weightRows(ip,tech,cell),shift(ip,tech,cell),feedback(ip,tech,cell),resultChoice(ip,tech,cell),resultKeep(ip,tech,cell),targetRead(ip,tech,cell),programMask(ip,tech,cell);
 inputIngress.init(K*8,2,input.capTgDrain,false);targetIngress.init(N*8,2,target.capTgDrain,false);weightIngress.init(heldBits,2,weight.capTgDrain,false);
 inputRow.init(8,K,rowInput.capTgDrain);inputBit.init(1,8,cn*B*L);
 shift.init(B*L,8,cn);feedback.init(B*L,outputGroups,add.capNandInput+sub.capNandInput,false);
 resultKeep.init(N*B,2,cn,false);resultChoice.init(B*L,2,resultKeep.cin*outputGroups,false);
 shift.decode.CalculateLatency(1e20,(shift.mux.capTgGateN+resultChoice.mux.capTgGateN)*B*L,(shift.mux.capTgGateP+resultChoice.mux.capTgGateP)*B*L,1,1);shift.delay=shift.mux.readLatency+shift.decode.readLatency;
 add.CalculateLatency(1e20,resultChoice.cin,1);sub.CalculateLatency(1e20,resultChoice.cin,1);
 // Explicit fanout of sign extension through all eight shift choices, bounded by the MSB.
 int signFanout=0;for(int bit=0;bit<8;bit++)signFanout+=std::max(0,B-7-bit);
 weightRows.init(8*L,heldRows,shift.cin*signFanout+request::operand_route_cap_F);
 weightGroups.init(8*L*heldRows,heldGroups,weightRows.present?weightRows.cin:shift.cin*signFanout+request::operand_route_cap_F);
 targetRead.init(8*L,outputGroups,compare.capNandInput,false);
 programMask.init(request::program_lanes,(N*8)/request::program_lanes,cnoin+request::program_control_cap_F);
 compare.CalculateLatency(1e20,cnoin,1);counter.CalculateLatency(1e20,cn,1);
 int failBits=9*L,failDepth=(int)std::ceil(std::log2(failBits));double failReduce=failDepth*orDelay(cnoin),sticky=orDelay(cn)+andDelay(status.capTgDrain);
 int clearBits=N*B+3;auto clearDrive=drive(clearBits*cn);double clearComb=clearDrive.first+clearGate;
 // Separate capture-address decoders ensure unselected words retain their previous bits.
 double captureDecoderArea=0;
 auto captureAddress=[&](int bits,int portBits,Select&keep,const char*prefix){int groups=(bits+portBits-1)/portBits;double latency=0,area=0;
  if(groups>1){RowDecoder decode(ip,tech,cell);decode.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(groups)),true);decode.CalculateArea(0,0,NONE);decode.CalculateLatency(1e20,keep.mux.capTgGateN*portBits,keep.mux.capTgGateP*portBits,1,1);latency=decode.readLatency;area=decode.area;}
  std::string name=prefix;emit((name+"_beats").c_str(),groups);emit((name+"_select_s").c_str(),latency+keep.mux.readLatency);emit((name+"_area_m2").c_str(),area+keep.mux.area);captureDecoderArea+=area;return latency+keep.mux.readLatency;};
 double inputPort=captureAddress(K*8,request::input_port_bits,inputIngress,"input_ingress");
 double targetPort=captureAddress(N*8,request::resident_port_bits,targetIngress,"target_ingress");
 double weightPort=captureAddress(heldBits,request::weight_capture_bits,weightIngress,"weight_ingress");
 // Group decoder for output-bank feedback/hold is physical and distinct from the array decoder.
 double groupDelay=0,groupArea=0;
 if(outputGroups>1){RowDecoder group(ip,tech,cell);group.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(outputGroups)),true);group.CalculateArea(0,0,NONE);
  group.CalculateLatency(1e20,(feedback.mux.capTgGateN+resultKeep.mux.capTgGateN)*B*L+targetRead.mux.capTgGateN*8*L,(feedback.mux.capTgGateP+resultKeep.mux.capTgGateP)*B*L+targetRead.mux.capTgGateP*8*L,1,1);groupDelay=group.readLatency;groupArea=group.area;}
 double inputArrival=inputBit.delay+maskDelay;
 double weightArrival=weightGroups.delay+weightRows.delay+shift.delay+maskDelay;
 double arithmetic=std::max({inputArrival,weightArrival,groupDelay+feedback.delay})+std::max(add.readLatency,sub.readLatency);
 double chosen=std::max(arithmetic,shift.decode.readLatency)+resultChoice.delay;
 double mac=std::max(chosen,groupDelay)+resultKeep.mux.readLatency+clearGate;
 double verify=std::max(groupDelay+targetRead.delay,weightGroups.delay+weightRows.delay)+compare.readLatency+failReduce+sticky;
 double critical=std::max({mac,verify,inputPort,targetPort,weightPort,inputRow.delay,clearComb,counter.readLatency+clearGate,programMask.delay+orDelay(request::program_control_cap_F)});
 double area=input.area+rowInput.area+weight.area+target.area+result.area+status.area+retry.area+add.area+sub.area+compare.area+counter.area+groupArea+captureDecoderArea;
 for(auto*s:{&inputIngress,&targetIngress,&weightIngress,&inputRow,&inputBit,&weightGroups,&weightRows,&shift,&feedback,&resultChoice,&resultKeep,&targetRead,&programMask})area+=s->area;
 area+=(B*L+clearBits)*(hn*wna+hi*wi)+(failBits-1)*(hno*wno+hi*wi)+hno*wno+hi*wi+clearDrive.second;
 emit("input_rows",K);emit("input_cols",N*8);emit("logical_K",K);emit("logical_N",N);emit("accumulator_bits",B);emit("extra_25bit_adder_lanes",L);
 emit("input_hold_bits",input.numDff);emit("target_hold_bits",target.numDff);emit("weight_hold_bits",weight.numDff);emit("weight_hold_rows",heldRows);emit("weight_hold_outputs",heldOutputs);emit("signed_output_hold_bits",result.numDff);
 emit("input_capture_s",input.readLatency);emit("target_hold_capture_s",target.readLatency);emit("weight_hold_capture_s",weight.readLatency);emit("signed_capture_s",result.readLatency);emit("input_row_capture_s",rowInput.readLatency);
 emit("input_row_select_s",inputRow.delay);emit("input_bit_select_s",inputBit.delay);emit("weight_group_select_s",weightGroups.delay);emit("weight_row_select_s",weightRows.delay);emit("weight_keep_s",weightIngress.mux.readLatency);
 emit("extra_shifted_weight_mux_s",shift.mux.readLatency);emit("extra_shift_select_s",shift.decode.readLatency);emit("group_select_s",groupDelay);emit("data_zero_mask_s",maskDelay);emit("extra_accumulator_feedback_mux_s",feedback.delay);
 emit("extra_25bit_adder_s",add.readLatency);emit("signed_correction_s",sub.readLatency);emit("add_sub_result_select_s",resultChoice.delay);emit("accumulator_keep_s",resultKeep.mux.readLatency+clearGate);
 emit("verify_target_select_s",groupDelay+targetRead.delay);emit("verify_data_select_s",weightGroups.delay+weightRows.delay);emit("verify_byte_compare_s",compare.readLatency);emit("verify_fail_reduce_s",failReduce);emit("verify_sticky_or_s",sticky);emit("verify_status_capture_s",status.readLatency);
 emit("program_target_select_s",programMask.delay);emit("program_target_mask_logic_s",orDelay(request::program_control_cap_F));emit("retry_increment_s",counter.readLatency+clearGate);emit("retry_state_capture_s",retry.readLatency);
 emit("state_clear_bits",clearBits);emit("state_clear_s",clearComb+result.readLatency);emit("state_clear_comb_s",clearComb);emit("state_clear_gates",clearBits*2+2);
 emit("data_zero_mask_gates",B*L*2);emit("weight_sign_extension_max_fanout",signFanout);emit("digital_mac_comb_s",mac);emit("digital_verify_comb_s",verify);
 emit("digital_critical_comb_s",critical);emit("digital_halfcycle_min_period_s",2*critical);emit("digital_clock_budget_satisfied",1/request::clock_Hz>=2*critical);
 emit("native_digital_area_m2",area);emit("native_vdd_V",tech.vdd);emit("native_vth_V",tech.vth);emit("component_only",1);return 0;
}

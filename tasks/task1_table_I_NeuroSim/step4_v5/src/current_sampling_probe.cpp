// Current-integration and explicit ADC input/sampling-load interface. No GC cell state model.
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include "constant.h"
#include "formula.h"
#include "SarADC.h"
#include "Mux.h"
#include "DFF.h"
#include "SwitchMatrix.h"
#include "Param.h"
#include "request.h"
Param *param;
static void out(const char*k,double x){if(!std::isfinite(x)){std::cerr<<"V5_INVALID "<<k;std::exit(2);}std::cout<<k<<"="<<std::setprecision(17)<<x<<"\n";}
int main(){
 Param p;param=&p;p.technode=request::technology_nm;p.temp=request::temperature_K;p.readVoltage=request::precharge_voltage_V;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
 Technology t;t.Initialize(ip.processNode,LSTP,conventional);MemCell c{};c.accessType=CMOS_access;c.readVoltage=request::rwl_voltage_V;c.writeVoltage=0;
 SarADC adc(ip,t,c);adc.Initialize(request::adc_lanes,1<<request::adc_bits,request::clock_Hz,request::adc_lanes);adc.CalculateUnitArea();adc.CalculateArea(0,request::array_width_m,NONE);adc.CalculateLatency(1);
 Mux isolate(ip,t,c),sample(ip,t,c);isolate.Initialize(request::adc_lanes,1,request::array_isolation_target_ohm,false);sample.Initialize(request::adc_lanes,1,request::sample_switch_target_ohm,false);
 isolate.CalculateArea(0,0,NONE);sample.CalculateArea(0,0,NONE);
 double preWidth=request::precharge_width_F*t.featureSize,resetWidth=request::adc_reset_width_F*t.featureSize;
 double preDrain=CalculateDrainCap(preWidth,PMOS,MAX_TRANSISTOR_HEIGHT*t.featureSize,t);
 double resetDrain=CalculateDrainCap(resetWidth,NMOS,MAX_TRANSISTOR_HEIGHT*t.featureSize,t);
 double ci=request::integration_cap_F+request::node_parasitic_cap_F+isolate.capTgDrain+sample.capTgDrain+preDrain;
 double ca=request::adc_input_cap_F+sample.capTgDrain+resetDrain;
 double current=request::active_rows*request::cell_current_A;
 double vi=request::precharge_voltage_V-current*request::integration_time_s/ci;
 double sampled=(ci*vi+ca*request::adc_initial_voltage_V)/(ci+ca);
 // Native TG widths plus a declared low-field overdrive correction. It is a compact
 // port validity envelope, not BSIM. Both branches may lose headroom near midrail.
 auto effectiveR=[&](const Mux&m,double voltage){
  double gn=0,gp=0,normal=t.vdd-t.vth;
  double nhead=t.vdd-voltage-t.vth,phead=voltage-t.vth;
  if(nhead>0)gn=nhead/(normal*CalculateOnResistance(m.widthTgN,NMOS,ip.temperature,t));
  if(phead>0)gp=phead/(normal*CalculateOnResistance(m.widthTgP,PMOS,ip.temperature,t));
  return gn+gp>0?1/(gn+gp):1e30;
 };
 double isolR=0,sampleR=0;
 for(int i=0;i<=100;i++){
  double v=vi+(request::precharge_voltage_V-vi)*i/100.;isolR=std::max(isolR,effectiveR(isolate,v));
  double vs=std::min(sampled,vi)+(std::max(sampled,vi)-std::min(sampled,vi))*i/100.;sampleR=std::max(sampleR,effectiveR(sample,vs));
 }
 // Read-mask selection has real native DFFs and row TGs; expose edge separately
 // from the included half-cycle capture, so capture wait is never integrated as I*t.
 SwitchMatrix rwl(ip,t,c);rwl.Initialize(ROW_MODE,request::physical_rows,request::rwl_target_ohm,true,false,1,1,request::adc_lanes,request::adc_lanes,1,request::clock_Hz);
 rwl.CalculateArea(0,0,NONE);rwl.CalculateLatency(1e20,request::rwl_load_F,request::rwl_wire_ohm,1,1);
 double preHead=request::precharge_voltage_V-t.vth;
 double preR=preHead>0?CalculateOnResistance(preWidth,PMOS,ip.temperature,t)*(t.vdd-t.vth)/preHead:1e30;
 double preTime=-std::log(request::precharge_error_fraction)*preR*(ci+request::write_qualified_cap_F);
 double resetR=CalculateOnResistance(resetWidth,NMOS,ip.temperature,t);
 double resetTime=-std::log(request::sampling_error_fraction)*resetR*ca;
 auto control=[&](double gates){double w=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*w,h,wg,cin,cout;
  CalculateGateArea(INV,1,w,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h,&wg);CalculateGateCapacitance(INV,1,w,wp,h,t,&cin,&cout);
  double scale=std::max(1.,std::ceil(std::sqrt(gates/cin))),h2,w2,ci2,co2;CalculateGateArea(INV,1,w*scale,wp*scale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h2,&w2);CalculateGateCapacitance(INV,1,w*scale,wp*scale,h2,t,&ci2,&co2);
  double latency=horowitz(CalculateOnResistance(w,NMOS,ip.temperature,t)*(cout+ci2),0,1e20,nullptr)+horowitz(CalculateOnResistance(w*scale,NMOS,ip.temperature,t)*(co2+gates),0,1e20,nullptr);
  return std::pair<double,double>{latency,h*wg+h2*w2};};
 auto icontrol=control(request::adc_lanes*(isolate.capTgGateN+isolate.capTgGateP));auto scontrol=control(request::adc_lanes*(sample.capTgGateN+sample.capTgGateP));
 auto pcontrol=control(request::adc_lanes*CalculateGateCap(preWidth,t));auto rcontrol=control(request::adc_lanes*CalculateGateCap(resetWidth,t));
 double hp,wp0,hr,wr;CalculateGateArea(INV,1,0,preWidth,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hp,&wp0);CalculateGateArea(INV,1,resetWidth,0,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hr,&wr);
 double cellMin=vi-current*isolR;
 double settle=-std::log(request::sampling_error_fraction)*sampleR*ci*ca/(ci+ca);
 double writeLoad=request::write_intrinsic_cap_F+isolate.capTgDrain;
 DFF hold(ip,t,c);hold.Initialize(request::adc_bits*request::adc_lanes,request::clock_Hz);hold.CalculateArea(0,0,NONE);hold.CalculateLatency(1e20,1);
 out("native_vdd_V",t.vdd);out("native_vth_V",t.vth);out("adc_bits",request::adc_bits);out("adc_lanes",request::adc_lanes);
 out("native_ADC_s",adc.readLatency);out("native_ADC_area_m2",adc.area);out("native_ADC_Cin_provided",0);
 out("explicit_ADC_input_cap_F",request::adc_input_cap_F);out("integration_node_total_cap_F",ci);out("ADC_node_total_cap_F",ca);
 out("array_isolation_drain_F",isolate.capTgDrain);out("sampling_switch_drain_F",sample.capTgDrain);
 out("array_isolation_effective_R_bound_ohm",isolR);out("sampling_switch_effective_R_bound_ohm",sampleR);
 out("integrated_current_A",current);out("integration_node_final_V",vi);out("cell_BL_min_bound_V",cellMin);out("sampled_ADC_voltage_V",sampled);
 out("sampling_charge_sharing_factor",ci/(ci+ca));out("sampling_settle_s",settle);
 out("input_current_domain_valid",cellMin>=request::current_valid_min_V&&request::precharge_voltage_V<=request::current_valid_max_V);
 out("ADC_voltage_domain_valid",sampled>=0&&sampled<=t.vdd);
 out("write_connected_load_F",writeLoad);out("write_load_match_cap_F",request::write_qualified_cap_F-writeLoad);out("write_load_qualification_feasible",writeLoad<=request::write_qualified_cap_F);
 out("isolation_area_m2",isolate.area);out("sample_switch_area_m2",sample.area);out("ADC_result_hold_bits",hold.numDff);out("ADC_result_capture_s",hold.readLatency);out("ADC_result_hold_area_m2",hold.area);
 out("RWL_update_s",rwl.readLatency);out("RWL_included_capture_s",rwl.dff.readLatency);out("RWL_edge_s",rwl.readLatency-rwl.dff.readLatency);
 out("RWL_load_F",request::rwl_load_F);out("RWL_native_area_m2",rwl.area);out("RWL_native_voltage_compatible",request::rwl_voltage_V<=t.vdd&&request::rwl_voltage_V>0);
 out("precharge_PMOS_R_ohm",preR);out("precharge_added_drain_F",preDrain);out("precharge_RC_s",preTime);out("precharge_control_s",pcontrol.first);out("precharge_bias_feasible",preHead>0&&request::precharge_voltage_V<=t.vdd);
 out("ADC_external_reset_s",resetTime+rcontrol.first);out("ADC_external_reset_drain_F",resetDrain);out("ADC_external_reset_area_m2",request::adc_lanes*hr*wr+rcontrol.second);
 out("array_isolation_control_s",icontrol.first);out("sample_switch_control_s",scontrol.first);
 out("sampling_and_isolation_control_area_m2",icontrol.second+scontrol.second);out("precharge_area_m2",request::adc_lanes*hp*wp0+pcontrol.second);
 out("component_only",1);return 0;
}

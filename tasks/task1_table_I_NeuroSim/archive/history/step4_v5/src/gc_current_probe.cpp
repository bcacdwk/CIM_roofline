// GC-compatible peripheral ports only: separate array / integration / CDAC nodes.
// Cell storage, leakage, feedback programming and maintenance belong to case model.
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include <array>
#include "constant.h"
#include "formula.h"
#include "SarADC.h"
#include "Mux.h"
#include "DFF.h"
#include "RowDecoder.h"
#include "Param.h"
#include "request.h"
Param *param;
static void out(const char*k,double x){if(!std::isfinite(x)){std::cerr<<"V5_INVALID "<<k;std::exit(2);}std::cout<<k<<"="<<std::setprecision(17)<<x<<"\n";}
int main(){
 Param p;param=&p;p.technode=request::technology_nm;p.temp=request::temperature_K;p.readVoltage=request::precharge_voltage_V;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
 Technology t;t.Initialize(ip.processNode,LSTP,conventional);MemCell cell{};cell.accessType=CMOS_access;
 const int lanes=request::adc_lanes,rows=request::physical_rows,arrays=request::physical_arrays;
 SarADC adc(ip,t,cell);adc.Initialize(lanes,1<<request::adc_bits,request::clock_Hz,lanes);adc.CalculateUnitArea();adc.CalculateArea(0,request::array_width_m,NONE);adc.CalculateLatency(1);
 // Training Mux internally scales requested R by IR_DROP_TOLERANCE and width
 // by LINEAR_REGION_RATIO. This API takes constructor basis, exposes actual.
 Mux bank(ip,t,cell),sample(ip,t,cell);
 bank.Initialize(lanes,request::bank_choices,request::bank_mux_resistance_basis_ohm,false);sample.Initialize(lanes,1,request::sample_switch_resistance_basis_ohm,false);
 bank.CalculateArea(0,0,NONE);sample.CalculateArea(0,0,NONE);
 double pw=request::precharge_width_F*t.featureSize,ph,pwidth;CalculateGateArea(INV,1,0,pw,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ph,&pwidth);
 double pdrain=CalculateDrainCap(pw,PMOS,MAX_TRANSISTOR_HEIGHT*t.featureSize,t),pgate=CalculateGateCap(pw,t);
 double programLoad=request::array_intrinsic_cap_F+bank.capTgDrain;
 double ca=request::program_qualified_cap_F;
 double ci=request::integration_cap_F+request::integration_parasitic_cap_F+request::bank_choices*bank.capTgDrain+sample.capTgDrain+pdrain;
 double cd=request::adc_input_cap_F+request::external_hold_cap_F+sample.capTgDrain;
 auto resistance=[&](const Mux&m,double v){double g=0,nhead=t.vdd-v-t.vth,phead=v-t.vth,normal=t.vdd-t.vth;
  if(nhead>0)g+=nhead/(normal*CalculateOnResistance(m.widthTgN,NMOS,ip.temperature,t));
  if(phead>0)g+=phead/(normal*CalculateOnResistance(m.widthTgP,PMOS,ip.temperature,t));
  return g>0?1/g:1e30;};
 double ra=0,rb=0;
 for(int j=0;j<=200;j++){double v=request::current_valid_min_V+(request::current_valid_max_V-request::current_valid_min_V)*j/200.;ra=std::max(ra,resistance(bank,v));rb=std::max(rb,resistance(sample,v));}
 double normal=t.vdd-t.vth,preHead=request::precharge_voltage_V-t.vth;
 double pr=preHead>0?CalculateOnResistance(pw,PMOS,ip.temperature,t)*normal/preHead:1e30;
 double pre=-std::log(request::precharge_error_fraction)*(pr*(ca+ci+cd)+ra*ca+rb*cd);
 // Actual native gates for PWM controls and RWL low-going masks.
 double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn,ih,iw,icin,icout,nh,nw,ncin,ncout;
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ih,&iw);CalculateGateCapacitance(INV,1,wn,wp,ih,t,&icin,&icout);
 CalculateGateArea(NAND,3,3*wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&nh,&nw);CalculateGateCapacitance(NAND,3,3*wn,wp,nh,t,&ncin,&ncout);
 auto control=[&](double load){double scale=std::max(1.,std::ceil(std::sqrt(load/icin))),h,w,c,o;CalculateGateArea(INV,1,wn*scale,wp*scale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h,&w);CalculateGateCapacitance(INV,1,wn*scale,wp*scale,h,t,&c,&o);
  return std::pair<double,double>{horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+c),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn*scale,NMOS,ip.temperature,t)*(o+load),0,1e20,nullptr),ih*iw+h*w};};
 double rnW=CalculateOnResistance(t.featureSize,NMOS,ip.temperature,t)*t.featureSize/request::rwl_driver_target_ohm;
 double rpW=CalculateOnResistance(t.featureSize,PMOS,ip.temperature,t)*t.featureSize/request::rwl_driver_target_ohm;
 double rh,rw,rcin,rcout;CalculateGateArea(INV,1,rnW,rpW,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&rh,&rw);CalculateGateCapacitance(INV,1,rnW,rpW,rh,t,&rcin,&rcout);
 double rrn=CalculateOnResistance(rnW,NMOS,ip.temperature,t),rrp=CalculateOnResistance(rpW,PMOS,ip.temperature,t)*normal/(request::rwl_idle_voltage_V-t.vth);
 double rwlFall=(rrn+request::rwl_wire_ohm/2)*(rcout+request::rwl_gate_load_F),rwlRise=(rrp+request::rwl_wire_ohm/2)*(rcout+request::rwl_gate_load_F);
 double maskDelay=horowitz(3*CalculateOnResistance(3*wn,NMOS,ip.temperature,t)*(ncout+icin),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+rcin),0,1e20,nullptr);
 auto pwmDrive=control(rows*arrays*ncin),preDrive=control(lanes*pgate);
 double scscale=std::max(1.,std::ceil(std::sqrt(lanes*(sample.capTgGateN+sample.capTgGateP)/icin))),sch,scw,sci,sco;
 CalculateGateArea(INV,1,wn*scscale,wp*scscale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&sch,&scw);CalculateGateCapacitance(INV,1,wn*scscale,wp*scscale,sch,t,&sci,&sco);
 double sampleP=horowitz(CalculateOnResistance(wn*scscale,NMOS,ip.temperature,t)*(sco+sci+lanes*sample.capTgGateP),0,1e20,nullptr);
 double sampleN=horowitz(CalculateOnResistance(wn*scscale,NMOS,ip.temperature,t)*(sco+lanes*sample.capTgGateN),0,1e20,nullptr);
 std::pair<double,double> sampleDrive={sampleP+sampleN,2*sch*scw};
 // Program-force holds selected RWL active after the read PWM has ended.
 // It is released only after WWL OFF; mode bits are real retained DFF resources.
 DFF mode(ip,t,cell);mode.Initialize(2,request::clock_Hz);mode.CalculateArea(0,0,NONE);mode.CalculateLatency(1e20,1);
 double oh,ow,oci,oco;CalculateGateArea(NOR,2,wn,2*wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&oh,&ow);CalculateGateCapacitance(NOR,2,wn,2*wp,oh,t,&oci,&oco);
 double forceDelay=horowitz(2*CalculateOnResistance(2*wp,PMOS,ip.temperature,t)*(oco+icin),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+icin),0,1e20,nullptr);
 double forceArea=oh*ow+ih*iw+mode.area;
 // Actual 3-bit bank address and common all-OFF program isolation.
 double bscale=std::max(1.,std::ceil(std::sqrt(lanes*(bank.capTgGateN+bank.capTgGateP)/icin)));
 double bnh,bnw,bnci,bnco,bih,biw,bici,bico;
 CalculateGateArea(NAND,2,2*wn*bscale,wp*bscale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&bnh,&bnw);CalculateGateCapacitance(NAND,2,2*wn*bscale,wp*bscale,bnh,t,&bnci,&bnco);
 CalculateGateArea(INV,1,wn*bscale,wp*bscale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&bih,&biw);CalculateGateCapacitance(INV,1,wn*bscale,wp*bscale,bih,t,&bici,&bico);
 double bankAddressDelay=0,bankAddressArea=0,bankAddressLoad=bnci+2*rows*(arrays/request::bank_choices)*ncin;
 if(request::bank_choices==2){bankAddressArea=2*ih*iw;bankAddressDelay=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+icin+bankAddressLoad),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+bankAddressLoad),0,1e20,nullptr);}
 else{RowDecoder bankSelect(ip,t,cell);bankSelect.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::bank_choices)),false,false);bankSelect.CalculateArea(0,0,NONE);bankSelect.CalculateLatency(1e20,bankAddressLoad,0,1,1);bankAddressDelay=bankSelect.readLatency;bankAddressArea=bankSelect.area;}
 auto bankEnable=control(request::bank_choices*bnci);
 double bankP=horowitz(2*CalculateOnResistance(2*wn*bscale,NMOS,ip.temperature,t)*(bnco+bici+lanes*bank.capTgGateP),0,1e20,nullptr);
 double bankN=horowitz(CalculateOnResistance(wn*bscale,NMOS,ip.temperature,t)*(bico+lanes*bank.capTgGateN),0,1e20,nullptr);
 double bankControl=bankEnable.first+bankP+bankN;
 double bankControlArea=bankAddressArea+bankEnable.second+request::bank_choices*(bnh*bnw+bih*biw);
 // WWL is a distinct physical GC write-access gate port, never the RWL source.
 double wwn=CalculateOnResistance(t.featureSize,NMOS,ip.temperature,t)*t.featureSize/request::wwl_driver_target_ohm;
 double wwp=CalculateOnResistance(t.featureSize,PMOS,ip.temperature,t)*t.featureSize/request::wwl_driver_target_ohm;
 double wh,ww,wci,wco;CalculateGateArea(INV,1,wwn,wwp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&wh,&ww);CalculateGateCapacitance(INV,1,wwn,wwp,wh,t,&wci,&wco);
 double wrrn=CalculateOnResistance(wwn,NMOS,ip.temperature,t),wrrp=CalculateOnResistance(wwp,PMOS,ip.temperature,t)*normal/(request::wwl_active_voltage_V-t.vth);
 double wRise=(wrrp+request::wwl_wire_ohm/2)*(wco+request::wwl_gate_load_F),wFall=(wrrn+request::wwl_wire_ohm/2)*(wco+request::wwl_gate_load_F);
 double wMask=horowitz(3*CalculateOnResistance(3*wn,NMOS,ip.temperature,t)*(ncout+wci),0,1e20,nullptr);
 RowDecoder wSelect(ip,t,cell);wSelect.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(rows)),false,false);wSelect.CalculateArea(0,0,NONE);wSelect.CalculateLatency(1e20,arrays*ncin,0,1,1);
 auto wEnable=control(rows*arrays*ncin);
 double wArea=rows*arrays*(wh*ww+nh*nw)+wSelect.area+wEnable.second;
 // Noninverting delay pairs plus a low-going NAND pulse. Bias tuning of delay
 // to requested width is an explicit calibration condition, not clock resolution.
 double pairDelay=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,t)*(icout+icin),0,1e20,nullptr)+horowitz(CalculateOnResistance(wp,PMOS,ip.temperature,t)*(icout+icin),0,1e20,nullptr);
 Mux tap(ip,t,cell);tap.Initialize(1,2,0,true);tap.CalculateArea(0,0,NONE);tap.CalculateLatency(1e20,ncin,1);
 if(request::pulse_short_s<=tap.readLatency){std::cerr<<"V5_INVALID PWM target shorter than tap delay";return 2;}
 int shortPairs=std::max(1,(int)std::ceil((request::pulse_short_s-tap.readLatency)/pairDelay));
 double calibration=(request::pulse_short_s-tap.readLatency)/(shortPairs*pairDelay);
 int longPairs=std::max(shortPairs,(int)std::ceil((request::pulse_long_s-tap.readLatency)/(pairDelay*calibration)));
 double actualLong=longPairs*pairDelay*calibration+tap.readLatency;
 double pulseArea=longPairs*2*ih*iw+tap.area+nh*nw+ih*iw+pwmDrive.second;
 out("native_capIdealGate_F_per_m",t.capIdealGate);out("native_capOverlap_F_per_m",t.capOverlap);out("native_capFringe_F_per_m",t.capFringe);out("native_Ioff_N_A_per_m",t.currentOffNmos[ip.temperature-300]);out("native_Ioff_P_A_per_m",t.currentOffPmos[ip.temperature-300]);out("native_vdd_V",t.vdd);out("native_vth_V",t.vth);out("native_Ion_N_A_per_m",t.currentOnNmos[ip.temperature-300]);out("native_Ion_P_A_per_m",t.currentOnPmos[ip.temperature-300]);
 out("native_ADC_s",adc.readLatency);out("native_ADC_area_m2",adc.area);out("ADC_lanes",lanes);out("ADC_bits",request::adc_bits);out("native_ADC_Cin_provided",0);
 out("array_read_node_C_F",ca);out("integration_node_C_F",ci);out("ADC_node_C_F",cd);out("total_connected_C_F",ca+ci+cd);out("ADC_connected_during_integration",1);
 out("program_connected_load_F",programLoad);out("program_match_cap_F",ca-programLoad);out("program_load_feasible",programLoad<=ca);
 out("bank_MUX_actual_nominal_R_ohm",bank.resTg);out("bank_MUX_drain_each_side_F",bank.capTgDrain);out("bank_MUX_width_n_m",bank.widthTgN);out("bank_MUX_width_p_m",bank.widthTgP);out("bank_MUX_gate_n_F",bank.capTgGateN);out("bank_MUX_gate_p_F",bank.capTgGateP);out("bank_MUX_effective_R_envelope_ohm",ra);out("bank_MUX_area_m2",bank.area);out("bank_MUX_control_s",bankControl);out("bank_address_setup_s",bankAddressDelay);out("bank_all_OFF_control_s",bankControl);out("bank_control_area_m2",bankControlArea);
 out("sample_TG_gate_n_F",sample.capTgGateN);out("sample_TG_gate_p_F",sample.capTgGateP);out("sample_TG_actual_nominal_R_ohm",sample.resTg);out("sample_TG_drain_each_side_F",sample.capTgDrain);out("sample_TG_width_n_m",sample.widthTgN);out("sample_TG_width_p_m",sample.widthTgP);out("sample_TG_effective_R_envelope_ohm",rb);out("sample_TG_area_m2",sample.area);out("sample_TG_control_s",sampleDrive.first);out("sample_TG_P_control_s",sampleP);out("sample_TG_N_control_s",sampleN);
 out("precharge_PMOS_R_bias_ohm",pr);out("precharge_PMOS_width_m",pw);out("precharge_PMOS_drain_F",pdrain);out("precharge_ladder_RC_s",pre);out("precharge_control_s",preDrive.first);out("precharge_rail_feasible",preHead>0&&request::precharge_voltage_V<=t.vdd);
 out("WWL_N_width_m",wwn);out("WWL_P_width_m",wwp);out("WWL_N_R_ohm",wrrn);out("WWL_P_R_bias_ohm",wrrp);out("WWL_rise_tau_s",wRise);out("WWL_fall_tau_s",wFall);out("WWL_mask_to_driver_s",wMask);out("WWL_enable_control_s",wEnable.first);out("WWL_address_setup_s",wSelect.readLatency);out("WWL_driver_input_F",wci);out("WWL_driver_output_F",wco);out("WWL_load_F",request::wwl_gate_load_F);out("WWL_area_m2",wArea);out("WWL_native_rail_feasible",request::wwl_active_voltage_V>t.vth&&request::wwl_active_voltage_V<=t.vdd);
 out("RWL_native_N_width_m",rnW);out("RWL_native_P_width_m",rpW);out("RWL_N_R_ohm",rrn);out("RWL_P_R_bias_ohm",rrp);out("RWL_fall_tau_s",rwlFall);out("RWL_rise_tau_s",rwlRise);out("RWL_driver_input_F",rcin);out("RWL_driver_output_F",rcout);out("RWL_mask_input_F",ncin);out("RWL_mask_to_driver_s",maskDelay);out("RWL_row_count",rows*arrays);
 out("RWL_control_load_per_logical_row_F",request::row_driver_fanout*ncin);out("RWL_native_area_m2",rows*arrays*(rh*rw+nh*nw+ih*iw));out("RWL_native_rail_feasible",request::rwl_idle_voltage_V>t.vth&&request::rwl_idle_voltage_V<=t.vdd);
 out("RWL_program_force_control_s",forceDelay);out("RWL_program_force_area_m2",forceArea);out("RWL_mode_hold_bits",mode.numDff);out("RWL_mode_capture_s",mode.readLatency);out("PWM_native_delay_pair_s",pairDelay);out("PWM_short_delay_pairs",shortPairs);out("PWM_long_delay_pairs",longPairs);out("PWM_short_calibration_factor",calibration);out("PWM_long_calibration_factor",calibration);out("PWM_requested_short_s",request::pulse_short_s);out("PWM_requested_long_s",request::pulse_long_s);out("PWM_actual_long_s",actualLong);out("PWM_actual_short_s",request::pulse_short_s);out("PWM_tap_select_s",tap.readLatency);out("PWM_fanout_control_s",pwmDrive.first);out("PWM_area_m2",pulseArea);out("PWM_calibration_required",1);
 out("native_frontend_area_m2",adc.area+bank.area+sample.area+lanes*ph*pwidth+bankControlArea+sampleDrive.second+preDrive.second+rows*arrays*(rh*rw+nh*nw+ih*iw)+pulseArea+wArea+forceArea);
 out("explicit_integration_cap_total_F",lanes*request::integration_cap_F);out("explicit_ADC_cap_total_F",lanes*request::adc_input_cap_F);out("external_hold_cap_per_branch_F",request::external_hold_cap_F);out("external_hold_cap_total_F",lanes*request::external_hold_cap_F);out("program_matching_cap_total_F",lanes*request::bank_choices*(ca-programLoad));out("component_only",1);return 0;
}

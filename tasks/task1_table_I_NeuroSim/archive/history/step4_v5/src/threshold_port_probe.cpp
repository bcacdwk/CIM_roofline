// P2 isolated threshold-device port probe. No RRAM SubArray or programming path.
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include "formula.h"
#include "constant.h"
#include "RowDecoder.h"
#include "Mux.h"
#include "VoltageSenseAmp.h"
#include "DFF.h"
#include "request.h"
#include "../Param.h"
Param *param;
static void out(const char*k,double v){if(!std::isfinite(v)){std::cerr<<"V5_INVALID "<<k;std::exit(2);}std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
int main(){
 Param p;p.processNode=request::technology_nm;param=&p;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;
 Technology t;t.Initialize(ip.processNode,LSTP);
 // MemCell is only a local VSA current-operator carrier. These V/I fields are never
 // used as storage-FET geometry, transient resistance, selection or write mechanism.
 MemCell c{};c.readVoltage=1;c.resMemCellOn=1/request::sense_current_high_A;c.resMemCellOff=1/request::sense_current_low_A;
 c.resistanceOn=c.resMemCellOn;c.resistanceOff=c.resMemCellOff;c.resistanceAvg=(c.resistanceOn+c.resistanceOff)/2;
 RowDecoder select(ip,t,c);select.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::rows*request::layers)),false);
 select.CalculateArea(0,0,NONE);
 // Address selection at native VDD followed by an explicit global-enable NAND
 // and a final INV powered by the chosen positive lower gate rail.
 double gw=request::gate_driver_width_F*t.featureSize,gp=gw*t.pnSizeRatio;
 double h,w,gcin,gcout,nh,nw,ncin,ncout;
 CalculateGateArea(INV,1,gw,gp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h,&w);
 CalculateGateCapacitance(INV,1,gw,gp,h,t,&gcin,&gcout);
 double minw=MIN_NMOS_SIZE*t.featureSize,minp=t.pnSizeRatio*minw;
 CalculateGateArea(NAND,2,2*minw,minp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&nh,&nw);
 CalculateGateCapacitance(NAND,2,2*minw,minp,nh,t,&ncin,&ncout);
 select.CalculateLatency(1e20,ncin,0,1,1);
 double normal=t.vdd-t.vth,head=request::selected_gate_V-t.vth;
 double gateRP=head>0?CalculateOnResistance(gp,PMOS,ip.temperature,t)*normal/head:1e30;
 double gateRN=CalculateOnResistance(gw,NMOS,ip.temperature,t);
 double gateTauRise=gateRP*(gcout+request::actual_gate_load_F);
 double gateTauFall=gateRN*(gcout+request::actual_gate_load_F);
 double nandDelay=horowitz(2*CalculateOnResistance(2*minw,NMOS,ip.temperature,t)*(ncout+gcin),0,1e20,nullptr);
 // Two INV buffer drives actual global fanout. Report its propagation separately
 // from the output exponential/ramp; case dynamics consumes the latter.
 auto control=[&](double load){double ih,iw,ci,co;CalculateGateArea(INV,1,minw,minp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ih,&iw);CalculateGateCapacitance(INV,1,minw,minp,ih,t,&ci,&co);
  double scale=std::max(1.,std::ceil(std::sqrt(load/ci))),h2,w2,ci2,co2;
  CalculateGateArea(INV,1,minw*scale,minp*scale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h2,&w2);CalculateGateCapacitance(INV,1,minw*scale,minp*scale,h2,t,&ci2,&co2);
  double dt=horowitz(CalculateOnResistance(minw,NMOS,ip.temperature,t)*(co+ci2),0,1e20,nullptr)+horowitz(CalculateOnResistance(minw*scale,NMOS,ip.temperature,t)*(co2+load),0,1e20,nullptr);
  return std::pair<double,double>{dt,ih*iw+h2*w2};};
 int rows=request::rows*request::layers,lanes=request::cols/request::read_mux;
 std::pair<double,double> enControl;
 double gateArea;
 Mux mux(ip,t,c);mux.Initialize(request::cols/request::read_mux,request::read_mux,request::mux_target_ohm,false);mux.CalculateArea(0,0,NONE);mux.CalculateLatency(1e20,request::actual_BL_load_F,1);
 RowDecoder muxSelect(ip,t,c);muxSelect.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::read_mux)),true);muxSelect.CalculateArea(0,0,NONE);
 muxSelect.CalculateLatency(1e20,mux.capTgGateN*(request::cols/request::read_mux),mux.capTgGateP*(request::cols/request::read_mux),1,1);
 VoltageSenseAmp sense(ip,t,c);sense.Initialize(request::cols/request::read_mux,request::clock_Hz);sense.voltageSenseDiff=request::sense_threshold_V;
 sense.CalculateUnitArea();sense.CalculateArea(mux.widthTgShared);
 // PMOS from declared read rail to sensed node; all WL and reference TG OFF
 // while precharging. Selected data BL is reached through the read MUX.
 double preW=request::precharge_width_F*t.featureSize,ph,pw;
 CalculateGateArea(INV,1,0,preW,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&ph,&pw);
 double preD=CalculateDrainCap(preW,PMOS,MAX_TRANSISTOR_HEIGHT*t.featureSize,t);
 double preG=CalculateGateCap(preW,t),preHead=request::precharge_voltage_V-t.vth;
 double preR=preHead>0?CalculateOnResistance(preW,PMOS,ip.temperature,t)*normal/preHead:1e30;
 auto preControl=control(2*lanes*preG);
 Mux refSwitch(ip,t,c);refSwitch.Initialize(lanes,1,request::reference_switch_target_ohm,false);refSwitch.CalculateArea(0,0,NONE);
 // Complementary control: first INV output drives P gate and next INV;
 // second drives N gate. Explicit unequal propagation is passed to case ODE.
 double rch,rcw,rcci,rcco,rcscale=std::max(1.,std::ceil(std::sqrt(lanes*(refSwitch.capTgGateN+refSwitch.capTgGateP)/gcin)));
 CalculateGateArea(INV,1,minw*rcscale,minp*rcscale,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&rch,&rcw);
 CalculateGateCapacitance(INV,1,minw*rcscale,minp*rcscale,rch,t,&rcci,&rcco);
 enControl=control(rows*ncin+rcci);gateArea=rows*(h*w+nh*nw)+enControl.second;
 double rcRN=CalculateOnResistance(minw*rcscale,NMOS,ip.temperature,t),rcRP=CalculateOnResistance(minp*rcscale,PMOS,ip.temperature,t);
 double refPtau=rcRN*(rcco+rcci+lanes*refSwitch.capTgGateP),refNtau=rcRP*(rcco+lanes*refSwitch.capTgGateN);
 std::pair<double,double> refControl={.69*(refPtau+refNtau),2*rch*rcw};
 double load=request::actual_BL_load_F+mux.capTgDrain*(request::read_mux+1)+preD;
 sense.CalculateLatency(load,1);
 DFF hold(ip,t,c);hold.Initialize(request::cols,request::clock_Hz);hold.CalculateArea(0,0,NONE);hold.CalculateLatency(1e20,1);
 out("actual_gate_load_F",request::actual_gate_load_F);out("actual_BL_load_F",request::actual_BL_load_F);out("actual_SL_load_F",request::actual_SL_load_F);
 out("active_layer_count",1);out("layer_count",request::layers);out("capacity_cells",request::rows*request::cols*request::layers);
 out("native_gate_driver_compatible",head>0&&request::selected_gate_V<=t.vdd&&request::unselected_gate_V==0);
 out("actual_native_gate_rail_V",t.vdd);out("requested_gate_rail_V",request::selected_gate_V);
 out("native_select_s",select.readLatency);out("native_mux_select_s",muxSelect.readLatency);out("native_mux_s",mux.readLatency);
 out("native_sense_endpoint_diagnostic_s",sense.readLatency);out("native_sense_precharge_s",2.3*sense.resPrecharge*sense.capS1);
 out("native_sense_control_s",2/request::clock_Hz);out("native_sense_node_cap_F",load+sense.capS1+sense.capNmosDrain);
 out("native_sense_count",sense.numReadCol);out("native_hold_bits",hold.numDff);out("native_hold_s",hold.readLatency);
 out("actual_mux_target_ohm",mux.resTg);out("actual_mux_width_n_m",mux.widthTgN);out("actual_mux_width_p_m",mux.widthTgP);
 out("native_Ioff_N_A_per_m",t.currentOffNmos[ip.temperature-300]);out("native_Ioff_P_A_per_m",t.currentOffPmos[ip.temperature-300]);out("native_vth_V",t.vth);out("native_Ion_N_A_per_m",t.currentOnNmos[ip.temperature-300]);out("native_Ion_P_A_per_m",t.currentOnPmos[ip.temperature-300]);
 out("native_gate_address_s",select.readLatency);out("gate_enable_control_s",enControl.first);out("gate_enable_NAND_s",nandDelay);
 out("gate_driver_width_n_m",gw);out("gate_driver_width_p_m",gp);out("gate_driver_input_cap_F",gcin);out("gate_driver_output_cap_F",gcout);
 out("gate_driver_R_n_ohm",gateRN);out("gate_driver_R_p_bias_ohm",gateRP);out("gate_rise_tau_s",gateTauRise);out("gate_fall_tau_s",gateTauFall);out("gate_enable_area_m2",gateArea);out("gate_global_enable_load_F",rows*ncin+rcci);out("reference_first_INV_input_F",rcci);
 out("actual_mux_drain_F",mux.capTgDrain);out("actual_mux_gate_n_F",mux.capTgGateN);out("actual_mux_gate_p_F",mux.capTgGateP);
 out("precharge_PMOS_width_m",preW);out("precharge_PMOS_R_bias_ohm",preR);out("precharge_PMOS_drain_F",preD);out("precharge_PMOS_gate_F",preG);out("precharge_control_s",preControl.first);out("precharge_count",2*lanes);
 out("precharge_voltage_V",request::precharge_voltage_V);out("precharge_error_fraction",request::precharge_error_fraction);
 double sensedC=load+sense.capS1+sense.capNmosDrain;
 out("precharge_data_lumped_RC_s",-std::log(request::precharge_error_fraction)*(preR+mux.resTg)*sensedC);
 out("precharge_reference_lumped_RC_s",-std::log(request::precharge_error_fraction)*preR*sensedC);
 out("precharge_bias_compatible",preHead>0&&request::precharge_voltage_V<=t.vdd);
 out("reference_TG_width_n_m",refSwitch.widthTgN);out("reference_TG_width_p_m",refSwitch.widthTgP);out("reference_TG_nominal_R_ohm",refSwitch.resTg);
 out("reference_TG_R_n_native_ohm",CalculateOnResistance(refSwitch.widthTgN,NMOS,ip.temperature,t));out("reference_TG_R_p_native_ohm",CalculateOnResistance(refSwitch.widthTgP,PMOS,ip.temperature,t));
 out("reference_TG_drain_each_side_F",refSwitch.capTgDrain);out("reference_TG_gate_n_F",refSwitch.capTgGateN);out("reference_TG_gate_p_F",refSwitch.capTgGateP);
 out("reference_TG_P_gate_fall_tau_s",refPtau);out("reference_TG_N_gate_rise_tau_s",refNtau);out("reference_TG_N_gate_delay_s",.69*refPtau);out("reference_TG_control_s",refControl.first);out("reference_TG_count",lanes);out("reference_TG_area_m2",refSwitch.area+refControl.second);
 out("reference_capacitor_node_total_F",sensedC);out("reference_internal_initial_V",0);
 out("reference_match_cap_F",sensedC-(sense.capS1+sense.capNmosDrain+preD+refSwitch.capTgDrain));
 out("reference_match_feasible",sensedC>=(sense.capS1+sense.capNmosDrain+preD+refSwitch.capTgDrain));
 out("native_periphery_area_m2",select.area+mux.area+muxSelect.area+sense.area+hold.area+gateArea+refSwitch.area+refControl.second+2*lanes*ph*pw+preControl.second);
 out("sense_current_high_A",request::sense_current_high_A);out("sense_current_low_A",request::sense_current_low_A);
 out("probe_only",1);return 0;
}

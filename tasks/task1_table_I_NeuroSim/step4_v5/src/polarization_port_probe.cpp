// Polarization-charge/destructive-read port fixture plus native voltage sensing.
// This is neither nvCap nor an ordinary DRAM-cell substitute.
#include <iostream>
#include <iomanip>
#include <cmath>
#include "constant.h"
#include "SenseAmp.h"
#include "RowDecoder.h"
#include "DFF.h"
#include "formula.h"
#include "request.h"
#include "../Param.h"
Param *param;
static void out(const char*k,double x){if(!std::isfinite(x)){std::cerr<<"V5_INVALID "<<k;std::exit(2);}std::cout<<k<<"="<<std::setprecision(17)<<x<<"\n";}
int main(){
 Param p;p.processNode=request::technology_nm;param=&p;InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;
 Technology t;t.Initialize(ip.processNode,LSTP);MemCell c{};
 SenseAmp sa(ip,t,c);sa.Initialize(request::read_columns,false,request::sense_target_V,request::sense_pitch_m,request::clock_Hz,request::read_columns);sa.CalculateArea(0,0,NONE);sa.CalculateLatency(1);
 double accessW=request::access_width_F*t.featureSize;
 double nativeAccessC=CalculateDrainCap(accessW,NMOS,MAX_TRANSISTOR_HEIGHT*t.featureSize,t);
 double accessC=request::case_charge_ports?request::external_access_drain_F:nativeAccessC;
 double cbl=request::BL_external_cap_F+sa.capLoad+accessC;
 // Fixture Q_s(V_FE)=C_dielectric*V_FE + switched polarization charge (0 or Qsw).
 // Both branches end in the same polarization after a successful destructive read.
 double low=request::FE_dielectric_cap_F*request::plate_read_voltage_V/(cbl+request::FE_dielectric_cap_F);
 double high=(request::FE_dielectric_cap_F*request::plate_read_voltage_V+request::polarization_switch_charge_C)/(cbl+request::FE_dielectric_cap_F);
 double margin=std::min(request::reference_voltage_V-low,high-request::reference_voltage_V);
 double accessR=request::case_charge_ports?request::external_access_R_ohm:CalculateOnResistance(accessW,NMOS,ip.temperature,t);
 double rc=-std::log(request::settle_error_fraction)*accessR*cbl*request::FE_dielectric_cap_F/(cbl+request::FE_dielectric_cap_F);
 double plateCharge=request::read_columns*(request::polarization_switch_charge_C+request::FE_dielectric_cap_F*request::plate_read_voltage_V)+request::plate_line_cap_F*request::plate_read_voltage_V;
 RowDecoder select(ip,t,c);select.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::rows)),false);select.CalculateArea(0,0,NONE);select.CalculateLatency(1e20,request::case_charge_ports?request::decoder_LV_load_F:request::WL_load_F,0,1,1);
 DFF hold(ip,t,c);hold.Initialize(request::destructive_domain_bits,request::clock_Hz);hold.CalculateArea(0,0,NONE);hold.CalculateLatency(1e20,1);
 out("case_charge_ports",request::case_charge_ports);out("external_HV_access_required",request::case_charge_ports);out("synthetic_charge_solution_eligible",!request::case_charge_ports);out("native_access_diagnostic_drain_F",nativeAccessC);out("native_decoder_load_F",request::case_charge_ports?request::decoder_LV_load_F:request::WL_load_F);out("native_decoder_area_m2",select.area);out("native_vdd_V",t.vdd);out("native_SA_internal_cap_F",sa.capLoad);out("actual_access_drain_F",accessC);out("actual_BL_total_cap_F",cbl);
 if(!request::case_charge_ports){out("state_nonswitch_BL_V",low);out("state_switch_BL_V",high);out("state_switch_FE_final_V",request::plate_read_voltage_V-high);out("minimum_reference_margin_V",margin);}
 out("native_voltage_sense_s",sa.readLatency);out("native_sense_included_enable_s",1/request::clock_Hz);out("native_SA_area_m2",sa.area);
 out("effective_access_R_ohm",accessR);out("access_R_source_external",request::case_charge_ports);out("native_access_R_ohm",CalculateOnResistance(accessW,NMOS,ip.temperature,t));if(!request::case_charge_ports){out("charge_transfer_RC_s",rc);out("plate_worst_charge_C",plateCharge);out("plate_current_lower_time_s",plateCharge/request::plate_current_limit_A);
 out("sense_margin_valid",margin>=request::sense_target_V);out("sense_voltage_range_valid",low>=0&&high<=t.vdd&&request::reference_voltage_V<=t.vdd);
 out("polarization_switch_domain_valid",request::plate_read_voltage_V-high>=request::switch_min_FE_voltage_V);}
 out("native_WL_gate_compatible",std::abs(request::WL_high_voltage_V-t.vdd)<1e-12);out("native_WL_select_s",select.readLatency);out("native_LV_decoder_s",select.readLatency);
 out("physical_activation_domain_bits",request::destructive_domain_bits);out("destructive_domain_bits",request::destructive_read?request::destructive_domain_bits:0);out("actual_state_hold_bits",hold.numDff);out("native_state_capture_s",hold.readLatency);
 out("restore_batches",request::destructive_read?std::ceil(double(request::destructive_domain_bits)/request::restore_lanes):0);out("restore_required",request::destructive_read);if(request::destructive_read)out("post_read_polarization_state",1);
 out("native_hold_area_m2",hold.area);out("native_periphery_area_m2",hold.area+select.area+sa.area);out("component_only",1);return 0;
}

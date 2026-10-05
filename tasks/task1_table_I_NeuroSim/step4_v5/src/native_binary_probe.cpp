// V5 circuit integration probe. No complete device or Roofline service is claimed.
// Upstream classes retain their original license in each isolated build copy.
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include "SubArray.h"
#include "request.h"
#include "../Param.h"
Param *param;

static void emit(const char*k,double v){
 if(!std::isfinite(v)){std::cerr<<"V5_INVALID_NONFINITE "<<k<<"\n";std::exit(2);}
 std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";
}
int main(){
 Param settings;settings.processNode=request::technology_nm;param=&settings;
 InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;
 Technology tech;tech.Initialize(ip.processNode,LSTP);
 MemCell c{};c.memCellType=Type::RRAM;c.accessType=CMOS_access;
 c.featureSize=tech.featureSize;c.processNode=request::device_node_nm;
 // This native branch uses peripheral F for geometry: physical pitches are converted once.
 c.widthInFeatureSize=request::cell_pitch_x_m/tech.featureSize;
 c.heightInFeatureSize=request::cell_pitch_y_m/tech.featureSize;
 c.resistanceOn=request::resistance_on_ohm;c.resistanceOff=request::resistance_off_ohm;
 c.resistanceAvg=(c.resistanceOn+c.resistanceOff)/2;c.resCellAccess=request::access_resistance_ohm;
 c.readVoltage=request::read_voltage_V;c.accessVoltage=request::access_voltage_V;
 // Write voltage only establishes a decoder port in this probe; it is not a device pulse.
 c.writeVoltage=request::write_port_voltage_V;c.writePulseWidth=0;c.readPulseWidth=0;
 SubArray a(ip,tech,c);a.digitalModeNeuro=true;a.parallelRead=false;a.readCircuitMode=CMOS;
 a.relaxArrayCellHeight=false;a.relaxArrayCellWidth=false;
 a.numColMuxed=request::read_mux;a.numWriteColMuxed=request::write_mux;
 a.numCellPerSynapse=8;a.avgWeightBit=8;a.numReadPulse=1;a.shiftAddEnable=false;
 a.numWritePulse=1;a.maxNumWritePulse=1;a.maxNumIntBit=8;a.clkFreq=request::clock_Hz;
 a.activityRowRead=1./request::rows;a.activityRowWrite=1./request::rows;a.activityColWrite=1;
 a.numReadCellPerOperationNeuro=request::cols/request::read_mux;
 a.numWriteCellPerOperationNeuro=request::cols/request::write_mux;
 a.sequentialReadMuxFraction=request::read_mux_IR_fraction;a.writeColumnTargetResistance=request::write_mux_target_ohm;
 a.spikingMode=NONSPIKING;a.Initialize(request::rows,request::cols,request::wire_ohm_per_m);
 a.voltageSenseAmp.voltageSenseDiff=request::sense_threshold_V;
 a.CalculateArea();a.CalculateLatency(1e20);
 emit("input_rows",request::rows);emit("input_cols",request::cols);
 emit("input_temperature_K",ip.temperature);emit("input_technology_nm",ip.processNode);
 emit("input_device_node_nm",c.processNode);emit("input_read_voltage_V",c.readVoltage);
 emit("input_Ron_ohm",c.resistanceOn);emit("input_Roff_ohm",c.resistanceOff);
 emit("input_access_ohm",c.resCellAccess);emit("input_pitch_x_m",request::cell_pitch_x_m);
 emit("input_pitch_y_m",request::cell_pitch_y_m);emit("input_wire_ohm_per_m",a.unitWireRes);
 emit("input_read_mux",a.numColMuxed);emit("input_write_mux",a.numWriteColMuxed);
 emit("input_clock_Hz",a.clkFreq);emit("input_extra_column_cap_F",request::extra_column_cap_F);emit("input_write_port_voltage_V",c.writeVoltage);emit("input_access_voltage_V",c.accessVoltage);
 emit("actual_tech_vdd_V",tech.vdd);emit("actual_tech_vth_V",tech.vth);
 emit("actual_tech_Ion_N_A_per_m",tech.currentOnNmos[ip.temperature-300]);
 emit("actual_access_Ion_at_native_bias_A",tech.currentOnNmos[ip.temperature-300]*c.widthAccessCMOS*tech.featureSize);
 emit("actual_access_bias_matches_native",std::abs(c.accessVoltage-tech.vdd)<1e-12);
 emit("actual_access_width_F",c.widthAccessCMOS);emit("actual_access_width_m",c.widthAccessCMOS*tech.featureSize);
 emit("actual_Ron_total_ohm",c.resMemCellOn);emit("actual_Roff_total_ohm",c.resMemCellOff);
 emit("array_row_m",a.lengthRow);emit("array_col_m",a.lengthCol);
 emit("array_WL_cap_F",a.capRow2);emit("array_BL_cap_F",a.capCol);
 emit("array_row_res_ohm",a.resRow);emit("array_col_res_ohm",a.resCol);
 emit("actual_mux_n_m",a.mux.widthTgN);emit("actual_mux_p_m",a.mux.widthTgP);
 emit("actual_mux_res_ohm",a.mux.resTg);
 emit("input_read_mux_IR_fraction",a.sequentialReadMuxFraction);emit("input_write_mux_target_ohm",a.writeColumnTargetResistance);
 emit("input_write_current_A",request::write_current_A);emit("upstream_oversized_read_mux_target_diagnostic_ohm",c.resMemCellOn/request::rows/2);
 double writeIon=tech.currentOnNmos[ip.temperature-300]*a.colDecoderDriver.widthTgN+tech.currentOnPmos[ip.temperature-300]*a.colDecoderDriver.widthTgP;
 emit("write_mux_width_N_m",a.colDecoderDriver.widthTgN);emit("write_mux_width_P_m",a.colDecoderDriver.widthTgP);
 emit("write_mux_native_Ion_A",writeIon);emit("write_mux_voltage_drop_V",request::write_current_A*a.colDecoderDriver.resTg);
 emit("write_mux_current_compliance",request::write_current_A<=writeIon&&request::write_current_A*a.colDecoderDriver.resTg<request::write_port_voltage_V);
 emit("write_mux_area_m2",a.colDecoderDriver.area);emit("native_area_m2",a.area);
 emit("native_used_area_m2",a.usedArea);emit("native_sa_count",a.voltageSenseAmp.numReadCol);
 emit("native_adder_count",a.adder.numAdder);emit("native_adder_bits",a.adder.numBit);
 emit("native_accumulator_bits",a.dff.numDff);
 emit("native_WL_s",a.wlDecoder.readLatency);emit("native_mux_decoder_s",a.muxDecoder.readLatency);
 emit("native_mux_s",a.mux.readLatency);emit("native_SA_s",a.voltageSenseAmp.readLatency);
 emit("native_adder_s",a.adder.readLatency);emit("native_capture_s",a.dff.readLatency);
 emit("native_subtract_s",a.subtractor.readLatency);emit("native_shiftadd_s",a.shiftAdd.readLatency);
 emit("native_read_aggregate_s",a.readLatency);emit("native_write_selection_s",a.writeLatency);
 emit("write_WL_decoder_without_enable_s",a.wlDecoder.writeLatency);
 emit("write_column_decoder_one_batch_s",a.colDecoder.writeLatency/a.numWriteColMuxed);
 // DecoderDriver's write return is only writePulseWidth*numWrite. Its read calculation
 // is the actual same TG/column RC; use that control-port settle, never as thermal programming.
 emit("write_column_driver_native_pulse_proxy_s",a.colDecoderDriver.writeLatency/(a.numWriteColMuxed*2));
 emit("write_column_driver_base_edge_diagnostic_s",a.colDecoderDriver.readLatency);
 emit("write_column_TG_ohm",a.colDecoderDriver.resTg);
 emit("actual_mux_decoder_area_m2",a.muxDecoder.area);
 emit("native_col_delay_diagnostic_s",a.colDelay);
 // Patched native call loads the initialized access drains. For audit only, show
 // the original wire-only load and re-evaluate the SAME VSA with optional external C.
 double muxC=a.mux.capTgDrain*(2+a.numColMuxed-1);
 double nativeLoad=a.lengthCol*0.2e-15/1e-6+muxC;
 double preWidth=request::precharge_width_F*tech.featureSize;
 double preDrain=CalculateDrainCap(preWidth,NMOS,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech);
 double writeOffDrain=2*a.colDecoderDriver.capTgDrain;
 double fullLoad=a.capCol+muxC+request::extra_column_cap_F+preDrain+writeOffDrain;
 emit("write_off_drain_added_to_read_F",writeOffDrain);
 // Native TG driver adds its own two output drains internally. Add other connected
 // precharge/read-selection/source-network loads once to its external column load.
 double writeExternalLoad=a.capCol+request::extra_column_cap_F+preDrain+a.mux.capTgDrain;
 a.colDecoderDriver.CalculateLatency(a.colDecoder.rampOutput,writeExternalLoad,a.lengthCol*0.2e-15/1e-6+preDrain+a.mux.capTgDrain,a.resCol,1,1);
 emit("write_column_driver_one_edge_s",a.colDecoderDriver.readLatency);
 emit("write_external_column_cap_F",writeExternalLoad);
 emit("write_total_connected_cap_F",writeExternalLoad+writeOffDrain);
 double baseSA=a.voltageSenseAmp.readLatency;
 a.voltageSenseAmp.CalculateLatency(nativeLoad,a.numColMuxed);
 emit("upstream_unpatched_SA_diagnostic_s",a.voltageSenseAmp.readLatency);
 a.voltageSenseAmp.CalculateLatency(fullLoad,a.numColMuxed);
 emit("upstream_wire_only_sa_input_cap_F",nativeLoad);emit("native_sa_input_cap_F",a.capCol+muxC);emit("adapted_sa_input_cap_F",fullLoad);
 emit("adapted_SA_s",a.voltageSenseAmp.readLatency);
 emit("adapted_read_aggregate_s",a.readLatency-baseSA+a.voltageSenseAmp.readLatency);
 emit("sense_threshold_V",a.voltageSenseAmp.voltageSenseDiff);
 emit("sa_precharge_per_group_s",2.3*a.voltageSenseAmp.resPrecharge*a.voltageSenseAmp.capS1);
 emit("sa_control_per_group_s",2/request::clock_Hz);
 emit("sa_effective_node_cap_F",fullLoad+a.voltageSenseAmp.capS1+a.voltageSenseAmp.capNmosDrain);
 emit("sa_native_linear_develop_per_group_s",a.voltageSenseAmp.voltageSenseDiff*(fullLoad+a.voltageSenseAmp.capS1+a.voltageSenseAmp.capNmosDrain)/(c.readVoltage/c.resMemCellOn-c.readVoltage/c.resMemCellOff));
 // Independent passive two-column bound. It is NOT a characterization of a regulated clamp.
 double rlo=c.resMemCellOn+a.resCol+a.mux.resTg,rhi=c.resMemCellOff+a.resCol+a.mux.resTg;
 double capacitance=fullLoad+a.voltageSenseAmp.capS1+a.voltageSenseAmp.capNmosDrain;
 double tpeak=capacitance*std::log(rhi/rlo)/(1/rlo-1/rhi);
 double peak=c.readVoltage*(std::exp(-tpeak/(rhi*capacitance))-std::exp(-tpeak/(rlo*capacitance)));
 double iL=c.readVoltage/rlo,iH=c.readVoltage/rhi;
 emit("port_I_lowR_A",iL);emit("port_I_highR_A",iH);emit("port_delta_I_A",iL-iH);
 emit("passive_peak_signal_V",peak);emit("passive_peak_time_s",tpeak);
 emit("passive_threshold_reachable",peak>=a.voltageSenseAmp.voltageSenseDiff);
 emit("unregulated_linear_ramp_time_s",a.voltageSenseAmp.voltageSenseDiff*capacitance/(iL-iH));
 // Real storage and signed-result correction components, separate from native unsigned accumulation.
 DFF inputHold(ip,tech,c),signedHold(ip,tech,c),targetHold(ip,tech,c);
 int outputs=request::cols/request::read_mux/8;
 inputHold.Initialize(request::rows*8,request::clock_Hz);
 signedHold.Initialize(25*(request::cols/8),request::clock_Hz);
 targetHold.Initialize(request::cols,request::clock_Hz);
 for(auto*d:{&inputHold,&signedHold,&targetHold}){d->CalculateArea(0,0,NONE);d->CalculateLatency(1e20,1);}
 Subtractor signedCorrection(ip,tech,c);signedCorrection.Initialize(25,outputs);
 signedCorrection.CalculateArea(0,0,NONE);signedCorrection.CalculateLatency(1e20,signedHold.capTgDrain,1);
 emit("input_hold_bits",inputHold.numDff);emit("target_hold_bits",targetHold.numDff);
 emit("target_hold_capture_s",targetHold.readLatency);emit("target_hold_input_cap_F",targetHold.capTgDrain);
 emit("signed_output_hold_bits",signedHold.numDff);emit("input_capture_s",inputHold.readLatency);
 emit("signed_correction_s_pre_connection_diagnostic",signedCorrection.readLatency);emit("signed_capture_s",signedHold.readLatency);
 emit("additional_storage_area_m2",inputHold.area+signedHold.area+targetHold.area);
 emit("additional_correction_area_m2",signedCorrection.area);
 // Additional 25-bit digital MAC datapath. Native short adder remains separately reported.
 Adder wideAdder(ip,tech,c);wideAdder.Initialize(25,outputs);
 wideAdder.CalculateArea(0,0,NONE);wideAdder.CalculateLatency(1e20,signedHold.capTgDrain,1);
 Mux shiftedWeight(ip,tech,c),feedback(ip,tech,c);
 shiftedWeight.Initialize(25*outputs,8,0,true);feedback.Initialize(25*outputs,request::read_mux,0,true);
 for(auto*m:{&shiftedWeight,&feedback}){m->CalculateArea(0,0,NONE);m->CalculateLatency(1e20,wideAdder.capNandInput,1);}
 RowDecoder shiftSelect(ip,tech,c);shiftSelect.Initialize(REGULAR_ROW,3,true);
 shiftSelect.CalculateArea(0,0,NONE);
 shiftSelect.CalculateLatency(1e20,shiftedWeight.capTgGateN*25*outputs,shiftedWeight.capTgGateP*25*outputs,1,0);
 emit("extra_25bit_adder_s_pre_connection_diagnostic",wideAdder.readLatency);emit("extra_25bit_adder_area_m2",wideAdder.area);
 emit("extra_25bit_adder_lanes",outputs);emit("extra_25bit_adder_input_cap_F",wideAdder.capNandInput);
 emit("extra_25bit_register_input_cap_F",signedHold.capTgDrain);
 emit("extra_shifted_weight_mux_s_pre_connection_diagnostic",shiftedWeight.readLatency);emit("extra_shift_select_s_pre_connection_diagnostic",shiftSelect.readLatency);
 emit("extra_accumulator_feedback_mux_s_pre_connection_diagnostic",feedback.readLatency);
 emit("extra_datapath_mux_area_m2",shiftedWeight.area+feedback.area+shiftSelect.area);
 // Real input row and bit selection, plus sensed-weight holding.
 DFF rowInput(ip,tech,c),weightHold(ip,tech,c),verifyStatus(ip,tech,c),retryState(ip,tech,c);
 rowInput.Initialize(8,request::clock_Hz);weightHold.Initialize(request::cols,request::clock_Hz);
 verifyStatus.Initialize(1,request::clock_Hz);retryState.Initialize(2,request::clock_Hz);
 for(auto*d:{&rowInput,&weightHold,&verifyStatus,&retryState}){d->CalculateArea(0,0,NONE);d->CalculateLatency(1e20,1);}
 Mux inputRow(ip,tech,c),inputBit(ip,tech,c);
 inputRow.Initialize(8,request::rows,0,true);inputBit.Initialize(1,8,0,true);
 inputRow.CalculateArea(0,0,NONE);inputRow.CalculateLatency(1e20,rowInput.capTgDrain,1);
 inputBit.CalculateArea(0,0,NONE);inputBit.CalculateLatency(1e20,shiftedWeight.capTgGateN*25*outputs,1);
 RowDecoder inputAddress(ip,tech,c),inputBitAddress(ip,tech,c);
 inputAddress.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(request::rows)),true);
 inputBitAddress.Initialize(REGULAR_ROW,3,true);
 inputAddress.CalculateArea(0,0,NONE);inputBitAddress.CalculateArea(0,0,NONE);
 inputAddress.CalculateLatency(1e20,inputRow.capTgGateN*8,inputRow.capTgGateP*8,1,1);
 inputBitAddress.CalculateLatency(1e20,inputBit.capTgGateN,inputBit.capTgGateP,1,1);
 // Byte difference plus OR reduction gives exact equality, with sticky capture and retry state.
 Subtractor verifyCompare(ip,tech,c);verifyCompare.Initialize(8,outputs);verifyCompare.CalculateArea(0,0,NONE);
 double wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn,hn,wnor,hi,wi,cn,co,ci,cio;
 CalculateGateArea(NOR,2,wn,wp*2,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hn,&wnor);
 CalculateGateCapacitance(NOR,2,wn,wp*2,hn,tech,&cn,&co);
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hi,&wi);
 CalculateGateCapacitance(INV,1,wn,wp,hi,tech,&ci,&cio);
 verifyCompare.CalculateLatency(1e20,cn,1);
 int failBits=9*outputs,failDepth=(int)std::ceil(std::log2(failBits));
 double norR=2*CalculateOnResistance(wp*2,PMOS,ip.temperature,tech);
 double norDelay=horowitz(norR*(co+ci),0,1e20,nullptr);
 double invDelay=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+std::max(cn,verifyStatus.capTgDrain)),0,1e20,nullptr);
 double failReduce=failDepth*(norDelay+invDelay);
 Adder retryIncrement(ip,tech,c);retryIncrement.Initialize(2,1);retryIncrement.CalculateArea(0,0,NONE);retryIncrement.CalculateLatency(1e20,retryState.capTgDrain,1);
 emit("input_row_select_s",inputAddress.readLatency+inputRow.readLatency);emit("input_row_capture_s",rowInput.readLatency);
 emit("input_bit_select_s_pre_connection_diagnostic",inputBitAddress.readLatency+inputBit.readLatency);
 emit("weight_hold_bits",weightHold.numDff);emit("weight_hold_capture_s",weightHold.readLatency);
 emit("verify_byte_compare_s",verifyCompare.readLatency);emit("verify_fail_reduce_s",failReduce);
 emit("verify_status_capture_s",verifyStatus.readLatency);emit("verify_sticky_or_s_pre_clear_diagnostic",norDelay+invDelay);
 emit("retry_increment_s_pre_clear_diagnostic",retryIncrement.readLatency);emit("retry_state_capture_s",retryState.readLatency);
 emit("verify_compare_lanes",outputs);emit("verify_fail_bits",failBits);emit("verify_reduce_gates",2*(failBits-1));
 emit("input_selection_area_m2",inputRow.area+inputBit.area+inputAddress.area+inputBitAddress.area+rowInput.area);
 emit("weight_hold_area_m2",weightHold.area);
 emit("verify_control_area_m2",verifyCompare.area+(failBits-1)*(hn*wnor+hi*wi)+verifyStatus.area+retryState.area+retryIncrement.area+hn*wnor+hi*wi);
 // An explicit enable gates every WL so data/reference precharge occurs with all access off.
 // Two-input NAND plus INV is a real per-row gate, separate from address decoding.
 double hwe,wwe,cwe,cweo,hwi,wwi,cwi,cwio;
 double wen=4*wn,wep=2*wp;
 CalculateGateArea(NAND,2,wen,wep,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hwe,&wwe);
 CalculateGateCapacitance(NAND,2,wen,wep,hwe,tech,&cwe,&cweo);
 CalculateGateArea(INV,1,wen,wep,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hwi,&wwi);
 CalculateGateCapacitance(INV,1,wen,wep,hwi,tech,&cwi,&cwio);
 double wlGate=horowitz(2*CalculateOnResistance(wen,NMOS,ip.temperature,tech)*(cweo+cwi),0,1e20,nullptr)+
   horowitz(CalculateOnResistance(wep,PMOS,ip.temperature,tech)*(cwio+a.capRow2)+a.resRow*a.capRow2/2,0,1e20,nullptr);
 double enableScale=std::max(1.,std::ceil(std::sqrt((request::rows+1)*cwe/ci)));
 double he,we,ce,ceo;CalculateGateArea(INV,1,wn*enableScale,wp*enableScale,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&he,&we);
 CalculateGateCapacitance(INV,1,wn*enableScale,wp*enableScale,he,tech,&ce,&ceo);
 double wlEnableDrive=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+ce),0,1e20,nullptr)+
   horowitz(CalculateOnResistance(wn*enableScale,NMOS,ip.temperature,tech)*(ceo+(request::rows+1)*cwe),0,1e20,nullptr);
 a.wlDecoder.CalculateLatency(1e20,cwe,0,1,1);
 double wlSetup=a.wlDecoder.readLatency+wlEnableDrive+wlGate;
 double wlRelease=wlEnableDrive+wlGate;
 emit("write_WL_select_one_s",wlSetup);emit("WL_enable_setup_s",wlSetup);emit("WL_release_s",wlRelease);
 emit("WL_enable_gate_area_m2",request::rows*(hwe*wwe+hwi*wwi)+hi*wi+he*we);
 emit("WL_enable_fanout_cap_F",(request::rows+1)*cwe);emit("WL_address_setup_s",a.wlDecoder.readLatency);emit("WL_enable_edge_only_s",wlRelease);
 // Low-read-rail NMOS precharge port. Native Ion/R at Vdd is corrected for reduced
 // gate overdrive; this compact extension is explicitly conditioned on positive headroom.
 double headroom=tech.vdd-c.readVoltage-tech.vth;
 double preR=headroom>0?CalculateOnResistance(preWidth,NMOS,ip.temperature,tech)*(tech.vdd-tech.vth)/headroom:0;
 double preNodeC=fullLoad+a.voltageSenseAmp.capS1+a.voltageSenseAmp.capNmosDrain;
 double preRC=headroom>0?-std::log(request::precharge_error_fraction)*preR*preNodeC:0;
 double hg,wg,cg,cgd;CalculateGateArea(INV,1,preWidth,0,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hg,&wg);
 CalculateGateCapacitance(INV,1,preWidth,0,hg,tech,&cg,&cgd);
 int preBranches=2*a.voltageSenseAmp.numReadCol;
 double driveScale=std::max(1.,std::ceil(std::sqrt(preBranches*cg/ci)));
 double hd,wd,cd,cdo;CalculateGateArea(INV,1,wn*driveScale,wp*driveScale,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hd,&wd);
 CalculateGateCapacitance(INV,1,wn*driveScale,wp*driveScale,hd,tech,&cd,&cdo);
 double preControl=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+cd),0,1e20,nullptr)+horowitz(CalculateOnResistance(wn*driveScale,NMOS,ip.temperature,tech)*(cdo+preBranches*cg),0,1e20,nullptr);
 emit("input_precharge_width_F",request::precharge_width_F);emit("input_precharge_error_fraction",request::precharge_error_fraction);
 emit("precharge_headroom_V",headroom);emit("precharge_bias_feasible",headroom>0);emit("precharge_branch_R_ohm",preR);
 emit("precharge_added_drain_cap_F",preDrain);emit("precharge_branches",preBranches);
 emit("precharge_external_RC_s",preRC);emit("precharge_control_s",preControl);
 emit("precharge_external_area_m2",preBranches*hg*wg+hi*wi+hd*wd);
 emit("native_sa_resPrecharge_ohm",a.voltageSenseAmp.resPrecharge);
 double combo=std::max({wideAdder.readLatency+shiftedWeight.readLatency+feedback.readLatency+shiftSelect.readLatency,
  signedCorrection.readLatency,inputAddress.readLatency+inputRow.readLatency,inputBitAddress.readLatency+inputBit.readLatency,
  verifyCompare.readLatency+failReduce+norDelay+invDelay,retryIncrement.readLatency});
 emit("digital_critical_comb_s_pre_connection_diagnostic",combo);emit("digital_halfcycle_min_period_s_pre_connection_diagnostic",2*combo);
 emit("digital_clock_budget_satisfied_pre_connection_diagnostic",1/request::clock_Hz>=2*combo);
 // Individually schedulable group primitive, excluding native short arithmetic.
 emit("read_frontend_one_group_s",std::max(wlSetup,a.muxDecoder.readLatency+a.mux.readLatency)+a.voltageSenseAmp.readLatency/a.numColMuxed);
 // Close the complete bit-serial gate/hold graph. Zero bits do not bypass hardware.
 Mux resultChoice(ip,tech,c),accumulatorKeep(ip,tech,c),weightGroup(ip,tech,c),weightKeep(ip,tech,c),targetRead(ip,tech,c),programMask(ip,tech,c);
 resultChoice.Initialize(25*outputs,2,0,true);accumulatorKeep.Initialize(25*(request::cols/8),2,0,true);
 weightGroup.Initialize(8*outputs,request::read_mux,0,true);weightKeep.Initialize(request::cols,2,0,true);
 targetRead.Initialize(8*outputs,request::read_mux,0,true);programMask.Initialize(request::cols/request::write_mux,request::write_mux,0,true);
 for(auto*m:{&resultChoice,&accumulatorKeep,&weightGroup,&weightKeep,&targetRead,&programMask})m->CalculateArea(0,0,NONE);
 double hm,wm,cm,cmo,hmi,wmi,cmi,cmio;
 CalculateGateArea(NAND,2,2*wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hm,&wm);
 CalculateGateCapacitance(NAND,2,2*wn,wp,hm,tech,&cm,&cmo);
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hmi,&wmi);
 CalculateGateCapacitance(INV,1,wn,wp,hmi,tech,&cmi,&cmio);
 double maskDelay=horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,tech)*(cmo+cmi),0,1e20,nullptr)+
  horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cmio+wideAdder.capNandInput+signedCorrection.capNandInput),0,1e20,nullptr);
 shiftedWeight.CalculateLatency(1e20,cm,1);
 inputBit.CalculateLatency(1e20,cm*25*outputs,1);
 feedback.CalculateLatency(1e20,wideAdder.capNandInput+signedCorrection.capNandInput,1);
 wideAdder.CalculateLatency(1e20,resultChoice.capTgDrain,1);signedCorrection.CalculateLatency(1e20,resultChoice.capTgDrain,1);
 resultChoice.CalculateLatency(1e20,accumulatorKeep.capTgDrain*request::read_mux,1);
 accumulatorKeep.CalculateLatency(1e20,signedHold.capTgDrain,1);weightKeep.CalculateLatency(1e20,weightHold.capTgDrain,1);
 weightGroup.CalculateLatency(1e20,shiftedWeight.capTgDrain*8,1);
 targetRead.CalculateLatency(1e20,verifyCompare.capNandInput,1);
 programMask.CalculateLatency(1e20,cn,1);
 shiftSelect.CalculateLatency(1e20,(shiftedWeight.capTgGateN+resultChoice.capTgGateN)*25*outputs,
  (shiftedWeight.capTgGateP+resultChoice.capTgGateP)*25*outputs,1,1);
 double groupN=a.mux.capTgGateN*a.voltageSenseAmp.numReadCol+feedback.capTgGateN*25*outputs+
   weightGroup.capTgGateN*8*outputs+accumulatorKeep.capTgGateN*25*outputs+weightKeep.capTgGateN*8*outputs+targetRead.capTgGateN*8*outputs;
 double groupP=a.mux.capTgGateP*a.voltageSenseAmp.numReadCol+feedback.capTgGateP*25*outputs+
   weightGroup.capTgGateP*8*outputs+accumulatorKeep.capTgGateP*25*outputs+weightKeep.capTgGateP*8*outputs+targetRead.capTgGateP*8*outputs;
 a.muxDecoder.CalculateLatency(1e20,groupN,groupP,1,1);
 // Partial external-port captures keep all other input/target bits through actual feedback MUXes.
 auto ingress=[&](int bits,int portBits,double dcap,const char*name){
   int groups=(bits+portBits-1)/portBits;double time=0,area=0;
   if(groups>1){Mux keep(ip,tech,c);RowDecoder select(ip,tech,c);keep.Initialize(bits,2,0,true);keep.CalculateArea(0,0,NONE);keep.CalculateLatency(1e20,dcap,1);
     select.Initialize(REGULAR_ROW,(int)std::ceil(std::log2(groups)),true);select.CalculateArea(0,0,NONE);
     select.CalculateLatency(1e20,keep.capTgGateN*portBits,keep.capTgGateP*portBits,1,1);
     time=select.readLatency+keep.readLatency;area=keep.area+select.area;
   }
   std::string prefix=name;emit((prefix+"_select_s").c_str(),time);emit((prefix+"_area_m2").c_str(),area);emit((prefix+"_beats").c_str(),groups);
   return time;
 };
 double inIngress=ingress(request::rows*8,request::input_port_bits,inputHold.capTgDrain,"input_ingress");
 double targetIngress=ingress(request::cols,request::resident_port_bits,targetHold.capTgDrain,"target_ingress");
 // Actual reference isolation: OFF during precharge, ON during differential development,
 // then native VSA regeneration holds the decision before both branches release.
 Mux refSwitch(ip,tech,c);refSwitch.Initialize(a.voltageSenseAmp.numReadCol,1,a.mux.resTg,false);
 // Reference isolation uses its NMOS branch driven by a matched WL replica; PMOS
 // gate is held at Vdd. Double the native half-conductance N width to retain target R.
 refSwitch.widthTgN*=2;refSwitch.resTg=CalculateOnResistance(refSwitch.widthTgN,NMOS,ip.temperature,tech);
 refSwitch.CalculateArea(0,0,NONE);
 refSwitch.CalculateLatency(1e20,fullLoad,1);
 double refGateC=a.voltageSenseAmp.numReadCol*refSwitch.capTgGateN;
 double refScale=std::max(1.,std::ceil(std::sqrt(refGateC/ci)));
 double hrd,wrd,crd,crdo;CalculateGateArea(INV,1,wn*refScale,wp*refScale,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hrd,&wrd);
 CalculateGateCapacitance(INV,1,wn*refScale,wp*refScale,hrd,tech,&crd,&crdo);
 double refControl=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+crd),0,1e20,nullptr)+
  horowitz(CalculateOnResistance(wn*refScale,NMOS,ip.temperature,tech)*(crdo+refGateC),0,1e20,nullptr);
 emit("reference_isolation_count",a.voltageSenseAmp.numReadCol);emit("reference_switch_R_ohm",refSwitch.resTg);
 emit("reference_switch_gate_N_F",refSwitch.capTgGateN);emit("reference_switch_gate_P_F",refSwitch.capTgGateP);
 emit("reference_switch_drain_F",refSwitch.capTgDrain);emit("reference_switch_area_m2",refSwitch.area);
 double replicaWireC=a.lengthRow*0.2e-15/1e-6;
 double matchEnableC=a.capRow2-refGateC-replicaWireC;
 emit("reference_enable_matching_cap_F",matchEnableC);
 emit("reference_enable_load_match_feasible",matchEnableC>=0);
 emit("reference_switch_active_N_only",1);emit("reference_PMOS_gate_static_V",tech.vdd);
 emit("reference_switch_RC_diagnostic_s",refSwitch.readLatency);
 emit("reference_unmatched_control_diagnostic_s",refControl);
 emit("reference_enable_control_s",wlRelease);emit("reference_isolation_edge_s",wlRelease);
 emit("reference_control_area_m2",hwe*wwe+hwi*wwi);emit("reference_control_gate_load_F",refGateC);
 // Explicit synchronous state clear: every output/status/retry D input passes
 // a NAND+INV AND with !CLEAR. No reset functionality is inferred from native DFF.
 int clearBits=signedHold.numDff+verifyStatus.numDff+retryState.numDff;
 double clearGate=horowitz(2*CalculateOnResistance(2*wn,NMOS,ip.temperature,tech)*(cmo+cmi),0,1e20,nullptr)+
   horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cmio+signedHold.capTgDrain),0,1e20,nullptr);
 double clearScale=std::max(1.,std::ceil(std::sqrt(clearBits*cm/ci)));
 double hclr,wclr,cclr,cclro;CalculateGateArea(INV,1,wn*clearScale,wp*clearScale,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hclr,&wclr);
 CalculateGateCapacitance(INV,1,wn*clearScale,wp*clearScale,hclr,tech,&cclr,&cclro);
 double clearControl=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(cio+cclr),0,1e20,nullptr)+
   horowitz(CalculateOnResistance(wn*clearScale,NMOS,ip.temperature,tech)*(cclro+clearBits*cm),0,1e20,nullptr);
 accumulatorKeep.CalculateLatency(1e20,cm,1);retryIncrement.CalculateLatency(1e20,cm,1);
 emit("state_clear_bits",clearBits);emit("state_clear_gates",2*clearBits+2);
 emit("state_clear_control_load_F",clearBits*cm);emit("state_clear_control_s",clearControl);
 emit("state_clear_data_gate_s",clearGate);emit("state_clear_comb_s",clearControl+clearGate);
 emit("state_clear_s",clearControl+clearGate+signedHold.readLatency);
 emit("state_clear_area_m2",clearBits*(hm*wm+hmi*wmi)+hi*wi+hclr*wclr);
 emit("verify_sticky_or_s",norDelay+invDelay+clearGate);emit("retry_increment_s",retryIncrement.readLatency+clearGate);
 emit("extra_25bit_adder_s",wideAdder.readLatency);emit("signed_correction_s",signedCorrection.readLatency);
 emit("extra_shifted_weight_mux_s",shiftedWeight.readLatency);emit("extra_shift_select_s",shiftSelect.readLatency);
 emit("extra_accumulator_feedback_mux_s",feedback.readLatency);emit("input_bit_select_s",inputBitAddress.readLatency+inputBit.readLatency);
 emit("data_zero_mask_s",maskDelay);emit("data_zero_mask_gates",2*25*outputs);emit("data_zero_mask_area_m2",25*outputs*(hm*wm+hmi*wmi));
 emit("add_sub_result_select_s",resultChoice.readLatency);emit("add_sub_result_select_area_m2",resultChoice.area);
 emit("accumulator_keep_s",accumulatorKeep.readLatency+clearGate);emit("accumulator_keep_area_m2",accumulatorKeep.area);
 emit("weight_group_select_s",weightGroup.readLatency);emit("weight_group_select_area_m2",weightGroup.area);
 emit("weight_keep_s",weightKeep.readLatency);emit("weight_keep_area_m2",weightKeep.area);
 emit("verify_target_select_s",targetRead.readLatency);emit("verify_target_select_area_m2",targetRead.area);
 emit("program_target_select_s",programMask.readLatency);emit("program_target_select_area_m2",programMask.area);
 emit("program_target_mask_logic_s",norDelay+invDelay);emit("program_target_mask_area_m2",(request::cols/request::write_mux)*(hn*wnor+hi*wi));
 emit("group_select_s",a.muxDecoder.readLatency);emit("group_select_load_N_F",groupN);emit("group_select_load_P_F",groupP);
 emit("input_port_bits",request::input_port_bits);emit("resident_port_bits",request::resident_port_bits);
 double macPath=std::max({shiftSelect.readLatency+shiftedWeight.readLatency+maskDelay,inputBitAddress.readLatency+inputBit.readLatency+maskDelay,feedback.readLatency})+
   std::max(wideAdder.readLatency,signedCorrection.readLatency)+resultChoice.readLatency+accumulatorKeep.readLatency+clearGate;
 double finalCombo=std::max({macPath,combo+clearGate,inIngress,targetIngress,a.muxDecoder.readLatency,clearControl+clearGate});
 emit("digital_critical_comb_s",finalCombo);emit("digital_halfcycle_min_period_s",2*finalCombo);
 emit("digital_clock_budget_satisfied",1/request::clock_Hz>=2*finalCombo);
 emit("read_frontend_one_group_with_control_s",std::max(wlSetup,a.muxDecoder.readLatency+a.mux.readLatency)+a.voltageSenseAmp.readLatency/a.numColMuxed);
 emit("probe_only",1);
 return 0;
}

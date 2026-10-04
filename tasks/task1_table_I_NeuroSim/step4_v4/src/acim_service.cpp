#include <cmath>
#include <iomanip>
#include <iostream>
#include <vector>
#include "Param.h"
#include "SubArray.h"
#include "constant.h"
#define STEP4_TRAINING
#include "correction.h"
#include "input_serializer.h"
#include "request.h"
Param *param;
int main(int argc,char**argv){
 const int rows=request::physical_rows,cols=request::physical_cols,mux=request::read_mux,writecols=request::write_parallel_bits;
 const double act=request::read_activity,access=request::sram_access_width_F;
 const int adcbits=request::adc_bits;
 if(mux!=8||rows!=request::logical_K||cols/8-1!=request::logical_N||writecols>cols||writecols<1)return 2;
 param=new Param();param->numBitInput=request::input_bits;param->numColPerSynapse=request::weight_bits;param->numRowPerSynapse=1;
 // Param constructor already consumed authoritative temperature/node/wire/device fields.
 param->unitLengthWireResistance*=request::wire_resistance_scale;
 InputParameter ip={};ip.temperature=param->temp;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;ip.processNode=param->technode;
 Technology tech;tech.Initialize(param->technode,LSTP,conventional);
 MemCell cell={};cell.memCellType=Type::SRAM;cell.accessType=CMOS_access;cell.featureSize=param->featuresize;
 cell.heightInFeatureSize=param->heightInFeatureSizeSRAM;cell.widthInFeatureSize=param->widthInFeatureSizeSRAM;
 cell.widthSRAMCellNMOS=param->widthSRAMCellNMOS;cell.widthSRAMCellPMOS=param->widthSRAMCellPMOS;cell.widthAccessCMOS=param->widthAccessCMOS;
 cell.minSenseVoltage=param->minSenseVoltage;cell.readVoltage=tech.vdd;cell.writeVoltage=tech.vdd;cell.readPulseWidth=0;
 SubArray a(ip,tech,cell); a.conventionalSequential=false;a.conventionalParallel=true;a.BNNparallelMode=false;a.BNNsequentialMode=false;a.XNORparallelMode=false;a.XNORsequentialMode=false;a.trainingEstimation=false;a.parallelBP=false;
 a.activityRowRead=act;a.activityRowWrite=1;a.activityColWrite=1;a.activityBPColRead=0;
 a.levelOutput=pow(2,adcbits);a.levelOutputBP=2;a.numColMuxed=mux;a.numRowMuxedBP=1;a.clkFreq=1e9;a.relaxArrayCellHeight=false;a.relaxArrayCellWidth=false;
 a.numReadPulse=request::input_bits;a.numReadPulseBP=1;a.avgWeightBit=1;a.numCellPerSynapse=request::weight_bits;a.SARADC=true;a.currentMode=true;a.spikingMode=NONSPIKING;a.FPGA=false;a.parallelWrite=false;a.neuro=true;
 a.numReadCellPerOperationNeuro=cols;a.numWriteCellPerOperationNeuro=writecols;a.numWriteCellPerOperationMemory=writecols;a.numReadCellPerOperationMemory=cols;a.numWriteCellPerOperationFPGA=cols;a.numReadCellPerOperationFPGA=cols;a.maxNumWritePulse=1;a.numWritePulse=1;a.totalNumWritePulse=rows;
 a.Initialize(rows,cols,param->unitLengthWireResistance);
 a.muxDecoder.widthDriverInvN=2*MIN_NMOS_SIZE*tech.featureSize*request::mux_driver_scale;
 a.muxDecoder.widthDriverInvP=2*tech.pnSizeRatio*MIN_NMOS_SIZE*tech.featureSize*request::mux_driver_scale;
 a.CalculateArea();
 a.muxDecoder.muxSelectWireRes=a.mux.width*param->unitLengthWireResistance;
 a.muxDecoder.muxSelectWireCap=a.mux.width*0.2e-15/1e-6;
 a.muxDecoder.muxSelectFanout=cols/mux;
 // Same-backend signed correction. Public shared helper is copied into this isolated run.
 const int n=cols/8-1, outbits=25, batches=rows*int(ceil(double(cols)/writecols));
 DFF input(ip,tech,cell),writeData(ip,tech,cell);
 input.Initialize(rows*request::input_bits,1e9);writeData.Initialize(writecols,1e9);
 input.CalculateArea(0,a.widthArray,NONE);writeData.CalculateArea(0,a.widthArray,NONE);
 InputSerializer serializer(ip,tech,cell,rows,1e9,a.heightArray,param->unitLengthWireResistance,a.wlSwitchMatrix.dff.capTgDrain);
 OffsetCorrection correction(ip,tech,cell,n,1e9,a.heightArray,a.width,param->unitLengthWireResistance);
 double wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn,hinv,winv,cin,cout;
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hinv,&winv);
 CalculateGateCapacitance(INV,1,wn,wp,hinv,tech,&cin,&cout);
 auto invDelay=[&](double load){double rr=CalculateOnResistance(wn,NMOS,ip.temperature,tech),gg=CalculateTransconductance(wn,NMOS,tech);return horowitz(rr*(cout+load),1/(rr*gg),1e20,nullptr);};
 const double correctionInv=correction.inverter_s,encodeInv=invDelay(writeData.capTgDrain);
 a.shiftAddWeight.adder.CalculateLatency(1e20,a.shiftAddWeight.dff.capTgDrain,1);
 a.shiftAddInput.adder.CalculateLatency(1e20,a.shiftAddInput.dff.capTgDrain,1);
 const double clockPeriod=request::clock_reservation_factor*std::max(correction.combinational_s,std::max(a.shiftAddInput.adder.readLatency,a.shiftAddWeight.adder.readLatency));
 const double clk=1/clockPeriod,half=clockPeriod/2;
 a.clkFreq=clk;a.wlSwitchMatrix.clkFreq=clk;a.wlSwitchMatrix.dff.clkFreq=clk;
 a.shiftAddWeight.clkFreq=clk;a.shiftAddWeight.dff.clkFreq=clk;a.shiftAddInput.clkFreq=clk;a.shiftAddInput.dff.clkFreq=clk;
 input.clkFreq=clk;writeData.clkFreq=clk;correction.operand.clkFreq=clk;
 correction.stage1.clkFreq=clk;correction.stage2.clkFreq=clk;correction.output.clkFreq=clk;
 correction.stage1.CalculateLatency(1e20,1);correction.stage2.CalculateLatency(1e20,1);correction.output.CalculateLatency(1e20,1);
 input.CalculateLatency(1e20,1);writeData.CalculateLatency(1e20,batches);correction.operand.CalculateLatency(1e20,1);
 std::vector<double> r(cols,10000);a.CalculateLatency(1e20,r,r);
 // Respect native ShiftAdd overlap with an ACTUAL per-column-group acquisition interval.
 // Both precharge and colDelay are aggregated over mux groups by the corrected SubArray.
 cell.readPulseWidth=(a.precharger.readLatency+a.colDelay+a.sarADC.readLatency)/mux;
 a.CalculateLatency(1e20,r,r);
 const double nativeRead8=a.readLatency*request::input_bits,nativeWrite=a.writeLatency,prechargeRecovery=a.precharger.readLatency/mux;
 serializer.address.clkFreq=clk;serializer.address.CalculateLatency(1e20,1);
 const double serialization=2*request::input_bits*(serializer.combinational_s+serializer.address.readLatency);
 const double correctionTime=3*clockPeriod;
 const double stream=input.readLatency+2*(nativeRead8+correction.operand.readLatency)+correctionTime+serialization; // input bank held across both passes; only one external acceptance
 const double resident=nativeWrite+writeData.readLatency+batches*encodeInv+prechargeRecovery;

 auto o=[](const char*k,double v){std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";};
 o("technology_nm",param->technode);o("resolved_read_mux",a.numColMuxed);o("resolved_adc_bits",log2(a.sarADC.levelOutput));o("write_port_bits",a.numWriteCellPerOperationNeuro);
 o("mux_driver_scale",request::mux_driver_scale);o("clock_reservation_factor",request::clock_reservation_factor);
 o("mux_tg_n_m",a.mux.widthTgN);o("mux_tg_p_m",a.mux.widthTgP);o("mux_tg_res_ohm",a.mux.resTg);
 o("mux_load_n_F",a.mux.capTgGateN*(cols/mux));o("mux_load_p_F",a.mux.capTgGateP*(cols/mux));o("mux_driver_n_m",a.muxDecoder.widthDriverInvN);o("mux_driver_p_m",a.muxDecoder.widthDriverInvP);o("mux_driver_input_F",a.muxDecoder.capDriverInvInput);o("mux_select_wire_R_ohm",a.muxDecoder.muxSelectWireRes);o("mux_select_wire_C_F",a.muxDecoder.muxSelectWireCap);o("mux_select_fanout",a.muxDecoder.muxSelectFanout);
 o("wire_resistance_ohm_per_m",param->unitLengthWireResistance);o("wire_rho_ohm_m",param->Rho);o("physical_row_length_m",a.lengthRow);o("physical_col_length_m",a.lengthCol);o("critical_comb_s",clockPeriod/request::clock_reservation_factor);o("wl_tg_n_m",a.wlSwitchMatrix.widthTgN);o("wl_tg_p_m",a.wlSwitchMatrix.widthTgP);o("mux_decoder_area_m2",a.muxDecoder.area);o("input_acceptances",1);o("input_bits",param->numBitInput);o("weight_bits",param->numColPerSynapse);
 o("input_serialization_s",serialization);o("input_select_comb_s",serializer.combinational_s);o("input_select_address_capture_s",serializer.address.readLatency);o("input_selector_area_m2",serializer.area_m2);o("resolved_adc_count",a.sarADC.numCol);o("resolved_adc_levels",a.sarADC.levelOutput);o("weight_shift_units",a.shiftAddWeight.numUnit);o("input_shift_units",a.shiftAddInput.numUnit);o("input_selector_control_bits",serializer.address.numDff);o("input_selector_control_area_m2",serializer.address.area);o("temperature_K",ip.temperature);o("technology_feature_m",tech.featureSize);o("cell_geometry_feature_m",cell.featureSize);o("param_memcelltype",param->memcelltype);o("param_wire_width_nm",param->wireWidth);o("param_feature_m",param->featuresize);o("logical_K",rows);o("logical_N",n);o("stream_latency_s",stream);o("delta_s",stream);o("resident_s",resident);o("clock_period_s",clockPeriod);o("native_unsigned_8bit_s",nativeRead8);o("input_capture_per_pass_s",input.readLatency);o("pass1_hold_capture_s",correction.operand.readLatency);o("correction_s",correctionTime);o("correction_stage_capture_s",correction.stage1.readLatency);o("correction_adder_s",correction.adder_s);o("correction_inv_s",correctionInv);o("write_encode_inv_s",encodeInv);o("write_capture_all_s",writeData.readLatency);o("recovery_s",prechargeRecovery);o("integration_slot_s",cell.readPulseWidth);o("write_batches",batches);o("payload_BS",rows);o("payload_BR",rows*n);o("rho_Bps",rows/stream);o("tau_Bps",rows*n/resident);o("RI_star",resident/(n*stream));o("U_star",resident/stream);o("total_area_m2",a.area+input.area+writeData.area+correction.area_m2+serializer.area_m2+(writecols/8)*hinv*winv);o("correction_area_m2",correction.area_m2);o("correction_broadcast_s",correction.broadcast_s);o("correction_broadcast_wire_m",correction.broadcast_wire_m);o("physical_rows",a.numRow);o("physical_cols",a.numCol);o("rows",rows);o("cols",cols);o("read_per_bit_s",a.readLatency);o("read_8bits_s",a.readLatency*request::input_bits);o("write_all_s",a.writeLatency);o("wl_read_s",a.wlSwitchMatrix.readLatency);o("wl_write_s",a.wlSwitchMatrix.writeLatency);o("precharge_read_s",a.precharger.readLatency);o("precharge_write_s",a.precharger.writeLatency);o("write_driver_s",a.sramWriteDriver.writeLatency);o("adc_s",a.sarADC.readLatency);o("mux_s",a.mux.readLatency);o("muxdecoder_s",a.muxDecoder.readLatency);o("col_s",a.colDelay);o("weight_shift_s",a.shiftAddWeight.readLatency);o("input_shift_s",a.shiftAddInput.readLatency);o("caprow_F",a.capRow1);o("capcol_F",a.capCol);o("capaccess_F",a.capCellAccess);o("capcell_F",cell.capSRAMCell);o("raccess_ohm",a.resCellAccess);o("rrow_ohm",a.resRow);o("rcol_ohm",a.resCol);o("area_m2",a.area);o("vdd_V",tech.vdd);o("wl_dff_s",a.wlSwitchMatrix.dff.readLatency);
}

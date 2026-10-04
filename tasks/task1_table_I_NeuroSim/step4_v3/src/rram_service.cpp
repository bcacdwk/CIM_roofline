#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include <algorithm>
#include <map>
#include <string>
#include "SubArray.h"
#include "Param.h"
#include "LevelShifter.h"
#include "Comparator.h"
#define STEP4_TRAINING
#include "correction.h"
#include "input_serializer.h"
#include "rram_verify.h"
Param *param;
struct Config{int rows=256,cols=288,batch=32,levels=1024;double pulse=1e-8,activity=0,access=5000,wireScale=1;};
std::map<std::string,double> run(Config c,double hz){
 Param p;param=&p;p.technode=22;p.temp=300;p.clkFreq=hz;p.numBitInput=8;p.cellBit=1;p.numColPerSynapse=8;p.numRowSubArray=c.rows;p.numColSubArray=c.cols;p.wireWidth=32;p.featuresize=32e-9;p.unitLengthWireResistance=c.wireScale*4.51e-8/(32e-9*32e-9*1.9);
 InputParameter ip{};ip.temperature=300;ip.processNode=22;ip.transistorType=conventional;ip.deviceRoadmap=LSTP;Technology tech;tech.Initialize(22,LSTP,conventional);
 MemCell cell{};cell.memCellType=Type::RRAM;cell.accessType=CMOS_access;cell.resistanceOn=8000;cell.resistanceOff=24000;cell.resistanceAvg=16000;cell.resistanceAccess=c.access;cell.readVoltage=.5;cell.accessVoltage=1.1;cell.writeVoltage=1;cell.writePulseWidth=c.pulse;cell.readPulseWidth=(log2(c.levels)+1)*1e-9;cell.featureSize=32e-9;cell.widthInFeatureSize=8;cell.heightInFeatureSize=4;cell.maxNumLevelLTP=2;cell.maxNumLevelLTD=2;
 int groups=(c.cols+c.batch-1)/c.batch,batches=c.rows*groups,phases=2;
 SubArray s(ip,tech,cell);s.conventionalParallel=true;s.conventionalSequential=false;s.XNORparallelMode=false;s.XNORsequentialMode=false;s.BNNparallelMode=false;s.BNNsequentialMode=false;s.trainingEstimation=false;s.parallelBP=false;s.parallelWrite=false;s.FPGA=false;s.neuro=true;s.relaxArrayCellHeight=false;s.relaxArrayCellWidth=false;s.numColMuxed=9;s.numRowMuxedBP=1;s.numReadPulse=8;s.numReadPulseBP=1;s.numCellPerSynapse=8;s.avgWeightBit=1;s.levelOutput=c.levels;s.levelOutputBP=2;s.SARADC=true;s.currentMode=true;s.spikingMode=NONSPIKING;s.clkFreq=hz;s.activityRowRead=c.activity;s.activityRowWrite=1;s.activityColWrite=1;s.activityBPColRead=0;s.numReadCellPerOperationNeuro=c.cols;s.numReadCellPerOperationMemory=c.cols;s.numReadCellPerOperationFPGA=c.cols;s.numWriteCellPerOperationNeuro=c.batch;s.numWriteCellPerOperationMemory=c.batch;s.numWriteCellPerOperationFPGA=c.batch;s.maxNumWritePulse=1;s.numWritePulseAVG=1;s.totalNumWritePulse=phases*batches;s.layerNumber=0;
 s.Initialize(c.rows,c.cols,p.unitLengthWireResistance);s.CalculateArea();
 DFF input(ip,tech,cell),writeData(ip,tech,cell),ref(ip,tech,cell),difference(ip,tech,cell);input.Initialize(c.rows*8,hz);writeData.Initialize(c.cols,hz);ref.Initialize(32*(int)log2(c.levels),hz);difference.Initialize(32*(int)log2(c.levels),hz);
 for(auto*d:{&input,&writeData,&ref,&difference}){d->CalculateArea(s.height,0,NONE);d->CalculateLatency(1e20,1);}
 Adder baseline(ip,tech,cell);baseline.Initialize((int)log2(c.levels),32);baseline.CalculateArea(s.height,0,NONE);baseline.CalculateLatency(1e20,difference.capTgDrain,1);
 RramVerify verify(ip,tech,cell,(int)log2(c.levels),hz,s.height,s.width);
 InputSerializer serializer(ip,tech,cell,c.rows,hz,s.height,p.unitLengthWireResistance,s.wlNewSwitchMatrix.dff.capTgDrain);
 OffsetCorrection correction(ip,tech,cell,31,hz,s.height,s.width,p.unitLengthWireResistance);
 double hi,wi,ci,co,wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn;CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hi,&wi);CalculateGateCapacitance(INV,1,wn,wp,hi,tech,&ci,&co);double inv=horowitz(CalculateOnResistance(wn,NMOS,300,tech)*(co+2*baseline.capNandInput),0,1e20,nullptr);
 double encodeInv=horowitz(CalculateOnResistance(wn,NMOS,300,tech)*(co+writeData.capTgDrain),0,1e20,nullptr);
 serializer.address.CalculateLatency(1e20,1);verify.control.CalculateLatency(1e20,1);verify.status.CalculateLatency(1e20,1);
 correction.operand.CalculateLatency(1e20,1);correction.stage1.CalculateLatency(1e20,1);correction.stage2.CalculateLatency(1e20,1);correction.output.CalculateLatency(1e20,1);
 LevelShifter wlls(ip,tech,cell),slls(ip,tech,cell);wlls.Initialize(c.rows,c.activity,hz);slls.Initialize(c.cols,1,hz);wlls.CalculateArea(s.height,0,NONE);slls.CalculateArea(0,s.width,NONE);
 double wlLSload=(s.wlNewSwitchMatrix.capTgGateN+s.wlNewSwitchMatrix.capTgGateP)*3;
 double slLSload=(s.slSwitchMatrix.capTgGateN+s.slSwitchMatrix.capTgGateP)*2;
 wlls.CalculateLatency(1e20,wlLSload,0,1,2*phases*batches);slls.CalculateLatency(1e20,slLSload,0,0,2*phases*batches);
 std::vector<double> r(c.cols,(cell.resMemCellOff+s.resRow+s.resCol)/std::max(1.,c.rows*c.activity)),rr(c.rows,cell.resMemCellOff/c.cols);s.CalculateLatency(1e20,r,rr);
 std::map<std::string,double> o;auto out=[&](const char*k,double v){o[k]=v;};
 double nativeRead=s.readLatency*8,readADC=s.readLatencyADC*8,readAccum=s.readLatencyAccum*8,readOther=s.readLatencyOther*8;
 double nativeWrite=s.writeLatency,writePulse=s.writeLatencyArray;
 // Native SubArray counts SET+RESET enables; same physical switches are also used for release.
 double writeEnable=std::max(s.wlNewSwitchMatrix.writeLatency,s.slSwitchMatrix.writeLatency);
 double writeRelease=writeEnable; // explicit identical RC + DFF boundary at each pulse deassertion
 double wlRC=(s.wlNewSwitchMatrix.readLatency-.5/hz); // one read selection
 double slRC=(s.slSwitchMatrix.writeLatency/(phases*batches)-.5/hz);
 double baselineComb=inv+baseline.readLatency;
 double maxComb=std::max({correction.combinational_s,baselineComb,s.shiftAddWeight.adder.readLatency,s.shiftAddInput.adder.readLatency,verify.combinational_s});
 double baselineExtra=8*(8*(baselineComb+difference.readLatency)+ref.readLatency); // eight data bits + ref capture, all input planes; no free baseline correction
 double unsignedService=nativeRead+baselineExtra+8*wlls.readLatency;
 // Same array, switches, MUX and ADC, one-hot read; existing accumulators are bypassed for verify raw codes.
 s.numReadPulse=1;s.activityRowRead=1.0/c.rows;std::fill(r.begin(),r.end(),cell.resMemCellOff+s.resRow+s.resCol);s.CalculateLatency(1e20,r,rr);
 double verifyOne=s.readLatency-s.readLatencyAccum+9*(verify.selector_s+verify.control.readLatency+verify.combinational_s+verify.status.readLatency)+wlls.readLatency;
 double verifyTotal=phases*c.rows*verifyOne;
 double matrixDataCapture=batches*(writeData.readLatency+encodeInv); // one complete 288-bit expected-row buffer per row from 32-bit port, held through RESET/SET and both verifies
 double levels=2*phases*batches*std::max(wlls.writeLatency/(2*phases*batches),slls.writeLatency/(2*phases*batches));
 double serialization=16*(serializer.combinational_s+serializer.address.readLatency);
 double stream=input.readLatency+2*(unsignedService+correction.operand.readLatency)+serialization+3/hz;
 double resident=writePulse+writeEnable+writeRelease+levels+matrixDataCapture+verifyTotal;
 out("operand_capture_per_pass_s",correction.operand.readLatency);out("input_serialization_s",serialization);out("input_selector_comb_s",serializer.combinational_s);out("verify_target_select_s",verify.selector_s);out("verify_compare_s",verify.compare_s);out("verify_encode_s",verify.encode_s);out("verify_mismatch_OR_s",verify.or_s);out("verify_comparator_count",64);out("adc_baseline_right_shift",log2(c.levels)-9);out("verify_expected_HRS_code",c.levels/512);out("verify_expected_LRS_code",c.levels/256);out("baseline_ref_capture_s",ref.readLatency);out("baseline_difference_capture_s",difference.readLatency);out("resident_port_capture_s",writeData.readLatency);out("logical_k",c.rows);out("logical_n",31);out("physical_rows",c.rows);out("physical_cols",c.cols);out("physical_cells",c.rows*c.cols);out("adc_count",s.sarADC.numCol);out("resolved_adc_levels",s.sarADC.levelOutput);out("weight_shift_units",s.shiftAddWeight.numUnit);out("input_shift_units",s.shiftAddInput.numUnit);out("input_selector_control_bits",serializer.address.numDff);out("input_selector_control_area_m2",serializer.address.area);out("param_memcelltype",p.memcelltype);out("param_wire_width_nm",p.wireWidth);out("technology_feature_m",tech.featureSize);out("temperature_K",ip.temperature);out("mux",9);out("adc_bits",log2(c.levels));out("write_batch_cols",c.batch);out("write_batches_per_direction",batches);out("write_pulses",phases*batches);out("write_transitions",2*phases*batches);out("verify_rows",phases*c.rows);out("expected_row_buffer_bits",c.cols);out("resident_port_bits",c.batch);out("resident_input_beats",batches);out("verify_adc_rounds",phases*c.rows*9);
 out("cell_height_F",cell.heightInFeatureSize);out("cell_width_F",cell.widthInFeatureSize);out("vdd_v",tech.vdd);out("access_voltage_v",cell.accessVoltage);out("write_voltage_v",cell.writeVoltage);out("access_width_f",cell.widthAccessCMOS);out("access_resistance_ohm",cell.resCellAccess);out("r_on_ohm",cell.resMemCellOn);out("r_off_ohm",cell.resMemCellOff);out("cap_col_f",s.capCol);out("cap_row_f",s.capRow2);out("res_col_ohm",s.resCol);out("res_row_ohm",s.resRow);out("wire_resistance_ohm_per_m",p.unitLengthWireResistance);out("length_row_m",s.lengthRow);out("length_col_m",s.lengthCol);
 out("max_combinational_s",maxComb);out("clock_period_s",1/hz);out("read_activity",c.activity);out("wl_logic_s",wlRC);out("sl_logic_s",slRC);out("mux_logic_s",(s.mux.readLatency+s.muxDecoder.readLatency)/9);out("correction_logic_s",correction.combinational_s);out("native_read_8bit_s",nativeRead);out("native_read_adc_s",readADC);out("native_read_accum_s",readAccum);out("native_read_other_s",readOther);out("hrs_subtract_s",baselineExtra);out("baseline_combinational_s",baselineComb);out("read_levelshift_s",8*wlls.readLatency);out("unsigned_8bit_service_s",unsignedService);out("signed_correction_s",3/hz);out("stream_input_capture_s",input.readLatency);out("stream_single_s",stream);out("delta_s",stream);out("native_write_s",nativeWrite);out("write_pulse_s",writePulse);out("write_enable_s",writeEnable);out("write_release_s",writeRelease);out("write_levelshift_s",levels);out("write_data_capture_s",matrixDataCapture);out("verify_one_row_s",verifyOne);out("verify_total_s",verifyTotal);out("resident_s",resident);out("rho_Bps",c.rows/stream);out("tau_Bps",(c.rows*31.)/resident);out("ri_star",resident/(31*stream));out("u_star",resident/stream);out("area_native_m2",s.area);out("area_added_m2",input.area+writeData.area+ref.area+difference.area+baseline.area+verify.area_m2+serializer.area_m2+correction.area_m2+wlls.area+slls.area+32*log2(c.levels)*hi*wi);
 return o;
}
int main(int argc,char**argv){Config c;for(int i=1;i+1<argc;i+=2){std::string k=argv[i];double v=std::stod(argv[i+1]);if(k=="--rows")c.rows=v;else if(k=="--batch")c.batch=v;else if(k=="--pulse")c.pulse=v;else if(k=="--activity")c.activity=v;else if(k=="--access")c.access=v;else if(k=="--wire-scale")c.wireScale=v;else if(k=="--levels")c.levels=v;else return 2;}if(c.activity==0)c.activity=1.0/c.rows;Config clockConfig=c;clockConfig.activity=1.0/c.rows;auto first=run(clockConfig,1e9);double hz=1/(2*first.at("max_combinational_s"));auto o=run(c,hz);std::cout<<std::setprecision(17);for(const auto &[k,v]:o){if(!std::isfinite(v)||v<0)return 3;std::cout<<k<<"="<<v<<"\n";}}

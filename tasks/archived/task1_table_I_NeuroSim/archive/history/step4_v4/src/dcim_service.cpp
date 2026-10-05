#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <new>
#include <vector>
#include "Param.h"
#include "SubArray.h"
#include "ProcessingUnit.h"
#include "correction.h"
#include "input_serializer.h"
#include "request.h"
Param *param;
void emit(const char*k,double v){std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
int main(int argc,char**argv){
 double wireScale=request::wire_resistance_scale;
 double accessScale=request::access_width_scale;
 int writeGroups=request::write_groups_parallel;
 double activity=request::read_activity;
 if((writeGroups!=1&&writeGroups!=2&&writeGroups!=4)||wireScale<=0||accessScale<=0)return 2;
 void* storage=std::calloc(1,sizeof(Param)); param=new(storage)Param();
 param->readVoltage=request::read_voltage_v;param->writeVoltage=request::write_voltage_v; // request owns SRAM rail identity, native eNVM table is inapplicable
 param->numBitInput=request::input_bits;param->numColPerSynapse=request::weight_bits;param->numRowPerSynapse=1;
 param->toggle_enforce=0;param->realtime_toggle=0;param->synchronous=true;
 param->Metal0_unitwireresis*=wireScale;param->Metal1_unitwireresis*=wireScale;
 param->widthAccessCMOS*=accessScale;
 InputParameter ip{};Technology tech{};MemCell cell{};SubArray*s=nullptr;
 ProcessingUnitInitialize(s,ip,tech,cell,1,1,1,1);
 s->activityRowRead=activity;s->activityRowWrite=1;s->activityColWrite=1;
 s->drivecapin=0; s->drivecapout=0;param->drivecapin=0;
 s->CalculateLatency(1e20,std::vector<double>(256,1e5),true);
 double core=s->readLatency;
 s->CalculateLatency(1e20,std::vector<double>(256,1e5),false);
 double serviceCycles=request::input_bits*s->readLatency;
 s->shiftAddInput.adder.CalculateLatency(1e20,s->shiftAddInput.dff.capTgDrain,1);
 double shadd=s->shiftAddInput.adder.readLatency;
 OffsetCorrection corr(ip,tech,cell,31,1e9,s->height,s->width,param->Metal0_unitwireresis);
 DFF inReg(ip,tech,cell),writeReg(ip,tech,cell);
 inReg.Initialize(request::logical_K*request::input_bits,1e9);writeReg.Initialize(64*writeGroups,1e9);
 inReg.CalculateArea(s->height,0,NONE);writeReg.CalculateArea(s->height,0,NONE);
 // Pass FSM phase selects A/C or B/D operand bank; other bank clock held.
 // Merge output zero-extends to 25 bits and captures DIRECTLY into corr.operand.
 Adder merge(ip,tech,cell);merge.Initialize(24,32,1e9);merge.CalculateArea(s->height,0,NONE);merge.CalculateLatency(1e20,corr.operand.capTgDrain,1);
 InputSerializer serializer(ip,tech,cell,256,1e9,s->height,param->Metal0_unitwireresis,s->wlSwitchMatrix.dff.capTgDrain,true);
 double inputSelectComb=serializer.combinational_s;
 double criticalComb=std::max(std::max(core,shadd),std::max(merge.readLatency,std::max(corr.combinational_s,inputSelectComb)));
 double period=request::clock_reservation_factor*criticalComb;
 // DCIM native memory peripherals consist of four numCol/4 groups.
 // All 256 storage bits per row, independent of compute nibble precision.
 double writeCapCol=s->capCol+s->capCellAccess*256;
 double writeCapRow=s->capRow1+2*CalculateGateCap(cell.widthAccessCMOS*tech.featureSize,tech)*256;
 s->wlDecoder.CalculateLatency(1e20,writeCapRow,0,s->resRow,256,0,1);
 s->precharger.CalculateLatency(1e20,writeCapCol,0,1);
 s->sramWriteDriver.CalculateLatency(1e20,writeCapCol,s->resCol,1);
 // The stored Qbar node also drives one native product NOR gate.
 cell.capSRAMCell+=param->capNORInput;
 double rp=(CalculateOnResistance(cell.widthSRAMCellNMOS*tech.featureSize,NMOS,ip.temperature,tech)+CalculateOnResistance(cell.widthSRAMCellPMOS*tech.featureSize,PMOS,ip.temperature,tech))/2;
 double gm=(CalculateTransconductance(cell.widthSRAMCellNMOS*tech.featureSize,NMOS,tech)+CalculateTransconductance(cell.widthSRAMCellPMOS*tech.featureSize,PMOS,tech))/2;
 double flip=horowitz(rp*cell.capSRAMCell,1/(rp*gm),1e20,nullptr);
 // Ready supplies, deterministic overwrite incl unchanged/reference cells.
 // One capture edge then bitline-drive, row-select, cell flip, deselect, restore.
 double ci,co,hi,wi;
 double wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn;
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hi,&wi);
 CalculateGateCapacitance(INV,1,wn,wp,hi,tech,&ci,&co);
 double ri=CalculateOnResistance(wn,NMOS,ip.temperature,tech),gmi=CalculateTransconductance(wn,NMOS,tech);
 double encode=horowitz(ri*(co+s->sramWriteDriver.capInvInput),1/(ri*gmi),1e20,nullptr);
 double writeAnalog=2*s->wlDecoder.writeLatency+s->precharger.writeLatency+s->sramWriteDriver.writeLatency+flip+encode;
 double writeBeat=period*(1+std::ceil(writeAnalog/period));
 int beats=256*(4/writeGroups);
 double stream=(1+2*(1+serviceCycles+1)+3)*period;
 // Sync branch DFF outputs are cycles. Explicitly execute at derived frequency.
 DFF* registers[]={&inReg,&writeReg,&corr.operand,&corr.stage1,&corr.stage2,&corr.output,&s->dff,&s->shiftAddInput.dff,&s->wlSwitchMatrix.dff,&serializer.address};
 for(DFF*d:registers){d->clkFreq=1/period;d->CalculateLatency(1e20,1);}
 emit("input_selector_control_bits",serializer.address.numDff);emit("input_selector_control_area_m2",serializer.address.area);emit("native_write_driver_columns_per_group",s->sramWriteDriver.numCol);emit("dff_capture_return_cycles",inReg.readLatency);
 emit("input_complement_for_NOR",1);emit("input_polarity_inv_s",serializer.polarity_inv_s);emit("write_cell_node_cap_f",cell.capSRAMCell);emit("native_product_NOR_input_cap_f",param->capNORInput);emit("input_select_fill_cycles_per_pass",1);emit("input_select_comb_s",inputSelectComb);emit("input_mux_s",serializer.mux.readLatency);emit("input_select_decoder_s",serializer.decoder.readLatency);
 emit("input_bits",param->numBitInput);emit("weight_bits",param->numColPerSynapse);emit("logical_K",s->numRow);emit("logical_N",s->numCol/param->numColPerSynapse-1);emit("physical_rows",s->numRow);emit("physical_cols",s->numCol);
 emit("physical_bits",65536);emit("native_tree_count",s->numCol/param->parallel_weightprecision);emit("native_tree_bits",param->parallel_weightprecision);emit("native_tree_rows",s->numRow);
 emit("clock_period_s",period);emit("native_bit_core_s",core);emit("native_unsigned_cycles",serviceCycles);
 emit("native_tree_s",param->addertree_delay);emit("native_nor_s",param->NOR_delay);emit("native_wl_s",param->WL_delay);
 emit("native_shiftadd_comb_s",shadd);emit("nibble_merge_s",merge.readLatency);emit("merge_direct_operand_capture",1);emit("correction_comb_s",corr.combinational_s);
 emit("correction_broadcast_s",corr.broadcast_s);emit("input_capture_s",period);emit("correction_s",3*period);
 emit("stream_latency_s",stream);emit("delta_s",stream);emit("resident_s",beats*writeBeat);
 emit("write_groups_parallel",writeGroups);emit("write_port_bits",64*writeGroups);emit("write_beats",beats);emit("write_beat_s",writeBeat);
 emit("write_analog_s",writeAnalog);emit("write_busy_cycles",std::ceil(writeAnalog/period));emit("write_capture_s",period);emit("write_decoder_one_edge_s",s->wlDecoder.writeLatency);emit("write_precharge_s",s->precharger.writeLatency);
 emit("write_driver_s",s->sramWriteDriver.writeLatency);emit("write_cell_flip_s",flip);emit("write_encode_s",encode);
 emit("write_cap_col_f",writeCapCol);emit("write_cap_row_f",writeCapRow);emit("wire_cap_col_f",s->capCol);emit("cell_cap_access_f",s->capCellAccess);
 emit("array_area_m2",s->area);emit("area_m2",s->area+corr.area_m2+merge.area+inReg.area+writeReg.area+serializer.area_m2+32*hi*wi);
 emit("read_voltage_v",cell.readVoltage);emit("write_voltage_v",cell.writeVoltage);emit("vdd_v",tech.vdd);emit("technology_nm",param->technode);emit("temperature_k",ip.temperature);emit("metal0_ohm_per_m",param->Metal0_unitwireresis);
 emit("alpha",param->alpha);emit("beta",param->beta);emit("wire_width_nm",param->wireWidth);emit("cell_width_F",cell.widthInFeatureSize);emit("cell_height_F",cell.heightInFeatureSize);emit("row_length_m",s->lengthRow);emit("col_length_m",s->lengthCol);emit("width_access_f",cell.widthAccessCMOS);
 emit("row_read_activity",activity);emit("validated",param->validated);emit("wire_scale",wireScale);

 emit("clock_reservation_factor",request::clock_reservation_factor);emit("critical_comb_s",criticalComb);emit("clock_reserved_s",period-criticalComb);
 emit("stream_cycles",stream/period);emit("resident_cycles",beats*writeBeat/period);emit("write_analog_over_period",writeAnalog/period);
 emit("metal1_ohm_per_m",param->Metal1_unitwireresis);emit("wire_temp_factor",1+0.00451*std::abs(param->temp-300));
 emit("row_wire_ohm",s->resRow);emit("col_wire_ohm",s->resCol);emit("array_height_m",s->height);emit("array_width_m",s->width);
 emit("wl_tg_n_m",s->wlSwitchMatrix.widthTgN);emit("wl_tg_p_m",s->wlSwitchMatrix.widthTgP);emit("wl_tg_res_ohm",s->wlSwitchMatrix.resTg);
 emit("selector_tg_n_m",serializer.mux.widthTgN);emit("selector_tg_p_m",serializer.mux.widthTgP);
 emit("write_decoder_inv_n_m",s->wlDecoder.widthInvN);emit("write_decoder_driver_n_m",s->wlDecoder.widthDriverInvN);
 emit("sram_pull_n_F",cell.widthSRAMCellNMOS);emit("sram_pull_p_F",cell.widthSRAMCellPMOS);emit("sram_access_ohm",s->resCellAccess);
 emit("native_accumulator_bits",s->shiftAddInput.numDff);emit("native_accumulator_adder_bits",s->shiftAddInput.numAdderBit);emit("native_tree_register_bits",s->dff.numDff);
 emit("reset_fill_cycles_per_pass",1);emit("a_bank_hold_during_b_pass",1);emit("all8slots_second_pass_retained",1);
 return !(std::isfinite(stream)&&stream>0&&std::isfinite(beats*writeBeat)&&writeBeat>0);
}

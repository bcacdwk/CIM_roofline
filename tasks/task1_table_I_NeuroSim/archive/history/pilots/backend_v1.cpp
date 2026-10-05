// Step 3 adapter. Links locked NeuroSim primitives; no upstream formula edits.
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include "Param.h"
#include "SarADC.h"
#include "Adder.h"
#include "AdderTree.h"
#include "DFF.h"
#include "formula.h"
#include "constant.h"
#include "request.h"
Param *param=nullptr;
static void emit(const std::string& k,double v){std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
struct Gates {
 const Technology &t; double ci,co,ni,no,wn,wp,wire,rwire;
 Gates(const Technology &tech,double length,double resistance):t(tech){
  wn=MIN_NMOS_SIZE*t.featureSize;wp=t.pnSizeRatio*wn;
  CalculateGateCapacitance(INV,1,wn,wp,t.featureSize*MAX_TRANSISTOR_HEIGHT,t,&ci,&co);
  CalculateGateCapacitance(NAND,2,2*wn,wp,t.featureSize*MAX_TRANSISTOR_HEIGHT,t,&ni,&no);
  wire=length*0.2e-15; rwire=resistance*length*1e-6;
 }
 double inv(double load,double &ramp){
  double rn=CalculateOnResistance(wn,NMOS,300,t),rp=CalculateOnResistance(wp,PMOS,300,t);
  double res=fmax(rn,rp),gm=CalculateTransconductance(rn>=rp?wn:wp,rn>=rp?NMOS:PMOS,t);
  return horowitz(res*(co+load+wire)+rwire*(wire/2+load),1/(res*gm),ramp,&ramp);
 }
 // NAND2 fanin: series NMOS, sized 2x to recover unit pull-down resistance.
 double nand2(double load,double &ramp){
  
  double rn=2*CalculateOnResistance(2*wn,NMOS,300,t),rp=CalculateOnResistance(wp,PMOS,300,t);
  double res=fmax(rn,rp),gm=CalculateTransconductance(rn>=rp?2*wn:wp,rn>=rp?NMOS:PMOS,t);
  return horowitz(res*(no+load+wire)+rwire*(wire/2+load),1/(res*gm),ramp,&ramp);
 }
 double chain(int n,double load,double &ramp){double d=0;for(int i=0;i<n;++i)d+=nand2(i==n-1?load:3*ni,ramp);return d;}
 // Logical balanced INV distribution, at most four sinks per driven net.
 double distribute(int sinks,double sinkcap,double &ramp){
  int depth=0;for(int n=sinks;n>1;n=(n+3)/4)++depth;
  double d=0;for(int i=0;i<depth;++i)d+=inv(4*(i==depth-1?sinkcap:ci),ramp);return d;
 }
};
int main(int argc,char**argv){
 if(argc!=4)return 2;double hz=atof(argv[1]),wire_um=atof(argv[2]);int adc_bits=atoi(argv[3]);
 param=new Param();
 // Constructor primaries specialized by backend.py; only main-owned precision/mode fields below.
 param->synapseBit=8;param->numBitInput=8;param->numColPerSynapse=8;param->numRowPerSynapse=1;
 param->clkFreq=hz;param->synchronous=false;param->pipeline=false;param->SARADC=ADC_COUNT>0;
 param->levelOutput=1<<adc_bits;param->dumcolshared=param->levelOutput;
 InputParameter ip{};ip.processNode=param->technode;ip.temperature=param->temp;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
 Technology tech;tech.Initialize(ip.processNode,LSTP,conventional);MemCell cell{};
 cell.memCellType=IS_RRAM?Type::RRAM:Type::SRAM;cell.processNode=NATIVE_NODE;
 cell.readVoltage=NATIVE_READ_V;cell.resistanceOn=NATIVE_RON;cell.resistanceOff=NATIVE_ROFF;
 cell.resistanceAvg=(NATIVE_RON+NATIVE_ROFF)/2;cell.readPulseWidth=NATIVE_READ_NS*1e-9;
 Gates g(tech,wire_um,param->unitLengthWireResistance);
 DFF input(ip,tech,cell),output(ip,tech,cell),controller(ip,tech,cell),encoded(ip,tech,cell),mask(ip,tech,cell);
 input.Initialize(INPUT_BITS,hz);input.CalculateArea(0,0,NONE);
 output.Initialize(OUTPUT_BITS,hz);output.CalculateArea(0,0,NONE);
 controller.Initialize(32,hz);controller.CalculateArea(0,0,NONE);
 // Existing native SRAM capture remains opaque; only explicit RRAM buffers are instantiated here.
 double area=input.area+output.area+controller.area;
 if(IS_RRAM){encoded.Initialize(128,hz);encoded.CalculateArea(0,0,NONE);mask.Initialize(128,hz);mask.CalculateArea(0,0,NONE);area+=encoded.area+mask.area;}
 double dcap=3*output.capTgDrain+output.capInvInput;
 double ramp=1e20; double setup=g.inv(dcap,ramp);setup+=g.inv(g.ci,ramp);
 ramp=1e20;double cq=g.inv(g.ci,ramp);cq+=g.inv(3*g.ni,ramp);double q_ramp=ramp;
 emit("source_q_ramp",q_ramp);emit("setup_s",setup);emit("clock_q_s",cq);emit("dff_data_cap_F",dcap);emit("gate_input_cap_F",g.ci);emit("wire_cap_F",g.wire);emit("wire_res_ohm",g.rwire);
 // 10-bit control counter -> 4 NAND decode levels -> explicit fanout4 tree -> capture mux.
 Adder ctr(ip,tech,cell);ctr.Initialize(10,1,hz);ctr.CalculateArea(0,0,NONE);ramp=q_ramp;
 double control=cq;ctr.CalculateLatency(ramp,4*g.ni+g.wire,1);control+=ctr.readLatency;ramp=ctr.rampOutput;
 control+=g.chain(4,g.ci,ramp);control+=g.distribute(128,g.ni,ramp);control+=g.chain(2,dcap,ramp);control+=setup;emit("control_path_s",control);area+=ctr.area;
 ramp=q_ramp;double io=cq+g.chain(6,dcap,ramp)+setup;emit("io_path_s",io);
 ramp=q_ramp;double clear=cq;clear+=g.chain(4,g.ci,ramp);clear+=g.distribute(OUTPUT_BITS,g.ni,ramp);clear+=g.chain(2,dcap,ramp);clear+=setup;emit("accumulator_clear_path_s",clear);
 emit("nand_input_cap_F",g.ni);emit("control_fanout_max",4);emit("control_target_sinks",128);emit("clear_target_sinks",OUTPUT_BITS);
 if(IS_RRAM){ramp=q_ramp;double done=cq;done+=g.chain(4,3*g.ni,ramp);done+=g.chain(14,dcap,ramp);done+=setup;emit("verify_done_path_s",done);}
 if(ADC_COUNT){
  SarADC sar(ip,tech,cell);sar.Initialize(ADC_COUNT,1<<adc_bits,hz,ACTIVE_TERMS);sar.CalculateUnitArea();sar.CalculateArea(0,1e-4,NONE);sar.CalculateLatency(1);
  emit("sar_active_terms",sar.numReadCellPerOperationNeuro);emit("sar_installed_count",sar.numCol);emit("sar_levelOutput",sar.levelOutput);emit("sar_s",sar.readLatency);emit("sar_area_m2",sar.area);area+=sar.area;
  // Conservative explicit ripple tree: no intermediate register, full carry-width at every level.
  Adder neg(ip,tech,cell),a0(ip,tech,cell),a1(ip,tech,cell),a2(ip,tech,cell),sign(ip,tech,cell),acc(ip,tech,cell);
  neg.Initialize(18,16,hz);a0.Initialize(18,64,hz);a1.Initialize(19,32,hz);a2.Initialize(20,16,hz);sign.Initialize(23,16,hz);acc.Initialize(23,16,hz);
  for(Adder*a:{&neg,&a0,&a1,&a2,&sign,&acc}){a->CalculateArea(0,0,NONE);area+=a->area;}
  ramp=q_ramp;double d=cq;d+=g.inv(neg.capNandInput*2+g.wire,ramp);
  neg.CalculateLatency(ramp,a0.capNandInput*4+g.wire,1);d+=neg.readLatency;ramp=neg.rampOutput;emit("weight_negate_s",d-cq);
  double tree=0;
  Adder* as[]={&a0,&a1,&a2};double loads[]={4*a1.capNandInput+g.wire,4*a2.capNandInput+g.wire,8*g.ni+g.wire};
  for(int i=0;i<3;++i){as[i]->CalculateLatency(ramp,loads[i],1);tree+=as[i]->readLatency;ramp=as[i]->rampOutput;emit("tree_level"+std::to_string(i)+"_s",as[i]->readLatency);}
  d+=tree;
  // 3-stage binary 8:1 barrel shift mux: two NAND data levels each. Fixed plane weights/normalization are wires.
  double shift=g.chain(6,4*g.ni,ramp);d+=shift;emit("shift_mux_s",shift);
  // XOR (three NAND levels) + increment for sign input bit, followed by accumulator and destination enable mux.
  double sg=g.chain(3,2*sign.capNandInput+g.wire,ramp);sign.CalculateLatency(ramp,2*acc.capNandInput+g.wire,1);sg+=sign.readLatency;ramp=sign.rampOutput;d+=sg;emit("input_sign_s",sg);
  acc.CalculateLatency(ramp,3*g.ni+g.wire,1);d+=acc.readLatency;ramp=acc.rampOutput;emit("accumulator_s",acc.readLatency);
  double enable=g.chain(2,dcap,ramp);d+=enable+setup;emit("output_enable_s",enable);emit("reconstruct_path_s",d);
  // Bank feedback is explicitly selected from existing N*23 containers into16 lanes.
  ramp=q_ramp;double feedback=cq+g.chain(IS_RRAM?4:6,2*acc.capNandInput+g.wire,ramp);
  acc.CalculateLatency(ramp,3*g.ni+g.wire,1);feedback+=acc.readLatency;ramp=acc.rampOutput;
  feedback+=g.chain(2,dcap,ramp)+setup;emit("bank_feedback_path_s",feedback);
  // Controller-selected shift/sign path, up to16*23 bit mux control sinks.
  ramp=q_ramp;double select=cq;select+=g.chain(4,g.ci,ramp);select+=g.distribute(16*23,g.ni,ramp);
  select+=g.chain(6,4*g.ni,ramp);select+=g.chain(3,2*sign.capNandInput+g.wire,ramp);
  sign.CalculateLatency(ramp,2*acc.capNandInput+g.wire,1);select+=sign.readLatency;ramp=sign.rampOutput;
  acc.CalculateLatency(ramp,3*g.ni+g.wire,1);select+=acc.readLatency;ramp=acc.rampOutput;
  select+=g.chain(2,dcap,ramp)+setup;emit("control_select_path_s",select);
  emit("bank_select_fanin",IS_RRAM?4:8);emit("sign_extension_max_nand_loads",8);
  AdderTree reference(ip,tech,cell);reference.Initialize(8,18,16,hz);reference.CalculateArea(0,1e-4,NONE);reference.CalculateLatency(1,8,dcap);
  emit("diagnostic_upstream_tree_s",reference.readLatency);emit("full_width_tree_s",tree);
 }
 param->synchronous=true;input.CalculateLatency(1e20,1);output.CalculateLatency(1e20,1);controller.CalculateLatency(1e20,1);
 emit("dff_cycle",input.readLatency);emit("output_cycle",output.readLatency);emit("controller_cycle",controller.readLatency);
 emit("partial_module_area_m2",area);emit("clkFreq_hz",hz);emit("technode_nm",param->technode);emit("temperature_K",param->temp);emit("vdd_V",tech.vdd);emit("tech_featureSize_m",tech.featureSize);
 emit("param_featuresize_m",param->featuresize);emit("param_rows",param->numRowSubArray);emit("param_cols",param->numColSubArray);emit("param_rowParallel",param->numRowParallel);emit("param_maxConductance_S",param->maxConductance);emit("param_minConductance_S",param->minConductance);
 // Unused MemCell numeric sentinels deliberately not emitted as physical parameters.
 emit("beta",param->beta);emit("gamma",param->gamma);emit("delta",param->delta);emit("alpha",param->alpha);emit("epsilon",param->epsilon);emit("zeta",param->zeta);
 return 0;
}

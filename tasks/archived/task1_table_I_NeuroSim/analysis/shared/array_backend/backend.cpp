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
#include "paths_dag.h"
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
  // Shared installed 16-lane topology: 4x9,2x11,1x15 + fused23bit accumulator.
  Adder a9(ip,tech,cell),a11(ip,tech,cell),a15(ip,tech,cell),acc(ip,tech,cell);
  a9.Initialize(9,64,hz);a11.Initialize(11,32,hz);a15.Initialize(15,16,hz);acc.Initialize(23,16,hz);
  for(Adder*a:{&a9,&a11,&a15,&acc}){a->CalculateArea(0,0,NONE);area+=a->area;}
  BitDAG graph(tech,acc,g.wire,g.rwire,300);
  WeightedReconstruct arithmetic(graph,0,1e20,0,1e20,0,1e20,IS_RRAM?6:8);
  for(int i:arithmetic.out)graph.nodes[i].cap+=3*g.ni;
  // Each source is timed with its actual DAG load. Counts have independent
  // SAR result outputs; ibit is distributed to all sixteen lanes. Existing
  // accumulator bank data AND held group select have a real mux path.
  double max_source=0,control_source=0,bank_source=0;
  for(auto &node:graph.nodes)if(node.a<0 && !node.constant){
   double slope=1e20;double arrival=g.inv(g.ci,slope);
   if(node.name.find("ibit_")==0){
    arrival+=g.inv(g.ci,slope);
    int sinks=std::max(1,(int)std::ceil(16*node.cap/acc.capNandInput));
    arrival+=g.distribute(sinks,acc.capNandInput,slope);control_source=std::max(control_source,arrival);
   }else if(node.name.find("old_acc_")==0){
    arrival+=g.inv(3*g.ni,slope);arrival+=g.chain(IS_RRAM?4:6,node.cap,slope);
    double sel_slope=q_ramp;double sel=cq;sel+=g.chain(4,g.ci,sel_slope);
    sel+=g.distribute(16*23,g.ni,sel_slope);sel+=g.chain(IS_RRAM?4:6,node.cap,sel_slope);
    // Preserve both possible bank-data/control arrival/slew labels.
    node.arcs={{arrival,slope},{sel,sel_slope}};bank_source=std::max(bank_source,std::max(arrival,sel));
   }else{arrival+=g.inv(node.cap,slope);max_source=std::max(max_source,arrival);}
   node.at=arrival;node.ramp=slope;
  }
  graph.evaluate();double full=0,bit_data=0;int labels=0;
  for(int i:arithmetic.out)for(auto x:graph.nodes[i].arcs){double slope=x.ramp;double d=x.at;
   bit_data=std::max(bit_data,d);d+=g.chain(2,dcap,slope);d+=setup;full=std::max(full,d);++labels;}
  emit("reconstruct_path_s",full);emit("bit_DAG_before_capture_mux_s",bit_data);
  emit("SAR_source_driver_max_s",max_source);emit("ibit_distribution_max_s",control_source);emit("bank_source_max_s",bank_source);
  emit("arrival_labels_at_outputs",labels);emit("DAG_nodes_per_lane",graph.nodes.size());
  // E1 phase toggle can only control the E2 write-enable. This remains ONE cycle.
  double phase_ramp=q_ramp;double phase=cq;phase+=g.chain(4,g.ci,phase_ramp);
  phase+=g.distribute(16*23,g.ni,phase_ramp);phase+=g.chain(2,dcap,phase_ramp);phase+=setup;
  emit("capture_enable_path_s",phase);
  emit("normalized_count_bits",IS_RRAM?6:8);emit("installed_partial_sum_bits",15);
  emit("semantic_partial_sum_bits",IS_RRAM?13:15);emit("accumulator_bits",23);
  emit("adder9_count",a9.numAdder);emit("adder11_count",a11.numAdder);emit("adder15_count",a15.numAdder);emit("adder23_count",acc.numAdder);
  // Same gate graph executes deterministic arithmetic: test every stage,
  // conditional add/sub and container wrap, not an unrelated sum-only oracle.
  int coeff[]={1,2,4,8,16,32,64,-128};int fixtures=0;
  for(int pattern=0;pattern<12;++pattern)for(int ib=0;ib<8;++ib)for(int old:{0,100,-100,1000000,-1000000}){
   int c[8],w=0;for(int k=0;k<8;++k){int m=ACTIVE_TERMS;
    c[k]=pattern==0?0:pattern==1?m:pattern==2?(k==7?m:0):pattern==3?(k==7?0:m):(pattern*37+k*53)%(m+1);
    graph.set(arithmetic.c[k],c[k]);w+=coeff[k]*c[k];}
   graph.set(arithmetic.ibit,ib);graph.set(arithmetic.acc,old);graph.evaluate();
   int p0=c[0]+2*c[1],p1=c[2]+2*c[3],p2=c[4]+2*c[5],p3=c[6]-2*c[7];
   assert(graph.value(arithmetic.p0)==p0 && graph.value(arithmetic.p1)==p1 && graph.value(arithmetic.p2)==p2 && graph.value(arithmetic.p3,true)==p3);
   assert(graph.value(arithmetic.l0)==p0+4*p1 && graph.value(arithmetic.l1,true)==p2+4*p3 && graph.value(arithmetic.w,true)==w);
   int64_t expected=(old+coeff[ib]*w)&((1<<23)-1);if(expected&(1<<22))expected-=1<<23;
   assert(graph.value(arithmetic.out,true)==expected);++fixtures;
  }
  emit("same_graph_arithmetic_fixtures",fixtures);
  // Public module methods still provide initialized electrical dimensions,
  // area and independent timing diagnostics; scalar timings do not get summed.
  acc.CalculateLatency(q_ramp,3*g.ni+g.wire,1);emit("diagnostic_Adder23_s",acc.readLatency);
  AdderTree reference(ip,tech,cell);reference.Initialize(8,15,16,hz);reference.CalculateArea(0,1e-4,NONE);reference.CalculateLatency(1,8,dcap);
  emit("diagnostic_AdderTree15_s",reference.readLatency);

 }
 param->synchronous=true;input.CalculateLatency(1e20,1);output.CalculateLatency(1e20,1);controller.CalculateLatency(1e20,1);
 emit("dff_cycle",input.readLatency);emit("output_cycle",output.readLatency);emit("controller_cycle",controller.readLatency);
 emit("partial_module_area_m2",area);emit("clkFreq_hz",hz);emit("technode_nm",param->technode);emit("temperature_K",param->temp);emit("vdd_V",tech.vdd);emit("tech_featureSize_m",tech.featureSize);
 emit("param_featuresize_m",param->featuresize);emit("param_rows",param->numRowSubArray);emit("param_cols",param->numColSubArray);emit("param_rowParallel",param->numRowParallel);emit("param_maxConductance_S",param->maxConductance);emit("param_minConductance_S",param->minConductance);
 // Unused MemCell numeric sentinels deliberately not emitted as physical parameters.
 emit("beta",param->beta);emit("gamma",param->gamma);emit("delta",param->delta);emit("alpha",param->alpha);emit("epsilon",param->epsilon);emit("zeta",param->zeta);
 return 0;
}

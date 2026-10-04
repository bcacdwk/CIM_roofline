// Step 2 interface probe; links unmodified locked V1.4 implementation.
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
#include "Param.h"
#include "ProcessingUnit.h"
#include "SubArray.h"
#include "SarADC.h"
#include "DFF.h"
#include "ShiftAdd.h"
#include "AdderTree.h"
#include "constant.h"
Param *param = nullptr;
static void n(const char* k,double v){std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
// Restricted, audited initializer: node/roadmap/temp/material never change here.
// Every permitted overwrite and its dependent fields are assigned before any module exists.
static void configure(double hz,int planes,int bits,int mux,int rowsParallel){
 param=new Param();
 param->numRowSubArray=16; param->numColSubArray=16;
 param->numRowParallel=rowsParallel; param->numColMuxed=mux;
 param->numBitInput=bits; param->synapseBit=planes; param->cellBit=1;
 param->numColPerSynapse=planes; param->numRowPerSynapse=1;
 param->SARADC=true; param->levelOutput=256; param->dumcolshared=256;
 param->clkFreq=hz; param->pipeline=false; param->novelMapping=false;
 // No change to constructor-derived geometry/conductance/access/wire fields.
}
int main(int argc,char**argv){
 if(argc<2)return 2; std::string mode=argv[1];
 if(mode=="mutation"){
  param=new Param();n("before.technode",param->technode);n("before.featuresize_m",param->featuresize);
  n("before.maxConductance_S",param->maxConductance);n("before.numRowParallel",param->numRowParallel);
  param->technode=65;param->resistanceOn=50000;param->numRowSubArray=16;
  n("after.technode",param->technode);n("after.featuresize_m",param->featuresize);
  n("after.resistanceOn_ohm",param->resistanceOn);n("after.maxConductance_S",param->maxConductance);
  n("after.numRowSubArray",param->numRowSubArray);n("after.numRowParallel",param->numRowParallel);return 0;
 }
 if(mode=="sar" || mode=="dff"){
  if(argc!=7)return 2;
  int node=atoi(argv[2]), count=atoi(argv[3]), nr=atoi(argv[4]), setting=atoi(argv[5]); double hz=atof(argv[6]);
  param=new Param(); InputParameter ip{};ip.processNode=node;ip.temperature=300;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
  Technology tech;tech.Initialize(node,LSTP,conventional);MemCell cell{};
  n("node_nm",ip.processNode);n("clkFreq_hz",hz);n("count",count);n("numRead",nr);
  if(mode=="sar"){
   SarADC adc(ip,tech,cell);adc.Initialize(count,1<<setting,hz,count);adc.CalculateUnitArea();adc.CalculateArea(0,1e-4,NONE);adc.CalculateLatency(nr);
   n("bits",setting);n("levelOutput",adc.levelOutput);n("readLatency_s",adc.readLatency);n("area_m2",adc.area);
  }else{
   param->synchronous=setting;DFF dff(ip,tech,cell);dff.Initialize(count,hz);dff.CalculateArea(0,0,NONE);dff.CalculateLatency(1e20,nr);
   n("synchronous",setting);n("readLatency_raw",dff.readLatency);n("capTgDrain_F",dff.capTgDrain);n("area_m2",dff.area);
  }return 0;
 }
 if(mode=="digital"){
  if(argc!=4)return 2;int bits=atoi(argv[2]);double hz=atof(argv[3]);configure(hz,1,1,2,8);
  InputParameter ip{};ip.processNode=22;ip.temperature=300;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
  Technology tech;tech.Initialize(22,LSTP,conventional);MemCell cell{};cell.readPulseWidth=param->readPulseWidth;
  DFF output(ip,tech,cell);output.Initialize(bits+5,hz);output.CalculateArea(0,0,NONE);
  AdderTree tree(ip,tech,cell);tree.Initialize(32,bits,1,hz);tree.CalculateArea(0,1e-4,NONE);
  param->synchronous=false;tree.CalculateLatency(1,32,output.capTgDrain);double physical=tree.readLatency;
  param->synchronous=true;tree.CalculateLatency(1,32,output.capTgDrain);output.CalculateLatency(1e20,1);
  n("fan_in",32);n("input_bits",bits);n("output_bits",bits+5);n("clkFreq_hz",hz);n("tree_physical_s",physical);n("tree_cycles",tree.readLatency);n("output_dff_cycles",output.readLatency);n("output_capLoad_F",output.capTgDrain);n("area_m2",tree.area+output.area);
  return 0;
 }
 if(mode=="subarray"){
  if(argc!=9)return 2;bool sync=atoi(argv[2]);double hz=atof(argv[3]);int planes=atoi(argv[4]),bits=atoi(argv[5]),mux=atoi(argv[6]),parallel=atoi(argv[7]),active=atoi(argv[8]);
  if(16%parallel || 16%mux || 16%planes || mux%planes || active<0 || active>16)return 3;
  configure(hz,planes,bits,mux,parallel);param->synchronous=sync;
  InputParameter ip{};Technology tech;MemCell cell{};SubArray *sa=nullptr;
  ProcessingUnitInitialize(sa,ip,tech,cell,1,1,1,1); // includes Initialize then CalculateArea
  sa->activityRowRead=active/16.;sa->activityColRead=1;sa->activityRowWrite=1;sa->activityColWrite=1;
  std::vector<std::vector<double>> input(16,std::vector<double>(1,0));
  for(int i=0;i<active;++i)input[i][0]=1;
  double activity=0;auto iv=GetInputVector(input,0,&activity);
  std::vector<std::vector<double>> weight(16,std::vector<double>(16,param->maxConductance));
  auto resist=GetColumnResistance(iv,weight,cell,true,sa->resCellAccess);
  sa->CalculateLatency(1e20,resist,true);double critical=sa->readLatency;
  sa->CalculateLatency(1e20,resist,false);
  n("param.technode_nm",param->technode);n("tech.featureSize_m",tech.featureSize);n("param.featuresize_m",param->featuresize);
  n("param.resistanceOn_ohm",param->resistanceOn);n("param.maxConductance_S",param->maxConductance);n("cell.resistanceOn_ohm",cell.resistanceOn);
  n("param.numRowSubArray",param->numRowSubArray);n("param.numRowParallel",param->numRowParallel);n("param.parallelRead",param->parallelRead);
  n("param.levelOutput",param->levelOutput);n("param.dumcolshared",param->dumcolshared);n("param.numColPerSynapse",param->numColPerSynapse);
  n("param.numBitInput",param->numBitInput);n("param.clkFreq_hz",param->clkFreq);n("subarray.clkFreq_hz",sa->clkFreq);
  n("synchronous",sync);n("numRow",sa->numRow);n("numCol",sa->numCol);n("numAdd",sa->numAdd);n("mux_rounds",sa->numColMuxed);
  n("sar_lanes",sa->sarADC.numCol);n("activity",activity);n("columnResistance_ohm",resist.at(0));
  n("area_m2",sa->area);n("capCol_F",sa->capCol);n("dff_capTgDrain_F",sa->dff.capTgDrain);
  n("critical_s",critical);n("readLatency_raw",sa->readLatency);n("readLatencyADC_raw",sa->readLatencyADC);
  n("readLatencyAccum_raw",sa->readLatencyAccum);n("readLatencyOther_raw",sa->readLatencyOther);n("writeLatency_raw",sa->writeLatency);
  n("adder_delay_s",sa->adder.readLatency);n("weight_shift_adder_delay_s",sa->shiftAddWeight.adder.readLatency);n("input_shift_adder_delay_s",sa->shiftAddInput.adder.readLatency);
  n("wl_driver_physical_s",sa->wlSwitchMatrix.readLatency);n("wl_driver_write_mixed_raw",sa->wlSwitchMatrix.writeLatency);n("wl_driver_dff_raw",sa->wlSwitchMatrix.dff.readLatency);n("mux_physical_s",sa->mux.readLatency+sa->muxDecoder.readLatency);n("precharge_physical_s",sa->precharger.readLatency);
  n("beta",param->beta);n("alpha",param->alpha);n("gamma",param->gamma);n("delta",param->delta);n("epsilon",param->epsilon);n("zeta",param->zeta);
  return 0;
 }return 2;
}

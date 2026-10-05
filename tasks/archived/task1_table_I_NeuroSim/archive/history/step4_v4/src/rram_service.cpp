#include <iostream>
#include <iomanip>
#include <vector>
#include <memory>
#include <cmath>
#include <algorithm>
#include <map>
#include <string>
#include "SubArray.h"
#include "Param.h"
#include "LevelShifter.h"
#include "Comparator.h"
#include "AdderTree.h"
#include "Bus.h"
#include "request.h"
#define STEP4_TRAINING
#include "correction.h"
#include "input_serializer.h"
#include "rram_verify.h"
Param *param;

// Minimal terminal wrapper: two native formula inverters preserving polarity. The first
// stage sees the actual resized second-stage Cin; the second drives every stated
// D/enable pin plus an RC route with conservative far-end lumping of pin C. This is not a gate graph.
struct PinDrive {
 double latency_s=0,area_m2=0,input_cap_F=0,sink_cap_F=0,wire_cap_F=0,wire_res_ohm=0;
 double second_n_m=0,second_p_m=0,wire_m=0,size=0;
 void Initialize(const InputParameter&i,const Technology&t,int bits,double sinks,double length,double wireR){
  double wn=MIN_NMOS_SIZE*t.featureSize,wp=t.pnSizeRatio*wn,hi,wi,ci,co,h2,w2,ci2,co2;
  CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&hi,&wi);
  CalculateGateCapacitance(INV,1,wn,wp,hi,t,&ci,&co);
  sink_cap_F=sinks;wire_m=length;wire_cap_F=length*0.2e-15/1e-6;wire_res_ohm=length*wireR;
  size=std::max(1.,std::ceil(std::sqrt((sink_cap_F+wire_cap_F)/ci)));
  second_n_m=wn*size;second_p_m=wp*size;
  CalculateGateArea(INV,1,second_n_m,second_p_m,MAX_TRANSISTOR_HEIGHT*t.featureSize,t,&h2,&w2);
  CalculateGateCapacitance(INV,1,second_n_m,second_p_m,h2,t,&ci2,&co2);
  auto edge=[&](bool rising){
   int firstType=rising?NMOS:PMOS,lastType=rising?PMOS:NMOS;
   double firstW=rising?wn:wp,lastW=rising?second_p_m:second_n_m;
   double r1=CalculateOnResistance(firstW,firstType,i.temperature,t),g1=CalculateTransconductance(firstW,firstType,t);
   double r2=CalculateOnResistance(lastW,lastType,i.temperature,t),g2=CalculateTransconductance(lastW,lastType,t);
   return horowitz(r1*(co+ci2),1/(r1*g1),1e20,nullptr)
    +horowitz(r2*(co2+sink_cap_F+wire_cap_F)+wire_res_ohm*(wire_cap_F/2+sink_cap_F),1/(r2*g2),1e20,nullptr);
  };
  latency_s=std::max(edge(false),edge(true));input_cap_F=ci;area_m2=bits*(hi*wi+h2*w2);
 }
};

struct Config {
 int rows=request::bank_rows,banks=request::banks,cols=request::physical_cols,mux=request::read_mux,levels=1<<request::adc_bits,batch=request::write_parallel_bits,designRows=request::mux_design_rows,driverScale=request::mux_driver_scale,attempts=request::program_attempts;
 double temp=request::temperature_K,ron=request::resistance_on_ohm,roff=request::resistance_off_ohm,access=request::access_resistance_ohm,vr=request::read_voltage_V,vw=request::write_voltage_V,va=request::access_voltage_V,pulse=request::write_pulse_s,wireScale=request::wire_resistance_scale,activity=request::read_activity;
};
// Equal banks share one evaluated native unit model; replication is explicit in resources,
// area and operations. Bank compute occurs in parallel; a single public32bit write port
// visits all16banks. No replica can perform an uncounted or independent write.
std::map<std::string,double> run(Config c,double hz){
 Param p;param=&p;p.clkFreq=hz;p.numBitInput=request::input_bits;p.numColPerSynapse=request::weight_bits;
 p.unitLengthWireResistance*=c.wireScale; // authoritative constructor already propagated native temperature coefficient
 InputParameter ip{};ip.temperature=p.temp;ip.processNode=p.technode;ip.transistorType=conventional;ip.deviceRoadmap=LSTP;
 Technology tech;tech.Initialize(p.technode,LSTP,conventional);
 MemCell cell{};cell.memCellType=Type::RRAM;cell.accessType=CMOS_access;cell.resistanceOn=c.ron;cell.resistanceOff=c.roff;cell.resistanceAvg=(c.ron+c.roff)/2;cell.resistanceAccess=c.access;cell.readVoltage=c.vr;cell.accessVoltage=c.va;cell.writeVoltage=c.vw;cell.writePulseWidth=c.pulse;cell.readPulseWidth=(log2(c.levels)+1)*1e-9;cell.featureSize=p.featuresize;cell.widthInFeatureSize=p.widthInFeatureSize1T1R;cell.heightInFeatureSize=p.heightInFeatureSize1T1R;cell.maxNumLevelLTP=2;cell.maxNumLevelLTD=2;
 const int lanes=32,bits=(int)log2(c.levels),passes=2,groups=(c.cols+c.batch-1)/c.batch,batches=c.rows*groups,phases=2,logicalK=c.rows*c.banks;
 SubArray s(ip,tech,cell);s.conventionalParallel=true;s.conventionalSequential=false;s.XNORparallelMode=false;s.XNORsequentialMode=false;s.BNNparallelMode=false;s.BNNsequentialMode=false;s.trainingEstimation=false;s.parallelBP=false;s.parallelWrite=false;s.FPGA=false;s.neuro=true;s.relaxArrayCellHeight=false;s.relaxArrayCellWidth=false;s.numColMuxed=c.mux;s.numRowMuxedBP=1;s.numReadPulse=request::input_bits;s.numReadPulseBP=1;s.numCellPerSynapse=request::weight_bits;s.avgWeightBit=1;s.levelOutput=c.levels;s.levelOutputBP=2;s.SARADC=true;s.currentMode=true;s.spikingMode=NONSPIKING;s.clkFreq=hz;s.activityRowRead=c.activity?c.activity:1./c.rows;s.activityRowWrite=1;s.activityColWrite=1;s.activityBPColRead=0;s.numReadCellPerOperationNeuro=c.cols;s.numReadCellPerOperationMemory=c.cols;s.numReadCellPerOperationFPGA=c.cols;s.numWriteCellPerOperationNeuro=c.batch;s.numWriteCellPerOperationMemory=c.batch;s.numWriteCellPerOperationFPGA=c.batch;s.maxNumWritePulse=1;s.numWritePulseAVG=1;s.totalNumWritePulse=phases*batches;s.layerNumber=0;
 s.Initialize(c.rows,c.cols,p.unitLengthWireResistance);
 // Preserve the V3 mux conductance target in every smaller bank. Actual native TG
 // widths/caps/area/latency are recalculated before CalculateArea.
 s.mux.initialized=false;s.mux.Initialize(lanes,c.mux,cell.resMemCellOn/c.designRows,false);
 s.muxDecoder.widthDriverInvN=2*MIN_NMOS_SIZE*tech.featureSize*c.driverScale;s.muxDecoder.widthDriverInvP=2*tech.pnSizeRatio*MIN_NMOS_SIZE*tech.featureSize*c.driverScale;
 s.CalculateArea();s.muxDecoder.muxSelectWireRes=s.mux.width*p.unitLengthWireResistance;s.muxDecoder.muxSelectWireCap=s.mux.width*0.2e-15/1e-6;s.muxDecoder.muxSelectFanout=lanes;
 DFF input(ip,tech,cell),writeData(ip,tech,cell),ref(ip,tech,cell),difference(ip,tech,cell);
 input.Initialize(c.rows*request::input_bits,hz);writeData.Initialize(c.cols,hz);ref.Initialize(lanes*bits,hz);difference.Initialize(lanes*bits,hz);
 for(auto*d:{&input,&writeData,&ref,&difference}){d->CalculateArea(s.height,0,NONE);d->CalculateLatency(1e20,1);}
 Adder baseline(ip,tech,cell);baseline.Initialize(bits,lanes);baseline.CalculateArea(s.height,0,NONE);baseline.CalculateLatency(1e20,difference.capTgDrain,1);
 double adcGain=16/(c.vr*(1/cell.resMemCellOn-1/cell.resMemCellOff));
 int codeH=std::lround(adcGain*c.vr/cell.resMemCellOff),codeL=std::lround(adcGain*c.vr/cell.resMemCellOn);
 RramVerify verify(ip,tech,cell,bits,hz,s.height,s.width,p.unitLengthWireResistance,codeH,codeL);
 InputSerializer serializer(ip,tech,cell,c.rows,hz,s.height,p.unitLengthWireResistance,s.wlNewSwitchMatrix.dff.capTgDrain);
 // Fixed two-attempt-per-phase controller; requested attempts is conditional service demand,
 // not a probability. Expected row remains retained. Failure at the bound publishes invalid.
 DFF retryCounter(ip,tech,cell);Adder retryIncrement(ip,tech,cell);
 retryCounter.Initialize(2,hz);retryCounter.CalculateArea(s.height,0,NONE);retryCounter.CalculateLatency(1e20,1);
 retryIncrement.Initialize(2,1);retryIncrement.CalculateArea(s.height,0,NONE);retryIncrement.CalculateLatency(1e20,retryCounter.capTgDrain,1);
 double hi,wi,ci,co,wn=MIN_NMOS_SIZE*tech.featureSize,wp=tech.pnSizeRatio*wn;
 CalculateGateArea(INV,1,wn,wp,MAX_TRANSISTOR_HEIGHT*tech.featureSize,tech,&hi,&wi);CalculateGateCapacitance(INV,1,wn,wp,hi,tech,&ci,&co);
 double inv=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(co+2*baseline.capNandInput),0,1e20,nullptr);
 double encodeInv=horowitz(CalculateOnResistance(wn,NMOS,ip.temperature,tech)*(co+writeData.capTgDrain),0,1e20,nullptr);
 serializer.address.CalculateLatency(1e20,1);verify.control.CalculateLatency(1e20,1);verify.status.CalculateLatency(1e20,1);
 LevelShifter wlls(ip,tech,cell),slls(ip,tech,cell);wlls.Initialize(c.rows,s.activityRowRead,hz);slls.Initialize(c.cols,1,hz);wlls.CalculateArea(s.height,0,NONE);slls.CalculateArea(0,s.width,NONE);
 double wlLSload=(s.wlNewSwitchMatrix.capTgGateN+s.wlNewSwitchMatrix.capTgGateP)*3,slLSload=(s.slSwitchMatrix.capTgGateN+s.slSwitchMatrix.capTgGateP)*2;
 wlls.CalculateLatency(1e20,wlLSload,0,1,2*phases*batches);slls.CalculateLatency(1e20,slLSload,0,0,2*phases*batches);
 // Bank output selection is real hardware: one24bit word per shared external32bit-port beat.
 Mux wordMux(ip,tech,cell);RowDecoder wordDecoder(ip,tech,cell);DFF wordAddress(ip,tech,cell);Adder wordCounter(ip,tech,cell);
 wordMux.Initialize(24,lanes,0,true);wordMux.CalculateArea(0,s.height,NONE);
 wordDecoder.Initialize(REGULAR_ROW,5,true,false);wordDecoder.CalculateArea(s.height,0,NONE);
 wordDecoder.muxSelectWireCap=wordMux.width*0.2e-15/1e-6;wordDecoder.muxSelectWireRes=wordMux.width*p.unitLengthWireResistance;wordDecoder.muxSelectFanout=24;
 wordDecoder.CalculateLatency(1e20,24*wordMux.capTgGateN,24*wordMux.capTgGateP,1,0);
 wordAddress.Initialize(5,hz);wordAddress.CalculateArea(s.height,0,NONE);wordAddress.CalculateLatency(1e20,1);
 wordCounter.Initialize(5,1);wordCounter.CalculateArea(s.height,0,NONE);wordCounter.CalculateLatency(1e20,wordAddress.capTgDrain,1);
 const double bankEnableCap=c.cols*(writeData.capTgGateN+writeData.capTgGateP)+(c.rows+5)*(s.wlNewSwitchMatrix.dff.capTgGateN+s.wlNewSwitchMatrix.dff.capTgGateP);
 PinDrive writeSinkDrive,bankEnableDrive;
 // Every public data lane reaches9 target words in each of16banks. Local buffers
 // isolate the16banks; all16 physical wrappers are counted, no clock-enable C discount.
 writeSinkDrive.Initialize(ip,tech,c.batch,groups*writeData.capTgDrain,writeData.height,p.unitLengthWireResistance);
 bankEnableDrive.Initialize(ip,tech,1,bankEnableCap,s.height,p.unitLengthWireResistance);
 const double localArea=s.area+input.area+writeData.area+ref.area+difference.area+baseline.area+verify.area_m2+serializer.area_m2+wlls.area+slls.area+lanes*bits*hi*wi+wordMux.area+wordDecoder.area+wordAddress.area+wordCounter.area+retryCounter.area+retryIncrement.area+writeSinkDrive.area_m2+bankEnableDrive.area_m2;
 const double bankH=s.height,bankW=std::max(s.width,localArea/bankH);
 // Explicit512x24 staging DFF array, addressed at input and parallel Q-wired to32trees.
 DFF stagingWord(ip,tech,cell),stagingAddress(ip,tech,cell);Adder stagingCounter(ip,tech,cell);RowDecoder stagingDecoder(ip,tech,cell);
 stagingWord.Initialize(24,hz);stagingWord.CalculateArea(0,0,NONE);stagingWord.CalculateLatency(1e20,1);
 stagingAddress.Initialize(9,hz);stagingAddress.CalculateArea(0,0,NONE);stagingAddress.CalculateLatency(1e20,1);
 stagingCounter.Initialize(9,1);stagingCounter.CalculateArea(0,0,NONE);stagingCounter.CalculateLatency(1e20,stagingAddress.capTgDrain,1);
 const int stagingWords=c.banks*lanes;
 stagingDecoder.Initialize(REGULAR_ROW,9,false,false);stagingDecoder.CalculateArea(stagingWord.height*stagingWords,0,NONE);
 const double stagingEnableCap=24*(stagingWord.capTgGateN+stagingWord.capTgGateP)+stagingWord.width*0.2e-15/1e-6;
 stagingDecoder.CalculateLatency(1e20,stagingEnableCap,0,1,0);
 PinDrive stagingDataDrive;
 stagingDataDrive.Initialize(ip,tech,24,stagingWords*stagingWord.capTgDrain,stagingWord.height*stagingWords,p.unitLengthWireResistance);
 const double stagingArea=stagingWords*stagingWord.area+stagingAddress.area+stagingCounter.area+stagingDecoder.area+stagingDataDrive.area_m2;
 DFF bankAddress(ip,tech,cell);bankAddress.Initialize(4,hz);bankAddress.CalculateArea(0,0,NONE);bankAddress.CalculateLatency(1e20,1);
 RowDecoder bankDecoder(ip,tech,cell),hubSelect(ip,tech,cell);Mux hubMux(ip,tech,cell);
 bankDecoder.Initialize(REGULAR_ROW,4,false,false);bankDecoder.CalculateArea(0,0,NONE);
 hubMux.Initialize(c.batch,c.banks,0,true);hubMux.CalculateArea(0,0,NONE);
 hubSelect.Initialize(REGULAR_ROW,4,true,false);hubSelect.CalculateArea(0,0,NONE);
 hubSelect.muxSelectWireCap=hubMux.width*0.2e-15/1e-6;hubSelect.muxSelectWireRes=hubMux.width*p.unitLengthWireResistance;hubSelect.muxSelectFanout=c.batch;
 hubSelect.CalculateLatency(1e20,c.batch*hubMux.capTgGateN,c.batch*hubMux.capTgGateP,1,0);
 hubMux.CalculateLatency(1e20,stagingDataDrive.input_cap_F+(c.banks-1)*hubMux.capTgDrain,1);
 AdderTree reduction(ip,tech,cell);reduction.Initialize(c.banks,24,lanes);
 // One-way repeated native links. Read:16 bank->hub point links plus hub16:1 mux.
 // Write:16 separately driven hub->bank branches carrying the same broadcast32bitword.
 // Data directions are physically distinct; only the external32bitport/transaction is shared.
 struct Links {std::unique_ptr<Bus> h,v;};
 std::vector<Links> readLinks,writeLinks,enableLinks;
 PinDrive writeRootDrive;
 std::unique_ptr<OffsetCorrection> correctionModel;
 double macroW=std::max(4*bankW,4*bankH),macroH=macroW;
 double readLinksArea=0,writeLinksArea=0,enableLinksArea=0,layoutArea=0,busArea=0;
 double readLinkTime=0,writeLinkTime=0,enableLinkTime=0,readLengthMax=0,gatherLenH=0,gatherLenV=0;
 int layoutIterations=0;
 auto makeSegment=[&](BusMode mode,int width,double length){
  auto q=std::make_unique<Bus>(ip,tech,cell);q->wireWidth=0;
  q->Initialize(mode,mode==HORIZONTAL?1:2,mode==HORIZONTAL?2:1,0,width,length,length);
  q->CalculateArea(1,false);q->CalculateLatency(1);return q;
 };
 auto recalcLayout=[&](){
  reduction.CalculateArea(0,macroW,NONE); // must precede every area sum, including the final geometry
  correctionModel=std::make_unique<OffsetCorrection>(ip,tech,cell,31,hz,macroH,macroW,p.unitLengthWireResistance,29);
  readLinks.clear();writeLinks.clear();enableLinks.clear();readLinksArea=writeLinksArea=enableLinksArea=0;readLinkTime=writeLinkTime=enableLinkTime=0;
  double rootLoad=0,rootSpan=0;
  for(int b=0;b<c.banks;++b){
   double dx=((b%4)+.5)*macroW/4,dy=((b/4)+.5)*macroH/4;
   Links r{makeSegment(HORIZONTAL,c.batch,dx),makeSegment(VERTICAL,c.batch,dy)};
   Links w{makeSegment(HORIZONTAL,c.batch,dx),makeSegment(VERTICAL,c.batch,dy)};
   Links e{makeSegment(HORIZONTAL,1,dx),makeSegment(VERTICAL,1,dy)};
   // Native Bus models a terminal repeater-input load. All actual next-stage inputs
   // below are no greater than that modeled load; large D arrays are behind PinDrive.
   if(r.v->capInvInput+1e-30<hubMux.capTgDrain || w.v->capInvInput+1e-30<writeSinkDrive.input_cap_F || e.v->capInvInput+1e-30<bankEnableDrive.input_cap_F)throw std::runtime_error("link terminal load exceeds native modeled load");
   readLinksArea+=r.h->area+r.v->area;writeLinksArea+=w.h->area+w.v->area;enableLinksArea+=e.h->area+e.v->area;
   readLinkTime=std::max(readLinkTime,r.h->readLatency+r.v->readLatency);writeLinkTime=std::max(writeLinkTime,w.h->readLatency+w.v->readLatency);enableLinkTime=std::max(enableLinkTime,e.h->readLatency+e.v->readLatency);
   rootLoad+=w.h->capInvInput;rootSpan+=w.h->wInv;
   if(dx+dy>readLengthMax){readLengthMax=dx+dy;gatherLenH=dx;gatherLenV=dy;}
   readLinks.push_back(std::move(r));writeLinks.push_back(std::move(w));enableLinks.push_back(std::move(e));
  }
  writeRootDrive.Initialize(ip,tech,c.batch,rootLoad,rootSpan,p.unitLengthWireResistance);
  busArea=readLinksArea+writeLinksArea+enableLinksArea+writeRootDrive.area_m2;
  layoutArea=c.banks*localArea+stagingArea+reduction.area+correctionModel->area_m2+bankAddress.area+bankDecoder.area+hubMux.area+hubSelect.area+busArea;
 };
 // Fixed near-square area containment rule for all scenarios, not a speed-selected layout.
 // Expand both dimensions together and recompute every geometry-dependent object.
 for(int it=0;it<100;++it){layoutIterations=it+1;recalcLayout();double next=std::max({4*bankW,4*bankH,std::sqrt(layoutArea)});
  if(next<=macroW*(1+1e-12)){break;}macroW=macroH=next*(1+1e-10);
 }
 recalcLayout(); // independent final object areas, widths and all directional routes
 if(layoutArea>macroW*macroH*(1+1e-12))throw std::runtime_error("actual final component sum exceeds square floorplan");
 auto& correction=*correctionModel;
 for(auto*d:{&correction.operand,&correction.stage1,&correction.stage2,&correction.output})d->CalculateLatency(1e20,1);
 reduction.CalculateLatency(1,c.banks,std::max(2*reduction.adder.capNandInput,correction.operand.capTgDrain));
 bankDecoder.CalculateLatency(1e20,enableLinks.front().h->capInvInput,0,1,0);
 wordMux.CalculateLatency(1e20,readLinks.front().h->capInvInput+31*wordMux.capTgDrain,1);
 const double writeRoute=writeRootDrive.latency_s+writeLinkTime+writeSinkDrive.latency_s;
 const double enableRoute=enableLinkTime+bankEnableDrive.latency_s;
 const double wordDataComb=wordDecoder.readLatency+wordMux.readLatency+readLinkTime+hubMux.readLatency+stagingDataDrive.latency_s;
 const double counterStep=std::max(wordCounter.readLatency+wordAddress.readLatency,stagingCounter.readLatency+stagingAddress.readLatency);
 const double gatherBeat=counterStep+std::max(wordDataComb,stagingDecoder.readLatency)+stagingWord.readLatency;
 const double bankSelect=bankAddress.readLatency+std::max(bankDecoder.readLatency+enableRoute,hubSelect.readLatency);
 const double gatherTime=stagingAddress.readLatency+c.banks*bankSelect+stagingWords*gatherBeat;
 const double gatherArea=readLinksArea+hubMux.area+hubSelect.area;
 std::vector<double> r(c.cols,(cell.resMemCellOff+s.resRow+s.resCol)/std::max(1.,c.rows*s.activityRowRead)),rr(c.rows,cell.resMemCellOff/c.cols);cell.readPulseWidth=(log2(c.levels)+1)*1e-9+log(2*c.levels)*s.capCol*(*std::max_element(r.begin(),r.end()));s.CalculateLatency(1e20,r,rr);
 double nativeRead=s.readLatency*8,readADC=s.readLatencyADC*8,readAccum=s.readLatencyAccum*8,readOther=s.readLatencyOther*8;
 double nativeWrite=s.writeLatency,writePulse=s.writeLatencyArray,writeEnable=std::max(s.wlNewSwitchMatrix.writeLatency,s.slSwitchMatrix.writeLatency),writeRelease=writeEnable;
 double wlRC=s.wlNewSwitchMatrix.readLatency-.5/hz,slRC=s.slSwitchMatrix.writeLatency/(phases*batches)-.5/hz;
 double baselineComb=inv+baseline.readLatency;
 double maxComb=std::max({correction.combinational_s,baselineComb,s.shiftAddWeight.adder.readLatency,s.shiftAddInput.adder.readLatency,verify.combinational_s,verify.phase_combinational_s,retryIncrement.readLatency,reduction.readLatency,wordDataComb,hubSelect.readLatency,stagingDecoder.readLatency,wordCounter.readLatency,stagingCounter.readLatency,bankDecoder.readLatency+enableRoute,writeRoute+encodeInv,serializer.combinational_s});
 double baselineExtra=8*(8*(baselineComb+difference.readLatency)+ref.readLatency);
 double serialization=8*(serializer.combinational_s+serializer.address.readLatency);
 double bankUnsigned=nativeRead+baselineExtra+8*wlls.readLatency+serialization;
 // Onehot row verify reuses the same bank's installed ADC/mux and compare circuit.
 s.numReadPulse=1;s.activityRowRead=1./c.rows;std::fill(r.begin(),r.end(),cell.resMemCellOff+s.resRow+s.resCol);cell.readPulseWidth=(log2(c.levels)+1)*1e-9+log(2*c.levels)*s.capCol*(*std::max_element(r.begin(),r.end()));s.CalculateLatency(1e20,r,rr);
 double verifyOne=s.readLatency-s.readLatencyAccum+c.mux*(verify.selector_s+verify.control.readLatency+verify.combinational_s+verify.status.readLatency)+wlls.readLatency+verify.clear_s+verify.phase_finalize_s;
 double verifyTotal=phases*c.rows*verifyOne;
 double matrixDataCapture=batches*(writeData.readLatency+encodeInv);
 double levels=2*phases*batches*std::max(wlls.writeLatency/(2*phases*batches),slls.writeLatency/(2*phases*batches));
 // Complete final zero-mask transition, using the same actual WL switch and LS.
 double neutralReturn=s.wlNewSwitchMatrix.readLatency+wlls.readLatency;
 double retryControl=phases*c.rows*(retryCounter.readLatency+(c.attempts-1)*(retryIncrement.readLatency+retryCounter.readLatency));
 double bankProgram=(writePulse+writeEnable+writeRelease+levels+verifyTotal)*c.attempts+retryControl;
 double resident=c.banks*(matrixDataCapture+bankProgram+neutralReturn+bankAddress.readLatency+bankDecoder.readLatency+enableRoute)+c.banks*batches*writeRoute;
 // One parallel bank pass, native gather+tree, then global A/C or B/D operand capture.
 // Both full8bit passes are reserved. Read banks all release their WL masks together.
 double perPass=bankUnsigned+neutralReturn+gatherTime+reduction.readLatency+correction.operand.readLatency;
 double stream=input.readLatency+passes*perPass+3/hz;
 std::map<std::string,double> o;auto out=[&](const char*k,double v){o[k]=v;};
 double gainCodes=16/(c.vr*(1/cell.resMemCellOn-1/cell.resMemCellOff));
 out("technology_nm",p.technode);out("input_bits",p.numBitInput);out("weight_bits",p.numColPerSynapse);out("clock_reservation_factor",request::clock_reservation_factor);out("output_bits",29);out("fractional_output_bits",4);out("total_adc_count",c.banks*s.sarADC.numCol);out("wire_rho_ohm_m",p.Rho);out("temperature_K",ip.temperature);out("logical_k",logicalK);out("logical_n",31);out("physical_rows",logicalK);out("physical_cols",c.cols);out("bank_rows",c.rows);out("banks",c.banks);out("physical_cells",logicalK*c.cols);out("adc_count",c.banks*s.sarADC.numCol);out("adc_bits",bits);out("resolved_adc_levels",s.sarADC.levelOutput);out("weight_shift_units",c.banks*s.shiftAddWeight.numUnit);out("input_shift_units",c.banks*s.shiftAddInput.numUnit);out("bank_native_result_bits",s.shiftAddInput.numDff/lanes);out("bank_gather_bits_per_lane",24);out("reduction_output_bits",28);out("correction_bits",29);out("output_fractional_bits",4);out("bank_held_unsigned_max",c.rows*255.*255.*16);out("global_unsigned_max",logicalK*255.*255.*16);out("nominal_adc_codes_per_count",16);out("nominal_adc_gain_codes_per_A",gainCodes);out("verify_combinational_s",verify.combinational_s);out("verify_phase_combinational_s",verify.phase_combinational_s);out("verify_sticky_s",verify.sticky_s);out("verify_expected_HRS_code",codeH);out("verify_expected_LRS_code",codeL);out("verify_encode_direct_pins",verify.direct_code_pins);out("verify_encode_inverse_pins",verify.inverted_code_pins);out("verify_HRS_low_current_A",(codeH-.5)/gainCodes);out("verify_HRS_high_current_A",(codeH+.5)/gainCodes);out("verify_LRS_low_current_A",(codeL-.5)/gainCodes);out("verify_LRS_high_current_A",(codeL+.5)/gainCodes);out("adc_baseline_right_shift",0);out("adc_calibration_offset_codes",0);
 out("write_batch_cols",c.batch);out("resident_port_bits",c.batch);out("resident_input_beats",c.banks*batches);out("write_batches_per_direction",c.banks*batches);out("write_pulses",c.attempts*phases*c.banks*batches);out("write_transitions",2*c.attempts*phases*c.banks*batches);out("verify_rows",c.attempts*phases*logicalK);out("verify_adc_rounds",c.attempts*phases*logicalK*c.mux);out("program_attempts",c.attempts);out("program_attempt_limit",2);out("verify_sticky_lane_bits",32);out("verify_phase_result_bits",1);out("verify_clear_s_per_phase",verify.clear_s);out("verify_finalize_s_per_phase",verify.phase_finalize_s);out("retry_control_total_s",c.banks*retryControl);out("verify_comparator_count",c.banks*64);out("expected_row_buffer_bits",c.banks*c.cols);out("stream_bit_rounds_per_bank",16);out("mux_rounds_per_bit",c.mux);out("global_reduction_passes",2);out("global_reduction_trees",lanes);out("global_reduction_levels",reduction.numStage);out("gather_bus_segments",2*c.banks);out("write_bus_segments",2*c.banks);out("bank_enable_bus_segments",2*c.banks);out("read_point_links",c.banks);out("write_broadcast_point_branches",c.banks);out("bus_direction_count",2);out("hub_mux_lanes",c.batch);out("hub_mux_inputs",c.banks);out("hub_mux_s",hubMux.readLatency);out("read_link_worst_s",readLinkTime);out("write_link_worst_s",writeLinkTime);out("staging_data_drive_s",stagingDataDrive.latency_s);out("staging_data_drive_cap_F",stagingDataDrive.sink_cap_F);out("staging_data_drive_wire_m",stagingDataDrive.wire_m);out("staging_data_drive_wire_res_ohm",stagingDataDrive.wire_res_ohm);out("staging_data_drive_wire_cap_F",stagingDataDrive.wire_cap_F);out("staging_data_drive_width_n_m",stagingDataDrive.second_n_m);out("staging_D_pin_cap_F",stagingWord.capTgDrain);out("staging_data_loads_per_bit",stagingWords);out("write_data_D_pin_cap_F",writeData.capTgDrain);out("write_data_loads_per_bit_per_bank",groups);out("write_data_total_loads_per_port_bit",groups*c.banks);out("write_endpoint_buffers",c.banks*c.batch);out("write_sink_drive_s",writeSinkDrive.latency_s);out("write_sink_drive_cap_F",writeSinkDrive.sink_cap_F);out("write_sink_drive_wire_m",writeSinkDrive.wire_m);out("write_sink_drive_width_n_m",writeSinkDrive.second_n_m);out("write_root_drive_s",writeRootDrive.latency_s);out("write_root_drive_cap_F",writeRootDrive.sink_cap_F);out("write_root_drive_wire_m",writeRootDrive.wire_m);out("link_input_cap_F",readLinks.front().h->capInvInput);out("link_terminal_load_budget_F",readLinks.front().v->capInvInput);out("hub_mux_channel_input_cap_F",hubMux.capTgDrain);out("layout_iterations",layoutIterations);out("shared_bus_width_bits",c.batch);out("gather_beats_per_pass",stagingWords);out("staging_bits",stagingWords*24);out("staging_words",stagingWords);out("staging_word_bits",24);out("staging_capture_s_per_word",stagingWord.readLatency);out("staging_decoder_s",stagingDecoder.readLatency);out("staging_counter_s",stagingCounter.readLatency);out("word_mux_s",wordMux.readLatency);out("word_decoder_s",wordDecoder.readLatency);out("word_counter_s",wordCounter.readLatency);out("gather_beat_s",gatherBeat);out("gather_counter_step_s",counterStep);out("gather_word_data_comb_s",wordDataComb);out("read_bank_select_s_per_pass",c.banks*bankSelect);out("layout_area_m2",macroW*macroH);out("layout_containment_fraction",layoutArea/(macroW*macroH));out("bank_address_bits",4);out("bank_address_updates",c.banks);out("neutral_stream_updates",passes*c.banks);out("neutral_resident_updates",c.banks);
 out("cell_height_F",cell.heightInFeatureSize);out("cell_width_F",cell.widthInFeatureSize);out("vdd_v",tech.vdd);out("read_voltage_v",cell.readVoltage);out("access_voltage_v",cell.accessVoltage);out("write_voltage_v",cell.writeVoltage);out("device_write_pulse_s",cell.writePulseWidth);out("input_r_on_ohm",cell.resistanceOn);out("input_r_off_ohm",cell.resistanceOff);out("access_width_f",cell.widthAccessCMOS);out("access_resistance_ohm",cell.resCellAccess);out("r_on_ohm",cell.resMemCellOn);out("r_off_ohm",cell.resMemCellOff);out("cap_col_f",s.capCol);out("cap_row_f",s.capRow2);out("res_col_ohm",s.resCol);out("res_row_ohm",s.resRow);out("wire_resistance_ohm_per_m",p.unitLengthWireResistance);out("length_row_m",s.lengthRow);out("length_col_m",s.lengthCol);out("bank_width_m",bankW);out("bank_height_m",bankH);out("layout_width_m",macroW);out("layout_height_m",macroH);out("gather_h_length_m",gatherLenH);out("gather_v_length_m",gatherLenV);out("mux_design_rows",c.designRows);out("mux_driver_scale",c.driverScale);out("mux_res_tg_ohm",s.mux.resTg);out("mux_width_n_m",s.mux.widthTgN);out("mux_width_p_m",s.mux.widthTgP);out("mux_driver_n_m",s.muxDecoder.widthDriverInvN);out("mux_driver_p_m",s.muxDecoder.widthDriverInvP);out("mux_select_wire_res_ohm",s.muxDecoder.muxSelectWireRes);out("mux_select_wire_cap_F",s.muxDecoder.muxSelectWireCap);out("mux_load_n_F",s.muxDecoder.capLoad1);out("mux_load_p_F",s.muxDecoder.capLoad2);out("mux_driver_input_cap_F",s.muxDecoder.capDriverInvInput);out("bank_enable_cap_F",bankEnableCap);
 out("max_combinational_s",maxComb);out("clock_period_s",1/hz);out("read_activity",c.activity?c.activity:1./c.rows);out("wl_logic_s",wlRC);out("sl_logic_s",slRC);out("mux_logic_s",(s.mux.readLatency+s.muxDecoder.readLatency)/c.mux);out("correction_logic_s",correction.combinational_s);out("native_read_8bit_s",nativeRead);out("native_read_adc_s",readADC);out("native_read_accum_s",readAccum);out("native_read_other_s",readOther);out("hrs_subtract_s",baselineExtra);out("baseline_combinational_s",baselineComb);out("bank_input_serialization_8bit_s",serialization);out("read_levelshift_8bit_s",8*wlls.readLatency);out("bank_unsigned_8bit_service_s",bankUnsigned);out("gather_one_pass_s",gatherTime);out("reduction_one_pass_s",reduction.readLatency);out("operand_capture_per_pass_s",correction.operand.readLatency);out("global_unsigned_service_s",perPass);out("signed_correction_s",3/hz);out("stream_input_capture_s",input.readLatency);out("neutral_return_s",neutralReturn);out("stream_single_s",stream);out("delta_s",stream);out("native_write_bank_s",nativeWrite);out("write_pulse_s",c.attempts*c.banks*writePulse);out("write_enable_s",c.attempts*c.banks*writeEnable);out("write_release_s",c.attempts*c.banks*writeRelease);out("write_levelshift_s",c.attempts*c.banks*levels);out("write_data_capture_s",c.banks*matrixDataCapture);out("verify_one_row_s",verifyOne);out("verify_total_s",c.attempts*c.banks*verifyTotal);out("bank_select_capture_s",c.banks*bankAddress.readLatency);out("bank_decode_route_s",c.banks*(bankDecoder.readLatency+enableRoute));out("write_data_bus_s",c.banks*batches*writeRoute);out("write_neutral_return_s",c.banks*neutralReturn);out("resident_s",resident);out("rho_Bps",logicalK/stream);out("tau_Bps",(logicalK*31.)/resident);out("ri_star",resident/(31*stream));out("u_star",resident/stream);
 out("native_threshold_0p2tau_diagnostic_s",.2*s.capCol*(cell.resMemCellOff+s.resRow+s.resCol));out("shiftadd_read_window_s",cell.readPulseWidth);out("onehot_col_tau_s",s.capCol*(cell.resMemCellOff+s.resRow+s.resCol));out("onehot_10bit_settle_diagnostic_s",log(2*c.levels)*s.capCol*(cell.resMemCellOff+s.resRow+s.resCol));out("area_native_banks_m2",c.banks*s.area);out("area_all_local_banks_m2",c.banks*localArea);out("area_gather_bus_m2",gatherArea);out("area_reduction_m2",reduction.area);out("area_correction_m2",correction.area_m2);out("area_all_directional_links_and_root_m2",busArea);out("area_read_links_m2",readLinksArea);out("area_write_links_m2",writeLinksArea);out("area_enable_links_m2",enableLinksArea);out("area_write_root_drive_m2",writeRootDrive.area_m2);out("area_staging_data_drive_m2",stagingDataDrive.area_m2);out("area_write_endpoint_buffers_m2",c.banks*writeSinkDrive.area_m2);out("area_bank_enable_buffers_m2",c.banks*bankEnableDrive.area_m2);out("area_hub_select_m2",hubMux.area+hubSelect.area);out("area_bank_select_m2",bankAddress.area+bankDecoder.area);out("area_staging_m2",stagingArea);out("area_total_m2",layoutArea);
 return o;
}
int main(int argc,char**argv){
 if(argc!=1)return 2;
 Config c;
 if(c.attempts<1||c.attempts>2)return 6;
 if(c.rows!=16||c.banks!=16||c.cols!=288||c.temp<300||c.temp>400||c.levels!=1024||request::output_fractional_bits!=4)return 5;
 auto a=run(c,1e9);double hz=1/(request::clock_reservation_factor*a.at("max_combinational_s"));auto o=run(c,hz);
 std::cout<<std::setprecision(17);
 for(const auto &[k,v]:o){if(!std::isfinite(v)||v<0)return 3;std::cout<<k<<"="<<v<<"\n";}
}

// Step4 module-only adapter. No SubArray and no device-type array emulation.
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include "Param.h"
#include "SarADC.h"
#include "Adder.h"
#include "DFF.h"
#include "formula.h"
#include "constant.h"
#include "request.h"
#include "step4_dag.h"
Param *param=nullptr;
using Bits=BitDAG::Bits;
static void emit(const std::string&k,double v){std::cout<<k<<"="<<std::setprecision(17)<<v<<"\n";}
struct Gates {
 const Technology &t;double ci,co,ni,no,wn,wp,wire,rwire;
 Gates(const Technology&tech,double length,double resistance):t(tech){
  wn=MIN_NMOS_SIZE*t.featureSize;wp=t.pnSizeRatio*wn;
  CalculateGateCapacitance(INV,1,wn,wp,t.featureSize*MAX_TRANSISTOR_HEIGHT,t,&ci,&co);
  CalculateGateCapacitance(NAND,2,2*wn,wp,t.featureSize*MAX_TRANSISTOR_HEIGHT,t,&ni,&no);
  wire=length*0.2e-15;rwire=resistance*length*1e-6;
 }
 double inv(double load,double &ramp){double rn=CalculateOnResistance(wn,NMOS,300,t),rp=CalculateOnResistance(wp,PMOS,300,t),r=std::max(rn,rp);return horowitz(r*(co+load+wire)+rwire*(wire/2+load),1/(r*CalculateTransconductance(rn>=rp?wn:wp,rn>=rp?NMOS:PMOS,t)),ramp,&ramp);}
 double nand2(double load,double &ramp){double rn=2*CalculateOnResistance(2*wn,NMOS,300,t),rp=CalculateOnResistance(wp,PMOS,300,t),r=std::max(rn,rp);return horowitz(r*(no+load+wire)+rwire*(wire/2+load),1/(r*CalculateTransconductance(rn>=rp?2*wn:wp,rn>=rp?NMOS:PMOS,t)),ramp,&ramp);}
 double chain(int n,double load,double&ramp){double d=0;for(int i=0;i<n;++i)d+=nand2(i+1==n?load:3*ni,ramp);return d;}
 double distribute(int sinks,double cap,double&ramp){int levels=0;for(int n=sinks;n>1;n=(n+3)/4)++levels;double d=0;for(int i=0;i<levels;++i)d+=inv(4*(i+1==levels?cap:ci),ramp);return d;}
};
static int ilog2up(int n){int r=0;for(int p=1;p<n;p*=2)++r;return r;}
static int band(BitDAG&g,int a,int b){return g.invert(g.nand2(a,b));}
static int bor(BitDAG&g,int a,int b){return g.nand2(g.invert(a),g.invert(b));}
static Bits constantBits(BitDAG&g,int v,int n){Bits b;for(int i=0;i<n;++i)b.push_back((v>>i)&1);return b;}
static Bits variableShift(BitDAG&g,Bits a,Bits control,int outbits,int stride=1){
 a=g.extend(a,outbits,true);for(unsigned k=0;k<control.size();++k){Bits old=a;int ns=g.invert(control[k]),amount=stride*(1<<k);for(int j=0;j<outbits;++j)a[j]=g.mux(old[j],j>=amount?old[j-amount]:0,control[k],ns);}return a;
}
static Bits accumulate(BitDAG&g,Bits term,Bits ibit,Bits acc,bool base4=false,int external_sign=-1){
 Bits shifted=variableShift(g,term,ibit,acc.size(),base4?2:1);int sign=external_sign;
 if(sign<0){sign=ibit[0];for(unsigned i=1;i<ibit.size();++i)sign=band(g,sign,ibit[i]);}
 for(int&i:shifted)i=g.xorr(i,sign);return g.add(acc,shifted,acc.size(),sign);
}
// Compact exact weighted tree. Widths grow from the actual count container;
// final top sign plane uses subtraction rather than unsigned count summation.
static Bits weighted(BitDAG&g,const std::vector<Bits>&c){
 int b=c[0].size();Bits p0=g.add(g.extend(c[0],b+1),g.shift(c[1],1,b+1),b+1);
 Bits p1=g.add(g.extend(c[2],b+1),g.shift(c[3],1,b+1),b+1);
 Bits p2=g.add(g.extend(c[4],b+1),g.shift(c[5],1,b+1),b+1);
 Bits p3=g.subtract(g.extend(c[6],b+1),g.shift(c[7],1,b+1),b+1);
 Bits l0=g.add(g.extend(p0,b+3),g.shift(p1,2,b+3),b+3);
 Bits l1=g.add(g.extend(p2,b+3),g.shift(p3,2,b+3,true),b+3);
 return g.add(g.extend(l0,b+7),g.shift(l1,4,b+7,true),b+7);
}
struct Context{
 InputParameter ip{};Technology tech;MemCell cell{};Gates*g;Adder*unit;double hz,dcap,setup,cq,qramp,area;int fixtures=0;size_t dagNodes=0;
 Context(double freq,double wire):hz(freq){
  ip.processNode=22;ip.temperature=300;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;
  tech.Initialize(22,LSTP,conventional);
  // A mandatory constructor context only. Called DFF/Adder/SAR methods never
  // read cell fields; no material claim follows from this neutral enum.
  cell.memCellType=Type::SRAM;cell.processNode=0;cell.readVoltage=0;cell.resistanceOn=0;cell.resistanceOff=0;
  g=new Gates(tech,wire,param->unitLengthWireResistance);
  DFF d(ip,tech,cell);d.Initialize(1,hz);d.CalculateArea(0,0,NONE);dcap=3*d.capTgDrain+d.capInvInput;
  double ramp=1e20;setup=g->inv(dcap,ramp)+g->inv(g->ci,ramp);ramp=1e20;cq=g->inv(g->ci,ramp);cq+=g->inv(3*g->ni,ramp);qramp=ramp;
  unit=new Adder(ip,tech,cell);unit->Initialize(1,1,hz);unit->CalculateArea(0,0,NONE);area=0;
 }
 void dff(const std::string&name,int bits){if(!bits)return;DFF d(ip,tech,cell);d.Initialize(bits,hz);d.CalculateArea(0,0,NONE);area+=d.area;param->synchronous=true;d.CalculateLatency(1e20,1);emit(name+"_DFF_bits",bits);emit(name+"_DFF_cycles",d.readLatency);assert(d.readLatency==1);param->synchronous=false;}
 void adder(const std::string&name,int bits,int count){Adder a(ip,tech,cell);a.Initialize(bits,count,hz);a.CalculateArea(0,0,NONE);a.CalculateLatency(qramp,3*g->ni+g->wire,1);area+=a.area;emit(name+"_adder_bits",bits);emit(name+"_adder_count",count);emit(name+"_module_diagnostic_s",a.readLatency);}
 // Every DAG source is driven at its actual internal pin load. Shared
 // input/control signals get bounded-fanout distribution across active lanes.
 void path(const std::string&name,BitDAG&d,const Bits&out,int lanes,int banks=1){
  for(int i:out)d.nodes[i].cap+=3*g->ni;
  double maximum_load=0;for(auto&n:d.nodes)if(n.a<0 && !n.constant){
   double ramp=1e20;double arrival=g->inv(g->ci,ramp);
   bool shared=n.name.find("ibit_")==0 || n.name.find("digit_")==0 || n.name.find("sign_")==0 || n.name.find("input_")==0 || n.name.find("pop_input_")==0;
   if(shared){
    arrival+=g->inv(g->ci,ramp);int sinks=std::max(1,(int)std::ceil(n.cap*lanes/unit->capNandInput));
    if(n.name.find("input_")==0 && INPUT_GROUPS>1){
     // The selected 32-row bytes come directly from the full Kx8 input
     // register. There is no free selected-input shadow bank. Both bank
     // data and group-address paths precede distribution to MAC lanes.
     arrival+=g->chain(2*ilog2up(INPUT_GROUPS),g->ci,ramp);
     double sr=qramp,sa=cq+g->chain(2*ilog2up(INPUT_GROUPS),g->ci,sr);
     sa+=g->distribute(ACTIVE_TERMS*8*(INPUT_GROUPS-1),g->ni,sr);
     sa+=g->chain(2*ilog2up(INPUT_GROUPS),g->ci,sr);
     sa+=g->distribute(sinks,unit->capNandInput,sr);
     arrival+=g->distribute(sinks,unit->capNandInput,ramp);n.arcs={{arrival,ramp},{sa,sr}};
    }else{arrival+=g->distribute(sinks,unit->capNandInput,ramp);}
   }
   else if((n.name.find("encoded_source_")==0 || n.name.find("format_source_")==0) && NAND_WORD_BANKS>1){
    // Sixteen word lanes read the existing 4608-word input/staging bank.
    // A 288:1 mux is conservatively padded to 512, with 9 serial 2:1 muxes.
    // No selected-word register is inserted between mux and arithmetic.
    int depth=ilog2up(NAND_WORD_BANKS);arrival+=g->inv(3*g->ni,ramp);
    arrival+=g->chain(2*depth,n.cap,ramp);
    double sr=qramp,sa=cq+g->chain(1,g->ci,sr);
    sa+=g->distribute(lanes*(n.name.find("format_source_")==0?9:8)*(1<<(depth-1)),g->ni,sr);
    sa+=g->chain(2*depth,n.cap,sr);n.arcs={{arrival,ramp},{sa,sr}};
   }else if((CASE_KIND==7 && n.name.find("verify_target_byte_")==0)
          || (CASE_KIND==6 && n.name.find("verify_target_")==0)
          || (CASE_KIND==10 && (n.name.find("verify_target_")==0 || n.name.find("verify_binary_")==0))){
    // The verify comparator reads the declared target/sensed inventory,
    // never a free preselected shadow register. PCM selects 16 of 32 target
    // bytes before the plane mux; MRAM selects one 64-bit target branch;
    // FeNOR selects one 16-bit group of the 128-bit target/read capture.
    int groups=CASE_KIND==10?8:2,depth=ilog2up(groups),wordbits=CASE_KIND==7?8:1;
    arrival+=g->inv(3*g->ni,ramp);arrival+=g->chain(2*depth,n.cap,ramp);
    double sr=qramp,sa=cq+g->chain(1,g->ci,sr);
    sa+=g->distribute(VERIFY_LANES*wordbits*(groups/2),g->ni,sr);
    sa+=g->chain(2*depth,n.cap,sr);n.arcs={{arrival,ramp},{sa,sr}};
   }else{arrival+=g->inv(n.cap,ramp);}
   if(n.name.find("acc_")==0 && banks>1){arrival+=g->chain(2*ilog2up(banks),n.cap,ramp);double sr=qramp,sa=cq+g->chain(2*ilog2up(banks),g->ci,sr);sa+=g->distribute(lanes*OUTPUT_WIDTH,g->ni,sr);sa+=g->chain(2*ilog2up(banks),n.cap,sr);n.arcs={{arrival,ramp},{sa,sr}};}
   n.at=arrival;n.ramp=ramp;maximum_load=std::max(maximum_load,n.cap);
  }
  d.evaluate();double delay=0;for(int i:out){auto arcs=d.nodes[i].arcs;if(arcs.empty()&&!d.nodes[i].constant)arcs.push_back({d.nodes[i].at,d.nodes[i].ramp});for(auto a:arcs){double ramp=a.ramp;double v=a.at+g->chain(2,dcap,ramp)+setup;delay=std::max(delay,v);}}
  // V2: classify launch sources of the unchanged installed MAC graph.
  // Early-stable input/group sources are a frame establishment obligation,
  // while ibit, feedback and the first weight capture require one full cycle.
  // Electrical loads and logic constants are identical in every source pass.
  if(name=="digital_mac"){
  auto original=d.nodes;
  auto classify=[](const std::string&n)->std::string{
   if(n.find("ibit_")==0)return "ibit";
   if(n.find("acc_")==0)return "acc_data";
   if(n.find("input_")==0)return "input_data";
   if(n.find("weight_")==0)return "weight";
   if(n.find("sar_")==0)return "sar";
   if(n.find("calibration_threshold_")==0)return "threshold";
   if(n.find("pop_input_")==0)return "pop_input";
   return "other";
  };
  std::vector<std::string> classes={"ibit","acc_data","output_group_select","input_data","input_group_select","weight","sar","threshold","pop_input","other"};
  double maximum_class=0,dynamic_bound=0;
  for(auto which:classes){d.nodes=original;int selected=0;double arrivalmax=0;
   for(auto &n:d.nodes)if(n.a<0&&!n.constant){
    auto cl=classify(n.name);auto arcs=n.arcs;
    if(arcs.empty())arcs.push_back({n.at,n.ramp});
    n.arcs.clear();n.at=-1e99;n.ramp=1e20;
    for(unsigned j=0;j<arcs.size();++j){auto thiscl=cl;
     if(j==1&&cl=="input_data")thiscl="input_group_select";
     if(j==1&&cl=="acc_data")thiscl="output_group_select";
     if(thiscl==which){n.arcs.push_back(arcs[j]);n.at=std::max(n.at,arcs[j].at);n.ramp=arcs[j].ramp;++selected;arrivalmax=std::max(arrivalmax,arcs[j].at);}
    }
   }
   if(!selected)continue;
   d.evaluate();double part=0;
   for(int i:out){auto arcs=d.nodes[i].arcs;if(arcs.empty()&&!d.nodes[i].constant)arcs.push_back({d.nodes[i].at,d.nodes[i].ramp});for(auto a:arcs){double ramp=a.ramp;part=std::max(part,a.at+g->chain(2,dcap,ramp)+setup);}}
   emit(name+"_source_"+which+"_full_s",part);
   if(which=="ibit"||which=="acc_data"||which=="weight")dynamic_bound=std::max(dynamic_bound,part);
   emit(name+"_source_"+which+"_pin_s",arrivalmax);
   maximum_class=std::max(maximum_class,part);
  }
  assert(std::abs(maximum_class-delay)<1e-18);d.nodes=original;
  emit(name+"_conservative_all_sources_s",delay);
  emit(name+"_classes_recombine_to_full",1);
  assert(dynamic_bound>0);delay=dynamic_bound;
  }
  emit(name+"_path_s",delay);emit(name+"_nodes",d.nodes.size());emit(name+"_max_source_load_F",maximum_load);dagNodes+=d.nodes.size();
 }
};
static int64_t wrap(int64_t x,int bits){x&=(int64_t(1)<<bits)-1;if(x&(int64_t(1)<<(bits-1)))x-=int64_t(1)<<bits;return x;}

static void digitalMAC(Context&c){
 BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits ibit=g.sourceBits("ibit",3,0,1e20),acc=g.sourceBits("acc",OUTPUT_WIDTH,0,1e20);
 std::vector<Bits>x,w,terms;for(int row=0;row<ACTIVE_TERMS;++row){
  x.push_back(g.sourceBits("input_"+std::to_string(row),8,0,1e20));w.push_back(g.sourceBits("weight_"+std::to_string(row),8,0,1e20));
  Bits selected=x.back();for(int j=0;j<3;++j){Bits next;int ns=g.invert(ibit[j]);for(unsigned k=0;k<selected.size();k+=2)next.push_back(g.mux(selected[k],selected[k+1],ibit[j],ns));selected=next;}
  Bits term;for(int q:w.back())term.push_back(band(g,q,selected[0]));terms.push_back(term);
 }
 int width=8,level=0;while(terms.size()>1){std::vector<Bits>next;++width;for(unsigned i=0;i<terms.size();i+=2)next.push_back(g.add(g.extend(terms[i],width,true),g.extend(terms[i+1],width,true),width));c.adder("mac_level"+std::to_string(level++),width,next.size()*LANES);terms=next;}
 Bits out=accumulate(g,terms[0],ibit,acc);c.adder("mac_acc",OUTPUT_WIDTH,LANES);c.path("digital_mac",g,out,LANES,OUTPUT_BANKS);
 int coeff[8]={1,2,4,8,16,32,64,-128};
 for(int pat=0;pat<32;++pat)for(int bit=0;bit<8;++bit){int sum=0;for(int r=0;r<ACTIVE_TERMS;++r){int xv=pat==0?0:pat==1?-128:pat==2?127:((r*47+pat*31)%256)-128;int wv=pat==0?0:pat==1?-128:pat==2?127:((r*73+pat*17)%256)-128;g.set(x[r],xv);g.set(w[r],wv);sum+=((xv>>bit)&1)*wv;}int old=pat%2?100000:-100000;g.set(ibit,bit);g.set(acc,old);g.logicEvaluate();assert(g.value(out,true)==wrap(old+int64_t(coeff[bit])*sum,OUTPUT_WIDTH));++c.fixtures;}
 emit("mac_terms",ACTIVE_TERMS);emit("mac_signed_partial_bits",width);emit("mac_output_bits",OUTPUT_WIDTH);
}

// Pseudo-differential GC decoder: floor((signed_code + 8*popcount + 8)/16).
// All shifts are fixed wires; no ideal parity-lattice lookup or new popcount
// register. Popcount of the selected input-bit is part of this same DAG.
static void gainCell(Context&c,int adc_bits){
 assert(adc_bits>=7);BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits ibit=g.sourceBits("ibit",3,0,1e20),acc=g.sourceBits("acc",OUTPUT_WIDTH,0,1e20);
 std::vector<Bits>xs,pops,code,decoded;for(int r=0;r<ACTIVE_TERMS;++r){xs.push_back(g.sourceBits("pop_input_"+std::to_string(r),8,0,1e20));Bits sel=xs.back();for(int k=0;k<3;++k){Bits nxt;int ns=g.invert(ibit[k]);for(unsigned j=0;j<sel.size();j+=2)nxt.push_back(g.mux(sel[j],sel[j+1],ibit[k],ns));sel=nxt;}pops.push_back(sel);}
 int width=1,level=0;while(pops.size()>1){std::vector<Bits>nxt;++width;for(unsigned j=0;j<pops.size();j+=2)nxt.push_back(g.add(g.extend(pops[j],width),g.extend(pops[j+1],width),width));c.adder("gc_popcount_level"+std::to_string(level++),width,nxt.size()*LANES);pops=nxt;}
 int scale=1<<(adc_bits-7),denominator=2*scale,dwidth=adc_bits+2;
 for(int p=0;p<8;++p){code.push_back(g.sourceBits("sar_"+std::to_string(p),adc_bits,0,1e20));Bits sum=g.add(g.extend(code.back(),dwidth,true),g.shift(pops[0],adc_bits-7,dwidth),dwidth);sum=g.add(sum,constantBits(g,scale,dwidth),dwidth);decoded.push_back(Bits(sum.begin()+adc_bits-6,sum.begin()+adc_bits+1));}
 Bits sum=weighted(g,decoded),out=accumulate(g,sum,ibit,acc);c.adder("gc_decode_sum",dwidth,ADC_COUNT*2);c.adder("gc_tree_l0",8,LANES*4);c.adder("gc_tree_l1",10,LANES*2);c.adder("gc_tree_l2",14,LANES);c.adder("gc_acc",OUTPUT_WIDTH,LANES);c.path("gc_decode_reconstruct",g,out,LANES,OUTPUT_BANKS);
 int coeff[8]={1,2,4,8,16,32,64,-128};
 for(int activity=0;activity<=64;++activity)for(int pat=0;pat<4;++pat){int sum=0;g.set(ibit,3);g.set(acc,12345);for(int r=0;r<64;++r)g.set(xs[r],r<activity?8:0);for(int p=0;p<8;++p){int q=(pat==0?0:pat==1?activity:(pat*37+p*11)%(activity+1));int raw=scale*(2*q-activity);int limit=1<<(adc_bits-1);int adc=std::max(-limit,std::min(limit-1,raw));g.set(code[p],adc);int expected=(int)std::floor((adc+scale*activity+scale)/double(denominator));sum+=coeff[p]*expected;}g.logicEvaluate();assert(g.value(out,true)==wrap(12345+8*int64_t(sum),OUTPUT_WIDTH));++c.fixtures;}
 // Maintenance reads use signed SAR code -> sign decode -> existing 128bit
 // refresh-code hold, then the serial resident load/write schedule.
 BitDAG rf(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits adc=rf.sourceBits("sar_refresh",adc_bits,0,1e20);Bits bit{rf.invert(adc.back())};c.path("gc_refresh_sign",rf,bit,ADC_COUNT);emit("gc_partial_count_bits",7);emit("gc_weighted_partial_bits",14);
}

static void pcm(Context&c,int adc_bits){
 BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits ibit=g.sourceBits("ibit",3,0,1e20),acc=g.sourceBits("acc",OUTPUT_WIDTH,0,1e20);std::vector<Bits>code,decoded;
 // A calibrated 9-class decoder is already in the reference. Comparators
 // are evaluated electrically with unknown stable threshold inputs; these
 // inputs are not assigned invented calibrated values or additional DFFs.
 std::vector<std::vector<Bits>> thresholds;
 for(int p=0;p<8;++p){code.push_back(g.sourceBits("sar_"+std::to_string(p),adc_bits,0,1e20));std::vector<Bits>th;std::vector<Bits>pred;
  for(int j=0;j<8;++j){th.push_back(g.sourceBits("calibration_threshold_"+std::to_string(p)+"_"+std::to_string(j),adc_bits,0,1e20));Bits cmp=g.subtract(g.extend(code.back(),adc_bits+1),g.extend(th.back(),adc_bits+1),adc_bits+1);pred.push_back(Bits{g.invert(cmp.back())});}
  int width=1;while(pred.size()>1){std::vector<Bits>next;++width;for(unsigned i=0;i<pred.size();i+=2)next.push_back(g.add(g.extend(pred[i],width),g.extend(pred[i+1],width),width));pred=next;}decoded.push_back(pred[0]);thresholds.push_back(th);
 }
 Bits sum=weighted(g,decoded),out=accumulate(g,sum,ibit,acc);c.adder("pcm_threshold_compare",adc_bits+1,ADC_COUNT*8);c.adder("pcm_class_l0",2,ADC_COUNT*4);c.adder("pcm_class_l1",3,ADC_COUNT*2);c.adder("pcm_class_l2",4,ADC_COUNT);c.adder("pcm_tree_l0",5,LANES*4);c.adder("pcm_tree_l1",7,LANES*2);c.adder("pcm_tree_l2",11,LANES);c.adder("pcm_acc",OUTPUT_WIDTH,LANES);c.path("pcm_decode_reconstruct",g,out,LANES,OUTPUT_BANKS);
 // These test constants check the generic comparator network only. They
 // are not a PCM voltage/code transfer and never enter service inputs.
 int coeff[8]={1,2,4,8,16,32,64,-128},spacing=(1<<adc_bits)/10;
 for(int pat=0;pat<27;++pat)for(int bit=0;bit<8;++bit){int sum=0;for(int p=0;p<8;++p){int q=(pat+p*5)%9;for(int j=0;j<8;++j)g.set(thresholds[p][j],(j+1)*spacing);g.set(code[p],q*spacing+spacing/3);sum+=coeff[p]*q;}g.set(ibit,bit);g.set(acc,-12345);g.logicEvaluate();assert(g.value(out,true)==wrap(-12345+int64_t(coeff[bit])*sum,OUTPUT_WIDTH));++c.fixtures;}
 emit("pcm_class_bits",4);emit("pcm_class_levels",9);emit("pcm_weighted_partial_bits",11);emit("pcm_calibration_threshold_values_validated",0);
}

static void verify(Context&c,int adc_bits){
 BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);std::vector<Bits>code,target,lo,hi;Bits accepts;
 #if CASE_KIND==7
 Bits plane=g.sourceBits("verify_plane",3,0,1e20);
 for(int lane=0;lane<VERIFY_LANES;++lane){
  code.push_back(g.sourceBits("verify_sar_"+std::to_string(lane),adc_bits,0,1e20));
  target.push_back(g.sourceBits("verify_target_byte_"+std::to_string(lane),8,0,1e20));
  Bits selected=target.back();for(int k=0;k<3;++k){Bits nxt;int ns=g.invert(plane[k]);for(unsigned j=0;j<selected.size();j+=2)nxt.push_back(g.mux(selected[j],selected[j+1],plane[k],ns));selected=nxt;}
  lo.push_back(g.sourceBits("native_verify_lower_"+std::to_string(lane),adc_bits,0,1e20));
  hi.push_back(g.sourceBits("native_verify_upper_"+std::to_string(lane),adc_bits,0,1e20));
  Bits low=g.subtract(g.extend(code.back(),adc_bits+1),g.extend(lo.back(),adc_bits+1),adc_bits+1);
  Bits high=g.subtract(g.extend(hi.back(),adc_bits+1),g.extend(code.back(),adc_bits+1),adc_bits+1);
  // Native acceptance is strictly below lower / strictly above upper.
  // Equality at either calibration threshold belongs to the reject band.
  int lowok=low.back(),highok=high.back();
  int selectedok=g.mux(lowok,highok,selected[0],g.invert(selected[0]));
  int nonzero=0,nonrail=0;for(int bit:code.back()){nonzero=bor(g,nonzero,bit);nonrail=bor(g,nonrail,g.invert(bit));}
  accepts.push_back(band(g,selectedok,band(g,nonzero,nonrail)));
 }
 c.adder("pcm_endpoint_compare",adc_bits+1,VERIFY_LANES*2);
 #else
 for(int lane=0;lane<VERIFY_LANES;++lane){code.push_back(g.sourceBits("verify_binary_"+std::to_string(lane),1,0,1e20));target.push_back(g.sourceBits("verify_target_"+std::to_string(lane),1,0,1e20));accepts.push_back(g.invert(g.xorr(code.back()[0],target.back()[0])));}
 #endif
 while(accepts.size()>1){Bits next;for(unsigned i=0;i<accepts.size();i+=2)next.push_back(i+1<accepts.size()?band(g,accepts[i],accepts[i+1]):accepts[i]);accepts=next;}
 Bits old=g.sourceBits("verify_old_done",1,0,1e20);Bits out{band(g,accepts[0],old[0])};c.path("verify_compare",g,out,1);
 for(int test=0;test<16;++test){bool expected=true;g.set(old,test%8==7?0:1);if(test%8==7)expected=false;
  #if CASE_KIND==7
  g.set(plane,2);int limit=1<<adc_bits,lower=limit/4,upper=3*limit/4;
  #endif
  for(int lane=0;lane<VERIFY_LANES;++lane){
   #if CASE_KIND==7
   bool set=(lane+test/8)%2;int value=set?upper+1:lower-1;g.set(target[lane],set?4:0);g.set(lo[lane],lower);g.set(hi[lane],upper);
   if(lane==0){switch(test%8){case 1:value=lower+1;expected=false;break;case 2:value=set?limit-1:0;expected=false;break;case 3:value=lower;expected=false;break;case 4:value=upper;expected=false;break;case 5:value=upper+1;expected=set;break;case 6:value=lower-1;expected=!set;break;}}
   g.set(code[lane],value);
   #else
   int value=(lane+test)%2;g.set(target[lane],value);if(test%3==1&&lane==0){value=1-value;expected=false;}g.set(code[lane],value);
   #endif
  }g.logicEvaluate();assert(g.value(out)==expected);++c.fixtures;
 }
 emit("verify_active_lanes",VERIFY_LANES);emit("verify_graph_fixtures",16);
 #if CASE_KIND==7
 emit("verify_threshold_equalities_reject_checked",1);emit("verify_both_rails_reject_checked",1);emit("verify_old_done_zero_checked",1);
 #endif
}

static void nand(Context&c){
 {BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits x=g.sourceBits("encoded_source",8,0,1e20),v=x;for(int&i:v)i=g.xorr(i,x.back());Bits mag=g.add(v,constantBits(g,0,8),8,x.back());Bits out=mag;out.push_back(x.back());c.adder("nand_magnitude",8,16);c.path("nand_sign_magnitude",g,out,16);
 for(int a=-128;a<=127;++a){g.set(x,a);g.logicEvaluate();assert(g.value(mag)==std::abs(a));++c.fixtures;}}
 {BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits source=g.sourceBits("format_source",9,0,1e20),digit=g.sourceBits("digit",2,0,1e20),polarity=g.sourceBits("sign",1,0,1e20);
  Bits pair;for(int b=0;b<2;++b){Bits selected;for(int k=0;k<4;++k)selected.push_back(source[2*k+b]);for(int k=0;k<2;++k){Bits next;int ns=g.invert(digit[k]);for(unsigned j=0;j<selected.size();j+=2)next.push_back(g.mux(selected[j],selected[j+1],digit[k],ns));selected=next;}pair.push_back(selected[0]);}
  int enable=g.invert(g.xorr(source[8],polarity[0]));int low=band(g,pair[0],enable),high=band(g,pair[1],enable);Bits out{low,high,high};c.path("nand_page_formatter",g,out,16);
  for(int value=-128;value<=127;++value)for(int d=0;d<4;++d)for(int s=0;s<2;++s){g.set(source,std::abs(value)|((value<0?1:0)<<8));g.set(digit,d);g.set(polarity,s);g.logicEvaluate();int v=((value<0)==bool(s))?((std::abs(value)>>(2*d))&3):0;assert(g.nodes[low].value==bool(v&1));assert(g.nodes[high].value==bool(v&2));++c.fixtures;}
  emit("nand_page_formatter_entries_per_tick",16);emit("nand_page_formatter_useful_bits_per_tick",48);emit("nand_word_bank_mux_fanin",NAND_WORD_BANKS);
 }
 {BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);std::vector<Bits>x;for(int k=0;k<4;++k)x.push_back(g.sourceBits("count_"+std::to_string(k),14,0,1e20));Bits p0=g.add(g.extend(x[0],16),g.shift(x[1],2,16),16),p1=g.add(g.extend(x[2],16),g.shift(x[3],2,16),16);Bits out=g.add(g.extend(p0,20),g.shift(p1,4,20),20);c.adder("nand_merge_l0",16,32);c.adder("nand_merge_l1",20,16);c.path("nand_base4_merge",g,out,16);
 for(int a=0;a<64;++a){int sum=0;for(int k=0;k<4;++k){int v=(a*211+k*1879)%10369;g.set(x[k],v);sum+=v*(1<<(2*k));}g.logicEvaluate();assert(g.value(out)==sum);++c.fixtures;}}
 {BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits p=g.sourceBits("positive",20,0,1e20),n=g.sourceBits("negative",20,0,1e20);Bits out=g.subtract(g.extend(p,21),g.extend(n,21),21);c.adder("nand_polarity",21,8);c.path("nand_polarity_subtract",g,out,8);for(int a=0;a<64;++a){int pval=a*13703,nval=(63-a)*11923;g.set(p,pval);g.set(n,nval);g.logicEvaluate();assert(g.value(out,true)==pval-nval);++c.fixtures;}}
 {BitDAG g(c.tech,*c.unit,c.g->wire,c.g->rwire,300);Bits x=g.sourceBits("difference",21,0,1e20),digit=g.sourceBits("digit",2,0,1e20),sign=g.sourceBits("sign",1,0,1e20),acc=g.sourceBits("acc",OUTPUT_WIDTH,0,1e20);Bits out=accumulate(g,x,digit,acc,true,sign[0]);c.adder("nand_acc",OUTPUT_WIDTH,8);c.path("nand_shift_accumulate",g,out,8,OUTPUT_BANKS);
 for(int a=-10;a<=10;++a)for(int k=0;k<4;++k)for(int s=0;s<2;++s){g.set(x,a*13703);g.set(digit,k);g.set(sign,s);g.set(acc,123456);g.logicEvaluate();assert(g.value(out,true)==wrap(123456+int64_t(s?-1:1)*a*13703*(1<<(2*k)),OUTPUT_WIDTH));++c.fixtures;}}
 emit("nand_affine_multiplier_path_validated",0);emit("nand_calibration_divider_path_validated",0);
}

int main(int argc,char**argv){
 if(argc!=4)return 2;double hz=atof(argv[1]),wire=atof(argv[2]);int bits=atoi(argv[3]);assert(hz>0&&wire>=0&&bits>=2&&bits<=16);
 param=new Param();param->clkFreq=hz;param->synchronous=false;param->pipeline=false;param->SARADC=ADC_COUNT>0;param->levelOutput=1<<bits;param->dumcolshared=param->levelOutput;
 Context c(hz,wire);c.dff("input",INPUT_BITS);c.dff("output",OUTPUT_BITS);c.dff("operand_hold",OPERAND_BITS);c.dff("resident_staging",RESIDENT_BITS);c.dff("mask",MASK_BITS);c.dff("declared_extra",EXTRA_BITS);c.dff("controller",CONTROL_STATE_BITS);
 emit("boundary_setup_s",c.setup);emit("clock_q_s",c.cq);emit("dff_data_cap_F",c.dcap);emit("wire_cap_F",c.g->wire);emit("wire_resistance_ohm",c.g->rwire);
 // Fully serial controller counter, state decode, fanout, capture mux/setup.
 Adder ctr(c.ip,c.tech,c.cell);ctr.Initialize(CONTROL_BITS,1,hz);ctr.CalculateArea(0,0,NONE);double ramp=c.qramp,delay=c.cq;ctr.CalculateLatency(ramp,4*c.g->ni+c.g->wire,1);delay+=ctr.readLatency;ramp=ctr.rampOutput;delay+=c.g->chain(4,c.g->ci,ramp);delay+=c.g->distribute(CONTROL_SINKS,c.g->ni,ramp);delay+=c.g->chain(2,c.dcap,ramp);delay+=c.setup;emit("controller_path_s",delay);c.area+=ctr.area;
 ramp=c.qramp;delay=c.cq+c.g->chain(2*ilog2up(OUTPUT_BANKS)+2,c.dcap,ramp)+c.setup;emit("io_path_s",delay);
 ramp=c.qramp;delay=c.cq+c.g->chain(4,c.g->ci,ramp);delay+=c.g->distribute(OUTPUT_BITS,c.g->ni,ramp);delay+=c.g->chain(2,c.dcap,ramp)+c.setup;emit("accumulator_clear_path_s",delay);
 if(ADC_COUNT){SarADC sar(c.ip,c.tech,c.cell);sar.Initialize(ADC_COUNT,1<<bits,hz,ACTIVE_TERMS);sar.CalculateUnitArea();sar.CalculateArea(0,1e-4,NONE);sar.CalculateLatency(1);emit("sar_s",sar.readLatency);emit("sar_active_terms",sar.numReadCellPerOperationNeuro);emit("sar_installed_count",sar.numCol);emit("sar_bits",bits);c.area+=sar.area;}
 // E1 changes only the existing phase state. Its E2 capture-enable path
 // cannot borrow E0's data cycle; same physical output mux, no extra bank.
 #if CASE_KIND==7 || CASE_KIND==9
 ramp=c.qramp;delay=c.cq+c.g->chain(4,c.g->ci,ramp);
 delay+=c.g->distribute(LANES*OUTPUT_WIDTH,c.g->ni,ramp);
 delay+=c.g->chain(2,c.dcap,ramp)+c.setup;emit("capture_enable_path_s",delay);
 #endif
 // Explicit case dispatch rejects new/unmapped cases at compile time.
 #if CASE_KIND==3 || CASE_KIND==6 || CASE_KIND==8 || CASE_KIND==10
 digitalMAC(c);
 #elif CASE_KIND==4
 nand(c);
 #elif CASE_KIND==7
 pcm(c,bits);
 #elif CASE_KIND==9
 gainCell(c,bits);
 #else
 #error No approved Step4 backend mapping
 #endif
 // Terminal compare/done reduction for actual endpoint/absolute-state users.
 #if CASE_KIND==6 || CASE_KIND==7 || CASE_KIND==10
 verify(c,bits);
 #endif
 emit("same_graph_arithmetic_fixtures",c.fixtures);emit("DAG_nodes_total",c.dagNodes);emit("partial_initialized_module_area_m2",c.area);emit("clkFreq_hz",hz);emit("technode_nm",22);emit("temperature_K",300);emit("vdd_V",c.tech.vdd);emit("dff_cycle",1);emit("native_memcell_fields_read",0);return 0;
}

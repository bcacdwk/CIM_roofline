#ifndef PILOT_PATHS_DAG_H
#define PILOT_PATHS_DAG_H
// Step3 V2: bit-arrival DAG of the standard 9-NAND full adder used in
// locked Adder's 9*numBit area method. Its electrical dimensions/capacitances
// are taken from a caller-initialized Adder; no replacement cell library.
#include <vector>
#include <string>
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cmath>
#include "Adder.h"
#include "formula.h"
#include "constant.h"
struct BitDAG {
 struct Arrival {double at,ramp;};
 struct Node {int a,b; bool constant,value; double at,ramp,cap; std::string name; std::vector<Arrival> arcs;};
 const Technology&t;const Adder&unit; double wire,rwire,temp; std::vector<Node> nodes;
 typedef std::vector<int> Bits;
 BitDAG(const Technology&tech,const Adder&a,double wirecap,double resistance,double temperature):t(tech),unit(a),wire(wirecap),rwire(resistance),temp(temperature){constant(false);constant(true);}
 int constant(bool v){nodes.push_back({-1,-1,true,v,-1e99,1e20,0,"constant"});return nodes.size()-1;}
 int source(std::string name,double at,double ramp){nodes.push_back({-1,-1,false,false,at,ramp,0,name});return nodes.size()-1;}
 int nand2(int a,int b){
  // Keep installed gates and BOTH input pin loads even when their output
  // is provably constant. Timing inactivity is not physical cell removal.
  bool fixed=(nodes[a].constant && !nodes[a].value) || (nodes[b].constant && !nodes[b].value) || (nodes[a].constant && nodes[b].constant);
  bool value=!(nodes[a].value && nodes[b].value);
  nodes[a].cap+=unit.capNandInput;nodes[b].cap+=unit.capNandInput;
  nodes.push_back({a,b,fixed,value,0,0,0,"NAND2"});return nodes.size()-1;
 }
 int invert(int a){return nand2(a,1);}
 int xorr(int a,int b){int ab=nand2(a,b);return nand2(nand2(a,ab),nand2(b,ab));}
 int mux(int a,int b,int s,int ns){return nand2(nand2(a,ns),nand2(b,s));}
 Bits extend(Bits a,int n,bool sign=false){a.resize(n,sign?a.back():0);return a;}
 Bits shift(Bits a,int amount,int n,bool sign=false){a=extend(a,n,sign);Bits r(n,0);for(int i=amount;i<n;++i)r[i]=a[i-amount];return r;}
 Bits add(Bits a,Bits b,int n,int cin=0){
  assert((int)a.size()==n && (int)b.size()==n);Bits out;int carry=cin;
  for(int i=0;i<n;++i){
   // Nine-NAND FA: two XORs plus shared-product carry.
   int ab=nand2(a[i],b[i]);int ax=nand2(a[i],ab),bx=nand2(b[i],ab);int p=nand2(ax,bx);
   int pc=nand2(p,carry);int px=nand2(p,pc),cx=nand2(carry,pc);
   out.push_back(nand2(px,cx));carry=nand2(ab,pc);
  }return out;
 }
 Bits subtract(Bits a,Bits b,int n){for(int&i:b)i=invert(i);return add(a,b,n,1);}
 Bits sourceBits(std::string name,int n,double at,double ramp){Bits b;for(int i=0;i<n;++i)b.push_back(source(name+"_"+std::to_string(i),at,ramp));return b;}
 void set(Bits b,int64_t v){for(unsigned i=0;i<b.size();++i){bool bit=(uint64_t(v)>>i)&1;if(nodes[b[i]].constant)assert(nodes[b[i]].value==bit);else nodes[b[i]].value=bit;}}
 int64_t value(Bits b,bool sign=false){int64_t v=0;for(unsigned i=0;i<b.size();++i)v|=int64_t(nodes[b[i]].value)<<i;if(sign && nodes[b.back()].value)v-=int64_t(1)<<b.size();return v;}
 void evaluate(){
  for(unsigned i=0;i<nodes.size();++i){Node &n=nodes[i];if(n.a<0)continue;
   n.value=!(nodes[n.a].value&&nodes[n.b].value);
   if(n.constant){n.at=-1e99;n.arcs.clear();continue;}
   // Exact capacitance fanout in this declared DAG plus one declared wire/net.
   double rn=2*CalculateOnResistance(unit.widthNandN,NMOS,temp,t),rp=CalculateOnResistance(unit.widthNandP,PMOS,temp,t);
   double res=std::max(rn,rp);double gm=CalculateTransconductance(rn>=rp?unit.widthNandN:unit.widthNandP,rn>=rp?NMOS:PMOS,t);
   double tr=res*(unit.capNandOutput+n.cap+wire)+rwire*(wire/2+n.cap);
   // Keep non-dominated (arrival, slew) pairs: no impossible late/slow
   // recombination and no discarded earlier-but-slower arc. All paths are
   // structural envelopes, not sensitized STA paths.
   std::vector<Arrival> candidates;
   for(int j:{n.a,n.b})if(!nodes[j].constant){
    auto arcs=nodes[j].arcs;if(arcs.empty())arcs.push_back({nodes[j].at,nodes[j].ramp});
    for(auto x:arcs){double ramp;double at=x.at+horowitz(tr,1/(res*gm),x.ramp,&ramp);candidates.push_back({at,ramp});}
   }
   n.arcs.clear();
   for(auto x:candidates){bool dominated=false;
    for(auto y:n.arcs)if(y.at>=x.at && y.ramp<=x.ramp){dominated=true;break;}
    if(dominated)continue;
    n.arcs.erase(std::remove_if(n.arcs.begin(),n.arcs.end(),[&](Arrival y){return x.at>=y.at && x.ramp<=y.ramp;}),n.arcs.end());
    n.arcs.push_back(x);
   }
   n.at=-1e99;for(auto x:n.arcs)if(x.at>n.at){n.at=x.at;n.ramp=x.ramp;}

  }
 }
 double latest(Bits b){double latest=0;for(int i:b)latest=std::max(latest,nodes[i].at);return latest;}
};
struct WeightedReconstruct {
 BitDAG&g;std::vector<BitDAG::Bits> c;BitDAG::Bits ibit,acc,p0,p1,p2,p3,l0,l1,w,shifted,out;
 WeightedReconstruct(BitDAG&dag,double source_at,double source_ramp,double control_at,double control_ramp,double acc_at,double acc_ramp,int count_bits=8):g(dag){
  for(int i=0;i<8;++i)c.push_back(g.extend(g.sourceBits("c"+std::to_string(i),count_bits,source_at,source_ramp),8));
  ibit=g.sourceBits("ibit",3,control_at,control_ramp);acc=g.sourceBits("old_acc",23,acc_at,acc_ramp);
  // Bounds for declared 0..128 counts: p0..2 in[0,384], p3 in[-256,128],
  // l0 in[0,1920], l1 in[-1024,896], w in[-16384,16256].
  p0=g.add(g.extend(c[0],9),g.shift(c[1],1,9),9);
  p1=g.add(g.extend(c[2],9),g.shift(c[3],1,9),9);
  p2=g.add(g.extend(c[4],9),g.shift(c[5],1,9),9);
  p3=g.subtract(g.extend(c[6],9),g.shift(c[7],1,9),9);
  l0=g.add(g.extend(p0,11),g.shift(p1,2,11),11);
  l1=g.add(g.extend(p2,11),g.shift(p3,2,11,true),11);
  w=g.add(g.extend(l0,15),g.shift(l1,4,15,true),15);
  shifted=g.extend(w,23,true);
  for(int k=0;k<3;++k){auto src=shifted;int ns=g.invert(ibit[k]);for(int j=0;j<23;++j)shifted[j]=g.mux(src[j],j>=(1<<k)?src[j-(1<<k)]:0,ibit[k],ns);}
  // Input ibit==7 has coefficient-128. The phase/index register is held.
  int sign=g.invert(g.nand2(ibit[0],ibit[1]));sign=g.invert(g.nand2(sign,ibit[2]));
  auto signed_term=shifted;for(int&i:signed_term)i=g.xorr(i,sign);
  out=g.add(acc,signed_term,23,sign);
 }
};
#endif

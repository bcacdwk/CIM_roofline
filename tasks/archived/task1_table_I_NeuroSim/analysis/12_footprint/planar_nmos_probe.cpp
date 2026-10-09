// Geometry-only adapter for locked NeuroSim 2DInferenceV1.4.
// Upstream formula.cpp/constant.h/Technology.* remain unmodified and retain
// their ASU/Georgia Tech copyright and CC BY-NC 4.0 notices in the isolated build.
#include <iostream>
#include <iomanip>
#include <string>
#include <cmath>
#include "formula.h"
#include "Technology.h"
#include "Param.h"
#include "constant.h"
Param *param = nullptr;
int main() {
    std::cout << std::setprecision(17);
    std::string id;
    double F_um,W_um,L_um,H_um,contact_um,gap_um,enclosure_um;
    while(std::cin>>id>>F_um>>W_um>>L_um>>H_um>>contact_um>>gap_um>>enclosure_um) {
        if(F_um<0.022||W_um<=0||L_um<F_um||H_um<W_um+3.6*F_um-1e-12) return 2;
        Technology tech; // Geometry fields only; do NOT initialize unsupported electrical node.
        tech.featureSize=F_um*1e-6; tech.transistorType=conventional;
        const double H_m=(H_um+1e-12)*1e-6; // guard exact-boundary floating folding
        double h=0,w=0;
        double a=CalculateGateArea(INV,1,W_um*1e-6,0.0,H_m,tech,&h,&w);
        double maxW=H_m/1e-6-3.6*F_um;
        int fingers=(W_um<=maxW)?1:(int)std::ceil(W_um/maxW);
        double length_correction=fingers*(L_um-F_um);
        // Explicit real-channel strip plus individually contacted diffusion ends.
        double contact_span=fingers*L_um+(fingers+1)*contact_um+2*fingers*gap_um+2*enclosure_um;
        double adapted_w=std::fmax(w*1e6+length_correction,contact_span);
        std::cout<<id<<","<<w*1e6<<","<<h*1e6<<","<<a*1e12<<","<<fingers<<","<<length_correction<<","<<contact_span<<","<<adapted_w<<"\n";
    }
}

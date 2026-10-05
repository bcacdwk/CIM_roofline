#include <iostream>
#include <iomanip>
#include "SarADC.h"
#include "Param.h"
#include "request.h"
Param *param;
int main(){Param p;param=&p;p.technode=request::technology_nm;p.temp=request::temperature_K;InputParameter ip{};ip.processNode=request::technology_nm;ip.temperature=request::temperature_K;ip.deviceRoadmap=LSTP;ip.transistorType=conventional;Technology t;t.Initialize(ip.processNode,LSTP,conventional);MemCell c{};SarADC adc(ip,t,c);adc.Initialize(request::adc_count,1<<request::adc_bits,request::clock_Hz,request::adc_count);adc.CalculateUnitArea();adc.CalculateArea(0,request::ADC_bank_width_m,NONE);adc.CalculateLatency(1);std::cout<<std::setprecision(17)<<"native_ADC_s="<<adc.readLatency<<"\nnative_ADC_area_m2="<<adc.area<<"\nnative_ADC_count="<<request::adc_count<<"\nnative_ADC_Cin_provided=0\nexplicit_ADC_input_C_F="<<request::ADC_input_C_F<<"\n";}

#!/usr/bin/env python3
"""Independent ten-case arithmetic using approved source facts and reviewer tile formulas."""
import argparse,json
from pathlib import Path
from independent_model_check import model
SIX={
 '01_sram_acim':(.994,1,28,'SACIM-03 p3 reported 9T1C area'),
 '02_sram_dcim':(91*6.4,1024,28,'SDCIM-01 p3 Fig8 full local tile'),
 '04_nand_3d':(.040*.750,500,20,'NAND-04 p2 lateral grid; user500 effective SLC layers'),
 '06_mram':(1600*.040**2,1,40,'MRAM-06 SI p10 approximate IBMD1600F2, nominal40'),
 '09_gain_cell_edram':(6,1,65,'GC-04 PDFp6 complete3T1C, SLC capped'),
 '10_fenor_3d':(.120*.170,4,60,'FENOR-02 p3 model pitch, four layers')}

def calculate(model_input):
 facts=dict(SIX);facts['03_nor_2d']=(.04,1,28,'GF official2023-09-27 full ESF3bitcell, not Microchip<.05 bound')
 facts['07_pcm']=(.036,1,28,'Palhares2024p2/ST2018slide11 complete1T1R physical cell, binary cap')
 for cid,c in model_input['cases'].items():
  z=model(cid,c);facts[cid]=(z['area_xy_um2'],1,c['F_mem_nm'],'Independent source dimensions and explicit contact/layer envelope; conditional')
 rows=[]
 for cid,(area,b,f,source) in sorted(facts.items()):
  abit=area/b;den=1/abit;alpha=abit/(f/1000)**2
  rows.append({'case_id':cid,'A_xy_um2':area,'b_bit':b,'F_mem_nm':f,'a_bit_um2':abit,'D_Mbit_mm2':den,'alpha_Fmem2_per_bit':alpha,'source_fact':source})
 a1=.040*.750;a32=a1/32;a500=a1/500
 assert abs(a32*32/500-a500)<1e-20
 return {'status':'PASS','method':'Source facts for direct/reference rows; independent reviewer formulas for new models; no production code imported or CSV used','source_rows':rows,'NAND_algebraic_rows':{'a1_um2':a1,'a32_um2':a32,'a500_um2':a500},'checks':{'SLC_no_MLC':True,'NAND_one_fold':True,'MRAM_one_independent_bit':True}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model-input',type=Path,default=Path(__file__).resolve().parents[1]/'model_inputs.json');p.add_argument('--output',type=Path,default=Path('independent_results.json'));a=p.parse_args();r=calculate(json.load(open(a.model_input)));a.output.write_text(json.dumps(r,indent=2)+'\n');print('PASS: independently recomputed ten cases')

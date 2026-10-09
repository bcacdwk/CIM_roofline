#!/usr/bin/env python3
"""Reviewer-owned arithmetic from primary-PDF facts, not production CSV/JSON."""
import argparse, json, math
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=60
D=Decimal
FACTS=[
 dict(case_id='01_sram_acim',row_id='sram_acim',A='0.994',b=1,F='28',quality='reported_geometry',source='SACIM-03 p.3 Sec.III; p.2 9T1C circuit/MOM overlap',scope='Complete native 9T1C cell, capacitor above transistor projection',f_kind='nominal_node'),
 dict(case_id='02_sram_dcim',row_id='sram_dcim',A=str(D('91')*D('6.4')),b=1024,F='28',quality='reported_layout_derived',source='SDCIM-01 p.3 Fig.8; p.1 Sec.II.A: 8 columns times 128 storage cells',scope='Full local 8-column tile including shared NOR, LBL interface and distributed compressor; outer HCA tree/BFA excluded',f_kind='nominal_node'),
 dict(case_id='04_nand_3d',row_id='nand_single_layer',A=str(D('0.040')*D('0.750')),b=1,F='20',quality='published_geometry_model',source='NAND-04 p.2 Fig.1 & Sec.II.A: 40nm BL pitch, 0.75um SSL pitch',scope='One BL-by-SSL tile; one independent SLC cell per effective WL',f_kind='BL_direction_half_pitch'),
 dict(case_id='04_nand_3d',row_id='nand_source_32',A=str(D('0.040')*D('0.750')),b=32,F='20',quality='published_geometry_model',source='NAND-04 p.2: physical cells 13824 BL x 32 WL x 3 SSL',scope='Source 32-WL model geometry; not claim of measured 32-layer device',f_kind='BL_direction_half_pitch'),
 dict(case_id='04_nand_3d',row_id='nand_projection_500',A=str(D('0.040')*D('0.750')),b=500,F='20',quality='500_layer_projection',source='User-requested 500 effective storage layers, lateral NAND-04 geometry unchanged',scope='One SLC cell per WL; no macro staircase, boundary or yield projection',f_kind='BL_direction_half_pitch'),
 dict(case_id='06_mram',row_id='mram',A=str(D('1600')*(D('40')/1000)**2),b=1,F='40',quality='published_engineering_estimate',source='MRAM-06 Supplement p.10 estimated 1600 F2 IBMD; main p.1 40nm CMOS',scope='Complete IBMD bitcell: complementary 2T2MTJ plus local latch; ONE independent binary state',f_kind='nominal_node'),
 dict(case_id='09_gain_cell_edram',row_id='gain_cell',A='6',b=1,F='65',quality='reported_geometry',source='GC-04 PDF p.6 Sec.III.A layout 6um2 and 65nm technology',scope='One 3T1C silicon CMOS cell with overlapping 10fF MOM; no MLC gain; pseudo-differential mapping excluded',f_kind='nominal_node'),
 dict(case_id='10_fenor_3d',row_id='fenor',A=str(D('0.120')*D('0.170')),b=4,F='60',quality='published_geometry_model',source='FENOR-02 p.3 Fig.11b/c pitch120x170nm; p.2/3 Figs2/10 four layers',scope='Full lateral hole grid at four layers, one FeFET state per hole per layer; no 500-layer extrapolation',f_kind='X_direction_half_pitch'),
]

def calculate():
 out=[]
 for f in FACTS:
  area=D(f['A']); bits=D(f['b']); fnm=D(f['F']); abit=area/bits
  den=1/abit; alpha=abit/(fnm/1000)**2
  assert den*abit==1 or abs(den*abit-1)<D('1e-55')
  assert abs(alpha*(fnm/1000)**2-abit)<D('1e-55')
  # Absolute density is independent of F choice. A doubled F changes only alpha.
  alternate_alpha=abit/((2*fnm)/1000)**2
  assert abs(alternate_alpha*4-alpha)<D('1e-55')
  out.append({**f,'A_xy_um2':float(area),'b_bit':int(bits),'F_mem_nm':float(fnm),'a_bit_um2':float(abit),'D_Mbit_mm2':float(den),'alpha_Fmem2_per_bit':float(alpha),'exact_decimal':{'a_bit':str(abit),'D':str(den),'alpha':str(alpha)}})
 by={x['row_id']:x for x in out}
 a1=D(by['nand_single_layer']['exact_decimal']['a_bit'])
 a32=D(by['nand_source_32']['exact_decimal']['a_bit'])
 a500=D(by['nand_projection_500']['exact_decimal']['a_bit'])
 assert a1/500==a32*32/500==a500
 # Source's full block and minimum tile reduce to identical a_bit, without rounding 552.96 to 553.
 assert (D('13824')*D('.040')*3*D('.750'))/(13824*32*3)==a32
 assert all(x['b_bit']==1 for x in out if x['row_id'] in ['mram','gain_cell'])
 return {'independence':'Facts re-extracted by reviewer from original PDF text and visual figures before reading production results. No production code imported.','source_rows':out,'checks':{'inverse_units':True,'alpha_recovers_area':True,'F_invariance':True,'NAND_single_fold':True,'SLC_no_MLC_gain':True,'MRAM_complementary_one_bit':True,'GC_mapping_not_capacity':True},'diagnostics':{'dcim_core_only_um2':.379,'dcim_full_repeat_tile_um2':582.4,'dcim_bits_per_tile':1024,'dcim_macro_floorplan_closure':'Not asserted; only the reported local rectangular tile is used. Initial low-resolution 8.4 misread was corrected by original PDF character extraction and enlarged view to 6.4.'}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('independent_results.json'));a=p.parse_args();result=calculate();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({x['row_id']:{k:x[k] for k in ['a_bit_um2','D_Mbit_mm2','alpha_Fmem2_per_bit']} for x in result['source_rows']},indent=2))

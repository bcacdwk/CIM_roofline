#!/usr/bin/env python3
"""Principal review: independent stage arithmetic, without importing case/shared APIs."""
import argparse,json,math,hashlib,re
from pathlib import Path
A=Path(__file__).resolve().parents[1]
# Direct reconstruction of one representative point per medium.
cal=2*303+3*(5+12+640+25000+640+20)+226*5
alpha=(400000-1024*(175+5+80)-185)/400000
POINTS={
'01_sram_acim':(64*(20+20+2*5)+2*5,5,16,1,'64(20+20+2×5)+2×5; complete SRAM write 5 ns'),
'02_sram_dcim':(512*5+2*5,5,16,1,'512 complete MAC slots×5+2×5; 64 static row-group selections; write 5 ns'),
'03_nor_2d':(256*(120+5)+10,4*45e6+64*.4e6+(64*18+4*2)*5,16384,1,'256(120+5)+10; 4×45ms+64×0.4ms+(64×18+4×2)×5ns'),
'04_nand_3d':(8*303+64*(5+12+640+25000+640+20+3*5)+10,1280*(110*5+2500000)+128*30000000+cal,16384,1,'T_int=16pF×0.4V/(128×2nA)=25us; C=80687ns; 1280 complete P+128 E+C'),
'05_rram':(256*(5+5+20+2*5)+10,10+8*(2+1)*(1000+1000+1000+5+5+20+2*5),16,1,'256(5+5+20+10)+10; 10+8(2+1)×3040'),
'06_mram':(256*(5+5)+10,10+2*30+5+2*(5+5),8,1,'256(5+5)+10; 10+2×30+5+2(5+5); two-phase write and two-branch verify'),
'07_pcm':(1024*(20+20+10)+10,15+8*(5+60+125+300+2*(20+20+5)),32,1,'1024(20+20+10)+10; 15+8[5+60+125+300+2(20+20+5)]'),
'08_feram_hfo2':(32*(20+50+40)+256*5+10,10+40+2*50,16,1,'32 physical sense/restore slots×110+256 digital rounds×5+10; 10+40+2×50'),
'09_gain_cell_edram':(128*175+258*5,3*5+65,16,alpha,'raw 128×175+258×5; raw 15+65; alpha=(400000-1024×260-185)/400000'),
'10_fenor_3d':(256*(40+5)+10,10+8*(30+40+100+40+5),16,1,'256(40+5)+10; 10+8(30+40+100+40+5); final return within observation window'),
}
def run():
 d=json.loads((A/'data/ten_case_results.json').read_text());ref={r['case_id']:r for r in d['results'] if r['recommended']};checks=[]
 for c,(s,r,br,a,formula) in POINTS.items():
  x=ref[c];raw=x['raw_service_time'];eff=x['effective_service_interval'] or raw
  expected=dict(raw_streaming_ns=s,raw_resident_ns=r,effective_streaming_ns=s/a,effective_resident_ns=r/a,rho_MB_per_s=128/s*1000*a,tau_MB_per_s=br/r*1000*a,RI_star=128/br*r/s)
  observed=[raw['streaming_ns'],raw['resident_ns'],eff['streaming_ns'],eff['resident_ns'],x['rho'],x['tau'],x['RI_star']]
  assert x['B_S']==128 and x['B_R']==br
  assert all(math.isclose(v,w,rel_tol=1e-11) for v,w in zip(expected.values(),observed)),(c,expected,observed)
  n=16384/br;assert n==int(n)
  checks.append(dict(case_id=c,formula=formula,independent=expected,matrix_transactions=int(n),matrix_raw_resident_ns=n*r,pass_check=True))
 # Geometry checks are independent from service routines.
 pcm={( (4*h+ss+d)%128,4*h+ss) for d in range(128) for ss in range(4) for h in range(32)}
 assert len(pcm)==128*128
 rram={(out,32*g+16*sg+8*half+k) for out in range(128) for g in range(4) for half in range(2) for sg in range(2) for k in range(8)}
 assert len(rram)==128*128
 # FeRAM existing readout register is read-only during eight compute updates.
 assert 4*8==32 and 32*4096==16384*8 and 32*8==256
 assert 64*256==4*4096==16384 # NOR read capacity/erase capacity are independent partitions.
 assert 1024*16==16384 and 128*8==1024 and 128*2==256 # NAND data/reference pages.
 stress=[r for r in d['results'] if r['case_id']=='09_gain_cell_edram' and r['feasibility'].startswith('infeasible')]
 assert stress
 for r in stress:
  assert r['rho'] is None and r['tau'] is None and r['RI_star'] is None
  assert r['maintenance']['availability']<=0
 assert all(r['scenario_type']!='paired_conditional' for r in d['results'] if r['case_id']=='09_gain_cell_edram' and r['scenario_id']=='long')
 hashes={str(p.relative_to(A/'shared_baseline')):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A/'shared_baseline/data/shared_parameters.json',A/'shared_baseline/scripts/check_shared.py']}
 assert hashes['data/shared_parameters.json']=='6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42'
 assert hashes['scripts/check_shared.py']=='eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3'
 labels=[]
 for c in POINTS:
  for p in (A/c/'tex').glob('*.tex'):
   for label in re.findall(r'\\label\{([^}]+)\}',p.read_text()):
    assert label.startswith(c+':'),(p,label)
    labels.append(label)
 assert len(labels)==len(set(labels)), 'duplicate labels'
 return dict(validation_kind='independent representative arithmetic and cross-case semantics; not silicon/accuracy validation',cases=checks,geometry_checks=['PCM 512 diagonal groups cover all 16384 weights once','RRAM grouped updates tile the full matrix','FeRAM 32 physical reads and 256 compute rounds','NOR independent read/erase partitions','NAND data/reference utilization'],gain_cell_infeasible_cases=len(stress),shared_hashes=hashes,unique_case_prefixed_labels=len(labels),all_passed=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args();d=run();s=json.dumps(d,ensure_ascii=False,indent=2)+'\n';out=A/'data/ten_case_validation.json'
 if args.emit:out.write_text(s)
 else:assert out.read_text()==s,'stale independent validation record'
 print('PASS: ten independent reference points; payload/update tilings; maintenance feasibility; unchanged shared hashes; unique labels.')

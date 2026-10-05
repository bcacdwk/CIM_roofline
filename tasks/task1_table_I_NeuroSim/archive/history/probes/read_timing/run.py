#!/usr/bin/env python3
"""Run locked, unmodified V1.4 mechanism probes in a fresh local directory."""
import argparse, datetime, hashlib, json, math, os, pathlib, shutil, subprocess, sys
sys.dont_write_bytecode = True
SHA = '8a88abf85844c0e1ba17cc771ea535fff6040456'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(pathlib.Path.home()/'neurosim')));p.add_argument('--out',required=True);p.add_argument('--cxx',default=os.environ.get('CXX','g++-16'));a=p.parse_args()
 root=pathlib.Path(a.root).expanduser().resolve();out=pathlib.Path(a.out).expanduser().resolve();own=pathlib.Path(__file__).resolve().parent
 if root not in out.parents or any(x.lower() in str(root).lower() for x in ('onedrive','icloud','mobile documents')): raise SystemExit('out must be inside a nonsynchronized local root')
 if out.exists() and any(out.iterdir()): raise SystemExit('out must be new or empty')
 out.mkdir(parents=True,exist_ok=True);src=out/'src';src.mkdir();tmp=out/'tmp';tmp.mkdir()
 tree=pathlib.Path(json.loads((root/'worktrees.json').read_text())['2DInferenceV1.4']);core=tree/'Inference_pytorch/NeuroSIM'
 got=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
 if got!=SHA: raise SystemExit('locked SHA mismatch')
 hashes={}
 for f in sorted(core.iterdir()):
  if f.suffix in ('.cpp','.h'):
   shutil.copy2(f,src/f.name);hashes[f.name]=digest(f)
 shutil.copy2(own/'probe.cpp',src/'probe.cpp');shutil.copy2(__file__,out/'run.py')
 commands=[];checks=[];records={};env=dict(os.environ,TMPDIR=str(tmp))
 def command(argv,label):
  r=subprocess.run(argv,cwd=str(out),env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (out/(label+'.log')).write_text(r.stdout);commands.append({'argv':argv,'cwd':str(out),'returncode':r.returncode,'log':label+'.log'})
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  if r.returncode: raise RuntimeError(label+' failed; inspect '+str(out/(label+'.log')))
  return r.stdout
 exe=out/'probe';cpps=[str(f) for f in sorted(src.glob('*.cpp')) if f.name!='main.cpp']
 command([a.cxx,'-std=c++11','-O2','-fopenmp','-w','-I',str(src)]+cpps+['-o',str(exe)],'build')
 def run(label,*args):
  data={}
  for line in command([str(exe)]+list(map(str,args)),label).splitlines():
   if '=' in line:
    k,v=line.split('=',1)
    try:data[k]=float(v)
    except ValueError:pass
  records[label]=data;return data
 def check(name,ok,detail=None):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 def eq(x,y):return math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-20)
 for bits in (8,10):
  for nr in (1,2):
   for node,hz,lanes in ((22,1e9,1),(22,1e7,8),(65,1e9,1)):
    d=run('sar_%s_%s_%s_%s_%s'%(bits,nr,node,int(hz),lanes),'sar',node,lanes,nr,bits,hz)
    check('SAR formula '+str((bits,nr,node,hz,lanes)),eq(d['readLatency_s'],(bits+1)*1e-9*nr) and d['levelOutput']==2**bits and d['area_m2']>0)
 for sync in (0,1):
  for hz in (1e7,1e9):
   for nr in (1,2):
    d=run('dff_%s_%s_%s'%(sync,int(hz),nr),'dff',22,32,nr,sync,hz)
    expected=nr if sync else nr/(2*hz)
    check('DFF independent expected '+str((sync,hz,nr)),eq(d['readLatency_raw'],expected) and d['capTgDrain_F']>0)
 for width in (23,29):
  d=run('digital_'+str(width),'digital',width,2e8)
  check('digital tree physical/sync consistency '+str(width),d['tree_physical_s']>0 and d['tree_cycles']==math.ceil(d['tree_physical_s']*2e8) and d['output_dff_cycles']==1 and d['output_capLoad_F']>0)
  check('digital 200MHz compatibility '+str(width),d['tree_physical_s']<=5e-9,{'tree_delay_ns':d['tree_physical_s']*1e9,'assumed_serial_stages':['tree cycles','one output register cycle'],'pipeline_ii_proven':False})
 m=run('mutation','mutation');check('constructor mutation leaves stale dependents',m['after.featuresize_m']==m['before.featuresize_m'] and m['after.maxConductance_S']==m['before.maxConductance_S'] and m['after.numRowParallel']==128)
 for label,sync,planes,bits,mux,parallel,active in (
   ('sub_slow',1,1,1,2,8,16),('sub_zero',1,1,1,2,8,0),
   ('sub_mux4',1,1,1,4,8,16),('sub_rowgroup4',1,1,1,2,4,16),
   ('sub_reconstruction',1,2,8,4,8,16),('sub_async',0,1,1,2,8,16)):
  d=run(label,'subarray',sync,1e7,planes,bits,mux,parallel,active)
  check(label+' valid initialized path',all(math.isfinite(v) for v in d.values()) and d['area_m2']>0 and d['capCol_F']>0 and d['critical_s']>0 and d['readLatency_raw']>0)
  check(label+' derived configuration coherent',d['numRow']==16 and d['numCol']==16 and d['numAdd']==16//parallel and d['sar_lanes']==16//mux and d['param.maxConductance_S']==1/d['cell.resistanceOn_ohm'] and d['param.dumcolshared']==d['param.levelOutput'])
  check(label+' V1.4 write missing raw zero',d['writeLatency_raw']==0,{'normalized_write_ns':None,'status':'NOT_IMPLEMENTED_IN_AGGREGATION'})
  if sync:check(label+' ADC count owned by SubArray',d['readLatencyADC_raw']==mux*(16//parallel))
 check('SwitchMatrix sync write mixes cycles into seconds',records['sub_slow']['wl_driver_write_mixed_raw']>=1 and records['sub_slow']['wl_driver_dff_raw']==1 and records['sub_async']['wl_driver_write_mixed_raw']<1e-3,{'route':'do not use synchronous writeLatency; keep v3 write transaction'})
 s=records['sub_slow'];actual_period=max(1/s['param.clkFreq_hz'],s['critical_s']);conversion={'target_period_s':1/s['param.clkFreq_hz'],'physical_sensing_period_s':s['critical_s'],'actual_period_s':actual_period,'cycles':s['readLatency_raw'],'upstream_main_conversion_ns':s['readLatency_raw']*s['critical_s']*1e9,'adapter_conversion_ns':s['readLatency_raw']*actual_period*1e9,'clock_id':'probe_22nm_target10MHz','clock_domain_scope':'this probe only; not a ten-case frequency assignment'}
 check('slow target reveals main conversion mismatch',actual_period>s['critical_s'] and conversion['adapter_conversion_ns']>conversion['upstream_main_conversion_ns'])
 check('zero activity does not remove parallel fixed mux count',records['sub_zero']['activity']==0 and records['sub_zero']['readLatencyADC_raw']==s['readLatencyADC_raw'])
 # Primitive lanes are parallel: area scales, latency does not. Mux rounds remain an explicit outer scheduler count.
 b1=records['sar_8_1_22_1000000000_1'];b8=records['sar_8_1_22_10000000_8']
 check('parallel SAR lanes affect area not primitive latency',eq(b8['area_m2'],8*b1['area_m2']) and eq(b8['readLatency_s'],b1['readLatency_s']))
 summary={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','backend':{'branch':'2DInferenceV1.4','sha':SHA,'source_path':'Inference_pytorch/NeuroSIM','source_modified':False},'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'probe_source_sha256':digest(own/'probe.cpp'),'runner_sha256':digest(pathlib.Path(__file__)),'records':records,'clock_conversion':conversion,'assertions':checks,'upstream_source_sha256':hashes,'write_result':{'latency_ns':None,'status':'NOT_IMPLEMENTED_IN_V1_4_AGGREGATION'},'call_order':['fresh process','Param construction','restricted centralized configuration','InputParameter/Technology/MemCell binding via ProcessingUnitInitialize','SubArray Initialize','SubArray CalculateArea (inside ProcessingUnitInitialize)','SubArray CalculateLatency CalculateclkFreq=true: physical seconds','SubArray CalculateLatency CalculateclkFreq=false: cycles if synchronous, seconds otherwise'],'scope':'mechanism probe, not SRAM ACIM macro characterization or final ten-case results'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'status':summary['status'],'assertions':len(checks),'out':str(out),'clock_conversion':conversion}))
 return 0 if summary['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())

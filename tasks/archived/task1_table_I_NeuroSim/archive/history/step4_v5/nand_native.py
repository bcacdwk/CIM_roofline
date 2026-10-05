#!/usr/bin/env python3
"""Isolated native NAND peripheral builds; no change to reviewed P1/P2/P3 runners."""
import argparse,hashlib,json,math,os,re,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
from native_probe import dump,sha,execute
SPEC={'logic':('MLPInferenceV3.0','NeuroSim','src/nand_logic_probe.cpp',['Adder.cpp','Subtractor.cpp','Mux.cpp','RowDecoder.cpp','DFF.cpp','Technology.cpp','FunctionUnit.cpp','formula.cpp']),
      'sar':('2DTrainingV2.1','Training_pytorch/NeuroSIM','src/nand_sar_probe.cpp',['SarADC.cpp','Technology.cpp','FunctionUnit.cpp','formula.cpp','Param.cpp'])}
INTS={'technology_nm','temperature_K','logical_K','logical_N','lanes','adc_count','adc_bits','row_groups','page_bits','wordlines','blocks','bitlines'}
def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kind',choices=SPEC,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','/opt/homebrew/bin/g++-16'));a=p.parse_args();root=a.root.expanduser().absolute();out=root/'runs/step4-v5/p4'/('native-'+a.run_id+'-'+a.kind)
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id) or any(x.is_symlink() for x in (out,*out.parents)) or any(x in str(out) for x in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):raise ValueError('Unsafe native run path')
 r=json.loads(a.request.read_text());v=r['parameters']
 for key,value in v.items():
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise ValueError('Invalid numeric native parameter '+key)
  if key in INTS and not isinstance(value,int):raise ValueError('Native integer required')
 branch,core,driver,cpp=SPEC[a.kind];lock=json.loads((own/'provenance/dependencies.lock.json').read_text());dep=next(x for x in lock['branches'] if x['branch']==branch);tree=Path(json.loads((root/'worktrees.json').read_text())[branch]);head=subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
 if head!=dep['sha']:raise ValueError('Upstream SHA mismatch')
 out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();src=out/'src';src.mkdir();(src/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
 for f in (Path(__file__),own/'native_probe.py',own/driver,own/'provenance/dependencies.lock.json'):shutil.copy2(f,canon/f.name)
 dump(out/'input.json',r);upstream={}
 names=subprocess.check_output(['git','-C',str(tree),'ls-tree','-r','--name-only',head,core],text=True).splitlines()
 for name in names:
  f=Path(name)
  if str(f.parent)!=core or f.suffix not in ('.cpp','.h') or (f.suffix=='.cpp' and f.name not in cpp):continue
  data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name])
  if (tree/f).read_bytes()!=data:raise ValueError('Modified locked upstream '+name)
  (src/f.name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
 if a.kind=='logic':
  for name in ('Param.cpp','Param.h'):
   data=subprocess.check_output(['git','-C',str(tree),'show',head+':'+name]);(out/name).write_bytes(data);upstream[name]=hashlib.sha256(data).hexdigest()
  patch=own/'patches/mlp_decoder_consistency.patch';shutil.copy2(patch,canon/patch.name);execute(['patch','-p1','--batch','-i',canon/patch.name],src,out/'patch.log')
 declarations=['#pragma once','namespace request {']
 for key in sorted(v):
  if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key):raise ValueError('Invalid key')
  declarations.append('inline constexpr '+('int' if key in INTS else 'double')+' '+key+' = '+format(v[key],'.17g')+';')
 (src/'request.h').write_text('\n'.join(declarations)+'\n}\n');shutil.copy2(canon/Path(driver).name,src/'probe.cpp');exe=out/'native';argv=[a.cxx,'-std=c++17','-O2','-fopenmp','-I',src,*sorted(src.glob('*.cpp')),*([out/'Param.cpp'] if a.kind=='logic' else []),'-o',exe];execute(argv,out,out/'build.log');result=execute([exe],out,out/'native.log')
 if re.search(r'\b(?:Error|ERROR|V5_INVALID)\b',result):raise ValueError('Native error text')
 raw={k:float(value) for k,value in (line.split('=',1) for line in result.splitlines() if '=' in line)}
 if not raw or not all(math.isfinite(x) for x in raw.values()):raise ValueError('Invalid native fields')
 dump(out/'resolved.json',raw);dump(out/'source_manifest.json',{'backend':dep,'upstream':upstream,'canonical':{f.name:sha(f) for f in canon.iterdir()},'compiled_sources':{f.name:sha(f) for f in src.iterdir() if f.suffix in ('.h','.cpp')},'binary_sha256':sha(exe),'argv':list(map(str,argv))});print(json.dumps({'run_directory':str(out),'kind':a.kind,'status':'native_components_only'}))
if __name__=='__main__':main()

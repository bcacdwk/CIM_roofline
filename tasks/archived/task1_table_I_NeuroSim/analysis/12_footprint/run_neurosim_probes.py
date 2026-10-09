#!/usr/bin/env python3
"""Fresh isolated SRAM / 1T1R area-chain builds from locked NeuroSim sources."""
from __future__ import annotations
import argparse, difflib, hashlib, json, math, os, re, shutil, subprocess
from pathlib import Path
SHA = '8a88abf85844c0e1ba17cc771ea535fff6040456'
CORE = 'Inference_pytorch/NeuroSIM'
HERE = Path(__file__).resolve().parent

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, data): Path(p).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',Path.home()/'neurosim')))
    p.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'))
    args=p.parse_args(); out=args.run_dir.resolve()
    if 'OneDrive' in str(out): raise ValueError('Builds must remain outside OneDrive')
    out.mkdir(parents=True,exist_ok=False)
    tree=Path(json.loads((args.root/'worktrees.json').read_text())['2DInferenceV1.4'])
    assert subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()==SHA
    manifest={}
    for f in sorted((tree/CORE).iterdir()):
        if f.suffix not in ('.cpp','.h'): continue
        blob=subprocess.check_output(['git','-C',str(tree),'show',f'{SHA}:{CORE}/{f.name}'])
        assert hashlib.sha256(blob).hexdigest()==digest(f),f'Dirty upstream source: {f.name}'
        manifest[f.name]=digest(f)
    results=[]
    for name,kind in [('ordinary_sram',1),('conventional_1t1r',2)]:
        run=out/name; src=run/'src'; src.mkdir(parents=True); tmp=run/'tmp';tmp.mkdir()
        for name2 in manifest: shutil.copy2(tree/CORE/name2,src/name2)
        original=(src/'Param.cpp').read_text(); patched=original
        primaries={'operationmode':1,'memcelltype':kind,'technode':22,'temp':300,'deviceroadmap':2,'numRowSubArray':128,'numColSubArray':128,'relaxArrayCellWidth':0,'relaxArrayCellHeight':0}
        for key,value in primaries.items():
            patched,n=re.subn(r'(?m)^(\s*'+key+r'\s*=\s*)[^;]+;',lambda m:m[1]+str(value)+';',patched,count=1)
            assert n==1,key
        (src/'Param.cpp').write_text(patched)
        (run/'constructor.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='a/Param.cpp',tofile='b/Param.cpp')))
        shutil.copy2(HERE/'neurosim_area_probe.cpp',src/'area_probe.cpp')
        exe=run/'area_probe'
        cpp=[str(x) for x in sorted(src.glob('*.cpp')) if x.name!='main.cpp']
        command=[args.cxx,'-std=c++11','-O2','-fopenmp','-w','-I',str(src),*cpp,'-o',str(exe)]
        env=dict(os.environ,TMPDIR=str(tmp))
        build=subprocess.run(command,cwd=run,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (run/'build.log').write_text(build.stdout); dump(run/'build_command.json',command)
        build.check_returncode()
        execution=subprocess.run([str(exe)],cwd=run,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (run/'execution.log').write_text(execution.stdout); execution.check_returncode()
        values={}
        for line in execution.stdout.splitlines():
            if '=' in line:
                key,value=line.split('=',1)
                try: values[key]=float(value)
                except ValueError: pass
        assert all(math.isfinite(v) for v in values.values())
        expected=values['rows']*values['columns']*values['cell_width_in_feature_size']*values['cell_height_in_feature_size']*values['tech_featureSize_m']**2
        assert math.isclose(expected,values['areaArray_m2'],rel_tol=1e-12)
        assert math.isclose(values['area_m2']-values['usedArea_m2'],values['emptyArea_m2'],rel_tol=1e-12)
        assert values['area_m2']>=values['usedArea_m2']>=values['areaArray_m2']>0
        results.append({'name':name,'constructor_primaries':primaries,'values':values,'analytical_areaArray_m2':expected,'checks_passed':True,'constructor_patch_sha256':digest(run/'constructor.patch')})
    result={'scope':'Diagnostic ordinary SRAM and conventional 1T1R only; not ten-case geometries or macro PPA','upstream_branch':'2DInferenceV1.4','upstream_sha':SHA,'upstream_core':CORE,'compiler':subprocess.check_output([args.cxx,'--version'],text=True).splitlines()[0],'source_hashes':manifest,'probe_sha256':digest(HERE/'neurosim_area_probe.cpp'),'runner_sha256':digest(__file__),'results':results}
    dump(out/'probe_results.json',result)
    print(json.dumps({'output':str(out/'probe_results.json'),'results':[{k:x[k] for k in ('name','values','checks_passed')} for x in results]},indent=2))
if __name__=='__main__': main()

#!/usr/bin/env python3
"""Fresh locked NeuroSim planar-NMOS geometry primitives for native unit models.
No electrical Technology initialization, SubArray, timing, or macro evaluation.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
SHA='8a88abf85844c0e1ba17cc771ea535fff6040456'
CORE='Inference_pytorch/NeuroSIM'
UPSTREAM_FILES=['formula.cpp','formula.h','Technology.cpp','Technology.h','Param.h','constant.h','typedef.h']

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--model-input',type=Path,default=HERE/'model_inputs.json')
    parser.add_argument('--model-module',type=Path,default=HERE/'geometry_models.py')
    parser.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',Path.home()/'neurosim')))
    parser.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'))
    args=parser.parse_args();out=args.run_dir.resolve()
    if 'OneDrive' in str(out):raise ValueError('New builds and logs must be outside OneDrive')
    out.mkdir(parents=True,exist_ok=False);src=out/'src';src.mkdir();tmp=out/'tmp';tmp.mkdir()
    import importlib.util
    spec=importlib.util.spec_from_file_location('geometry_model_requests',args.model_module)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    inputs=json.loads(args.model_input.read_text());queries=module.primitive_queries(inputs)
    assert queries and len({q['id'] for q in queries})==len(queries)
    tree=Path(json.loads((args.root/'worktrees.json').read_text())['2DInferenceV1.4'])
    assert subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()==SHA
    hashes={}
    for name in UPSTREAM_FILES:
        f=tree/CORE/name
        original=subprocess.check_output(['git','-C',str(tree),'show',f'{SHA}:{CORE}/{name}'])
        assert hashlib.sha256(original).hexdigest()==digest(f),('modified upstream',name)
        hashes[name]=digest(f);shutil.copy2(f,src/name)
    shutil.copy2(HERE/'planar_nmos_probe.cpp',src/'planar_nmos_probe.cpp')
    exe=out/'planar_nmos_probe'
    command=[args.cxx,'-std=c++11','-O2','-w','-I',str(src),str(src/'formula.cpp'),str(src/'Technology.cpp'),str(src/'planar_nmos_probe.cpp'),'-o',str(exe)]
    env=dict(os.environ,TMPDIR=str(tmp))
    run=subprocess.run(command,cwd=out,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'build.log').write_text(run.stdout);dump(out/'build_command.json',command);run.check_returncode()
    keys=['id','F_um','W_um','L_um','H_um','contact_um','gap_um','enclosure_um']
    stdin=''.join(' '.join(str(q[k]) for k in keys)+'\n' for q in queries)
    (out/'primitive_request.txt').write_text(stdin);dump(out/'primitive_queries.json',queries)
    run=subprocess.run([str(exe)],cwd=out,env=env,input=stdin,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'execution.log').write_text(run.stdout);run.check_returncode()
    fields=['native_width_um','native_height_um','native_area_um2','fingers','length_correction_um','contact_span_um','adapted_width_um']
    by={q['id']:q for q in queries};primitives={}
    for parts in csv.reader(run.stdout.splitlines()):
        if not parts:continue
        assert len(parts)==8 and parts[0] in by,parts
        q=by[parts[0]];values=dict(zip(fields,map(float,parts[1:])))
        assert all(math.isfinite(v) and v>=0 for v in values.values())
        values['fingers']=int(values['fingers']);assert values['fingers']>=1
        assert math.isclose(values['native_area_um2'],values['native_width_um']*values['native_height_um'],rel_tol=1e-12)
        assert math.isclose(values['length_correction_um'],values['fingers']*(q['L_um']-q['F_um']),rel_tol=1e-12)
        assert math.isclose(values['adapted_width_um'],max(values['native_width_um']+values['length_correction_um'],values['contact_span_um']),rel_tol=1e-12)
        values['query']=q;primitives[parts[0]]=values
    assert set(primitives)==set(by)
    record={'schema_version':'planar-nmos-geometry-primitives-1','upstream_sha':SHA,'upstream_branch':'2DInferenceV1.4','source_hashes':hashes,
      'input_sha256':module.digest_object(inputs),'query_sha256':module.digest_object(queries),
      'adapter_sha256':digest(HERE/'planar_nmos_probe.cpp'),'runner_sha256':digest(__file__),'model_module_sha256':digest(args.model_module),
      'compiler':subprocess.check_output([args.cxx,'--version'],text=True).splitlines()[0],
      'geometry_method':'Locked CalculateGateArea(INV,1,Wn,0,H,tech) bulk planar branch; featureSize is an explicit geometry scale, not an initialized electrical process model.',
      'adapter_corrections':'fingers*(L-Fgeom) channel-length correction, then max against contacted source/drain span; +1e-12 um numerical H guard avoids false folding at an exact floating boundary.',
      'scope':'NMOS lower-plane geometry only; full native repeated-tile access/contact/routing and storage overlap are resolved by geometry_models.py. No electrical/timing claims.',
      'primitives':primitives}
    # Execute the consumer as well: all typed bindings and layout invariants must pass.
    models=module.calculate_models(inputs,record)
    dump(out/'primitive_record.json',record);dump(out/'geometry_model_results.json',models)
    print(json.dumps({'output':str(out/'primitive_record.json'),'primitive_count':len(primitives),'cases':{k:v['area_xy_um2'] for k,v in models['case_results'].items()},'checks':'PASS'},indent=2))
if __name__=='__main__':main()

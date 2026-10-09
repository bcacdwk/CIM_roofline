#!/usr/bin/env python3
"""Compute native SLC storage footprints; render density and F_mem²/bit panels."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, sys
from decimal import Decimal, localcontext
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
COLORS=['#2d63ad','#6e52a2','#a37622','#68737d','#c54e55','#178276','#ca6b2b','#338fa5','#7b8736','#ad5390']
CASE_IDS=['01_sram_acim','02_sram_dcim','03_nor_2d','04_nand_3d','05_rram','06_mram','07_pcm','08_feram_hfo2','09_gain_cell_edram','10_fenor_3d']
FIELDS=['row_id','case_id','label','evidence_class','unit_description','reference_identity','identity_relation','area_xy_um2','independent_bits','a_bit_um2','density_Mbit_mm2','F_mem_nm','F_kind','F_definition','alpha_F_mem2_per_bit','effective_layers','bits_per_layer','source_refs','missing_reason']
NUMBERS=['area_xy_um2','independent_bits','a_bit_um2','density_Mbit_mm2','F_mem_nm','alpha_F_mem2_per_bit']

def dec(v): return Decimal(str(v))
def decimal_string(v): return format(v,'f')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d): Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def close(a,b): return abs(a-b)<=max(abs(a),abs(b))*Decimal('1e-45')

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def check_reference_locks(document,result,lock_path):
    """Protect every field of the six accepted cases while completing four gaps."""
    lock=json.loads(lock_path.read_text())
    for key,rows,id_key in [('input_rows',document['cases'],'case_id'),
                            ('result_rows',result['main_rows'],'case_id'),
                            ('nand_diagnostic_rows',result['diagnostic_rows'],'row_id')]:
        by={r[id_key]:r for r in rows}
        for name,expected in lock[key].items():
            assert canonical_hash(by[name])==expected,('locked existing reference changed',key,name)
    return {'six_input_and_result_rows_unchanged':True,'nand_diagnostics_unchanged':True,'baseline_git_sha':lock['baseline_git_sha']}

def resolve_geometry_models(document,model_input_path,primitive_path):
    """Recompute newly modeled units and bind the authority area to that model."""
    modeled=[r for r in document['cases'] if r.get('model_ref')]
    if not modeled:
        return None
    from geometry_models import calculate_models
    inputs=json.loads(model_input_path.read_text())
    primitives=json.loads(primitive_path.read_text())
    models=calculate_models(inputs,primitives)
    for row in modeled:
        value=models['case_results'][row['case_id']]
        assert dec(row['area_xy_um2'])==dec(value['area_xy_um2']),('model area binding',row['case_id'])
        assert int(row['independent_bits'])==int(value['independent_bits']),('model bit binding',row['case_id'])
        assert dec(row['F_mem_nm'])==dec(value['F_mem_nm']),('model normalization binding',row['case_id'])
        row['area_xy_um2']=str(value['area_xy_um2'])
    models['binding_provenance']={'model_input_sha256':digest(model_input_path),
        'primitive_record_sha256':digest(primitive_path),'model_code_sha256':digest(HERE/'geometry_models.py'),
        'case_ids':[r['case_id'] for r in modeled],
        'policy':'Fresh model computation is required; typed authority area must match exactly. Ordinary SRAM/1T1R diagnostic areas are not used.'}
    return models

def derive(raw):
    r=dict(raw); exact={}
    with localcontext() as ctx:
        ctx.prec=50
        A=r.get('area_xy_um2');b=r.get('independent_bits');f=r.get('F_mem_nm')
        if A is not None:
            A=dec(A);b=dec(b);assert A>0 and b>0 and b==b.to_integral_value()
            a=A/b;density=1/a
            assert close(a*density,Decimal(1))
            exact.update(area_xy_um2=A,independent_bits=b,a_bit_um2=a,density_Mbit_mm2=density)
            if f is not None:
                f=dec(f);assert f>0;fsq=(f/1000)**2;alpha=a/fsq
                assert close(alpha*fsq,a)
                # Altering normalization alone preserves the absolute geometry/density.
                assert close((a/((2*f/1000)**2))*4,alpha)
                exact.update(F_mem_nm=f,alpha_F_mem2_per_bit=alpha)
            else:
                r['alpha_F_mem2_per_bit']=None
        else:
            assert r.get('missing_reason'),r['case_id']
            for k in ('a_bit_um2','density_Mbit_mm2','alpha_F_mem2_per_bit'):r[k]=None
        if f is not None and 'F_mem_nm' not in exact: exact['F_mem_nm']=dec(f)
        for k,v in exact.items():r[k]=float(v)
        r['exact_decimal']={k:decimal_string(v) for k,v in exact.items()}
        for k in NUMBERS:r.setdefault(k,None)
    return r

def compute(document):
    raw=document['cases'];assert [r['case_id'] for r in raw]==CASE_IDS
    rows=[];diagnostics=[]
    for source in raw:
        r=dict(source)
        assert r['bits_per_storage_element']==1,'Only SLC is authorized'
        if r['case_id']=='06_mram':assert r['independent_bits'] in (1,'1',None),'Complementary 2T2MTJ bitcell is one independent bit'
        if r.get('projection'):
            assert r['case_id']=='04_nand_3d'
            original=dict(r);original.pop('projection');original['row_id']='04_nand_3d_source_L0';original['main_plot']=False
            original=derive(original);diagnostics.append(original)
            L0=int(r['effective_layers']);per=int(r['bits_per_layer']);assert L0>0 and per>0
            assert dec(r['independent_bits'])==L0*per
            one=dict(source);one.pop('projection');one.update(row_id='04_nand_3d_single_layer_check',label='3D NAND, SLC, 1-layer algebraic check',effective_layers=1,independent_bits=per,main_plot=False,evidence_class='algebraic_check')
            diagnostics.append(derive(one))
            r.update(row_id='04_nand_3d_500_layer_projection',effective_layers=500,independent_bits=500*per,evidence_class='projection',main_plot=True,label='3D NAND, SLC, 500-layer projection')
            result=derive(r)
            with localcontext() as ctx:
                ctx.prec=50
                a0=dec(original['exact_decimal']['a_bit_um2']);a500=dec(result['exact_decimal']['a_bit_um2'])
                assert close(a500,a0*L0/500),'Fold L0 to 500 exactly once'
                d0=dec(original['exact_decimal']['density_Mbit_mm2']);d500=dec(result['exact_decimal']['density_Mbit_mm2'])
                assert close(d500,d0*500/L0)
                if result['alpha_F_mem2_per_bit'] is not None:
                    assert close(dec(result['exact_decimal']['alpha_F_mem2_per_bit']),dec(original['exact_decimal']['alpha_F_mem2_per_bit'])*L0/500)
            rows.append(result)
        else:
            r.setdefault('row_id',r['case_id']);r['main_plot']=True;rows.append(derive(r))
    return {'schema_version':1,'definition':document['definition'],'input_sha256':None,'main_rows':rows,'diagnostic_rows':diagnostics,'checks':{'reciprocal_units':True,'alpha_reconstruction':True,'normalization_invariance':True,'slc_only':True,'complementary_bit_count':True,'nand_single_folding':any(r['case_id']=='04_nand_3d' and r.get('projection') for r in rows)}}

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
        for r in rows:
            out={k:r.get('exact_decimal',{}).get(k,r.get(k)) for k in FIELDS}
            for k,v in out.items():
                if isinstance(v,(dict,list)):out[k]=json.dumps(v,ensure_ascii=False,separators=(',',':'))
            writer.writerow(out)

def plot(result,out):
    os.environ.setdefault('MPLCONFIGDIR',str(Path.home()/'.cache/cim-roofline/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from matplotlib.ticker import LogLocator, NullFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.edgecolor':'#afbac5','axes.labelcolor':'#182838','text.color':'#182838','xtick.color':'#657382','ytick.color':'#657382','hatch.linewidth':0.6})
    rows=result['main_rows'];fig,axes=plt.subplots(1,2,figsize=(16.6,9.0))
    fig.subplots_adjust(left=.063,right=.983,top=.77,bottom=.39,wspace=.21)
    fig.text(.063,.944,'Native binary storage density and bit footprint',fontsize=21,weight='bold')
    fig.text(.063,.895,'Same repeated cell / tile, projected area and independent-bit count in both panels',fontsize=12,color='#657382')
    fig.text(.063,.849,'3D NAND, SLC, 500-layer projection: fixed lateral cell grid; 500 effective data layers',fontsize=11,color='#495765')
    labels=['SRAM ACIM','SRAM DCIM','2D NOR\nGF28 ESF3 ref.','3D NAND\n500-layer','RRAM\nWH-2T1R model','MRAM','PCM, 28 nm\n1T1R geometry ref.','HZO FeRAM\n130 nm CUB model','GC-04\neDRAM','Vertical AND\nFeFET, 4 layers']
    for ax,key,ylabel,title,direction in zip(axes,['density_Mbit_mm2','alpha_F_mem2_per_bit'],['Storage density [Mbit/mm²]',r'Normalized bit footprint [$F_{\mathrm{mem}}^2$/bit]'],['(a) Absolute storage density','(b) Normalized bit footprint'],['Higher is denser','Lower is more compact']):
        vals=[r[key] for r in rows if r[key] is not None]
        low=10**math.floor(math.log10(min(vals)*.65));high=10**math.ceil(math.log10(max(vals)*2.3))
        ax.set_yscale('log');ax.set_ylim(low,high);ax.set_xlim(-.65,9.65)
        ax.set_ylabel(ylabel,fontsize=11);ax.set_title(title,loc='left',fontsize=13,weight='bold',pad=23)
        ax.text(1,1.025,direction,transform=ax.transAxes,ha='right',fontsize=9.5,color='#657382')
        ax.set_axisbelow(True);ax.grid(axis='y',which='major',color='#e5eaf0',linewidth=.8)
        ax.yaxis.set_major_locator(LogLocator(base=10,numticks=9));ax.yaxis.set_minor_formatter(NullFormatter())
        for spine in ('top','right'):ax.spines[spine].set_visible(False)
        for i,r in enumerate(rows):
            v=r[key]
            if v is None:
                ax.text(i,low*1.25,'N/A',ha='center',va='bottom',rotation=90,fontsize=9,color='#77838e')
                # Missing geometry is text-only, never a zero-height bar.
            else:
                hatch={'reported_geometry':'','geometric_estimate':'..','reference_proxy':'xx','projection':'///'}[r['evidence_class']]
                ax.bar(i,v-low,bottom=low,width=.63,color=COLORS[i],edgecolor='#233747',linewidth=.55,hatch=hatch)
                suffix='*' if key=='alpha_F_mem2_per_bit' and r['F_kind']=='nominal_node' else ''
                ax.text(i,v*1.13,f'{v:.3g}'+suffix,ha='center',va='bottom',fontsize=9,weight='bold')
        ax.set_xticks(range(10),labels,rotation=55,ha='right',fontsize=9.4)
        ax.tick_params(axis='x',length=0,pad=8)
    legend=[Patch(facecolor='#cad4dc',edgecolor='#233747',label='Reported geometry (incl. vendor)'),Patch(facecolor='#cad4dc',edgecolor='#233747',hatch='..',label='Model / engineering geometry'),Patch(facecolor='#cad4dc',edgecolor='#233747',hatch='xx',label='Published geometry proxy'),Patch(facecolor='#cad4dc',edgecolor='#233747',hatch='///',label='500-layer projection')]
    fig.legend(handles=legend,loc='lower left',bbox_to_anchor=(.063,.205),ncol=4,frameon=False,fontsize=9.7,borderaxespad=0)
    notes=[
      'Binary / SLC storage; a forced-complement pair counts as one independent bit. No multilevel capacity gain is applied.',
      '* Nominal-node normalization is identified separately from physical half-pitch; normalized bars do not share one universal F definition.',
      'NOR uses GF 28SLPe / SST ESF3; PCM uses a 28 nm 1T1R geometry reference. Neither replaces the existing throughput configuration.',
      'Projection excludes macro staircase / edge overhead. It is a density scenario, not a verified 500-layer SLC device or the existing throughput hardware.',
      'Cell / tile density excludes macro ADCs, reduction, pumps, I/O and global control; it is not effective INT8 weight density or complete-chip density.']
    for y,line in zip((.170,.139,.108,.077,.046),notes):fig.text(.063,y,line,fontsize=9.2,color='#657382')
    for ext in ('png','svg','pdf'):fig.savefig(out/f'storage_density_footprint.{ext}',dpi=220,facecolor='white',metadata={'Creator':'build_footprint.py'} if ext=='pdf' else None)
    plt.close(fig)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=HERE/'geometry_inputs.json');p.add_argument('--output-dir',type=Path,default=HERE/'results');p.add_argument('--figure-dir',type=Path,default=HERE/'output');p.add_argument('--model-input',type=Path,default=HERE/'model_inputs.json');p.add_argument('--primitive-record',type=Path,default=HERE/'primitive_record.json');p.add_argument('--no-figures',action='store_true');args=p.parse_args()
    document=json.loads(args.input.read_text())
    model_result=resolve_geometry_models(document,args.model_input,args.primitive_record)
    result=compute(document);result['input_sha256']=digest(args.input);result['generator_sha256']=digest(__file__)
    result['reference_lock_checks']=check_reference_locks(document,result,args.input.parent/'reference_lock.json')
    if model_result:
        result['geometry_model_binding']=model_result['binding_provenance']
        result['checks']['new_geometry_models_recomputed_and_bound']=True
    args.output_dir.mkdir(parents=True,exist_ok=True);dump(args.output_dir/'footprint_results.json',result)
    if model_result:dump(args.output_dir/'geometry_model_results.json',model_result)
    write_csv(args.output_dir/'footprint_main.csv',result['main_rows']);write_csv(args.output_dir/'footprint_all_rows.csv',result['main_rows']+result['diagnostic_rows'])
    if not args.no_figures:args.figure_dir.mkdir(parents=True,exist_ok=True);plot(result,args.figure_dir)
    print(json.dumps({'checks':result['checks'],'main_rows':len(result['main_rows']),'quantified_rows':sum(r['density_Mbit_mm2'] is not None for r in result['main_rows']),'diagnostic_rows':len(result['diagnostic_rows'])},indent=2))
if __name__=='__main__': main()

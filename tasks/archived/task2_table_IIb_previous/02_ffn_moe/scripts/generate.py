#!/usr/bin/env python3
"""Six fixed FFNs / single routed experts; shared production calculator.

Default is a read-only reproducibility check; --emit refreshes local artifacts.
Independent expectations live in check.py and never import this module.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

LOCAL = Path(__file__).resolve().parents[1]
ROOT = LOCAL.parents[1]
sys.path.insert(0, str(ROOT / 'shared/scripts'))
import counting as c

START = 'e472a0d864b8fb9afb14b0c306217a0e5653e122'
NAMES = ['Qwen3.5-2B','Ministral 3 8B','Qwen3.6-35B-A3B','Hy3 (295B)','Ling-1T','MiMo-V2.5-Pro']


def read(path): return json.loads((ROOT / path).read_text())
def sha(path): return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
def serial(value): return json.dumps(c.encode(value), ensure_ascii=False, indent=2) + '\n'


def layout(n, k):
    def axis(size):
        full, tail = divmod(size, 128)
        return dict(full_128_blocks=full, tail_valid_elements=tail, blocks=full + bool(tail))
    tiles = c.ceildiv(n,128) * c.ceildiv(k,128)
    return dict(matrix_N_K_per_copy=[n,k], copies=1, output_axis=axis(n), input_axis=axis(k),
                resident_tiles=tiles, valid_resident_bytes=n*k, allocated_tile_bytes=tiles*16384)


def make():
    plan = read('data/study_plan.json'); contract = read('shared/data/conventions.json')
    models = {m['id']:m for m in read('data/models.json')['models']}
    ids = plan['table_IIb']['columns_model_ids']
    assert len(ids) == 6 and plan['parameters']['B'] == [8,64,512]
    assert contract['reference_id'] == 'WS128-INT8-semantic-banks-v1'
    assert contract['mapping']['tile_N'] == contract['mapping']['tile_K'] == 128
    assert all(v == 1 for v in contract['precision']['role_bytes'].values())
    config = dict(schema_version='1.0', calculation='task2-step4-ffn-moe-v1',
                  reviewed_step3_and_start_HEAD=START, shared_reference_id=contract['reference_id'],
                  primary_boundary='ports', contrast_boundary='operator', tile_N_K=[128,128],
                  precision_role_bytes=contract['precision']['role_bytes'],
                  B=plan['parameters']['B'], model_order=ids, path_base='task2 root',
                  scope='one dense FFN or one routed expert; gate/up/down only; one load, B vector uses',
                  excluded_multipliers=['layers','top-k','all routed experts','shared experts'],
                  models={}, source_files_sha256={}, registered_sources=[])
    source_paths = ['data/models.json','data/sources.json','shared/data/conventions.json',
                    'shared/scripts/counting.py','shared/tex/counting_method.zh.tex',
                    'table_IIb/pilot/data/results.json',
                    'literature/02_ministral3_8b/raw/params.json',
                    'literature/04_hy3_295b/raw/convert_ckpt_to_outer.py',
                    'literature/00_shared/raw/transformers/configuration_hy_v3.py']
    registry = {s['local_path']:s for s in read('data/sources.json')}
    records=[]
    for mid in ids:
        m=models[mid]; f=m['ffn']; material=m['local_material']
        config['models'][mid] = dict(display_name=m['display_name'], model_revision=m['identity']['revision'],
            repository_url=m['identity']['repository_url'], selected_layer=f['selected_layer_index_zero_based'],
            D=f['hidden_size'], F=f['intermediate_size'], selected_kind=f['selected_kind'],
            native_precision=m['precision'], ffn=f, local_material=material)
        source_paths += [material[k] for k in ['raw_config','raw_model_card','implementation','structure_card']]
        source_paths.append(str(Path(material['raw_config']).with_name('hf_metadata.json')))
        for B in config['B']:
            result=c.ffn(f['hidden_size'],f['intermediate_size'],B)
            for part,(n,k) in f['matrices'].items():
                result['parts'][part]['layout']=layout(n,k)
                result['parts'][part]['window']=dict(input_vectors=B,full_weight_loads=1)
            result['capacity']={key:sum(p['layout'][key] for p in result['parts'].values())
                for key in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']}
            result['capacity']['meaning']='final state capacity; distinct from cumulative Q_R and from physical encoded capacity'
            records.append(dict(case_id=f'{mid}/ffn_or_moe/{B}',model_id=mid,row='ffn_or_moe',B=B,
                model_revision=m['identity']['revision'],selected_layer=f['selected_layer_index_zero_based'],
                shared_reference_id=contract['reference_id'],result=result))
    for path in sorted(set(source_paths)):
        config['source_files_sha256'][path]=sha(path)
        if path in registry:
            s=registry[path]
            config['registered_sources'].append({k:s[k] for k in ['id','url','revision','local_path','sha256'] if k in s})
    return config,dict(schema_version='1.0',cases=records)


def texnum(value):
    if isinstance(value,Fraction) and value.denominator != 1:
        return r'\frac{'+str(value.numerator)+'}{'+str(value.denominator)+'}'
    return str(value)


def table(rows, columns):
    return '\n'.join([r'\begin{tabular}{@{}'+columns+r'@{}}\toprule',*rows,r'\bottomrule\end{tabular}',''])


def outputs():
    config,data=make(); files={'data/config.json':serial(config),'data/results.json':serial(data)}
    out=io.StringIO(); w=csv.writer(out,lineterminator='\n')
    w.writerow(['case_id','component','boundary','Q_S_Byte_exact','Q_R_Byte_exact','RI_exact','tile_evaluations','valid_resident_Byte','allocated_tile_Byte','resident_tiles'])
    for r in data['cases']:
        for name,p in [('total',r['result']),*r['result']['parts'].items()]:
            cap=p.get('capacity',p.get('layout'))
            for b in ['ports','operator']:
                d=p[b];w.writerow([r['case_id'],name,b,*[d[k] for k in ['Q_S','Q_R','RI','tile_evaluations']],
                    *[cap[k] for k in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']]])
    files['data/results.csv']=out.getvalue()
    rows=[r'模型 & 层 & 对象 & $D$ & $F$ & $3DF$ (MiB) & tiles\\\midrule']
    shape_rows=[r'模型 & gate / up 的 $N\times K$ & down 的 $N\times K$ & 单矩阵 tiles\\\midrule']
    op_rows=[r'模型 & $B=8$ & $B=64$ & $B=512$\\\midrule']
    demand_rows=[r'模型 & $Q_R$ & $Q_S^{\rm ports}/B$ & $Q_S^{\rm op}/B$ & $C/B$\\\midrule']
    md=['# 六模型 FFN / 单路由专家概览','',
        '固定模型顺序；每窗口完整装载 gate/up/down 一次，B=8,64,512 为同一权重实际服务的向量数。所有 Byte 与分数均精确。','',
        '| 模型 | 层（零起点） | 对象 | D | F | Q_R / 容量 (Byte) | resident tiles |',
        '|---|---:|---|---:|---:|---:|---:|']
    for mid,name in zip(config['model_order'],NAMES):
        m=config['models'][mid];D,F=m['D'],m['F']; kind='Dense' if m['selected_kind']=='dense_swiglu' else '单专家'
        cases=[r for r in data['cases'] if r['model_id']==mid];r=cases[0]['result'];cap=r['capacity']
        rows.append(f'{name} & {m["selected_layer"]} & {kind} & {D} & {F} & {3*D*F//1048576} & {cap["resident_tiles"]}'+r'\\')
        shape_rows.append(f'{name} & ${F}\\times {D}$ & ${D}\\times {F}$ & {cap["resident_tiles"]//3}'+r'\\')
        op_rows.append(name+' & '+' & '.join('$'+texnum(x['result']['operator']['RI'])+'$' for x in cases)+r'\\[3pt]')
        demand_rows.append(name+' & '+' & '.join(str(x) for x in [3*D*F,r['ports']['Q_S']/8,r['operator']['Q_S']/8,cap['resident_tiles']])+r'\\')
        md.append(f'| {m["display_name"]} | {m["selected_layer"]} | {kind} | {D} | {F} | {3*D*F:,} | {cap["resident_tiles"]:,} |')
    files['tex/overview.generated.tex']=table(rows,'llrrrrr')
    files['tex/shapes.generated.tex']=table(shape_rows,'lrrr')
    files['tex/operator_ri.generated.tex']=table(op_rows,'lrrr')
    files['tex/demand.generated.tex']=table(demand_rows,'lrrrr')
    md += ['', 'ports RI 六模型均为 **1/16, 1/2, 4**；Q_S、调用数随 B 线性增加，Q_R、容量、resident tiles 不变。','',
           '| 模型 | operator RI，B=8 | B=64 | B=512 |','|---|---:|---:|---:|']
    for mid in config['model_order']:
        md.append('| '+config['models'][mid]['display_name']+' | '+' | '.join(str(r['result']['operator']['RI']) for r in data['cases'] if r['model_id']==mid)+' |')
    md+=['','六组 D、F 均整除 128，每项 ports Q_S=BDF/128、Q_R=DF，故总 RI=B/128。operator 汇总从三独立入口扣除 BD，保留 down 的新输入 BF，RI=B(D+F)/(3DF)。Qwen3.5 与 MiMo 的 D/F 互换，ports 和汇总 operator 全部相同；独立 gate/up 与 down 的 operator 输入互换，共享扣除量不同。','',
          '精确 18 工况与 54 分项见 [JSON](data/results.json) / [CSV](data/results.csv)；来源见 [config.json](data/config.json)，复算见 [checks.json](data/checks.json)。','']
    files['OVERVIEW.zh.md']='\n'.join(md)
    return files


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--emit',action='store_true');args=parser.parse_args()
    for name,content in outputs().items():
        target=LOCAL/name
        if args.emit:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
        else: assert target.read_text()==content, f'stale artifact: {name}'
    print('PASS: 18 FFN/MoE cases; 54 matrix parts; exact JSON/CSV and overview regenerated')


if __name__=='__main__': main()

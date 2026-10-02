#!/usr/bin/env python3
"""Main-agent acceptance: fixed schema, independent demands, migration, merger.

No producer imports. Default is read-only; --emit writes only this fourth folder.
READY manifests must already exist and match before any merged output is emitted.
"""
import argparse
from fractions import Fraction as F
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[1]
TASK=HERE.parents[1]
TABLE=HERE.parent
sys.path.insert(0,str(TASK / "scripts"))
from format_results import ri_decimal, count_label
ARCHIVE=TASK.parent/'archived/task2_table_IIb_previous'
FOLDERS=['01_qkv_projection','02_ffn_moe','03_attention']
WORKLOADS=['qkv_projection','ffn_or_moe','attention_prefill','attention_decode']


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(x):
    if isinstance(x,dict):
        if set(x)=={'numerator','denominator'}:return F(x['numerator'],x['denominator'])
        return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list):return [decode(v) for v in x]
    return x


def encode(x):
    if isinstance(x,F):return x.numerator if x.denominator==1 else dict(numerator=x.numerator,denominator=x.denominator)
    if isinstance(x,dict):return {k:encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [encode(v) for v in x]
    return x


def demand(s,r,initial,final):
    return dict(Q_S=s,Q_R=r,RI='infinity' if s=='infinity' else F(s,r),resident_bytes_initial=initial,resident_bytes_final=final)


def oracle(m,case):
    """Rows/valid causal prefixes from native dimensions; no partitioning."""
    row,U,L=case['workload'],case['U'],case['L'];D=m['D'];parts={}
    if row in ['qkv_projection','ffn_or_moe']:
        if row=='qkv_projection':
            specs=[('Q',m['H_q']*m['d_QK'],D,'x')]
            if m['D_g']:specs.append(('G',m['D_g'],D,'x'))
            specs += [('K',m['H_kv']*m['d_QK'],D,'x'),('V',m['H_kv']*m['d_V'],D,'x')]
        else:specs=[('gate',m['F'],D,'x'),('up',m['F'],D,'x'),('down',D,m['F'],'z')]
        sources={}
        for name,n,k,source in specs:
            weights=sum(len(range(k)) for _ in range(n))
            s='infinity' if U=='infinity' else sum(len(range(k)) for _ in range(U))
            parts[name]=dict(shape_N_K=[n,k],state_copies=1,**demand(s,weights,0,weights))
            assert source not in sources or sources[source]==k
            sources[source]=k
        total_input='infinity' if U=='infinity' else sum(sum(sources.values()) for _ in range(U))
        overlap='infinity' if U=='infinity' else sum(p['Q_S'] for p in parts.values())-total_input
    else:
        q,h,dq,dv=m['H_q'],m['H_kv'],m['d_QK'],m['d_V']
        initial=0 if row=='attention_prefill' else L-1
        prefixes=range(1,L+1) if row=='attention_prefill' else [L]
        s_qk=s_av=0
        for i in prefixes:s_qk+=q*dq;s_av+=q*i
        r_k=sum(h*dq for _ in range(initial,L));r_v=sum(h*dv for _ in range(initial,L))
        parts['QK']=dict(shape_N_K=[L,dq],state_copies=h,**demand(s_qk,r_k,initial*h*dq,L*h*dq))
        parts['AV']=dict(shape_N_K=[dv,L],state_copies=h,**demand(s_av,r_v,initial*h*dv,L*h*dv))
        total_input=s_qk+s_av;overlap=0
    total=demand(total_input,sum(p['Q_R'] for p in parts.values()),
        sum(p['resident_bytes_initial'] for p in parts.values()),sum(p['resident_bytes_final'] for p in parts.values()))
    total['shared_input_bytes_removed']=overlap
    return total,parts


def to_csv(cases,columns):
    buf=io.StringIO();writer=csv.DictWriter(buf,columns,lineterminator='\n');writer.writeheader()
    for c in cases:
        for name,item in [('total',c['result'])]+[(p['id'],p) for p in c['components']]:
            row={k:c[k] for k in columns[:8]};row['component']=name
            row.update(Q_S_Byte=item['Q_S'],Q_R_Byte=item['Q_R'],RI_exact=str(item['RI']),
                resident_initial_Byte=item['resident_bytes_initial'],resident_final_Byte=item['resident_bytes_final'])
            if name=='total':row['shared_input_removed_Byte']=item['shared_input_bytes_removed']
            else:row.update(N=item['shape_N_K'][0],K=item['shape_N_K'][1],state_copies=item['state_copies'])
            writer.writerow(row)
    return buf.getvalue()


def preview(cases,models,rules):
    labels={'qkv_projection':'QKV 投影','ffn_or_moe':'FFN／单路由专家',
            'attention_prefill':'Attention Prefill','attention_decode':'Attention Decode'}
    formulas={'qkv_projection':'RI=U/N_proj，N_proj 为 Q、可选 G、K、V 的总输出宽度。',
              'ffn_or_moe':'RI=U(D+F)/(3DF)，gate/up 同阶段共享输入，down 新输入另计。',
              'attention_prefill':'RI=g[d_QK+(L+1)/2]/(d_QK+d_V)，窗口从空KV建立到L。',
              'attention_decode':'RI=g(d_QK+L)/(d_QK+d_V)，已有L−1，追加一个后求值。'}
    lines=['# Table II(b)：统一算子级结果预览','',
        '原生模型与所选层固定，各矩阵数值角色1 Byte；表内 RI 按统一规则显示小数，1K=1024、1M=1024²。完整原始Byte、分项和初末有效状态见data/results.json。','']
    lookup={c['case_id']:c for c in cases}
    for workload in WORKLOADS:
        sweep,values=next(iter(rules['sweeps'][workload].items()))
        lines += ['## '+labels[workload],'',formulas[workload],'',
            '| 模型 | '+' | '.join(('U→∞' if v=='infinity' else f'{sweep}={count_label(v)}') for v in values)+' |',
            '|---|'+'---:|'*len(values)]
        for m in models:
            ratios=[lookup[m['model_id']+'/'+workload+'/'+str(v)]['result']['RI'] for v in values]
            lines.append('| '+m['display_name']+' | '+' | '.join(ri_decimal(x) for x in ratios)+' |')
        lines.append('')
    lines += ['QKV无穷列是一次装载的复用极限，写入量仍为有限权重大小。Ling-1T的64K沿用固定官方扩展条件。','',
        '本预览不替代三份中文正文；原始来源、统一计数边界与复算方法见本目录README和主审阅记录。','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    rules=read(HERE/'data/conventions.json');models=read(HERE/'data/model_inputs.json')['models'];by_model={m['model_id']:m for m in models}
    for path,digest in read(HERE/'data/protected_inputs.json')['files'].items():assert sha(TASK/path)==digest,path
    all_cases=[];deliveries=[];trace={};legacy=[];independent=[]
    for index,name in enumerate(FOLDERS):
        folder=TABLE/name;manifest=read(folder/'DELIVERY.json')
        assert manifest['schema_version']==1 and manifest['status']=='ready_for_review'
        for entry in manifest['files']:
            target=folder/entry['path'];assert target.resolve().is_relative_to(folder.resolve())
            assert sha(target)==entry['sha256'],str(target)
        data=decode(read(folder/'data/results.json'));cfg=read(folder/'data/config.json');checks=read(folder/'data/checks.json')
        assert set(data)==set(rules['results_root_keys']),name
        assert set(cfg)==set(rules['config_root_keys']),name
        assert set(checks)==set(rules['checks_root_keys']) and checks['status']=='PASS',name
        assert data['schema_version']==cfg['schema_version']==1
        assert data['reference_id']==cfg['reference_id']==rules['reference_id']
        assert data['boundary']==cfg['boundary']==rules['boundary']
        assert data['model_order']==cfg['model_order']==rules['model_order']
        assert type(cfg['models']) is list and type(cfg['sources']) is list
        for m in cfg['models']:assert set(m)==set(rules['config_model_keys'])
        for s in cfg['sources']:
            assert set(s)=={'path','sha256','locator'} and sha(TASK/s['path'])==s['sha256']
        expected_workloads=[WORKLOADS[index]] if index<2 else WORKLOADS[2:]
        assert data['workload_ids']==expected_workloads
        expected_ids=[mid+'/'+w+'/'+str(v) for mid in rules['model_order'] for w in expected_workloads for v in next(iter(rules['sweeps'][w].values()))]
        assert [c['case_id'] for c in data['cases']]==expected_ids
        old=decode(read(ARCHIVE/name/'data/results.json'));old_by={c['case_id']:c for c in old['cases']}
        for c in data['cases']:
            assert set(c)==set(rules['case_keys']),c['case_id']
            m=by_model[c['model_id']]
            assert c['model_revision']==m['model_revision'] and c['selected_layer']==m['selected_layer']
            assert set(c['window'])==set(rules['window_keys']) and all(isinstance(x,str) for x in c['window'].values())
            assert (c['kind']=='limit')==(c['U']=='infinity')
            if c['workload'].startswith('attention_'):assert c['U'] is None and c['L'] in [1024,8192,65536]
            else:assert c['L'] is None
            expected,parts=oracle(m,c)
            for item in [c['result'],*c['components']]:
                for key in rules['demand_keys']:
                    value=item[key]
                    assert type(value) in (int,F) or (value=='infinity' and key in ['Q_S','RI']), (c['case_id'],key,'non-exact type')
            assert c['result']==expected,(c['case_id'],'total',c['result'],expected)
            assert [x['id'] for x in c['components']]==list(parts)
            for part in c['components']:
                assert set(part)==set(rules['component_keys'])
                assert isinstance(part['input_role'],str)
                for k,v in parts[part['id']].items():assert part[k]==v,(c['case_id'],part['id'],k)
            independent.append(dict(case_id=c['case_id'],status='PASS'))
            if c['workload']=='ffn_or_moe':
                old_case=old_by[c['model_id']+'/ffn_or_moe/8'];old_result=old_case['result'];scale=F(c['U'],8)
                for k in ['Q_S','Q_R','RI']:
                    assert c['result'][k]==old_result['operator'][k]*(1 if k=='Q_R' else scale)
                assert c['result']['resident_bytes_final']==old_result['capacity']['valid_resident_bytes']
                for part in c['components']:
                    for k in ['Q_S','Q_R','RI']:
                        assert part[k]==old_result['parts'][part['id']]['operator'][k]*(1 if k=='Q_R' else scale)
                legacy.append(dict(case_id=c['case_id'],prior_case_id=old_case['case_id'],kind='changed_reuse_sweep',scale=scale,status='PASS'))
            elif c['workload'].startswith('attention_') and c['case_id'] in old_by:
                old_result=old_by[c['case_id']]['result']
                for k in ['Q_S','Q_R','RI']:assert c['result'][k]==old_result['operator'][k]
                assert c['result']['resident_bytes_initial']==old_result['initial_capacity']['valid_resident_bytes']
                assert c['result']['resident_bytes_final']==old_result['capacity']['valid_resident_bytes']
                for part in c['components']:
                    for k in ['Q_S','Q_R','RI']:assert part[k]==old_result['parts'][part['id']]['operator'][k]
                legacy.append(dict(case_id=c['case_id'],kind='unchanged_1K_operator_window',status='PASS'))
            elif c['workload']=='qkv_projection' and c['U']==1:
                old_result=old_by[c['model_id']+'/qkv_projection/one_token']['result']
                assert c['result']['Q_S']==old_result['operator']['Q_S']
                assert c['result']['Q_R']==old_result['capacity']['valid_resident_bytes']
                legacy.append(dict(case_id=c['case_id'],kind='user_changed_from_pre_resident_to_one_load',old_Q_R=0,new_Q_R=c['result']['Q_R'],status='PASS'))
            trace[c['case_id']]=dict(results_path=str((folder/'data/results.json').relative_to(TASK)),results_sha256=sha(folder/'data/results.json'),delivery_revision=manifest['revision'])
        generated_tex='\n'.join((folder/'tex'/f).read_text() for f in ['report.zh.tex','models.generated.tex','results.generated.tex'])
        uncommented=re.sub(r'(?m)%.*$','',generated_tex)
        assert not re.search(r'\b(tile|tiles|macro|macros|ports)\b|\\lceil|allocated_tile|分块',uncommented,re.I),name
        sections=re.findall(r'\\section\{([^}]+)\}',generated_tex)
        assert sections==['对象与公式','模型信息','代入结果','结果说明'],(name,sections)
        assert '../../04_crosscheck/template/preamble.tex' in generated_tex
        model_table=(folder/'tex/models.generated.tex').read_text()
        result_table=(folder/'tex/results.generated.tex').read_text()
        assert '\\ModelTableSetup' in model_table and '\\ResultTableSetup' in result_table,name
        assert 'p{0.32\\linewidth}' in model_table and 'p{0.32\\linewidth}' in result_table,name
        assert '\\RIFraction{' not in result_table and '\\frac{' not in result_table and '\\dfrac{' not in result_table,name
        assert re.search(r'\d+\.\d+', result_table), name
        preview_sections=re.findall(r'(?m)^## (.+)$',(folder/'PREVIEW.zh.md').read_text())
        assert preview_sections==['对象与公式','模型信息','代入结果','结果说明'],(name,preview_sections)
        qa=read(folder/'data/pdf_qa.json');assert qa['status']=='PASS' and qa['pdf']=='output/report.zh.pdf' and qa['page_count']<=3
        assert sha(folder/qa['pdf'])==qa['sha256']
        assert len(qa['page_reviews'])==qa['page_count']
        for page in qa['page_reviews']:
            image=folder/page['png']
            if image.is_file():assert sha(image)==page['sha256']
        actual_csv=(folder/'data/results.csv').read_text()
        assert list(csv.DictReader(io.StringIO(actual_csv)).fieldnames)==rules['csv_columns']
        assert list(csv.DictReader(io.StringIO(actual_csv)))==list(csv.DictReader(io.StringIO(to_csv(data['cases'],rules['csv_columns'])))),name
        deliveries.append(dict(directory=name,revision=manifest['revision'],sha256=sha(folder/'DELIVERY.json'),pdf_sha256=qa['sha256'],pages=qa['page_count']))
        all_cases.extend(data['cases'])
    ordered=[mid+'/'+w+'/'+str(v) for mid in rules['model_order'] for w in WORKLOADS for v in next(iter(rules['sweeps'][w].values()))]
    lookup={c['case_id']:c for c in all_cases};assert len(lookup)==len(all_cases)==96
    all_cases=[lookup[k] for k in ordered]
    assert sum(c['kind']=='finite' for c in all_cases)==90 and sum(c['kind']=='limit' for c in all_cases)==6
    assert len(legacy)==48
    out=dict(schema_version=1,reference_id=rules['reference_id'],boundary=rules['boundary'],model_order=rules['model_order'],workload_ids=WORKLOADS,cases=all_cases)
    report=dict(status='PASS',finite_cases=90,limit_cells=6,component_records=sum(len(c['components']) for c in all_cases),independent_checks=independent,legacy_comparison=legacy,deliveries=deliveries,protected_inputs='PASS')
    products={'data/results.json':out,'data/checks.json':report,'data/source_manifest.json':trace}
    for rel,obj in products.items():
        text=json.dumps(encode(obj),ensure_ascii=False,indent=2)+'\n';target=HERE/rel
        if args.emit:target.write_text(text)
        else:assert target.read_text()==text,'stale merged file: '+rel
    text=to_csv(all_cases,rules['csv_columns']);target=HERE/'data/results.csv'
    if args.emit:target.write_text(text)
    else:assert target.read_text()==text,'stale merged CSV'
    text=preview(all_cases,models,rules);target=HERE/'PREVIEW.zh.md'
    if args.emit:target.write_text(text)
    else:assert target.read_text()==text,'stale merged preview'
    print('PASS: 90 finite cases + 6 limits; 262 components; exact counts and decimal tables; 30 scaled FFN comparisons + 12 Attention overlaps + 6 QKV window comparisons')


if __name__=='__main__':main()

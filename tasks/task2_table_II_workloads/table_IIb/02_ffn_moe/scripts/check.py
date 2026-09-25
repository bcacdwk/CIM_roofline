#!/usr/bin/env python3
"""Independent raw-config, tile and input-identity oracle; no production imports.

Rebuild every matrix using actual row/column slices. Loads sum tile area; inputs
sum each tile receiver's column width for each vector. Operator uses explicit
(x-or-z, vector) identities. The pilot is only compared after independent checks.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

LOCAL=Path(__file__).resolve().parents[1]
ROOT=LOCAL.parents[1]


def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def decode(value):
    if isinstance(value,dict):
        if set(value)=={'numerator','denominator'}:return Fraction(value['numerator'],value['denominator'])
        return {k:decode(v) for k,v in value.items()}
    if isinstance(value,list):return [decode(v) for v in value]
    return value


def encode(value):
    if isinstance(value,Fraction):return value.numerator if value.denominator==1 else dict(numerator=value.numerator,denominator=value.denominator)
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    if isinstance(value,list):return [encode(v) for v in value]
    return value


def dmd(qs,qr,calls=None):return dict(Q_S=qs,Q_R=qr,RI=Fraction(qs,qr),tile_evaluations=calls)
def slices(size):return [(start,min(size,start+128)) for start in range(0,size,128)]


def oracle(D,F,B):
    parts={};entries={};histograms={}
    for name,n,k,source in [('gate',F,D,'x'),('up',F,D,'x'),('down',D,F,'z')]:
        rows=slices(n);cols=slices(k)
        tiles=[(r1-r0,c1-c0) for r0,r1 in rows for c0,c1 in cols]
        writes=sum(nv*kv for nv,kv in tiles)
        qs=calls=0
        for vector in range(B):
            for nv,kv in tiles:
                qs+=kv;calls+=1
            identity=(source,vector)
            assert identity not in entries or entries[identity]==sum(c1-c0 for c0,c1 in cols)
            entries[identity]=sum(c1-c0 for c0,c1 in cols)
        op=sum(c1-c0 for c0,c1 in cols)*B
        axis=lambda ranges:dict(full_128_blocks=sum(b-a==128 for a,b in ranges),
            tail_valid_elements=next((b-a for a,b in ranges if b-a<128),0),blocks=len(ranges))
        lay=dict(matrix_N_K_per_copy=[n,k],copies=1,output_axis=axis(rows),input_axis=axis(cols),
            resident_tiles=len(tiles),valid_resident_bytes=writes,allocated_tile_bytes=sum(128*128 for _ in tiles))
        parts[name]=dict(ports=dmd(qs,writes,calls),operator=dmd(op,writes),layout=lay,
            window=dict(input_vectors=B,full_weight_loads=1),
            tile_layout=dict(output_block_sizes=[b-a for a,b in rows],input_block_sizes=[b-a for a,b in cols],
                resident_tiles=len(tiles),load_events=len(tiles)))
        hist=Counter(tiles)
        histograms[name]=[dict(valid_N_K=[nv,kv],resident_tiles=count,calls=count*B)
                          for (nv,kv),count in sorted(hist.items())]
    qr=sum(p['ports']['Q_R'] for p in parts.values())
    result=dict(parts=parts,
        operator=dmd(sum(entries.values()),qr),
        operator_shared_input_overlap_removed=sum(p['operator']['Q_S'] for p in parts.values())-sum(entries.values()),
        ports=dmd(sum(p['ports']['Q_S'] for p in parts.values()),qr,sum(p['ports']['tile_evaluations'] for p in parts.values())),
        capacity={key:sum(p['layout'][key] for p in parts.values()) for key in ['valid_resident_bytes','allocated_tile_bytes','resident_tiles']})
    result['capacity']['meaning']='final state capacity; distinct from cumulative Q_R and from physical encoded capacity'
    return result,histograms


def source_audit(config):
    models={m['id']:m for m in read('data/models.json')['models']}
    registry={s['local_path']:s for s in read('data/sources.json')}
    for path,digest in config['source_files_sha256'].items():
        assert sha(path)==digest, path
        if path in registry:assert registry[path]['sha256']==digest,path
    common_separate=[
        'self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)',
        'self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)',
        'self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)']
    packed=[
        'self.intermediate_dim = config.moe_intermediate_size',
        'self.num_experts, 2 * self.intermediate_dim, self.hidden_dim',
        'self.num_experts, self.hidden_dim, self.intermediate_dim',
        'gate, up = nn.functional.linear(current_state, self.gate_up_proj[expert_idx]).chunk(2, dim=-1)',
        'current_hidden_states = self.act_fn(gate) * up',
        'current_hidden_states = nn.functional.linear(current_hidden_states, self.down_proj[expert_idx])']
    raw={}; audits=[]
    for mid in config['model_order']:
        m=models[mid];f=m['ffn'];material=m['local_material'];cfg=read(material['raw_config']);cfg=cfg.get('text_config',cfg)
        layer=m['backbone']['selected_layer_index_zero_based'];D=cfg['hidden_size']
        is_dense=mid in ['qwen35_2b','ministral3_8b_2512'];key='intermediate_size' if is_dense else 'moe_intermediate_size';F=cfg[key]
        assert D==m['backbone']['hidden_size']==f['hidden_size']==config['models'][mid]['D']
        assert F==f['intermediate_size']==config['models'][mid]['F']
        assert layer==f['selected_layer_index_zero_based']==config['models'][mid]['selected_layer']
        assert f['matrices']==dict(gate=[F,D],up=[F,D],down=[D,F])
        assert f['parameter_element_counts']['selected_ffn_or_single_expert']==D*F*3
        metadata=read(str(Path(material['raw_config']).with_name('hf_metadata.json')))
        assert metadata['sha']==m['identity']['revision']==config['models'][mid]['model_revision']
        anchors=list(common_separate if mid not in ['qwen36_35b_a3b','hy3_295b'] else packed)
        if mid=='qwen35_2b':
            assert layer==3 and cfg['layer_types'][layer]=='full_attention'
            anchors+=['self.mlp = Qwen3_5MLP(config, config.intermediate_size)',
                      'self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))']
        elif mid=='ministral3_8b_2512':
            params=read(str(Path(material['raw_config']).with_name('params.json')))
            assert D==params['dim'] and F==params['hidden_dim'] and layer==0
            anchors+=['self.intermediate_size = config.intermediate_size',
                      'self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))']
        elif mid=='qwen36_35b_a3b':
            assert layer==3 and cfg['layer_types'][layer]=='full_attention'
            assert cfg['num_experts']==256 and cfg['num_experts_per_tok']==8 and cfg['shared_expert_intermediate_size']==512
            anchors+=['self.experts = Qwen3_5MoeExperts(config)','self.shared_expert = Qwen3_5MoeMLP']
        elif mid=='hy3_295b':
            assert layer==1 and cfg['first_k_dense_replace']==1 and cfg['expert_hidden_dim']==F
            assert cfg['num_experts']==192 and cfg['num_experts_per_tok']==8 and cfg['num_shared_experts']==1
            anchors+=['self.mlp = HYV3MoE(config) if config.mlp_layer_types[layer_idx] == "sparse" else HYV3MLP(config)']
            config_text=(ROOT/'literature/00_shared/raw/transformers/configuration_hy_v3.py').read_text()
            assert 'self.mlp_layer_types = ["dense"] * (1 if self.num_hidden_layers > 0 else 0) + ["sparse"]' in config_text
            converter=(ROOT/'literature/04_hy3_295b/raw/convert_ckpt_to_outer.py').read_text()
            assert 'gate_up = torch.cat([exp["gate_proj"], exp["up_proj"]], dim=0)' in converter
            assert 'fused_gate_up = torch.stack(gate_up_list, dim=0)' in converter
        elif mid=='ling_1t':
            assert layer==4 and cfg['first_k_dense_replace']==4
            assert cfg['num_experts']==256 and cfg['num_experts_per_tok']==8 and cfg['num_shared_experts']==1
            anchors+=['BailingMoeV2MLP(config=self.config, intermediate_size=self.config.moe_intermediate_size)',
                      'if (config.num_experts is not None and layer_idx >= config.first_k_dense_replace)',
                      'self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))']
        else:
            assert mid=='mimo_v25_pro' and layer==7 and cfg['moe_layer_freq'][layer]==1 and cfg['hybrid_layer_pattern'][layer]==0
            assert cfg['n_routed_experts']==384 and cfg['num_experts_per_tok']==8 and cfg['n_shared_experts'] is None
            anchors+=['MiMoV2MLP(config, intermediate_size=config.moe_intermediate_size)',
                      'config.moe_layer_freq[layer_idx]',
                      'self.down_proj(self.act_fn(self.gate_proj(hidden_states)) * self.up_proj(hidden_states))']
        lines=(ROOT/material['implementation']).read_text().splitlines();located=[]
        for anchor in anchors:
            matches=[i for i,line in enumerate(lines,1) if anchor in line]
            assert matches,(mid,anchor)
            located.append(dict(path=material['implementation'],lines=matches,literal_anchor=anchor))
        raw[mid]=dict(D=D,F=F,layer=layer,revision=metadata['sha'])
        audits.append(dict(model_id=mid,raw_config=material['raw_config'],width_key=key,
            raw_dimensions=raw[mid],implementation_anchors=located,
            finding='PASS; raw config + static implementation + pinned metadata agree with extracted FFN'))
    return raw,audits


def leaf_count(value):
    if isinstance(value,dict):return sum(leaf_count(v) for v in value.values())
    if isinstance(value,list):return sum(leaf_count(v) for v in value)
    return 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--emit',action='store_true');args=parser.parse_args()
    config=json.loads((LOCAL/'data/config.json').read_text());data=decode(json.loads((LOCAL/'data/results.json').read_text()))
    raw,audits=source_audit(config);checks=[];seen=[]
    for r in data['cases']:
        d=raw[r['model_id']];B=r['B'];expected,hist=oracle(d['D'],d['F'],B)
        assert r['case_id']==f'{r["model_id"]}/ffn_or_moe/{B}'
        assert r['selected_layer']==d['layer'] and r['model_revision']==d['revision']
        assert r['shared_reference_id']==config['shared_reference_id'] and r['row']=='ffn_or_moe'
        assert r['result']==expected,r['case_id']
        assert expected['ports']['RI']==Fraction(B,128)
        seen.append(r['case_id']);checks.append(dict(case_id=r['case_id'],pass_=True,
            independent_result=expected,valid_N_K_call_histograms=hist))
    assert seen==[f'{mid}/ffn_or_moe/{B}' for mid in config['model_order'] for B in [8,64,512]]
    pilot=decode(read('table_IIb/pilot/data/results.json'));baseline={r['case_id']:r for r in pilot['cases'] if r['row']=='ffn_or_moe'}
    regress=[]
    for r in data['cases']:
        if r['case_id'] in baseline:
            assert r==baseline[r['case_id']],r['case_id']
            regress.append(dict(case_id=r['case_id'],pass_=True,compared_leaf_fields=leaf_count(r),
                                comparison='entire semantic record including exact dual-boundary demands, all parts/layouts/windows, capacity and tile calls'))
    assert len(regress)==6
    # Explicitly check the transpose pair without manufacturing a total difference.
    pairs=[]
    lookup={r['case_id']:r['result'] for r in data['cases']}
    for B in [8,64,512]:
        a=lookup[f'qwen35_2b/ffn_or_moe/{B}'];b=lookup[f'mimo_v25_pro/ffn_or_moe/{B}']
        for boundary in ['ports','operator']:assert a[boundary]==b[boundary]
        assert a['capacity']==b['capacity']
        assert a['parts']['gate']['operator']==b['parts']['down']['operator']
        assert a['parts']['down']['operator']==b['parts']['gate']['operator']
        assert b['operator_shared_input_overlap_removed']==3*a['operator_shared_input_overlap_removed']
        pairs.append(dict(B=B,total_equality=True,operator_gate_down_swap=True,shared_overlap_ratio=3))
    report=dict(status='PASS',main_case_count=18,matrix_part_count=54,pilot_overlap_count=6,
        method='Raw-config dimensions; explicit tile-slice receiver loops and tile-area writes; phase/vector input identities; no imports from production calculator or generator.',
        source_audit=audits,main_checks=checks,pilot_regression=regress,transpose_pair_checks=pairs,
        pilot_sha256=sha('table_IIb/pilot/data/results.json'),step1_step2_corrections_required=False)
    text=json.dumps(encode(report),ensure_ascii=False,indent=2)+'\n';dest=LOCAL/'data/checks.json'
    if args.emit:dest.write_text(text)
    else:assert dest.read_text()==text,'stale independent checks'
    print('PASS: 18 raw-config/tile cases, 54 parts, six complete pilot-record regressions, three transpose-pair checks')


if __name__=='__main__':main()

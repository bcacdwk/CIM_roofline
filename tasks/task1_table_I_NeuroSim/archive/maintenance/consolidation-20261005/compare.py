import json,math
from pathlib import Path
base=Path('/Users/shine/neurosim/runs/consolidation-20261005/integration'); old=base/'selected_evidence'; run=Path('/Users/shine/neurosim/runs/cim-reference/consolidation-integration-20261005')
checks={}; count=0
for c in sorted(old.glob('*/result.json')):
 cid=c.parent.name;o=json.loads(c.read_text());n=json.loads((run/cid/'result.json').read_text());a=json.loads((c.parent/'resolved.json').read_text());b=json.loads((run/cid/'resolved.json').read_text())
 row={k:o[k]==n[k] for k in ('clocks','stages','streaming','resident_load','maintenance','derived_metrics','checks','derived_snapshot')}
 row.update({k:a[k]==b[k] for k in ('logical','physical','resources','native_parameters_ns','backend')})
 # source provenance is metadata; adapter calculation values must match except relocated source reference.
 aa=a['adapter'].copy();bb=b['adapter'].copy()
 for x in (aa,bb):x.pop('source_inputs',None)
 row['adapter']=aa==bb
 assert all(row.values()),(cid,{k:v for k,v in row.items() if not v})
 checks[cid]=row
 count+=len(o['stages'])
result={'status':'PASS','comparison':'exact Python object equality for all selected numeric and semantic subtrees; no tolerance needed on this compiler','stage_rows_compared':count,'case_checks':checks,'compiler':json.loads((run/'invocation.json').read_text())['compiler'],'baseline_summary_sha256':'ef18e27c3b13a085506d2c69df0952c2fb42387bd63a7c206d935dd324f556b3','run':str(run)}
(base/'integration_regression.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(checks),'stage_rows':count}))

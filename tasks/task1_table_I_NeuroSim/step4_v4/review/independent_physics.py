#!/usr/bin/env python3
"""Read-only evidence: independently evaluate a voltage-fed resistor ladder and numerical widths."""
import json, math, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
# Every branch is fed by the same ideal bias. Collapse the ladder from its far end.
def current(mask,active,n,total_wire,terminal,voltage=.5):
    seg=total_wire/n
    down=math.inf
    for j in range(n-1,-1,-1):
        conductance=(1/(13000 if mask>>j&1 else 29000)) if active>>j&1 else 0
        if math.isfinite(down): conductance+=1/(seg+down)
        down=1/conductance if conductance else math.inf
    return voltage/(terminal+seg+down) if math.isfinite(down) else 0
scale=.5*(1/13000-1/29000)
thermal={}
for temp in (300,350,400):
    rw=32.63815789473685*(1+.00451*(temp-300)); n=16; active=(1<<n)-1
    ref=current(0,active,n,rw,12.6953125)
    dense=(current(active,active,n,rw,12.6953125)-ref)/scale
    maxerr=(-1,None,None)
    for mask in range(1<<n):
        value=(current(mask,active,n,rw,12.6953125)-ref)/scale
        err=abs(value-bin(mask).count('1'))
        if err>maxerr[0]: maxerr=(err,mask,value)
    # Complementary check: all possible activity maps with all active cells LRS.
    max_active=(-1,None,None)
    for active in range(1<<n):
        value=(current(active,active,n,rw,12.6953125)-current(0,active,n,rw,12.6953125))/scale
        err=abs(value-bin(active).count('1'))
        if err>max_active[0]: max_active=(err,active,value)
    onehot=[]
    for j in range(n):
        a=1<<j
        hrs=current(0,a,n,rw,12.6953125)/scale*16
        lrs=current(a,a,n,rw,12.6953125)/scale*16
        onehot.append({'row':j,'hrs_code':hrs,'lrs_code':lrs,'rounded_hrs':math.floor(hrs+.5),'rounded_lrs':math.floor(lrs+.5)})
    assert all(v['rounded_hrs']==13 and v['rounded_lrs']==29 for v in onehot)
    thermal[str(temp)]={'verify_onehot_codes':onehot,'wire_ohm':rw,'dense_count':dense,'dense_ratio':dense/16,
      'full_active_all_65536_state_max_error_count':maxerr,'all_65536_activation_maps_all_LRS_max_error_count':max_active}
v3=(current((1<<256)-1,(1<<256)-1,256,522.2105263157896,0)-current(0,(1<<256)-1,256,522.2105263157896,0))/scale
# Independently exhaust scalar signed identity including native Q4 scale retained to the end.
stage_min=[0,0,0];stage_max=[0,0,0]
for x in range(-128,128):
    for w in range(-128,128):
        q=x%256;u=w+128;sign=int(x<0)
        A=16*q*u;B=16*sign*u;C=16*q;D=16*sign
        stages=(A-128*C,A-128*C-256*B,A-128*C-256*B+32768*D)
        assert stages[-1]==16*x*w
        for i,value in enumerate(stages):
            stage_min[i]=min(stage_min[i],value*256);stage_max[i]=max(stage_max[i],value*256)
            assert -(2**28)<=value*256<2**28
max_raw_A=16*256*255*255
out={'identity':'Independent reviewer; no production model import; no evidence of historical engineering participation in this thread',
 'model':'Ideal stiff equal read voltage per active branch; 16 equally spaced taps; series terminal MUX; no source impedance, cell nonlinearity/noise or SPICE claim',
 'results':thermal,'V3_256row_wire_only_dense_count':v3,
 'numeric':{'scalar_signed_pairs':256*256,'q4_max_A_full_matrix':max_raw_A,'signed_29bit_max':2**28-1,'fits_signed29':max_raw_A<2**28,'matrix_stage_min':stage_min,'matrix_stage_max':stage_max},
 'qualification':'Analog error is not eliminated by Q4 arithmetic; 29bit output is container precision, not ENOB or exact integer guarantee.',
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE/'independent_physics.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

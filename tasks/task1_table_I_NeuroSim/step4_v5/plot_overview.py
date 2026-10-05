#!/usr/bin/env python3
"""Paired scientific rho/tau plots. Reads qualified tables only; no device computation."""
import argparse,hashlib,itertools,json,math,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
SCENARIOS=('optimistic','reference','pessimistic')
LABELS={'sram_acim':'SRAM ACIM','sram_dcim':'SRAM DCIM','rram':'1T1R RRAM','pcm':'PCM','mram':'MRAM','nor2d':'2D NOR','fenor3d':'Vertical AND FeFET','feram':'HZO FeRAM','gc04':'GC-04 (effective)','nand3d':'3D NAND'}
COLORS={'sram_acim':'#ba7836','sram_dcim':'#4269aa','rram':'#765499','pcm':'#c45863','mram':'#318678','nor2d':'#a28b26','fenor3d':'#348aac','feram':'#dd8434','gc04':'#73833c','nand3d':'#956f8d'}
V5_CASES=('pcm','mram','nor2d','fenor3d','feram','gc04','nand3d')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def minimum_circle(points):
 candidates=[(p.copy(),0.) for p in points]
 for a,b in itertools.combinations(points,2):
  c=(a+b)/2;candidates.append((c,float(np.linalg.norm(a-c))))
 if len(points)==3:
  a,b,p=points;matrix=2*np.vstack((b-a,p-a))
  if abs(float(np.linalg.det(matrix)))>1e-15:
   c=np.linalg.solve(matrix,np.array([b@b-a@a,p@p-a@a]));candidates.append((c,float(np.linalg.norm(a-c))))
 valid=[(c,r) for c,r in candidates if all(np.linalg.norm(x-c)<=r+1e-11 for x in points)]
 if not valid:raise ValueError('Cannot enclose finite scenario points')
 return min(valid,key=lambda v:v[1])
def circle(group):
 a,b,p=[np.log10([group[s]['tau_MB_per_s'],group[s]['rho_MB_per_s']]) for s in ('optimistic','pessimistic','reference')]
 middle=(a+b)/2;chord=b-a;norm=float(chord@chord);fallback=None;original=None
 if norm<=1e-24:fallback='coincident_or_numerically_degenerate_endpoints'
 else:
  center=p-float((p-middle)@chord)/norm*chord;radius=float(np.linalg.norm(a-center));distance=float(np.linalg.norm(p-center));original={'center_log10':center.tolist(),'radius_decades':radius,'reference_distance_decades':distance}
  if distance>radius+1e-11:fallback='reference_outside_projected_center_circle'
 if fallback:center,radius=minimum_circle([a,b,p])
 distances={s:float(np.linalg.norm(np.log10([r['tau_MB_per_s'],r['rho_MB_per_s']])-center)) for s,r in group.items()}
 if any(d>radius+1e-10 for d in distances.values()):raise ValueError('Envelope excludes an actual point')
 return {'rule':'minimum_enclosing_point' if radius<=1e-12 else 'minimum_enclosing_circle' if fallback else 'reference_projection_onto_endpoint_perpendicular_bisector','fallback_reason':fallback,'original':original,'center_log10':center.tolist(),'radius_decades':radius,'point_distances_decades':distances,'all_points_inside':True,'interpretation':'Finite paired samples only; not confidence or feasible-combination region'}
def geometry_examples():
 result={}
 fixtures={'all_coincident':[(0,0),(0,0),(0,0)],'opt_equals_reference':[(0,0),(0,0),(1,.5)],'endpoints_coincident':[(0,0),(1,.5),(0,0)],'reference_outside':[(0,0),(3,0),(1,0)]}
 for name,values in fixtures.items():
  group={s:{'tau_MB_per_s':10.**v[0],'rho_MB_per_s':10.**v[1]} for s,v in zip(SCENARIOS,values)};result[name]=circle(group)
 return {'scope':'geometry-only synthetic fixtures, never plotted as device points','cases':result}
def overlap(a,b,padding=2):return not(a.x1+padding<=b.x0 or b.x1+padding<=a.x0 or a.y1+padding<=b.y0 or b.y1+padding<=a.y0)
def label_groups(fig,ax,groups):
 placed=[];records=[];fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=ax.get_window_extent(renderer)
 from matplotlib.transforms import Bbox
 markers=[Bbox.from_bounds(*(ax.transData.transform((r['tau_MB_per_s'],r['rho_MB_per_s']))-7),14,14) for group in groups.values() for r in group.values()]
 for key,group in sorted(groups.items(),key=lambda kv:kv[1].get('reference',next(iter(kv[1].values())))['rho_MB_per_s'],reverse=True):
  ref=group.get('reference',next(iter(group.values())));label=LABELS.get(ref['case_id'],ref['case_id']);coincident=[]
  if len(group)<3:label+=' [partial]'
  elif len({(r['tau_MB_per_s'],r['rho_MB_per_s']) for r in group.values()})==1:label+=' [all coincide]'
  else:
   for s in ('optimistic','pessimistic'):
    if (group[s]['tau_MB_per_s'],group[s]['rho_MB_per_s'])==(ref['tau_MB_per_s'],ref['rho_MB_per_s']):coincident.append('opt' if s=='optimistic' else 'pess')
   if coincident:label+=' ['+'='.join(coincident+['ref'])+']'
  choices=[(12,12),(12,-18),(-12,12),(-12,-18),(0,28),(0,-30),(34,0),(-34,0),(35,24),(-35,24),(35,-26),(-35,-26)]
  if len(groups)>7:
   preferred={'nor2d':(-10,-28),'nand3d':(15,-26),'pcm':(15,-22),'gc04':(12,-26)}
   if ref['case_id'] in preferred:choices.insert(0,preferred[ref['case_id']])
  candidates=[]
  for dx,dy in choices:
   art=ax.annotate(label,(ref['tau_MB_per_s'],ref['rho_MB_per_s']),xytext=(dx,dy),textcoords='offset points',ha='left' if dx>0 else 'right' if dx<0 else 'center',va='center',fontsize=9.2,color=COLORS.get(ref['case_id'],'#444444'),zorder=9)
   bbox=art.get_window_extent(renderer);penalty=sum(overlap(bbox,b) for b in placed)*100+sum(overlap(bbox,b,0) for b in markers)*70
   penalty+=sum((max(bounds.x0-bbox.x0,0),max(bbox.x1-bounds.x1,0),max(bounds.y0-bbox.y0,0),max(bbox.y1-bounds.y1,0)))*10
   candidates.append((penalty,art,bbox,(dx,dy)))
  chosen=min(candidates,key=lambda x:x[0])
  for candidate in candidates:
   if candidate is not chosen:candidate[1].remove()
  placed.append(chosen[2]);records.append({'implementation_id':key,'label':label,'offset_points':chosen[3],'layout_penalty':chosen[0]})
 return records
def draw(dataset,out,include_circles,preview,stem):
 eligible=[];excluded=[]
 for r in dataset['points']:
  valid=bool(r.get('plot_eligible')) and r.get('accepted') is True and r['status'] not in ('blocked','infeasible')
  if not valid:excluded.append({'case_id':r['case_id'],'config_id':r['config_id'],'status':r['status'],'reason':'not accepted with matching review or physically invalid'});continue
  if not all(isinstance(r.get(k),(int,float)) and math.isfinite(r[k]) and r[k]>0 for k in ('rho_MB_per_s','tau_MB_per_s')):raise ValueError('Eligible point lacks positive rates')
  if r['case_id']=='gc04' and (r.get('rate_basis')!='long-term event schedule' or not r.get('maintenance_summary',{}).get('feasible')):raise ValueError('GC main graph must use feasible long-term effective service')
  eligible.append(r)
 if not eligible:raise ValueError('No accepted paired numeric points to plot')
 groups={}
 for r in eligible:
  key=r['implementation_id'];g=groups.setdefault(key,{})
  if r['scenario'] in g:raise ValueError('Duplicate scenario in a hardware identity')
  g[r['scenario']]=r
 specs={key:circle(g) for key,g in groups.items() if set(g)==set(SCENARIOS)} if include_circles else {}
 xy=np.log10([[r['tau_MB_per_s'],r['rho_MB_per_s']] for r in eligible]);lo=xy.min(axis=0);hi=xy.max(axis=0)
 for spec in specs.values():
  c=np.array(spec['center_log10']);radius=spec['radius_decades'];lo=np.minimum(lo,c-radius);hi=np.maximum(hi,c+radius)
 lo=np.floor((lo-.38)*2)/2;hi=np.ceil((hi+.42)*2)/2
 for axis in (0,1):
  if hi[axis]-lo[axis]<2:
   midpoint=(hi[axis]+lo[axis])/2;lo[axis]=midpoint-1;hi[axis]=midpoint+1
 fig=plt.figure(figsize=(10.2,max(7.0,min(10.5,7.7*(hi[1]-lo[1])/(hi[0]-lo[0])+1.8))));ax=fig.add_axes([.11,.26,.83,.62]);ax.set_xscale('log');ax.set_yscale('log');ax.set_xlim(10**lo[0],10**hi[0]);ax.set_ylim(10**lo[1],10**hi[1]);ax.set_aspect('equal',adjustable='box');ax.grid(True,which='major',alpha=.24,lw=.7);ax.grid(True,which='minor',alpha=.06,lw=.45)
 diagonal=[max(lo),min(hi)]
 if diagonal[1]>diagonal[0]:ax.plot(10**np.array(diagonal),10**np.array(diagonal),':',color='#8b9198',lw=1,zorder=0)
 geometry=[]
 for key,group in groups.items():
  ref=group.get('reference',next(iter(group.values())));color=COLORS.get(ref['case_id'],'#555555');generation=ref['generation'];ordered=[group[s] for s in SCENARIOS if s in group]
  if key in specs:
   spec=specs[key];c=np.array(spec['center_log10']);radius=spec['radius_decades'];theta=np.linspace(0,2*np.pi,361)
   if radius>1e-12:
    x=10**(c[0]+radius*np.cos(theta));y=10**(c[1]+radius*np.sin(theta));ax.fill(x,y,color=color,alpha=.075,zorder=1);ax.plot(x,y,color=color,lw=1.1,ls='--' if generation=='V4' else '-',alpha=.7,zorder=2)
   geometry.append(dict(implementation_id=key,case_id=ref['case_id'],generation=generation,**spec))
  ax.plot([r['tau_MB_per_s'] for r in ordered],[r['rho_MB_per_s'] for r in ordered],color=color,lw=1.25,alpha=.75,zorder=3)
  if 'reference' in group:
   r=group['reference'];ax.scatter(r['tau_MB_per_s'],r['rho_MB_per_s'],s=112,marker='o',facecolor=color,edgecolor='white',lw=1.1,zorder=5)
  for s,marker in (('optimistic','^'),('pessimistic','s')):
   if s in group:
    r=group[s];ax.scatter(r['tau_MB_per_s'],r['rho_MB_per_s'],s=38,marker=marker,facecolor='white',edgecolor=color,lw=1.15,zorder=6)
 labels=label_groups(fig,ax,groups)
 ax.set_xlabel(r'Resident update $\tau$ (decimal MB/s)',fontsize=11);ax.set_ylabel(r'Streaming input $\rho$ (decimal MB/s)',fontsize=11);ax.tick_params(labelsize=9)
 layers=sorted({r['generation'] for r in eligible});title=(' + historical '.join(layers[::-1]) if len(layers)>1 else layers[0])+' | '+str(len(groups))+' classes, '+str(len(eligible))+' qualified paired points'
 fig.suptitle(title,fontsize=14,fontweight='semibold',y=.96)
 fig.text(.5,.921,'LOCAL PREVIEW — incomplete V5 set' if preview else 'Finite reference scenarios; native sizes and model conditions are listed in the companion table',ha='center',fontsize=9.5,color='#7a4653' if preview else '#4d5359')
 handles=[Line2D([],[],marker='o',linestyle='None',color='#555555',markersize=8,label='Reference'),Line2D([],[],marker='^',linestyle='None',markerfacecolor='white',color='#555555',markersize=6,label='Optimistic'),Line2D([],[],marker='s',linestyle='None',markerfacecolor='white',color='#555555',markersize=5,label='Pessimistic'),Line2D([],[],linestyle=':',color='#8b9198',label=r'$RI^*=1$')]
 if include_circles:
  if 'V4' in layers:handles.append(Line2D([],[],ls='--',color='#777777',label='V4 thermal redesign'))
  if 'V5' in layers:handles.append(Line2D([],[],ls='-',color='#777777',label='V5 finite case scenarios'))
 fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.52,.105),ncol=3 if include_circles else 4,frameon=False,fontsize=8.4)
 footer='Equal log-decade lengths. Circles summarize sampled pairs, not confidence or all feasible combinations.\nDifferent K, N, precision and resources: MB/s is not an equal-work or equal-area ranking. GC uses effective rates.'
 missing=sorted(set(V5_CASES)-{r['case_id'] for r in eligible if r['generation']=='V5'})
 state_records=list(dataset.get('case_records',[]))+excluded
 if excluded and not missing:footer+='\nExcluded invalid/unreviewed scenarios: '+str(len(excluded))+'. Partial sets have no ordinary circle; see status table.'
 if missing:footer+='\nNot shown'+(' in this preview' if preview else '')+': '+', '.join(LABELS.get(x,x) for x in missing)+'. See status table.'
 fig.text(.11,.023,footer,ha='left',va='bottom',fontsize=7.7,color='#555b61',linespacing=1.5)
 fig.canvas.draw();display=ax.transData.transform(np.array([[1.,1.],[10.,1.],[1.,10.]]));xdec=float(display[1,0]-display[0,0]);ydec=float(display[2,1]-display[0,1])
 if not math.isclose(xdec,ydec,rel_tol=1e-10):raise ValueError('Log decades not equal on screen')
 for spec in geometry:
  c=np.array(spec['center_log10']);r=spec['radius_decades']
  if np.any(c-r<lo-1e-12) or np.any(c+r>hi+1e-12):raise ValueError('Clipped circle envelope')
 name=stem+('_circles' if include_circles else '_pairs');fig.savefig(out/(name+'.png'),dpi=190,facecolor='white');fig.savefig(out/(name+'.svg'),facecolor='white');plt.close(fig)
 return {'stem':name,'eligible_points':len(eligible),'classes':len(groups),'point_coordinates_unchanged':True,'points':[{'config_id':r['config_id'],'rho_MB_per_s':r['rho_MB_per_s'],'tau_MB_per_s':r['tau_MB_per_s']} for r in eligible],'envelopes':geometry,'labels':labels,'excluded':state_records,'log10_limits':[lo.tolist(),hi.tolist()],'pixels_per_decade':[xdec,ydec],'equal_log_scale':True,'outputs':{ext:sha(out/(name+'.'+ext)) for ext in ('png','svg')}}
def main():
 global np,plt,Line2D
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--points',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--stem',default='rho_tau');p.add_argument('--preview',action='store_true');a=p.parse_args();out=a.output_dir.absolute()
 if out.exists() or any(x.is_symlink() for x in (out,*out.parents)):raise ValueError('New non-symlink plot directory required')
 if any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):raise ValueError('Render locally first; whitelist export only after review')
 out.mkdir(parents=True,exist_ok=False);(out/'mpl-cache').mkdir();os.environ['MPLCONFIGDIR']=str(out/'mpl-cache');os.environ['MPLBACKEND']='Agg'
 import numpy as np
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.lines import Line2D
 plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':True,'axes.spines.right':True})
 dataset=json.loads(a.points.read_text());checks={'source_points':str(a.points.resolve()),'source_sha256':sha(a.points),'script_sha256':sha(Path(__file__)),'preview_only':a.preview,'geometry_examples':geometry_examples(),'figures':[draw(dataset,out,False,a.preview,a.stem),draw(dataset,out,True,a.preview,a.stem)]}
 (out/'geometry.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2,allow_nan=False)+'\n');print(json.dumps({'output_directory':str(out),'figures':4,'eligible_points':checks['figures'][0]['eligible_points'],'preview_only':a.preview,'equal_log_scale':True}))
if __name__=='__main__':main()

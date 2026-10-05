"""Two state-dependent net-leak alternatives, fitted only at100/700nA.

400nA is held out. Model family choice is disclosed; none is presented as a
unique zero-node extraction or a silicon population guarantee.
"""
import math,json,argparse,pathlib
from gc_model import Cell

class Leak:
    def __init__(self,kind):
        self.kind=kind;self.cell=Cell();self.T=400e-6
        self.transform=(math.log if kind=='ohmic_net_leak' else lambda x:x)
        self.inverse=(math.exp if kind=='ohmic_net_leak' else lambda x:x)
        y1,y2=map(self.transform,(100e-9,700e-9))
        f1,f2=map(self.transform,(120.4e-9,676.9e-9))
        self.A=(f2-f1)/(y2-y1);self.B=f1-self.A*y1
        self.yeq=self.B/(1-self.A);self.tau=-self.T/math.log(self.A)
    def current(self,i0,t):
        y=self.yeq+(self.transform(i0)-self.yeq)*math.exp(-t/self.tau)
        return self.inverse(y)
    def initial_leak(self,i0):
        c=self.cell
        if self.kind=='ohmic_net_leak':dV=c.vslope*(self.yeq-math.log(i0))/self.tau
        else:dV=c.vslope*(self.yeq/i0-1)/self.tau
        return c.cap*dV
    def summary(self):
        c=self.cell;i0=c.retained(False,0)['nominal_current_A']
        predicted=self.current(400e-9,self.T)
        ih=self.current(700e-9,self.T);il=self.current(i0,self.T)
        return {'kind':self.kind,'fit_sources':['100nA+20.4percent','700nA−3.3percent'],
          'heldout400nA_predicted_A':predicted,'heldout400nA_source_A':406e-9,
          'heldout_error_fraction_of400nA':(predicted-406e-9)/400e-9,
          'relaxation_tau_s':self.tau,'equilibrium_current_A':self.inverse(self.yeq),
          'initial_low_current_A':i0,'initial_zero_node_leak_A':self.initial_leak(i0),
          'low_at400us_A':il,'high_at400us_A':ih,'pair_difference_at400us_A':ih-il,
          'pair_drift_fraction':1-(ih-il)/(700e-9-i0),
          'refresh_halfscale_margin_A':(ih-il)-350e-9,
          'curve':[{'age_s':t,'high_A':self.current(700e-9,t),'low_A':self.current(i0,t),'heldout400_A':self.current(400e-9,t)} for t in (0,100e-6,200e-6,300e-6,400e-6)]}

def run():
    models=[Leak(k).summary() for k in ('ohmic_net_leak','off_access_subthreshold_plus_constant_sink')]
    c=Cell();base=c.retained(True,400e-6)['nominal_current_A']-c.retained(False,400e-6)['nominal_current_A']
    assert all(x['refresh_halfscale_margin_A']>0 for x in models)
    return {'status':'state_dependent_alternative_probe_not_silicon_retention_qualification',
      'source_domain':'GC04 Fig9 FF80C simulation.100/700 fitted;400nA+1.5percent heldout;notmeasuredroomtemperaturepopulation',
      'equations':{'ohmic_net_leak':'dV/dt=(Veq−V)/tau, resulting from linear net charge leakage; two fitted constants',
      'off_access_subthreshold_plus_constant_sink':'dQ/dt=A exp[−(V−V100)/(nUT)]−B; standard subthreshold source-voltage dependence plus constant sink; same slope as read, two fitted constants'},
      'selected_ohmic_model_pair_A':base,'models':models,
      'conclusion':['State-dependent alternatives predict substantially different zero-node drift, despite fitting identical100/700nA endpoints.',
       '400nA heldout disagreement is retained; models are not claimed to predict the complete multilevel population.',
       'All enumerated finite models retain binary-pair sign at400us, but that is a model-domain result, not99.7percentorall-bit guarantee.',
       'Complementarypair measuredretention andsinglenode inferredleak remain separate evidence;68xconstantleakmargin alone is insufficientqualification.',
       'A formalmodelreference may condition on a declared leakagefamily/envelope andreportanalogerror; it cannot call this measuredretention reliability.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();d=run();pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':a.out,'models':[{k:x[k] for k in ('kind','heldout_error_fraction_of400nA','low_at400us_A','pair_drift_fraction','refresh_halfscale_margin_A')} for x in d['models']]}))

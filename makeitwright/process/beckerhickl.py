__name__ = "beckerhickl"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
import matplotlib.pyplot as plt
import WrightTools as wt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

from .helpers import roi

def tmax(data):
    pass

def get_fits(data, channel='norm', function='biexp'):
    def exp(t, a, td):
        return a*np.exp(-t/td)     
    def biexp(t, a1, td1, a2, td2):
        return a1*np.exp(-t/td1) + a2*np.exp(-t/td2)
    
    functions = {
        "exp" : exp,
        "biexp" : biexp
        }
    
    fits = {}
    for i in range(len(data)):
        out = roi(data[i], {'t':[0]})
        fit, cov  = curve_fit(functions[function], out['t'][:], out[channel][:], bounds=(0,1000000), maxfev=1000*len(out['t'][:]))
        std = np.sqrt(np.diag(cov))
        
        if function=='biexp':
            sort = sorted(zip([fit[1],fit[3]], [std[1],std[3]], [fit[0],fit[2]], [std[0],std[2]]))
            tsorted = [t for t, tstd, a, astd in sort]
            tstdsorted = [tstd for t, tstd, a, astd in sort]
            asorted = [a for t, tstd, a, astd in sort]
            astdsorted = [astd for t, tstd, a, astd in sort]
            fitdict = {
                'function' : function,
                'A1' : (asorted[0], astdsorted[0]),
                't1' : (tsorted[0], tstdsorted[0]),
                'A2' : (asorted[1], astdsorted[1]),
                't2' : (tsorted[1], tstdsorted[1])
                }
            
        if function=='exp':
            fitdict = {
                'function' : function,
                'A' : (fit[0], std[0]),
                't' : (fit[1], std[1])
                }
        
        fitdict['r2'] = pearsonr(out[channel][:], functions[function](out['t'][:], *fit))[0]**2
            
        fits[f'{i}_{data[i].natural_name}'] = fitdict
        
        fig, gs = wt.artists.create_figure()
        ax = plt.subplot(gs[0])
        ax.scatter(out['t'][:], out[channel][:], color='orange', alpha=0.5, s=3)
        ax.plot(out['t'][:], functions[function](out['t'][:], *fit), '--', linewidth=3, color='blue')
        ax.set_title(f'{data[i].natural_name[:20]}')
        ax.set_ylabel("counts")
        ax.set_xlabel("t (ns)")
        ax.set_yscale('log')
        ax.set_ylim(1,np.max(out[channel][:]))

    return fits
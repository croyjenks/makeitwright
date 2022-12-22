__name__ = "iontof"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
import pySPM
import WrightTools as wt
from hyperspectral import remove_background
from helpers import parse_args, normalize_by_axis

def relative_proportion(data, channel0, channel1):
    """
    Calculate the relative proportion of signal between two channels on a scale of -1 to 1, with 0 being equal in proportion.
    
    Parameters
    ----------
    data : Data object of WrightTools data module
        The data to which the channels of interest belong.
        
    channel0, channel1 : str or int
        The natural names or indices of the channels to compare.

    Returns
    -------
    None.
    """
    
    #convert channel indices to natural names
    channels = parse_args(data, channel0, channel1, dtype='Channel')
    
    #ensure regions with no signal don't show up
    remove_background(data, *channels, threshold_value=0.99, new_value=1)
    dump = [data.channels[-2].natural_name, data.channels[-1].natural_name]
    
    #calculate normalized difference between channels
    normalize_by_axis(data, channels[0], 'x', 'y', 'scan')
    normalize_by_axis(data, channels[1], 'x', 'y', 'scan')
    ch_arr0 = data.channels[-2][:]
    dump.append(data.channels[-2].natural_name)
    ch_arr1 = data.channels[-1][:]
    dump.append(data.channels[-1].natural_name)        
    ch_arr = (ch_arr0-ch_arr1)/(ch_arr0+ch_arr1)
    ch_arr = np.nan_to_num(ch_arr)
    
    for trash in dump:
        data.remove_channel(trash, verbose=False)
    
    #create new channel
    ch_name = "rel_mass_"+channels[0]+"_"+channels[1]
    data.create_channel(ch_name, values=ch_arr, verbose=True)
    data[ch_name].signed = True

def ITApeaks(fpath):
    ita=pySPM.ITA(fpath)
    summ = ita.get_summary()
    return summ['peaks']

def from_ITA(fpath, name=None, select_channels=None):

    ita = pySPM.ITA(fpath)
    ita.show_summary()
    summ = ita.get_summary()
    
    xarr = np.linspace(0, summ['fov']*1e6, num=summ['pixels']['x'])
    yarr = np.linspace(0, summ['fov']*1e6, num=summ['pixels']['y'])
    scarr = np.linspace(1, int(summ['Scans']), num=int(summ['Scans']))
    charrs = {}
    if select_channels is not None:
        idxs = []
        for peak in summ['peaks']:
            if peak['id'] in select_channels or peak['assign'] in select_channels:
                idxs = idxs + [peak['id']]
        for idx in idxs:
            if summ['peaks'][idx]['assign']:
                chname = summ['peaks'][idx]['assign']
            elif summ['peaks'][idx]['desc']:
                chname = summ['peaks'][idx]['desc']
            else:
                chname = str(int(summ['peaks'][idx]['cmass'])) + 'mz'
            charr = ita.getImage(idx,0)        
            for i in range(1,len(scarr)):
                j = ita.getImage(idx,i)
                charr = np.dstack((charr,j))
            charrs[chname] = charr
            print("channel <" + chname + "> found")
    else:
        for peak in summ['peaks']:
            if peak['assign']:
                chname = peak['assign']
            elif peak['desc']:
                chname = peak['desc']
            else:
                chname = str(int(peak['cmass'])) + 'mz'
            idx = peak['id']
            charr = ita.getImage(idx,0)        
            for i in range(1,len(scarr)):
                j = ita.getImage(idx,i)
                charr = np.dstack((charr,j))
            charrs[chname] = charr
            print("channel <" + chname + "> found")
        
    d = wt.Data()
    d.create_variable(name='x', values=xarr[:,None,None], units='um')
    d.create_variable(name='y', values=yarr[None,:,None], units='um')
    d.create_variable(name='scan', values=scarr[None,None,:], units='s')
    for chname, charr in charrs.items():
        d.create_channel(name=chname, values=charr)
    d.transform('x','y','scan')

    return d
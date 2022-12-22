__name__ = "image"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

#import
import numpy as np
from helpers import parse_args

def remove_background(data, channel, threshold=0.5, negative=False, return_mask=False, max_ref_count=500):
    channel, = parse_args(data, channel, dtype='Channel')
        
    ch_arr = data[channel][:]
    if max_ref_count > ch_arr.size:
        max_ref_count = int(ch_arr.size/10)
    ordered = np.sort(ch_arr.flatten())[-max_ref_count:]
    ch_max = np.average(ordered)
    bkg = np.where(ch_arr < threshold*ch_max, 0, ch_arr)
    mask = np.where(bkg > 0, 1, bkg)
    if negative:
        mask = 1-mask
    nobkg = ch_arr * mask

    data.create_channel(name=channel+"_nobkg", values=nobkg, units=data[channel].units)
    data[channel+'_nobkg'].signed = data[channel].signed
    if return_mask:
        data.create_channel(name=data[channel].natural_name+"_mask", values=mask)
__name__ = "spectralprofile"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

#import
import numpy as np
from helpers import parse_args

def remove_background(data, channel, threshold=0.5, negative=False, return_mask=False, max_ref_count=10):
    channel, = parse_args(data, channel, dtype='Channel')
    
    y_arr = np.sum(data[channel][:], axis=0)
    if max_ref_count > y_arr.size:
        max_ref_count = int(y_arr.size/10)
    ordered = np.sort(y_arr)[-max_ref_count:]
    ch_max = np.average(ordered)
    bkg = np.where(y_arr < threshold*ch_max, 0, y_arr)
    bkg = np.where(bkg > 0, 1, bkg)
    mask = np.repeat(bkg[None,:], data.axes[0].size, axis=0)
    if negative:
        mask = 1-mask
    nobkg = data[channel][:] * mask

    data.create_channel(name=channel+"_nobkg", values=nobkg, units=data[channel].units)
    data[channel+'_nobkg'].signed = data[channel].signed
    if return_mask:
        data.create_channel(name=data[channel].natural_name+"_mask", values=mask)
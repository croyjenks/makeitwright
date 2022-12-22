__name__ = "hyperspectral"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

"""
Processing and plotting methods for 3-dimensional WrightTools data objects containing two spatial axes and one non-spatial axis (i.e. a spectral axis).

The two spatial axes are generally defined as x and y. 
The third axis is referred to as "spectral axis", 
but an arbitrary non-spatial or pseudo-spatial axis may be used where relevant.

Data axes must be ordered (spatial x, spatial y, non-spatial).
"""

#import
import numpy as np
from helpers import parse_args

def remove_background(data, channel, threshold=0.1, negative=False, return_mask=False, max_ref_count=10):
    """
    Remove background pixels from the x-y plane of the hyperspectral image using the spectrally binned image as a reference signal.
    Background x-y points will be set to 0 along the entire spectral axis.
    
    Parameters
    ----------
    data : Data object of WrightTools data module.
        The data for which the background-subtracted channel will be generated.
    channel : int or str
        The channel that will be duplicated with subtracted background.
    threshold : float between 0 and 1, optional
        The fraction of the maximum reference value below which is to be considered background. 
        The default is 0.1.
    negative : bool, optional
        Subtract everything but the background instead. Useful if the region of interest is the signal minimum. 
        The default is False.
    max_ref_count : int, optional
        The number of highest x-y points in the image to be averaged as a reference for the channel maximum. Useful to avoid false maxima caused by spikes.
        The default is 10.

    Returns
    -------
    None.
        Adds a background-subtracted channel to the Data instance.
    """
    #parse channel argument as str
    channel, = parse_args(data, channel, dtype='Channel')
    
    #generate a spectrally binned image of the channel
    ch_arr = np.sum(data[channel][:], axis=2)
    #get a representative maximum value from the reference image
    if max_ref_count > ch_arr.size:
        max_ref_count = int(ch_arr.size/10)
    ordered = np.sort(ch_arr.flatten())[-max_ref_count:]
    ch_max = np.average(ordered)
    #generate a mask array
    bkg = np.where(ch_arr < threshold*ch_max, 0, ch_arr)
    bkg = np.where(bkg > 0, 1, bkg)
    #remove background using mask
    mask = np.repeat(bkg[:,:,None], data.axes[2].size, axis=2)
    if negative:
        mask = 1-mask
    nobkg = data[channel][:] * mask
    #create background-subtracted channel
    data.create_channel(name=channel+"_nobkg", values=nobkg)
    data[channel+'_nobkg'].signed = data[channel].signed
    if return_mask:
        data.create_channel(name=data[channel].natural_name+"_mask", values=mask)
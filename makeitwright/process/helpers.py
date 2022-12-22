__name__ = "processhelpers"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
from scipy.signal import find_peaks_cwt
import matplotlib as mpl
from matplotlib import pyplot as plt
import WrightTools as wt

def parse_args(data, *args, dtype='Axis', return_name=True):
    argout = list(args)
    
    if dtype == 'Axis':
        for i, arg in enumerate(args):
            if return_name:
                if isinstance(arg, int):
                    argout[i] = data.axes[arg].natural_name
            else:
                if isinstance(arg, str):
                    argout[i] = [i for i, axis in enumerate(data.axes) if axis.natural_name==arg][0]
                
    if dtype == 'Channel':
        for i, arg in enumerate(args):
            if return_name:
                if isinstance(arg, int):
                    argout[i] = data.channels[arg].natural_name
            else:
                if isinstance(arg, str):
                    argout[i] = [i for i, channel in enumerate(data.channels) if channel.natural_name==arg][0]

    if len(argout) == 1:
        return (argout[0],)
    else:
        return tuple(argout)

def set_label(data, key, name):
    if type(key) is not str:
        raise TypeError(f'key must be string, function received {type(key)}')
    
    if type(data) is not list:
        data = [data]
    
    for d in data:
        try:
            d[key].attrs['label'] = name
        except KeyError:
            print(f'no object with key {key} in data {d.natural_name}')

def normalize(arr, tmin, tmax):
    diff = tmax-tmin
    arr_range = np.max(arr)-np.min(arr)
    norm_arr = np.nan_to_num((((arr-np.min(arr))*diff)/arr_range) + tmin)
    return norm_arr

def __split_n(arr, *axes):
    """
    Split an array sequentially along multiple axes. Multi-axis calls nested lists of arrays. Calling a single axis is equivalent to the numpy.split() method.

    Parameters
    ----------
    arr : numpy array
        The array to be split.
    *axes : interable of ints
        The axes along which the array will be split.

    Returns
    -------
    arr : lists of numpy arrays
        The split sub-arrays.
    """
    axes = list(axes)
    while axes:
        if type(arr) is list:
            spl_arr = []
            for a in arr:
                spl_arr.append(__split_n(a, *axes))
            arr = spl_arr
        else:
            arr = np.split(arr, arr.shape[axes[0]], axis=axes[0])
        del(axes[0])
    return arr

def __inverse_split_n(split_arr, *split_axes):
    """
    Reconstruct a split array into its original form, provided the list of axes that was used to split the array via split_n.

    Parameters
    ----------
    split_arr : lists of numpy arrays
        The split array in the form generated by split_n.
    *split_axes : int
        The axes arguments called in split_n to produce split_arr, in the same order.

    Returns
    -------
    split_arr : numpy array
        A single array matching the original unsplit dimensionality.
    """
    split_axes = list(split_axes)
    while split_axes:
        if type(split_arr[0]) is list:
            arr = []
            for l in split_arr:
                arr.append(__inverse_split_n(l, split_axes[-1]))
            split_arr = arr
            del(split_axes[-1])
        else:
            split_arr = np.concatenate(split_arr, axis=split_axes[-1])
            del(split_axes[-1])
    return split_arr

def normalize_by_axis(data, channel, *axes, bounds=(0,1)):
    """
    Normalize a channel of a data object along explicitly defined axes.
    EXAMPLE: For a 3-dimensional data set with axes (x, y, z):
        Normalizing by z produces independently normalized z-profiles for all (x, y).
        Normalizing by (x, y) produces independently normalized xy planes for every z-slice.
        Noramlizing by (x, y, z) normalized the channel as a whole.

    Parameters
    ----------
    data : Data object of WrightTools data module.
        The data containing the channel to be normalized.
    channel : string or int
        The key or index of the channel to be normalized.
    *axes : iterable of strings and/or ints
        The keys or indices of the axes along which to normalize the channel.
    bounds : iterable of numbers, optional
        The lower and upper bounds for normalization, in order.

    Returns
    -------
    None.
        Adds a normalized channel to the Data instance.
    """
    def __norm_split(split_arr, bounds): #TODO generalize to arbitrary operation
        if type(split_arr) is list:
            l = []
            for a in split_arr:
                l.append(__norm_split(a, bounds))
            split_arr = l
        else:
            split_arr = normalize(split_arr, bounds[0], bounds[1])
        return split_arr

    axes = parse_args(data, *axes, return_name=False)
    dims = [i for i, axis in enumerate(data.axes) if i not in axes]
    channel, = parse_args(data, channel, dtype='Channel')
    
    ch_arr = data[channel][:]
    ch_spl = __split_n(ch_arr, *dims)
    ch_spl_norm = __norm_split(ch_spl, bounds)
    ch_norm = __inverse_split_n(ch_spl_norm, *dims)
    ch_name = "norm_"
    for ax in [axis.natural_name for i, axis in enumerate(data.axes) if i not in dims]:
        ch_name = ch_name + data[ax].natural_name
    
    data.create_channel(ch_name, values=ch_norm)

def __at(arr, val):
    return (np.abs(arr-val)).argmin()

def roi(data, ROI, return_arrs=False, verbose=False):
    """
    Extract a region of interest (ROI) from data objects using a variety of operations, 
        without generating useless secondary data or collapsed variables.

    The extracted ROI's are of equivalent type as the input, unless return_arrs is set to True.
    The returned data are new instances distinct from the input, with their own unique .wt5 files. 
    Further modification of the output data will not affect the input data.

    Parameters
    ----------
    data : WrightTools Data, WrightTools Collection, or list of WrightTools Data
        The data from which the ROI will be extracted. 
        Axes of all input data must have axes with indices or names matched to the ROI, but they need not have identical shapes.
    
    ROI : dictionary
        The region of interest to extract from all input data. ROI's will be interpreted in the following ways:
            String keys will be interpreted as axis names.
            Integer keys will be interpreted as axis indices.
            
            Numerical values will extract the single point along that axis which is closest to the value, collapsing the axis.
            List values will extract the points along that axis which fall within the range of two numbers (if the list contains 2 numbers),
                or that lie beyond the number (if the list contains 1 number)
            Certain string values will collapse the points along that axis via a specified method. Valid methods include:
                'average', which yields arrays averaged along that axis
                'median', which extracts the median along that axis
                'sum', which yields arrays summed along that axis

            Tuple values will be interpreted as an ordered sequence of the operations described above.
    
    return_arrs : boolean, optional, default=False
        Specify the return format of the data.
            If False, the returned data will match the format of the input data.
            If True, the returned data will be formatted as a list of dictionaries 
                containing the variable and channel names as keys and their corresponding arrays as values.
    
    verbose : boolean, optional, default=False
        Toggle talkback.

    Returns
    -------
    out: Equivalent type to input data or list of dictionaries
        New Data instance(s) containing only the regions of interest from the original(s), with collapsed variables removed.

    Examples
    --------
    Using a 100mm x 100mm photograph as an example, stored as a Data instance my_data with axes ('x','y'), each in units mm.

    Calling the function "my_data_ROI = roi(my_data, ROI)" extracts the following data from my_data depending on the format of ROI: 
        if ROI = {'y':'sum'}: 
            Returns a 1D x-profile of the image. The channels will be the signals summed along the entire y-axis.
        
        if ROI = {'x':([20,80],'sum')}: 
            Returns a 1D y-profile of the image. The channels will be the summed signals along the x-axis from x=20mm - x=80mm.
        The ordering of the tuple affects the outcome. As a counterexample, if my_ROI = {'x':('sum',[20,80])}: 
            The 1D y-profile will summed along the entire x-axis. The function will ignore the second operation because the variable was already collapsed by the first.
        
        if ROI = {'x':[20,80], 'y':[50]}: 
            Returns a cropped (60mm x 50mm) image containing points from x=20mm - x=80mm and y=50mm - y=100mm.
        
        if ROI = {'x':[20,80], 1:50}: 
            Returns a cropped (60 mm) x-profile of the pixels at the row where y (axis 1) = 50mm, containing points from x=20mm - x=80mm.

    See Also
    --------
    WrightTools.Data.collapse
    WrightTools.Data.moment
    WrightTools.Data.split
    """
    def __copy_attrs(data, new_data, object_key):
        #do not overwrite default HDF5 parameters that come with new instances
        nocopy = {key for key in new_data[object_key].attrs.keys()}
        for key, value in data[object_key].attrs.items():
            if key not in nocopy:
                new_data[object_key].attrs[key] = value

    operations = {
        'sum' : np.sum,
        'product' : np.prod,
        'average' : np.average,
        'stdev' : np.std,
        'var' : np.var,
        'median' : np.median,
        'min' : np.min,
        'max' : np.max
    }

    if type(data) is not list and type(data) is not wt.Data and type(data) is not wt.Collection:
        raise TypeError(f'Unsupported data type {type(data)} was passed to the function. Supported data types include WrightTools Data objects, lists of WrightTools Data objects, or WrightTools Collection objects.')

    if type(data) is wt.Collection and not return_arrs:
        out = wt.Collection(name=data.natural_name)
        data = [data[d] for d in data]
    else:
        out = []
        if type(data) is not list:
            data = [data]

    for d in data:
        variables = dict([(var.natural_name, d[var.natural_name][:]) for var in d.variables])
        axes = [ax.natural_name for ax in d.axes]
        channels = dict([(ch.natural_name, d[ch.natural_name][:]) for ch in d.channels])

        for key, value in ROI.items():
            axis = key

            if key not in axes:
                if type(key) is int and key in range(len(d.axes)): #try indexing using the key provided if it isn't a valid axis name
                    axis = d.axes[key].natural_name
                else:
                    axis = None
                    print(f'axis {key} not found')

            if axis is not None:
                collapsed=False
                axarr = variables[axis]
                axidx = [i for i, dimlength in enumerate(axarr.shape) if dimlength>1]
                #if there is no dimension greater than 1 in the axis array, consider it a collapsed variable
                if not axidx:
                    collapsed=True
                else:
                    axidx = axidx[0]
                #interpret a single operation or a sequence of operations on the variable
                if type(value) is tuple:
                    ops = [op for op in value]
                else:
                    ops = [value]
                #extract the ROI
                for op in ops:
                    if not collapsed:
                        if type(op) is str and op in operations.keys():
                            for ch, charr in channels.items():
                                if charr.shape[axidx]==axarr.shape[axidx] and charr.ndim==axarr.ndim:
                                    channels[ch] = operations[op](charr, axis=axidx)
                            collapsed=True

                        if type(op) is int or type(op) is float:
                            ax0 = __at(axarr, op)
                            for ch, charr in channels.items():
                                if charr.shape[axidx]==axarr.shape[axidx] and charr.ndim==axarr.ndim:
                                    extracted = np.split(charr, charr.shape[axidx], axis=axidx)[ax0]
                                    channels[ch] = np.squeeze(extracted, axis=axidx)
                            collapsed=True
                            if verbose:
                                print(f'ROI extracted at {axis} = {op} for data {d.natural_name}')

                        if type(op) is list:
                            if len(op) not in [1, 2]:
                                print(f'specified bounds for split along axis {key} contained {len(op)} elements, but only 1 or 2 elements were expected')
                            bounds = sorted([__at(axarr, bound) for bound in op])
                            if np.split(axarr, bounds, axis=axidx)[1].shape[axidx]==1:
                                collapsed=True  

                            for ch, charr in channels.items():
                                if charr.ndim==axarr.ndim and charr.shape[axidx]==axarr.shape[axidx]:
                                    channels[ch] = np.split(charr, bounds, axis=axidx)[1]   
                            for var, varr in variables.items():
                                if varr.ndim==axarr.ndim and varr.shape[axidx]==axarr.shape[axidx]:
                                    variables[var] = np.split(varr, bounds, axis=axidx)[1]
                            if verbose:
                                print(f'extracted range {op[0]} to {op[-1]} along {axis} for data {d.natural_name}')

                        axarr = variables[axis]

                    else:
                        print(f'cannot interpret operation {op} for axis {axis} of data {d.natural_name} because the variable was already collapsed')

                    if collapsed:
                        variables.pop(axis)
                        axes.remove(axis)
                        for var, varr in variables.items():
                            if varr.ndim==axarr.ndim and varr.shape[axidx]==1:
                                variables[var] = np.squeeze(varr, axis=axidx)
                        for ch, charr in channels.items():
                            if charr.ndim==axarr.ndim and charr.shape[axidx]==1:
                                channels[charr] = np.squeeze(charr, axis=axidx)
                        if verbose:           
                            print(f'axis {axis} collapsed via operation {op} for data {d.natural_name}')        

        if return_arrs: #return a dictionary of arrays deconstructed from the original data object
            arrs = {}
            for var, varr in variables.items():
                if var in axes:
                    arrs[var] = varr
            for ch, charr in channels.items():
                arrs[ch] = charr
            out.append(arrs)

        else: #construct new Data objects
            if type(out) is wt.Collection:
                out.create_data(name=d.natural_name)
                d_out = out[-1]
            else:
                d_out = wt.Data(name=d.natural_name)
            
            keysHDF5 = {key for key in d_out.attrs.keys()}

            for var, varr in variables.items():
                if d[var].units is not None:
                    d_out.create_variable(var, values=varr, unit=d[var].units)
                else:
                    d_out.create_variable(var, values=varr, units=None)
                __copy_attrs(d, d_out, var)

            for ch, charr in channels.items():
                if d[ch].units is not None:
                    d_out.create_channel(ch, values=charr, units=d[ch].units)   
                else:
                    d_out.create_channel(ch, values=charr, units=None)
                if d[ch].signed:
                    d_out[ch].signed=True
                __copy_attrs(d, d_out, ch)

            for key, value in d.attrs.items():
                if key not in keysHDF5:
                    d_out.attrs[key] = value
            d_out.transform(*axes)
            if type(out) is not wt.Collection:
                out.append(d_out)

    if len(out)==1:
        out=out[0]

    return out

def show(data):
    if type(data) is not list:
        data = [data]
    return [f'{i} - name: {d.natural_name}, axes:{[ax.natural_name for ax in d.axes]}' for i, d in enumerate(data) if type(d) is wt.Data]
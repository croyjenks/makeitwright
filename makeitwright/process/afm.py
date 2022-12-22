__name__ = "AFM"
__author__ = "Chris R. Roy, Song Jin Research Group, Department of Chemistry, University of Wisconsin-Madison"
__version__ = 0.0

import numpy as np
import WrightTools as wt

def flatten(data, channel):
    pass

def ID_steps(data, channel):
    pass

def from_Gwyddion_traces(filepath, name=None):
    """
    Generate individual Data objects for a series of traces as exported from Gwyddion workup.
    
    ---Arguments---
    filepath - str - The path to where the data is located.
    
    ---Keyword Arguments---
    name - str - The base name for the data
    convert_units - bool - When True, converts the units of x and y into what is anticipated for typpical  AFM topography (um, nm)
    ID_steps - bool - When True, identifies the most significant topography change in the trace as a "step" and sets that position as 0 in the x array
    flatten - bool - When True, subtracts the median slope from the y trace
    ---Returns---
    data - WrightTools Data object or list of WrightTools Data objects - the data generated from the file's arrays
    """
    if name is None:
        basename = filepath.split('/')[-1].split('.')[0]
    else:
        basename = name

    header = 0
    delimiter = None
    dims = None
    units = None
    with open(filepath) as f:
        txt = f.readlines()
        for i, line in enumerate(txt):
            if not '.' in line: #assumes each row of data has a decimal somewhere
                header+=1
            if 'x' in line:
                spl = line.split()
                dims = [(spl[i], spl[i+1]) for i in range(0,len(spl),2)]
            if '[' in line:
                units = [l.strip('[]') for l in line.split()]
                units = [(units[i], units[i+1]) for i in range(0, len(units), 2)]
            if ',' in line and i>2:
                delimiter = ','
            if i>10:
                break
    arr = np.genfromtxt(filepath, skip_header=header, delimiter=delimiter)
    if arr.shape[1]>2:
        profiles = np.split(arr, arr.shape[1]/2, axis=1)
    else:
        profiles = [arr]
    profiles = [p[~np.isnan(p).any(axis=1)] for p in profiles]

    if dims is None:
        dims = [('x','y') for i in range(len(profiles))]
    if units is None:
        units = [None for i in range(len(profiles))]
    #return profiles, dims, units

    data = []
    for i, (profile, dim, unit) in enumerate(zip(profiles, dims, units)):
        x, y = profile[:,0], profile[:,1]

        if unit is None:
            x = wt.units.convert(x,'m','um')
            xunit, yunit = 'm', 'm'
            print(f'no units for x or y identified - assumed each to be meters')
        else:
            if wt.units.is_valid_conversion(unit[0], 'um'):
                x = wt.units.convert(x, unit[0], 'um')
                xunit = 'um'
            else:
                print(f'unrecognized unit {unit[0]} for x dimension of profile {i} - conversion did not proceed')
                xunit = unit[0]
            if wt.units.is_valid_conversion(unit[1], 'nm'):
                y = wt.units.convert(y, unit[1], 'nm')
                yunit = 'nm'
            else:
                print(f'unrecognized unit {unit[1]} for x dimension of profile {i} - conversion did not proceed')
                yunit = unit[1]

        xlabel = f'distance ({xunit})'

        if flatten:
            slope = np.median(np.gradient(y))/np.median(np.gradient(x))
            bkg = slope*x+y[0]
            y = y-bkg

        d = wt.Data(name=f'{basename}_profile{i}')
        d.create_variable(dim[0], values=x, units=xunit)
        d.create_channel(dim[1], values=y, units=yunit)
        d.create_channel(f'{dim[1]}_rel', values=y-np.min(y), units=yunit)
        d[dim[0]].attrs['label'] = xlabel
        d[dim[1]].attrs['label'] = f'topography ({yunit})'
        d[f'{dim[1]}_rel'].attrs['label'] = f'relative height ({yunit})'
        d.transform(dim[0])
        data.append(d)

    if len(data) == 1:
        data = data[0]
    return data
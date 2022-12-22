__name__ = "xrd"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
import WrightTools as wt

def from_Bruker_XRD(*filepath, name=None):
    header_size=None
    dtype = "Locked Coupled"
    with open(filepath) as f:
        txt = f.readlines()
    for i, line in enumerate(txt):
        if "ScanType" in line:
            dtype = line.split('=')[-1].strip()
        if "[Data]" in line:
            header_size = i+2
    if header_size is None:
        try:
            arr = np.genfromtxt(filepath, skip_header=166, delimiter=',')
            print("Data header was not identified in file. Data in instance may not reflect complete file information.")
        except:
            print("Unable to read data from file due to lack of expected data header.")
    else:
        arr = np.genfromtxt(filepath, skip_header=header_size, delimiter=',')
    
    if arr.size > 0:
        deg_arr = arr[:,0].flatten()
        ch_arr = arr[:,1].flatten()
        pattern = wt.Data(name=name)
        pattern.create_channel('sig', values=ch_arr)
        if dtype=="Locked Coupled":
            pattern.create_variable('ang', values=deg_arr, units='deg')
            pattern.transform('ang')
            pattern.attrs['acquisition'] = 'XRD_2theta'
        if dtype=="Z-Drive":
            pattern.create_variable('z', values=deg_arr, units='mm')
            pattern.transform('z')
            pattern.attrs['acquisition'] = 'XRD_2theta'
    else:
        print(f'file {filepath} was loaded but had no values')
    return pattern
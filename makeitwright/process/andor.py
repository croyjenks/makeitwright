__name__ = "andor"
__author__ = "Chris Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin - Madison"
__version__ = 0.0

import numpy as np
from matplotlib import pyplot as plt
import WrightTools as wt

from .helpers import __at, roi

scales = {
}

def get_PL(data, ybkg=None, yspot=None, cps=True):
    if type(data) is not list:
        data = [data]

    for d in data:
        k = 0
        if ybkg is not None:
            k = roi(d, {'y':(ybkg,'average')}, return_arrs=True)['sig']
            k = k.reshape((k.size,1))
            k = k.repeat(d['sig'][:].shape[1], axis=1)

        cycle_time = 1
        if cps:
            try:
                exposure = float(d.attrs["Exposure Time (secs)"])
            except KeyError:
                exposure = 1
            try:
                accum = int(d.attrs["Number of Accumulations"])
            except KeyError:
                accum = 1
            cycle_time = exposure*accum

        sig = d['sig'][:]
        if cps:
            d.create_channel('corr', values=(sig-k)/cycle_time, units='Hz')
            d['corr'].attrs['label'] = "PL intensity (cps)"
        else:
            d.create_channel('corr', values=(sig-k)/cycle_time)
            d['corr'].attrs['label'] = "PL counts"

    if yspot:
        return roi(data, {'y':(yspot,'sum')})

def microabsorbance(I_T, I_R, I0_T, I0_R, 
    substrate=None, wlbkg=None, ybkg=None, dark_ref=None):
    """
    Quantitatively computes the microabsorbance from transmission and reflection from a specular object and generates a new data object containing the transmittance, absorbance, and reflectance of the object.
    --------------------------
    Arguments
        I_T, I_R - Data objects of WrightTools.data module - The transmitted and reflected intensities from the same object of interest.
    """
 
    cwls = [float(d.attrs["Wavelength (nm)"]) for d in [I_T,I_R,I0_T,I0_R]]
    if len(set(cwls)) != 1:
        raise ValueError("center wavelengths are not matched for the data provided")

    I, wl, y = [d['sig'][:] for d in [I_T,I_R,I0_T,I0_R]], [d['wl'][:] for d in [I_T,I_R,I0_T,I0_R]], [d['y'][:] for d in [I_T,I_R,I0_T,I0_R]]

    substrate_refs = {
        'UVFS':'transmittance_references/UVFS.csv',
        'sapphire':'transmittance_references/sapphire.csv',
        'ThorLabs silver':'transmittance_references/Ag-P01.csv',
        'BK7':'transmittance_references/BK7.csv',
        'fluorite':'transmittance_references/CaF2.csv',
        'MgF2':'transmittance_references/MgF2.csv',
        'ThorLabs UV Al':'transmittance_references/UVAl.csv'
        }
    sub = [np.ones(w.size) for w in wl[:2]]
    if substrate is not None:
        try:
            subarrs = np.genfromtxt(substrate_refs[substrate], delimiter=',', skip_header=1)
            wls = subarrs[:,0].flatten()
            Is = subarrs[:,1].flatten()
            sub = [np.interp(w,wls,Is) for w in wl[:2]]
        except KeyError:
            print(f'reference data for substrate {substrate} was not found')
    Tsub, Rsub = np.repeat(sub[0].reshape((sub[0].size,1)), I[0].shape[1], axis=1), 1-np.repeat(sub[1].reshape((sub[1].size,1)), I[1].shape[1], axis=1)
    
    dark = []
    if type(dark_ref) is list and len(dark_ref)==4:
        for ref in dark_ref:
            if type(ref) is int:
                dark.append(ref)
            else:
                try:
                    dark.append(np.average(ref.channels[0][:]))
                except AttributeError:
                    print("unknown data type for dark reference encountered, reverting to wavelength reference for all data")
    if len(dark) != 4:
        if wlbkg is not None:
            if len(wlbkg)==1:
                wlbkg = wlbkg+[10000]
            dark = [np.average(a[__at(w,wlbkg[0]):__at(w,wlbkg[1]),:]) for a, w in zip(I,wl)]
        else:
            print("no dark count references found")
            dark = [0,0,0,0]
    
    exposure = []
    for d in [I_T,I_R,I0_T,I0_R]:
        ex = float(d.attrs["Exposure Time (secs)"])
        try:
            ex*=float(d.attrs["Number of Accumulations"])
        except:
            pass
        exposure.append(ex)
    
    I = [(a-k)/e for a, k, e in zip(I, dark, exposure)]
    
    corr = [1,1]
    if ybkg is not None:
        if len(ybkg)==1:
            ybkg = ybkg+[10000]
        bkg = [np.average(a[:,__at(ay,ybkg[0]):__at(ay,ybkg[1])]) for a, ay in zip(I,y)]
        corr = [bkg[0]/bkg[2], bkg[1]/bkg[3]]

    T, R = Tsub*(I[0]/(corr[0]*I[2])), Rsub*(I[1]/(corr[1]*I[3]))
    I_T.create_channel('corr', values=T)
    I_T['corr'].attrs['label'] = "transmittance"
    I_R.create_channel('corr', values=R)
    I_R['corr'].attrs['label'] = "reflectance"

    A = 1-T-R
    dA = wt.Data()
    dA.create_variable('wl', values=I_T['wl'][:])
    dA['wl'].attrs['label'] = "wavelength (nm)"
    dA.create_variable('y', values=I_T['y'][:])
    dA['y'].attrs['label'] = "y (µm)"
    dA.create_channel('corr', values=A)
    dA['corr'].attrs['label'] = "absorbance"
    dA.transform('wl','y')
    return dA

def spectcorr(s, s0, rois=[], T=False):
    if type(s) is not list:
        s = [s]
    dark = []
    corr = []
    arrs = []
    a0 = s0['sig'][:]
    dark0 = np.average(a0[0,:])
    a0 = a0-dark0
    a0 = np.where(a0<0,0,a0)
    if not rois:
        rois = [[None,None] for i in range(len(s))]

    for d in s:
        dark.append(np.average(d['sig'][0,:]))
        
    for d, r, k in zip(s, rois, dark):
        a = d['sig'][:]-k
        arrs.append(a)
        if r==[None,None]:
            corr.append(1)
            print(f'{d.natural_name} - no correction')
        else:
            y = d['y'][:]
            idx = [None,None]
            for i in range(2):
                if r[i] is not None:
                    idx[i] = __at(y, r[i])
            counts = []
            counts0 = []
            weights = []
            if r[0] is not None:
                counts.append(np.average(a[:,:idx[0]]))
                counts0.append(np.average(a0[:,:idx[0]]))
                weights.append(idx[0])
            if r[1] is not None:
                counts.append(np.average(a[:,idx[1]:]))
                counts0.append(np.average(a0[:,idx[1]:]))
                weights.append(a0.shape[1]-idx[1])
            pxcount = sum(weights)
            weights = [w/pxcount for w in weights]
            fact = sum([w*(c/c0) for w, c, c0 in zip(weights, counts, counts0)])
            print(f'{d.natural_name} - {fact}')
            corr.append(fact)

    for d, a, fact in zip(s, arrs, corr):        
        charr = np.nan_to_num(a/(fact*a0))
        charr = np.where(charr>5, 0, charr)
        if not T:
            #correction factor for slide reflectance vs mirror
            charr = 0.20103*charr
        d.create_channel('corr', values=charr)
        if T:
            Acharr = -np.nan_to_num(np.log10(charr))
            Acharr = np.where(Acharr>5, 0, Acharr)
            Acharr = np.where(Acharr<0, 0, Acharr)
            d.create_channel('A', values=Acharr)
            

def mask(im, bkgroi=None, window=0.05):
    #images must have same dimensions, bkgroi is not optional as currently written
    if type(im) is list:
        a = np.dstack(tuple([d['sig'][:] for d in im]))
        a = np.sum(a, axis=2)
        x, y,  = im[0]['x'][:], im[0]['y'][:]
    else:
        a = im['sig'][:]
        x, y,  = im['x'][:], im['y'][:]
    
    if bkgroi is None:
        print("background region needed")
        return
    else:
        xidx = [__at(x,bkgroi['x'][0]),__at(x,bkgroi['x'][1])]
        yidx = [__at(y,bkgroi['y'][0]),__at(x,bkgroi['y'][1])]
    bkg = np.average(a[xidx[0]:xidx[1],yidx[0]:yidx[1]])
    a = np.where(a<(1-window)*bkg,0,a)
    a = np.where(a>(1+window)*bkg,0,a)
    a = np.where(a>0,1,a)
    plt.imshow(np.rot90(a))
    plt.show()
    return a
    

def imcorr(im, im0, slitroi0=None, slitrois=[], mask=None, T=False):
    if type(im) is not list:
        im = [im]
    dark = []
    corr = []
    arrs = []
    a0 = im0['sig'][:]
    
    if slitroi0 is not None:
        x = im0['x'][:]
        idx = [__at(x, slitroi0[0]), __at(x, slitroi0[1])]
        dark0 = [np.average(a0[:idx[0],:]),np.average(a0[idx[1]:,:])]
        dark0 = (dark0[0]+dark0[1])/2 
    else:
        dark0 = 0
    a0 = a0-dark0
    a0 = np.where(a0<0,0,a0)
    
    if slitrois:
        for d, r in zip(im, slitrois):
            a = d['sig'][:]
            x = d['x'][:]
            idx = [__at(x, r[0]), __at(x, r[1])]
            k = [np.average(a[:idx[0],:]),np.average(a[idx[1]:,:])]
            k = (k[0]+k[1])/2
            dark.append(k)
    else:
        dark = [0 for i in range(len(im))]
    
    for d, k in zip(im, dark):
        a = d['sig'][:]-k
        a = np.where(a<0,0,a)
        arrs.append(a)
        if mask is not None:
            c, c0 = np.sum(a*mask), np.sum(a0*mask)
            corr.append(c/c0)
            print(f'{d.natural_name} - {c/c0}')
        else:
            corr.append(1)
            print(f'{d.natural_name} - no correction')
    
    for d, a, fact in zip(im, arrs, corr):
        charr = np.nan_to_num(a/(fact*a0))
        charr = np.where(charr>5, 0, charr)
        if not T:
            #correction factor for slide reflectance vs mirror
            charr = 0.20103*charr
        d.create_channel('corr', values=charr)
        if T:
            Acharr = -np.nan_to_num(np.log10(charr))
            Acharr = np.where(Acharr>5, 0, Acharr)
            Acharr = np.where(Acharr<0, 0, Acharr)
            d.create_channel('A', values=Acharr)        
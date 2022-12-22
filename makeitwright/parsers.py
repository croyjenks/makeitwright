__name__ = "parsers"
__author__ = 'Chris R. Roy, Song Jin Research Group, Dept. of Chemistry, University of Wisconsin-Madison'
__version__ = 0.0

from psutil import virtual_memory
from os import listdir
from os.path import isfile, isdir, getsize
import WrightTools as wt

from process.afm import from_Gwyddion_traces
from process.xrd import from_Bruker_XRD
from process.iontof import ITApeaks

def typeID(*fpaths):
    types = {}
    identified = 0
    for fpath in fpaths:
        if '.ita' in fpath:
            types[fpath] = 'iontof_SIMS'
            identified+=1
            print(f"file {fpath} is IonToF SIMS data")
            
        if '.txt' in fpath:
            with open(fpath) as f:
                txt = f.read()
            if "LabRAM HR" in txt:
                types[fpath] = 'LabRAM'
                identified+=1
            if "Goniometer" in txt:
                types[fpath] = 'Bruker_XRD'
                identified+=1
            if "[m]" in txt:
                types[fpath] = 'Gwyddion_traces'
                identified+=1

        if '.asc' in fpath:
            with open(fpath) as f:
                txt = f.read()
            if "*BLOCK" in txt:
                types[fpath] = 'TRPL'
                identified+=1
            else:
                types[fpath] = 'ASCII'
                identified+=1

        if '.wt5' in fpath:
            types[fpath] = 'wt5'
            identified+=1

    print(f"{identified} of {len(fpaths)} files identified as valid data types")
    return types

def listfiles(fdir, flist=[]):
    if len(flist) < 1000:
        dirlist = [f'{fdir}/{d}' for d in listdir(fdir) if isdir(f'{fdir}/{d}')]
        fpaths = flist+[f'{fdir}/{f}' for f in listdir(fdir) if isfile(f'{fdir}/{f}')]
        
        if dirlist:
            for d in dirlist:
                fpaths = listfiles(d, flist=fpaths)
        
        return fpaths
    else:
        print("Too many files in directory. Process terminated to prevent overflow.")
    

def parse(fdir, select_types=None, keywords=[], exclude=[]):
    files = listfiles(fdir)
    
    include = [1 for i in range(len(files))]
    if keywords:
        if type(keywords) is not list:
            keywords = [keywords]
        for kw in keywords:
            for i, f in enumerate(files):
                if kw not in f:
                    include[i]=0
    if exclude:
        if type(exclude) is not list:
            exclude = [exclude]
        for x in exclude:
            for i, f in enumerate(files):
                if x in f:
                    include[i]=0

    files = [file for i, file in enumerate(files) if include[i]]
    print(f'found {sum(include)} files matching keyword specifications')
    
    ftypes = typeID(*files)
    if select_types:
        to_delete=[]
        num_removed=0
        for key, value in ftypes.items():
            if value not in select_types:
                to_delete.append(key)
                num_removed+=1
        if to_delete:
            for key in to_delete:
                del(ftypes[key])
            print(f'excluded {num_removed} files that did not match specified data type(s)')
    
    if 'ASCII' in ftypes.values():
        objective = input(f'Enter objective lens magnification if all data in this directory used the same lens. Otherwise, press enter: ')
        if not objective:
            objective = 'prompt'

    #make sure call doesn't generate too much data, roughly 1 GB
    too_much_data = False
    if len([dtype for dtype in ftypes.values() if dtype=='iontof_SIMS']) > 1:
        too_much_data = True
    if len([dtype for dtype in ftypes.values() if dtype=='ASCII']) > 100:
        too_much_data = True
    if len(ftypes) > 200:
        too_much_data = True
    if sum([getsize(f) for f in files]) > virtual_memory().available:
        too_much_data = True

    if not too_much_data:
        d = []
        for fpath, dtype in ftypes.items():
            basename = fpath.split('/')[-1].split('.')[0]

            if dtype=='LabRAM':
                d.append(wt.data.from_LabRAM(fpath, name=basename))

            if dtype=='Bruker_XRD':
                l0 = len(d)
                d = d + from_Bruker_XRD(fpath, name=basename)
                l1 = len(d)-l0

            if dtype=='Gwyddion_traces':
                d.append(from_Gwyddion_traces(fpath, name=basename))

            if dtype=='iontof_SIMS':
                d.append((fpath, ITApeaks(fpath)))

            if dtype=='TRPL':
                l0 = len(d)
                d.append(wt.data.from_spcm(fpath, name=basename))
                l1 = len(d)-l0

            if dtype=='ASCII':
                try:
                    d.append(wt.data.from_Solis(fpath, name=basename))
                except:
                    print(f'attempted to extract ASCII data from path <{fpath}> but it was not recognized by the andor module')
            
            if dtype=='wt5':
                d.append(wt.open(fpath))

        return d
    else:
        print("too much data in directory, parsing cancelled to prevent storage overflow")

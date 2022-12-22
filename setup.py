from distutils.core import setup

setup(name='makeitwright', 
    version=0.7,
    description="Parsing, processing, and plotting methods for various scientific data types.",
    author="Chris Roy, Song Jin Research Group, Department of Chemistry, University of Wisconsin-Madison",
    packages=['makeitwright'],
    py_modules=['afm','andor','artists','beckerhickl','hyperspectral','image','iontof','parsers','plothelpers','processhelpers','spectra','spectralprofile','styles','xrd']
    )
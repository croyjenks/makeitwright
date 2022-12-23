# makeitwright - a python package for high-throughput scientific data processing

__makeitwright__ is a lightweight python package to categorize, load, and manipulate large volumes of scientific data in accordance with user-defined presets.

The package is designed to leverage the many features of [`WrightTools`](https://pypi.org/project/WrightTools/), a python package for manipulation and plotting of multidimensional spectroscopy data and other high-dimensional datasets.

## Introduction

A common time sink in a scientist's workflow is repetitive pre-processing of data. Depending on the data format and needs of the researcher, it's not uncommon to hop between many different applications performing the same operations on many iterations of the same data type. Some programs offer selections of automated processing routines, but often those routines are not exactly what a researcher needs. On the other hand, handwritten processing scipts offer exact precision in processing, but a library of processing scripts for different data formats can easily wind up clunky and disorganized.

`makeitwright` functions as a repository of processing methods and stylistic presets that a researcher can modify at will. It categorizes and imports volumes of data using the `parsers` module, applies select processing routines using the `process` library, and presents the data according to user-defined presets using the `artists` and `styles` modules. The imported data is formatted under a unified HDF5-derived framework, enabling the manipulation of arbitrary data types with common methods.

`makeitwright` does not bind researchers to python for any particular stage of their workflow; in fact, it can simply be used as a file converter if desired, but the possiblities extend a full processing chain entirely written in python.

## Disclaimer

This package is under development and there is no guaruntee of its functionality for any given data type. Constructive feedback is encouraged!

## Dependencies

`makeitwright` has several dependencies beyond python's standard library, most of which come with the [Anaconda distribution](https://www.anaconda.com/products/distribution) of python:
- `numpy`
- `scipy`
- [`WrightTools`](https://pypi.org/project/WrightTools/) (not installed with Anaconda)
- [`pySPM`](https://pypi.org/project/pySPM/) (not installed with Anaconda)

All of these packages can be installed using [`pip`](https://pip.pypa.io/en/stable/), python's standard package manager, by calling `pip install <package-name>` in your python environment.

## Installation

`makeitwright` must currently be dowloaded and installed locally. The files in this repository can either be downloaded to your local python packages folder for general import, or the `makeitwright` files can be placed in a specific working directory for local import and user-modification.
""" Install tifffile.c """

# Usage: ``python build_tifffile.py build_ext --inplace``
from distutils.core import setup, Extension
import numpy
setup(name='_tifffile',
    ext_modules=[Extension('_tifffile', ['tifffile.c'],
                           include_dirs=[numpy.get_include()])])
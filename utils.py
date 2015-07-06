# -*- coding: utf-8 -*-
# utils.py

# Written by: Eduardo Olimpio
# 6-7-2015 at AMOLF, Amsterdam

import re
import tifffile as tff
import lxml.etree as etree
import struct
import os

def readConfigFile(path):
    
    f = open(path, 'r')
    out = {}
    for line in f.readlines():
        if not line in ['\n', '\r\n']:
            if not line[0] == '#':
                aux = line.rstrip('\n').split('=')
                if len(aux) == 2:
                    name = aux[0].strip()
                    value = aux[1].strip()
                    out[name] = value
    f.close()
    return out

def corrTIFPath(path, symbol, value):

    reg_expr_search = '(\%s+)'%str(symbol)
    length_of_replace = len(re.search(reg_expr_search, path).group(0))
    str_format = '{0:%sd}'%'{0:02d}'.format(length_of_replace)
    str_replace = str_format.format(int(value))

    return re.sub(reg_expr_search, str_replace, path)

def readTIFImage(filename):
    sType = 'uint16'
    with tff.TiffFile(filename) as tif:
        im_out = tif.asarray().astype(sType)

    return im_out

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generate_stacked_images.py

# Written by: Eduardo Olimpio
# 18-6-2015 at AMOLF, Amsterdam

"""Create stacked TIFF from single files

This program creates stacked TIFF for images of different planes
in the same time frame. The structure is defined by the filename
with the time being given by the ? symbol and the 3-D variable
by the @ symbol.

You can cut the images by choosing the position of the up-right
corner and the size os the cut (cut_x, cut_y).
This is done by setting the parameter cut as True. 

The program works for 16-bit images but work for other types
under small changes

This program needs tiifile.py and its dependencies. See:
http://www.lfd.uci.edu/~gohlke/

"""

# --- Declarations --- #

import numpy as np
import matplotlib.pyplot as plt
import re
import tifffile as tff

# --- Parameters --- #

n_time = 121 # number of time frames
n_z = 41 # number of z-components per time frame

# Cutting parameters, used only if cut = True
cut = True
cut_x = 953 
cut_y = 953
pos_x = 30
pos_y = 30

# Type of the file
sType = 'uint16'

# In - out file path
path = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T?????\\T?????C01Z@@@.tif"
path_out = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T?????\\T?????.tif"

# --- Main program --- #

for t in range(n_time):
    t_str = '{0:05d}'.format(t+1)
    path_corr_int = re.sub('(\?+)', t_str, path)
    path_out_corr = re.sub('(\?+)', t_str, path_out)
    for z in range(n_z):
        z_str = '{0:03d}'.format(z+1)
        path_corr = re.sub('(\@+)',z_str,path_corr_int)
        with tff.TiffFile(path_corr) as tif:
            image = tif.asarray()
            size = image.shape
            if z == 0:
                if cut:
                    im_out = np.zeros((n_z, cut_x, cut_y)).astype(sType)
                else:
                    im_out = np.zeros((n_z, size[0], size[1])).astype(sType)
            for page in tif:
                image = page.asarray().astype(sType)
        
        if cut:
            im_out[z, :, :] = image[pos_x:(pos_x+cut_x), pos_y:(pos_y+cut_y)]
        else:
            im_out[z, :, :] = image
    
    tags = []
    # Set min and max as in the original file
    tags.append((280, 'H', 1, 0, False))
    tags.append((281, 'H', 1, 4095, False))
    # Change sample format to u-int for Amat et. al software
    # tags.append((339, 'H', 1, 1, False)) 

    with tff.TiffWriter(path_out_corr) as tif:
        tif.save(im_out, extratags = tags)
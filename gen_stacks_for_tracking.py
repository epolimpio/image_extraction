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

The inputs are read from the a configuration file which path
is given when the program is called.

"""

# --- Declarations --- #
import numpy as np
import matplotlib.pyplot as plt
import re
import tifffile as tff
from track_utils import readConfigFile, corrTIFPath

def main(*args):
    # Type of the file
    sType = 'uint16'

    config_path = 'config_generate_stacked_images.conf'
    if len(args) >= 1:
        config_path = str(args[0]).strip('"')
    else:
        print('ERROR: What is the configuration file?')
        return False

    # Read parameters in config file
    out = readConfigFile(config_path)

    cut = out['cut'].lower() == 'true'
    cut_x = int(out['cut_x'])
    pos_x = int(out['pos_x'])
    cut_y = int(out['cut_y'])
    pos_y = int(out['pos_y'])
    n_time = int(out['n_time'])
    n_z = int(out['n_z'])
    t_ini = int(out['t_ini'])

    path_in = str(out['path_in'].strip('"'))
    print(path_in)
    path_out = str(out['path_out'].strip('"'))
    print(path_out)

    # --- Main program --- #

    for t in range(n_time):
        t_str = '{0:05d}'.format(t+t_ini)
        print("Time -> " + t_str)
        path_in_corr = corrTIFPath(path_in, '?', t+t_ini)
        path_out_corr = corrTIFPath(path_out, '?', t+t_ini)
        for z in range(n_z):
            z_str = '{0:03d}'.format(z+1)
            path_corr = corrTIFPath(path_in_corr, '@', z+1)
            with tff.TiffFile(path_corr) as tif:
                image = tif.asarray()
                size = image.shape
                if z == 0:
                    if cut:
                        im_out = np.zeros((n_z, cut_y, cut_x)).astype(sType)
                    else:
                        im_out = np.zeros((n_z, size[0], size[1])).astype(sType)
                for page in tif:
                    image = page.asarray().astype(sType)
            
            if cut:
                im_out[z, :, :] = image[pos_y:(pos_y+cut_y), pos_x:(pos_x+cut_x)]
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

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
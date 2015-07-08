
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_amat_xml.py

# Written by: Eduardo Olimpio
# 6-7-2015 at AMOLF, Amsterdam

# --- Declarations --- #

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import re
import tifffile as tff
import lxml.etree as etree
import struct
import os
from track_utils import *

def calcPixelsAddress(svIDList, pixIDList, dimX, dimY):

    ini = True
    for svIDs in svIDList:
        for svID in svIDs:
            pixIDs = pixIDList[svID]
            pixs = np.zeros((pixIDs.shape[0], 3))
            szFrame = dimX*dimY
            pixs[:,2] = pixIDs // szFrame
            pixs[:,1] = (pixIDs % szFrame) // dimX
            pixs[:,0] = (pixIDs % szFrame) % dimX

            if ini:
                pixPoints = pixs
                ini = False
            else:
                pixPoints = np.vstack((pixPoints, pixs))

    return pixPoints

def writeEyeCheck(image_out_path, image_path, binary_path, pos, n_time):

    for time_to_analyze in range(n_time):
        # pos_arr is a matrix (3,numberOfPoints) where 3 determines the dimension
        # x -> 0, y-> 1, z-> 2
        pos_arr = np.asarray(pos[time_to_analyze][0:3])

        # SuperVoxel IDs
        svIDList = pos[time_to_analyze][3]

        # Cells IDs
        IDs = np.asarray(pos[time_to_analyze][4])
        
        # read the tiff stacked image
        im_out = readTIFImage(corrTIFPath(image_path, '?', time_to_analyze+1))

        # read the binary file with the supervoxels
        dims, pixIDList = readSuperVoxelFromFile(binary_path, time_to_analyze)
        pixPoints = calcPixelsAddress(svIDList, pixIDList, dims[0,0], dims[1,0])

        n_stacks = im_out.shape[0]
        ax = plt.subplot(1,1,1)
        for stack in range(n_stacks):
            print('Time: ' + str(time_to_analyze) + ', Stack: ' + str(stack))
            
            # Set the path for the image
            image_out_corr = corrTIFPath(image_out_path, '?', time_to_analyze)
            image_out_corr = corrTIFPath(image_out_corr, '@', stack+1)
            ensure_dir(image_out_corr)

            # get all the points to be included
            size = im_out[stack,:,:].shape
            to_include = np.equal(np.floor(pos_arr[2,:]), stack)
            to_include = np.logical_or(to_include, np.equal(np.ceil(pos_arr[2,:]), stack))

            # write a list with all ID numbers to include
            IDs_to_include = IDs[to_include].tolist()

            # data for the graphs
            x = pos_arr[0,to_include]
            y = pos_arr[1,to_include]
            error = np.abs(pos_arr[2,to_include]-stack)
            pix_x, pix_y = np.meshgrid(np.arange(0,size[1],1), np.arange(0,size[0],1))

            # get all coordinates of pixels in this stack
            sv_pix = pixPoints[np.equal(pixPoints[:,2],stack),:]
            sv_pix = sv_pix.astype(int)
            sv_image = np.zeros((size[0], size[1]))
            sv_image[sv_pix[:,1], sv_pix[:,0]] = 1


            # Plot the data and save figure
            ax.contourf(pix_x, pix_y, im_out[stack,:,:],
                zorder = -1, cmap = cm.Greys_r)
            ax.autoscale(False)
            ax.imshow(sv_image, alpha = 0.3, zorder = 0, cmap = cm.Blues)
            ax.scatter(x, y, c = error, cmap = cm.autumn, zorder = 1)
            for index, lin_text in enumerate(IDs_to_include):
                ax.annotate(str(lin_text)[1:-1], (x[index],y[index]),
                    zorder = 2, fontsize = 10)
            plt.savefig(image_out_corr)
            ax.clear()

def main(*args):

    n_time = 1
    date = "2015_6_22_15_33_43"
    if len(args) >= 2:
        n_time = int(args[0])
        date = str(args[1])

    # Define filenames
    xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"
    image_out_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\eye_check\\T?????\\Z@@@.png"
    binary_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht\\GMEMfinalResult_frame????.svb"
    log_file = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\experimentLog_0001.txt"
    f = open(log_file, 'r')
    image_path = f.readlines()[4]
    f.close()
    image_path = image_path.split('=')[1][:-1] + '.tif'

    # read positions from XML
    pos = readXMLAmat(xml_path, n_time)

    # Run main file
    writeEyeCheck(image_out_path, image_path, binary_path, pos, 1)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
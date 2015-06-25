
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_amat_xml.py

# Written by: Eduardo Olimpio
# 18-6-2015 at AMOLF, Amsterdam

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

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def readSuperVoxelFromFile(filename, imageDim = 3):
# Similar to functions the authors built in Matlab
# Not really used yet!
    fid = open(filename, 'rb')
    numSv, = struct.unpack('i', fid.read(4))
    TM = np.zeros(numSv)
    dataSizeInBytes = np.zeros(numSv)
    dataDims = np.zeros((imageDim, numSv))
    pixIDlist = [np.zeros(1),]*numSv
    for k in range(numSv):
        TM[k], = struct.unpack('i', fid.read(4))
        dataSizeInBytes[k], = struct.unpack('Q', fid.read(8))
        dataDims[:,k] = np.asarray(struct.unpack('Q'*imageDim, fid.read(8*imageDim)))
        ll, = struct.unpack('I', fid.read(4))
        if ll>0:
            pixIDlist[k] = np.asarray(struct.unpack('Q'*ll, fid.read(8*ll)))
        else:
            pixIDlist[k] = np.asarray([])

    return dataDims, pixIDlist

def readXML(filename, n_time):
# Here we read he positions
    pos = [[[],[],[],[]],]*n_time
    for t in range(n_time):
        t_str = '{0:04d}'.format(t+1)
        xml_path_corr = re.sub('(\?+)', t_str, filename)
        tree = etree.parse(xml_path_corr)
        root = tree.getroot()
        all_points = root.xpath('GaussianMixtureModel')
        x = [0.0,]*len(all_points)
        y = [0.0,]*len(all_points)
        z = [0.0,]*len(all_points)
        i = 0
        for point in all_points:
            [x[i], y[i], z[i]] = [float(x) for x in point.xpath('attribute::m')[0].split()]
            i += 1
        pos[t] = [x,y,z]
    return pos

def readImage(filename, t):
# Read the images for comparison
    sType = 'uint16'
    t_str = '{0:05d}'.format(t+1)
    path_corr = re.sub('(\?+)', t_str, filename)
    with tff.TiffFile(path_corr) as tif:
        im_out = tif.asarray().astype(sType)

    return im_out

def write_eye_check(image_out_path, pos, n_time):

    for time_to_analyze in range(n_time):
        # pos_arr is a matrix (3,numberOfPoints) where 3 determines the dimension
        # x -> 0, y-> 1, z-> 2
        pos_arr = np.asarray(pos[time_to_analyze])
        im_out = readImage(image_path, time_to_analyze)
        n_stacks = im_out.shape[0]

        for stack in range(n_stacks):
            print('Time: ' + str(time_to_analyze) + ', Stack: ' + str(stack))
            # Set the path for the image
            t_str = '{0:05d}'.format(time_to_analyze)
            image_out_corr = re.sub('(\?+)', t_str, image_out_path)
            z_str = '{0:03d}'.format(stack+1)
            image_out_corr = re.sub('(\@+)',z_str,image_out_corr)
            ensure_dir(image_out_corr)

            # get all the points to be included
            size = im_out[stack,:,:].shape
            to_include = np.equal(np.floor(pos_arr[2,:]), stack)
            to_include = np.logical_or(to_include, np.equal(np.ceil(pos_arr[2,:]), stack))

            # data for the graphs
            x = pos_arr[0,to_include]
            y = pos_arr[1,to_include]
            error = np.abs(pos_arr[2,to_include]-stack)
            pix_x, pix_y = np.meshgrid(np.arange(0,size[0],1), np.arange(0,size[1],1))

            # Plot the data and save figure
            ax = plt.subplot(1,1,1)
            ax.contourf(pix_x, pix_y, im_out[stack,:,:],
                zorder = 0, cmap = cm.Greys_r)
            ax.autoscale(False)
            ax.scatter(x, y, c = error, cmap = cm.autumn, zorder = 1)
            plt.savefig(image_out_corr)
            ax.clear()



# Define filenames
date = "2015_6_22_15_33_43"
xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"
image_out_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\eye_check\\T?????\\Z@@@.png"
binary_path = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T?????\\T?????_hierarchicalSegmentation_conn3D74_medFilRad2.bin"
image_path = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T?????\\T?????.tif"

# read positions from XML
n_time = 10
pos = readXML(xml_path, n_time)

# Plot the data and save figure
# ax = plt.subplot(1,1,1)
# ax.contourf(pix_x, pix_y, im_out[stack,:,:],
#     zorder = 0, cmap = cm.Greys_r)
# ax.autoscale(False)
# ax.scatter(x, y, c = error, cmap = cm.autumn, zorder = 1)
# plt.savefig(image_out_corr)
# ax.clear()

# Run main file
write_eye_check(image_out_path, pos, 1)
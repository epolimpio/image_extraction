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

def calcAllPixelsAddress(pixIDList, dimX, dimY):

    ini = True
    for pixIDs in pixIDList:
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

def plotAllSV(image_out_path, time, track):

    frame = time - track.configs[track.TIME_INI_KEY]

    # read the tiff stacked image
    im_out = track.readInputImage(frame)

    # read the binary file with the supervoxels
    dims, pixIDList = track.readSVFile(frame)
    IDsList, svIDList = track.getSvIDsInFrame(frame, filtered = False)
    print(len(pixIDList), len(svIDList)) 
    pixPoints = calcAllPixelsAddress(pixIDList, dims[0,0], dims[1,0])

    n_stacks = im_out.shape[0]
    ax = plt.subplot(1,1,1)
    for stack in range(n_stacks):
        print('Stack: ' + str(stack))
        
        # Set the path for the image
        image_out_corr = corrTIFPath(image_out_path, '?', time)
        image_out_corr = corrTIFPath(image_out_corr, '@', stack+1)
        ensure_dir(image_out_corr)

        # get all the points to be included
        size = im_out[stack,:,:].shape

        # data for the graphs
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
        ax.set_title('Time: %d, Stack: %d'%(time, stack+1))
        plt.savefig(image_out_corr)
        ax.clear()

def main(*args):

    if len(args) >= 2:
        time = int(args[0])
        date = str(args[1])
    else:
        print('Provide the arguments for the function')
        print('Call must be: py plot_all_supervoxels.py <time> <results_date>')
        return None

    folder = "D:\\image_software\\results\\GMEMtracking3D_"+date
    image_out_path = folder + "\\eye_check\\T?????_allSV\\Z@@@.png"

    track = TrackingAnalysis(folder)

    # Run main file
    plotAllSV(image_out_path, time, track)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
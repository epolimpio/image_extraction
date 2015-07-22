
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_amat_xml.py

# Written by: Eduardo Olimpio
# 6-7-2015 at AMOLF, Amsterdam

# --- Declarations --- #

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from track_utils import *

def correct_path(path_in, t, z):

    image_out_corr = corrTIFPath(corrTIFPath(path_in, '?', t), '@', z)
    ensure_dir(image_out_corr)

    return image_out_corr

def writeEyeCheck(frame_ini, frame_end, track):

    # initial time frame
    t_ini = track.configs[track.TIME_INI_KEY]

    # output files pattern
    image_out_path = track.folder + "\\eye_check\\T?????\\Z@@@.png"
    image_out_path_SV = track.folder + "\\eye_check\\T?????_allSV\\Z@@@.png"
    image_out_path_Stack = track.folder + "\\eye_check\\T?????_stackOnly\\Z@@@.png"

    for time_to_analyze in range(frame_ini, frame_end+1, 1):

        # pos_arr is a matrix (3,numberOfPoints) where 3 determines the dimension
        # x -> 0, y-> 1, z-> 2
        pos_arr = np.asarray(track.getAllPositions(time_to_analyze, filtered = True))

        # Get IDs and SuperVoxel IDs
        IDsList, svIDList = track.getSvIDsInFrame(time_to_analyze, filtered = True)

        # Cells IDs array
        IDs = np.asarray(IDsList)
        
        # read the tiff stacked image
        im_out = track.readInputImage(time_to_analyze)

        # read the binary file with the supervoxels
        dims, pixIDList = track.readSVFile(time_to_analyze)
        pixPoints = calcPixelsAddress(svIDList, pixIDList, dims[0,0], dims[1,0])
        pixPointsSV = calcAllPixelsAddress(pixIDList, dims[0,0], dims[1,0])

        n_stacks = im_out.shape[0]
        ax = plt.subplot(1,1,1)
        for stack in range(n_stacks):
            print('Time: ' + str(time_to_analyze+t_ini) + ', Stack: ' + str(stack+1))
            
            # === Print all the data from the software === #

            # Set the path for the image
            image_out_corr = correct_path(image_out_path, time_to_analyze+t_ini, stack+1)

            # get all the points to be included
            size = im_out[stack,:,:].shape
            to_include = np.equal(np.floor(pos_arr[2,:]), stack)
            to_include = np.logical_or(to_include, np.equal(np.ceil(pos_arr[2,:]), stack))

            # write a list with all track numbers to include 
            # IDs_to_include = IDs[to_include].tolist()
            IDs_to_include = [track.ID2Track(aux, time_to_analyze) for aux in IDs[to_include].tolist()]

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
                ax.annotate(str(lin_text), (x[index],y[index]),
                    zorder = 2, fontsize = 10)
            ax.set_title('Time: %d, Stack: %d'%(time_to_analyze+t_ini, stack+1))
            plt.savefig(image_out_corr)
            ax.clear()

            # === Print all supervoxels === #

            # Set the path for the image
            image_out_corr = correct_path(image_out_path_SV, time_to_analyze+t_ini, stack+1)

            # get all coordinates of pixels in this stack
            sv_pix = pixPointsSV[np.equal(pixPointsSV[:,2],stack),:]
            sv_pix = sv_pix.astype(int)
            sv_image = np.zeros((size[0], size[1]))
            sv_image[sv_pix[:,1], sv_pix[:,0]] = 1

            # Plot the data and save figure
            ax.contourf(pix_x, pix_y, im_out[stack,:,:],
                zorder = -1, cmap = cm.Greys_r)
            ax.autoscale(False)
            ax.imshow(sv_image, alpha = 0.3, zorder = 0, cmap = cm.Blues)
            ax.set_title('Time: %d, Stack: %d'%(time_to_analyze+t_ini, stack+1))
            plt.savefig(image_out_corr)
            ax.clear()

            # === Print only figure === #

            # Set the path for the image
            image_out_corr = correct_path(image_out_path_Stack, time_to_analyze+t_ini, stack+1)

            # Plot the data and save figure
            ax.contourf(pix_x, pix_y, im_out[stack,:,:],
                zorder = -1, cmap = cm.Greys_r)
            ax.autoscale(False)
            ax.set_title('Time: %d, Stack: %d'%(time_to_analyze+t_ini, stack+1))
            plt.savefig(image_out_corr)
            ax.clear()

def main(*args):

    if len(args) >= 3:
        frame_ini = int(args[0])
        frame_end = int(args[1])
        date = str(args[2])
    else:
        print('Provide the arguments for the function')
        print('Call must be: py write_eye_check.py <frame_ini> <frame_end> <results_date>')
        return None
    
    back = True
    if len(args) > 3:
        if (args[3].lower() == 'false') or (str(args[3]) == '0'):
            back = False


    folder = "D:\\image_software\\results\\GMEMtracking3D_"+date

    track = TrackingAnalysis(folder, back)

    # Run main file
    writeEyeCheck(frame_ini, frame_end, track)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
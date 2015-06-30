# Brute force calculation of MIP in spherical coordinates

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import re
import tifffile as tff
from math import *
import itertools

def readStackImage(filename, sType = 'uint16'):
    with tff.TiffFile(filename) as tif:
        image = tif.asarray().astype(sType)
        size = image.shape
    
    return image, size

def rayPoints(center, theta, phi, r_max, n_points):

    r = float(r_max)/n_points*(np.arange(n_points) + 1)
    points = np.zeros((3, n_points))
    points[0,:] = center[0] + r*sin(theta)*cos(phi)
    points[1,:] = center[1] + r*sin(theta)*sin(phi)
    points[2,:] = center[2] + r*cos(theta)

    return r, points

def calcTrilinearWeights(x, y, z, size):
    ijk = [(), ]*8
    weight = [0, ]*8
    cnt = 0
    for i in [floor(x), ceil(x)]:
        for j in [floor(y), ceil(y)]:
            for k in [floor(z), ceil(z)]:
                ijk[cnt] = (k, i, j)
                if ((i < size[1]) & (j < size[2]) & (k < size[0])
                    & (i >= 0) & (j >= 0) & (k >= 0)):
                    weight[cnt] = (1 - abs(x-i))*(1 - abs(y-j))*(1 - abs(z-k))
                else:
                    weight[cnt] = 0
                cnt += 1

    return ijk, weight



image_path = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T00001\\T00001.tif"

image, size = readStackImage(image_path)
center = np.array([size[0]/2,size[1]/2,0])
r_max = np.amax(size)/2 + 2

n_points = 100
n_theta = 100
n_phi = 100

all_theta = (pi/n_theta)*np.arange(n_theta)
all_phi = (2*pi/n_phi)*np.arange(n_phi) - pi

r_of_maxval = np.zeros((n_theta, n_phi))
all_max_val = np.zeros((n_theta, n_phi))
# iterate over all the angles to get projection
cnt_theta = 0
for theta in all_theta:
    cnt_phi = 0
    for phi in all_phi:
        # calculate all the points coordinates
        r, points = rayPoints(center, theta, phi, r_max, n_points)
        # iterate over all the r to get maximum
        max_val = 0
        r_aux = 0
        for cnt_point in range(n_points):
            point = points[:,cnt_point]
            # calculate trilinear interpolation
            ijk, weights = calcTrilinearWeights(point[0], point[1], point[2], size)
            val = 0
            for index, weight in zip(ijk, weights):
                if weight > 0:
                    val += weight*image[index]
            # check if maximum
            if val > max_val:
                max_val = val
                r_aux = r[cnt_point]
            # add counter for r
            cnt_point += 1

        # write output
        if r_aux > 0:
            r_of_maxval[cnt_theta, cnt_phi] = r_aux
            all_max_val[cnt_theta, cnt_phi] = max_val

        # add counter for phi
        cnt_phi += 1

    # add counter for theta
    print(cnt_theta, np.amax(all_max_val[cnt_theta, :]), np.amax(r_of_maxval[cnt_theta, :]))
    cnt_theta += 1

pix_phi, pix_theta =  np.meshgrid(np.array(all_phi), np.array(all_theta))
ax = plt.subplot(2,1,1)
ax.contourf(pix_phi, pix_theta, all_max_val,
    zorder = 0, cmap = cm.Greys_r)
ax.invert_yaxis()
ax = plt.subplot(2,1,2)
ax.contourf(pix_phi, pix_theta, r_of_maxval,
    zorder = 0)
ax.invert_yaxis()
plt.show()






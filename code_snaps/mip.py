# Brute force calculation of MIP in spherical coordinates

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import re
import tifffile as tff
from math import *
import itertools
from timeit import default_timer as timer
from numbapro import cuda, jit, float32, uint16, int16
from track_util import readXMLAmat

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
                if ((i < size[1]) and (j < size[2]) and (k < size[0])
                    and (i >= 0) and (j >= 0) and (k >= 0)):
                    weight[cnt] = (1 - abs(x-i))*(1 - abs(y-j))*(1 - abs(z-k))
                else:
                    weight[cnt] = 0
                cnt += 1

    return ijk, weight

def calcRay(all_theta, all_phi, image, n_points, r_max, center, all_max_val, r_of_maxval):
    
    size = image.shape
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

            # write output
            if r_aux > 0:
                r_of_maxval[cnt_theta, cnt_phi] = r_aux
                all_max_val[cnt_theta, cnt_phi] = max_val

            # add counter for phi
            cnt_phi += 1

        # add counter for theta
        cnt_theta += 1

@cuda.jit(argtypes = [float32[:], float32[:], uint16[:,:,:], float32[:], float32[:], float32[:,:], float32[:,:]])
def calcRay_CUDA(all_theta, all_phi, image, r, center, all_max_val, r_of_maxval):

    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    bx = cuda.blockIdx.x
    by = cuda.blockIdx.y
    bw = cuda.blockDim.x
    bh = cuda.blockDim.y
    xim = tx + bx * bw
    yim = ty + by * bh

    xy_max = all_max_val.shape

    if (xim < xy_max[0]) and (yim < xy_max[0]):

        theta = all_theta[xim]
        phi = all_phi[yim]
        size = image.shape
        n_points = r.shape[0]

        max_val = 0
        r_aux = 0
        for cnt_point in range(n_points):
            x = center[0] + r[cnt_point]*sin(theta)*cos(phi)
            y = center[1] + r[cnt_point]*sin(theta)*sin(phi)
            z = center[2] + r[cnt_point]*cos(theta)
            val = 0
            for ii in range(2):
                i = int16(floor(x) if ii == 0 else ceil(x))
                w1 = x-i if x>i else i-x 
                for jj in range(2):
                    j = int16(floor(y) if jj == 0 else ceil(y))
                    w2 = y-j if y>j else j-y 
                    for kk in range(2):
                        k = int16(floor(z) if kk == 0 else ceil(z))
                        w3 = z-k if z>k else k-z
                        if ((i < size[1]) and (j < size[2]) and (k < size[0])
                          and (i >= 0) and (j >= 0) and (k >= 0)):
                            weight = (1 - w1)*(1 - w2)*(1 - w3)
                            val += weight*image[k,i,j]

            # check if maximum
            if val > max_val:
                max_val = val
                scale = 16
                r_aux = x*x + y*y + scale*scale*z*z

        # write output
        r_of_maxval[xim, yim] = r_aux
        all_max_val[xim, yim] = max_val            

# Read the image
image_path = "C:\\Users\\olimpio\\Documents\\data\\XY-point-5\\slices\\T00001\\T00001.tif"
image, size = readStackImage(image_path)

center = np.array([size[1]/2,size[2]/2,0], dtype = np.float32)
r_max = np.amax(size)/2 + 2

n_points = 50
n_theta = 50
n_phi = 50

r = float(r_max)/n_points*(np.arange(n_points) + 1)
r = r.astype(np.float32)

all_theta = (pi/n_theta)*np.arange(n_theta, dtype = np.float32)
all_phi = (2*pi/n_phi)*np.arange(n_phi, dtype = np.float32) - pi

dt = all_theta[1]
dp = all_phi[1]+pi
dr = r[0]

print(dr, dt, dp)
print(r_max*dt, r_max*dp)

r_of_maxval = np.zeros((n_theta, n_phi), dtype = np.float32)
all_max_val = np.zeros((n_theta, n_phi), dtype = np.float32)
all_max_valcomp = np.zeros((n_theta, n_phi), dtype = np.float32)
r_of_maxvalcomp = np.zeros((n_theta, n_phi), dtype = np.float32)

# s = timer()
# calcRay(all_theta, all_phi, image, n_points, r_max, center, all_max_valcomp, r_of_maxval)
# e = timer()
# print(e-s)

# pix_phi, pix_theta =  np.meshgrid(np.array(all_phi), np.array(all_theta))
# ax = plt.subplot(2,1,1)
# ax.contourf(pix_phi, pix_theta, all_max_valcomp,
#     zorder = 0, cmap = cm.Greys_r)
# ax.invert_yaxis()

# ax = plt.subplot(2,1,2)
# ax.contourf(pix_phi, pix_theta, r_of_maxvalcomp,
#     zorder = 0)
# ax.invert_yaxis()

nThreads = (16,16)
nBlocks = (ceil(n_theta/nThreads[0]), ceil(n_phi/nThreads[1]))
print(nBlocks)

date = "2015_6_22_15_33_43"
xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"

# CUDA call of the image
s = timer()
d_theta = cuda.to_device(all_theta)
d_phi = cuda.to_device(all_phi)
d_image = cuda.to_device(image)
d_r = cuda.to_device(r)
d_center = cuda.to_device(center)
d_max_val = cuda.device_array_like(all_max_val)
d_r_max = cuda.device_array_like(r_of_maxval)
calcRay_CUDA[nBlocks, nThreads](d_theta, d_phi, d_image, d_r, d_center, d_max_val, d_r_max)
d_max_val.copy_to_host(all_max_val)
d_r_max.copy_to_host(r_of_maxval)
e = timer()
print(e-s)

n_time = 10
pos = readXML(xml_path, n_time)

# Calculate the points coordinates
pos_arr = np.asarray(pos[0][0:3])
n_cells = pos_arr.shape[1]
angles = np.zeros((3,n_cells))
for cell in range(n_cells):
    point = pos_arr[:,cell] - center
    if point[0] > 0:
        angles[1,cell] = atan(point[1]/point[0])
    else:
        adj = -pi if point[1] < 0 else pi 
        angles[1,cell] = atan(point[1]/point[0]) + adj
    rho = sqrt(point[0]**2 + point[1]**2)
    angles[0,cell] = atan(rho/point[2])
    angles[2,cell] = sqrt(rho**2 + (16*point[2])**2)

pix_phi, pix_theta =  np.meshgrid(np.array(all_phi), np.array(all_theta))
ax = plt.subplot(2,1,1)
ax.contourf(pix_phi, pix_theta, all_max_val-all_max_valcomp,
    zorder = 0, cmap = cm.Greys_r)
ax.scatter(angles[1,:], angles[0,:], c = angles[2,:], zorder = 1)
ax.invert_yaxis()

ax = plt.subplot(2,1,2)
ax.contourf(pix_phi, pix_theta, np.sqrt(r_of_maxval), 
   zorder = 0)
ax.scatter(angles[1,:], angles[0,:], c = angles[2,:], zorder = 1)
ax.invert_yaxis()
plt.show()




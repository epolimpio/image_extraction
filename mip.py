# This contains the functions needed in order
# to perform the Maximum Intensity projection
# of the tiff image

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import re
import tifffile as tff
from math import *

def readStackImage(filename, sType = 'uint16'):
    with tff.TiffFile(filename) as tif:
        image = tif.asarray().astype(sType)
        size = image.shape
    
    return image, size

def calculate_max_projection(theta = 0, phi = 0):

    # Define the view matrix
    # We first rotate around y to get the theta rotation (for phi=0) - Ry
    # Then we rotate around the old z-axis (now with components in x and z) by phi - Rxz
    Ry = np.array([[cos(theta), 0, sin(theta), 0],
                [0, 1, 0, 0],
                [-sin(theta), 0, cos(theta), 0],
                [0, 0, 0, 1]])
    Rxz = np.array([[(sin(theta))**2 + cos(phi)*(cos(theta))**2, -cos(theta)*sin(phi), -sin(theta)*cos(theta)*(1-cos(phi)), 0],
                [cos(theta)*sin(phi), cos(phi), sin(theta)*sin(phi), 0],
                [-sin(theta)*cos(theta)*(1-cos(phi)), -sin(theta)*sin(phi), (cos(theta))**2 + cos(phi)*(sin(theta))**2, 0],
                [0, 0, 0, 1]])
    return np.dot(Ry, Rxz)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
vec = np.array([1,0,0,0])
dphi = pi/3
dtheta = pi/5

r = np.linalg.norm(vec)
theta = acos(vec[2]/r);
phi = acos(vec[0]/(r*sin(theta)))

theta = theta + dtheta
phi = phi + dphi

print(r*sin(theta)*cos(phi), r*sin(theta)*sin(phi), r*cos(theta))
out = calculate_max_projection(dtheta, dphi).dot(vec)
print(out)
# xs = out[0]
# ys = out[1]
# zs = out[2]
# ax.scatter(xs, ys, zs)
# ax.scatter(0, 0, 1)
# plt.show()


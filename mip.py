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

def rotateArbitraryAxis(vec, axis_vec, angle):
    # Rotate an arbitrary vector around an arbitrary axis

    L = np.linalg.norm(axis_vec)
    axis_vec = axis_vec/L

    cos_theta = cos(angle)
    sin_theta = sin(angle)
    u = axis_vec[0]
    v = axis_vec[1]
    w = axis_vec[2]

    R = np.array([[(u**2)*(1-cos_theta)+cos_theta, u*v*(1-cos_theta)-w*sin_theta, u*w*(1-cos_theta)+v*sin_theta],
                [u*v*(1-cos_theta)+w*sin_theta, (v**2)*(1-cos_theta)+cos_theta, v*w*(1-cos_theta)-u*sin_theta],
                [u*w*(1-cos_theta)-v*sin_theta, v*w*(1-cos_theta)+u*sin_theta, (w**2)*(1-cos_theta)+cos_theta]])

    return R.dot(vec)

def rotateSphericalAngles(vec, theta = 0, phi = 0):

    r = np.linalg.norm(vec)
    if r == 0:
        return vec
    vec = vec/r
    if np.array_equal(np.round(vec).astype('int'), np.array([0,0,1]).astype('int')):
        vec_out = np.array([sin(theta)*cos(phi), 
                sin(theta)*cos(theta), cos(theta)])
    else:
        vec_out = np.array([1,1,1])

    return vec_out

def viewMatrix(dtheta = 0, dphi = 0):

    u = sphericalRotation(np.array([1,0,0]), dtheta, dphi)
    v = sphericalRotation(np.array([0,1,0]), dtheta, dphi)
    w = sphericalRotation(np.array([0,0,1]), dtheta, dphi)

    view = np.zeros((4, 4))
    view[3,3] = 1
    view[0,0:3] = u
    view[1,0:3] = v
    view[2,0:3] = w

    return view

print(rotateSphericalAngles([0,1,0]))



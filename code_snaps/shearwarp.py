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

def viewMatrix(dtheta = 0, dphi = 0):
    # Determines the view matrix given the spherical coordinates

    if (dtheta == 0) & (dphi == 0):
        return np.identity(3)
    elif dtheta == 0:
        axis = np.array([0, 0, 1])
        angle = dphi
    else:
        axis = np.array([-sin(dphi), cos(dphi), 0])
        angle = dtheta

    u = rotateArbitraryAxis(np.array([1,0,0]), axis, angle)
    v = rotateArbitraryAxis(np.array([0,1,0]), axis, angle)
    w = rotateArbitraryAxis(np.array([0,0,1]), axis, angle)

    view = np.zeros((4, 4))
    view[3,3] = 1
    view[0,0:3] = u
    view[1,0:3] = v
    view[2,0:3] = w
 
    return view

def getProjMatrix(viewMatrix):
    # Determined the projection matrix to be closer to the principal axis
    # given a view matrix

    vx = viewMatrix[0,1]*viewMatrix[1,2] - viewMatrix[1,1]*viewMatrix[0,2]
    vy = viewMatrix[1,0]*viewMatrix[0,2] - viewMatrix[0,0]*viewMatrix[1,2]
    vz = viewMatrix[0,0]*viewMatrix[1,1] - viewMatrix[1,0]*viewMatrix[0,1]

    aux = np.identity(3)
    aux = np.roll(aux, 2-np.argmax(np.array([vx, vy, vz])), axis=0)

    proj = np.identity(4)
    proj[0:3,0:3] = aux

    return proj

def shearMatrix(viewMatrix, kmax):
    # Determine the sharp and warp matrices given an affine view matrix

    vx = viewMatrix[0,1]*viewMatrix[1,2] - viewMatrix[1,1]*viewMatrix[0,2]
    vy = viewMatrix[1,0]*viewMatrix[0,2] - viewMatrix[0,0]*viewMatrix[1,2]
    vz = viewMatrix[0,0]*viewMatrix[1,1] - viewMatrix[1,0]*viewMatrix[0,1]

    sx = -vx/vz
    sy = -vy/vz

    tx = -sx*kmax if sx < 0 else 0
    ty = -sy*kmax if sy < 0 else 0

    shear = np.identity(4)
    shear[0,2] = sx
    shear[0,3] = tx
    shear[1,2] = sy
    shear[1,3] = ty

    warp = np.identity(3)
    warp[0:2,0:2] = viewMatrix[0:2,0:2]
    warp[0,2] = viewMatrix[0,3]-tx*viewMatrix[0,0]-ty*viewMatrix[0,1]
    warp[1,2] = viewMatrix[1,3]-tx*viewMatrix[1,0]-ty*viewMatrix[1,1]

    return shear, warp
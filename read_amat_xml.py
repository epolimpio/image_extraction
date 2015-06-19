
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_amat_xml.py

# Written by: Eduardo Olimpio
# 18-6-2015 at AMOLF, Amsterdam

# --- Declarations --- #

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import re
import tifffile as tff
import lxml.etree as etree

date = "2015_6_19_6_2_52"
xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"

n_time = 10 # number of time frames

# def readBinFile(filename):
# 	with open(filename, "rb") as f:
#     byte = f.read(1)
#     while byte != "":
#         # Do stuff with byte.
#         byte = f.read(1)


for t in range(n_time):
    t_str = '{0:04d}'.format(t+1)
    xml_path_corr = re.sub('(\?+)', t_str, xml_path)
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
    print(len(all_points))

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z)
plt.show()
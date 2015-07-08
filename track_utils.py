# -*- coding: utf-8 -*-
# utils.py

# Written by: Eduardo Olimpio
# 6-7-2015 at AMOLF, Amsterdam

import numpy as np
import re
import tifffile as tff
import lxml.etree as etree
import struct
import os

def readConfigFile(path):
    
    f = open(path, 'r')
    out = {}
    for line in f.readlines():
        if not line in ['\n', '\r\n']:
            if not line[0] == '#':
                aux = line.rstrip('\n').split('=')
                if len(aux) == 2:
                    name = aux[0].strip()
                    value = aux[1].strip()
                    out[name] = value
    f.close()
    return out

def corrTIFPath(path, symbol, value):

    reg_expr_search = '(\%s+)'%str(symbol)
    length_of_replace = len(re.search(reg_expr_search, path).group(0))
    str_format = '{0:%sd}'%'{0:02d}'.format(length_of_replace)
    str_replace = str_format.format(int(value))

    return re.sub(reg_expr_search, str_replace, path)

def readTIFImage(filename):
    sType = 'uint16'
    with tff.TiffFile(filename) as tif:
        im_out = tif.asarray().astype(sType)

    return im_out

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def readXMLAmat(filename, n_time, symbol = '?'):

    # Number of parameters to be read. Today is 6:
    # 0,1,2 -> point coordinates
    # 3 -> SuperVoxel ID
    # 4 -> ID
    # 5 -> Parent
    n_param_read = 6
    pos = [[[],]*n_param_read,]*n_time 
    for t in range(n_time):
        xml_path_corr = corrTIFPath(filename, symbol, t+1)
        tree = etree.parse(xml_path_corr)
        root = tree.getroot()
        all_points = root.xpath('GaussianMixtureModel')
        x = [0.0,]*len(all_points)
        y = [0.0,]*len(all_points)
        z = [0.0,]*len(all_points)
        svID = [[],]*len(all_points)
        ID = [0,]*len(all_points)
        parent = [0,]*len(all_points)
        i = 0
        for point in all_points:
            [x[i], y[i], z[i]] = [float(x) for x in point.xpath('attribute::m')[0].split()]
            svID[i] = [int(x) for x in point.xpath('attribute::svIdx')[0].split()]
            ID[i] = [int(x) for x in point.xpath('attribute::id')[0].split()]
            parent[i] = [int(x) for x in point.xpath('attribute::parent')[0].split()]
            i += 1
        pos[t] = [x,y,z,svID,ID,parent]
    return pos

def readSuperVoxelFromFile(filename, t=0, imageDim = 3, symbol = '?'):
# Similar to functions the authors built in Matlab
    path_corr = corrTIFPath(filename, symbol, t+1)
    fid = open(path_corr, 'rb')
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

class TrackingAnalysis:

    def __init__(self, file_proxy, n_time, symbol = '?'):
        self.pos = readXMLAmat(file_proxy, n_time, symbol)

        # variable initialization
        self.t_appearance = []
        self.id_seq = []
        self._n_cell = 0
        self.division = []
        self._idseq_in_time = []

    def _imposeIDsWithMinFrame(self, min_frames):
        """For each time frame we include only the ids that
        satisfy the condition of lasting for at least min_frames"""

    def getPositions(self, frame, min_frames = -1):
        """Get the position of all the particles that have a
        sequence bigger or equal than min_frames"""
        
        if self._n_cell == 0:
            # if not yet run
            self.trackCells()

        pos_arr = np.asarray(self.pos[frame][0:3])

        if (min_frames == -1):   
            # get all the points
            x = pos_arr[0,:]
            y = pos_arr[1,:]
            z = pos_arr[2,:]
        else:
            # check which indexed cells satisfy condition




        return x,y,z

    def _addTrack(self, t, id_num, ids, indexes):
        # Add a new sequence
        self.id_seq.append([])
        self.id_seq[self._n_cell].append(id_num)

        # Include the time it was added
        self.t_appearance.append(t)

        # Insert it in control variables
        ids.append(id_num)
        indexes.append(self._n_cell)
        self._n_cell += 1

    def _addDivision(self, t, child2_id, parent_index, ids, indexes):
        # First get the data to save
        parent_id = self.id_seq[parent_index][-2]
        child1_id = self.id_seq[parent_index][-1]

        # Remove previously added id in parent sequence
        self.id_seq[parent_index] = self.id_seq[parent_index][:-1]

        # Remove parent from control lists
        del ids[ids.index(child1_id)]
        del indexes[indexes.index(parent_index)]

        # Add childs to new indexes
        self._addTrack(t, child1_id, ids, indexes)
        self._addTrack(t, child2_id, ids, indexes)

        # Add data to division variable
        self.division.append({'t': t, 'parent_id': parent_id, 
            'child1_id': child1_id, 'child2_id': child2_id})


    def trackCells(self):

        """ The nuclei are indexed as they appear, and by
        verifying the parenting we check if the cell continues
        to exist in each frame.

        The variable id_seq carries the id sequence followed by
        this cell. The variable t_appearance states the frame the
        nucleus appeared.

        For easieness, we store the last ID of each tracked cell
        in the variables last_id and last_id_index"""  
        
        # variable initialization
        self.t_appearance = []
        self.id_seq = []
        self._n_cell = 0
        self.division = []

        last_id = []
        last_id_index =[] 

        # Initialize points with first frame
        for id_num in self.pos[0][4]:
            self._addTrack(0, id_num[0], last_id, last_id_index)
        
        # From frame=1 on...
        for t, data_t in enumerate(self.pos[1:]):
            # clear aux variables from last frame
            ids = []
            indexes = []
            # check all the cells in this frame
            for cell, id_num in enumerate(data_t[4]):
                parent, = data_t[5][cell]
                if parent == -1:
                    # new track
                    self._addTrack(t+1, id_num[0], ids, indexes)
                elif parent in last_id:
                # check of parent is in the previous list
                    index = last_id_index[last_id.index(parent)]
                    if index in indexes:
                        # then we have cell division, and we monitor the child separarely
                        self._addDivision(t+1, id_num[0], index, ids, indexes)
                    else:
                        # cell continues in the same track
                        self.id_seq[index].append(id_num[0])
                        indexes.append(index)
                        ids.append(id_num[0])
                else:
                    # weird things happened!
                    print("Warning! Time %s, Cell ID %s lost track"%(str(t+1), str(id_num)))

            # save the variable for use in the next frame
            last_id = ids
            last_id_index = indexes

        return self.id_seq, self.t_appearance


# -*- coding: utf-8 -*-
# track_utils.py

# Written by: Eduardo Olimpio
# 6-7-2015 at AMOLF, Amsterdam

import numpy as np
import re
import tifffile as tff
import lxml.etree as etree
import struct
import os
from os.path import join

def readConfigFile(path):
    """
    Read the standardized configuration file of this
    application. See for example config_stacked_images.conf.
    The output is a dictionary with the name of the variables
    and the string value to each of them
    """
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
    """
    Correct the path replacing the symbols with the integer value.
    This value is padded by zeros according to the sequence of symbols.
    """ 
    reg_expr_search = '(\%s+)'%str(symbol)
    length_of_replace = len(re.search(reg_expr_search, path).group(0))
    str_format = '{0:%sd}'%'{0:02d}'.format(length_of_replace)
    str_replace = str_format.format(int(value))

    return re.sub(reg_expr_search, str_replace, path)

def readTIFImage(filename):
    """
    Read the usual TIF file from the confocal microscope.
    """ 
    sType = 'uint16'
    with tff.TiffFile(filename) as tif:
        im_out = tif.asarray().astype(sType)

    return im_out

def ensure_dir(f):
    """
    Check if directory where we want to write the file f
    exists, otherwise creates it.
    """
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def readManualTrackFile(filename):
    """
    Read XML file with all the manual tracks
    Returns a dictionary with all the data
    """
    out = {}

    if os.path.isfile(filename):
        tree = etree.parse(filename)
        root = tree.getroot()
        for element in root.iter('track'):
            id_ = int(element.attrib['id'])
            out[id_] = {}
            for point in element.iter('point'):
                time = int(point.attrib['time'])
                x = int(point.attrib['x'])
                y = int(point.attrib['y'])
                z = int(point.attrib['z'])

                out[id_][time] = [round(x),round(y),z]

    return out

def readXMLAmat(filename, time_ini, time_end, symbol = '?'):
    """
    Reads the XML generated by the tracking software described by
    Amat et al., Nature methods, 11, 2014.
    ---
    PARAMETERS

    filename: file pattern for each time frame, with 'symbol' in place
    of the frame number
    time_ini: number of the initial frame
    time_end: number of the final frame
    symbol: symbol used in the filename pattern

    OUTPUT

    pos: general indexed list, with the following data
        0,1,2 -> point coordinates
        3 -> SuperVoxel ID
        4 -> ID
        5 -> Parent
    """
    # Number of parameters to be read. Today is 6.
    n_param_read = 6
    pos = [[[],]*n_param_read,]*(time_end-time_ini+1)
    for t, time_path in enumerate(range(time_ini, time_end+1, 1)):
        xml_path_corr = corrTIFPath(filename, symbol, time_path)
        tree = etree.parse(xml_path_corr)
        root = tree.getroot()
        all_points = root.xpath('GaussianMixtureModel')
        x = []
        y = []
        z = []
        svID = []
        ID = []
        parent = []
        for point in all_points:
            # Needs try catch to avoid the errors in XML
            try:
                [x_aux, y_aux, z_aux] = [float(x) for x in point.xpath('attribute::m')[0].split()]
                x.append(x_aux)
                y.append(y_aux)
                z.append(z_aux)
                svID.append([int(a) for a in point.xpath('attribute::svIdx')[0].split()])
                ID.append(int(point.xpath('attribute::id')[0].strip()))
                parent.append(int(point.xpath('attribute::parent')[0].strip()))
            except:
                print('Point ID {p_id} in file {f_path} is corrupted'.format( 
                        f_path = xml_path_corr, p_id = int(point.xpath('attribute::id')[0].strip())))
                continue
        pos[t] = [x,y,z,svID,ID,parent]
    return pos

def readLogAmat(path):
    """
    Read the parameters of the tracking software
    """    
    # Open file
    f = open(path, 'r')
    # initialize variables
    out = {}
    lines = f.readlines()

    # Read input image path pattern
    out[TrackingAnalysis.IMAGE_PATH_KEY] = lines[4].split('=')[1][:-1] + '.tif'
    # Read Z-Anisotrpy of the image
    out[TrackingAnalysis.ANISOTROPY_KEY] = float(lines[20].split('=')[1][:-1])
    times = lines[1].strip().split()
    out[TrackingAnalysis.TIME_INI_KEY] = int(times[-2])
    out[TrackingAnalysis.TIME_END_KEY] = int(times[-1])

    # close file
    f.close()

    return out

def readSuperVoxelFromFile(filename, imageDim = 3):
    """
    Reads the supervoxels binary files generated by the tracking software 
    described by Amat et al., Nature methods, 11, 2014.
    """
    # Similar to functions the authors built in Matlab
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

def calcPixelsAddress(svIDList, pixIDList, dimX, dimY):
    """
    Calculate the pixels addresses of the supervoxels
    This is only done for the supervoxels in svIdList
    """
    ini = True
    for svIDs in svIDList:
        for svID in svIDs:
            pixIDs = pixIDList[svID]
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

    if ini:
        return None
    else:
        return pixPoints

def calcAllPixelsAddress(pixIDList, dimX, dimY):
    """
    Calculate the pixels addresses of all the supervoxels
    """
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

class TrackingAnalysis(object):
    """
    This class reads the results from the tracking software and
    offer a myriad of functions to extract the data and filter
    the points.
    ---
    PARAMETERS

    folder: folder with the results to analyse
    background_detector (optional): boolean if to use the detector
    """
    # Filter constants
    MIN_FRAMES_KEY = 'MIN_FRAMES'
    BLACK_LIST_KEY = 'BLACK_LIST'

    # Amat log file constants
    IMAGE_PATH_KEY = 'IMAGE_PATH'
    ANISOTROPY_KEY = 'ANISOTROPY'
    TIME_INI_KEY = 'TIME_INI'
    TIME_END_KEY = 'TIME_END'
    LOG_PATH_KEY = 'LOG_PATH'
    XML_PATH_KEY = 'XML_PATH'
    BINATY_PATH_KEY = 'BINATY_PATH'

    def __init__(self, folder, background_detector = True):
        """
        Constructor
        """
        # Folders
        self.folder = folder.strip('\\')
        log_path = self.getLogPath(folder)
        mtrack_filename = join(join(self.folder,'manual_track_config'),'manual_track.xml')
        if background_detector:
            xml_path = join(join(self.folder,'XML_finalResult_lht_bckgRm'),'GMEMfinalResult_frame????.xml')
        else:
            xml_path = join(join(self.folder,'XML_finalResult_lht'),'GMEMfinalResult_frame????.xml')

        # Configurations of the run
        self.configs = readLogAmat(log_path)
        self.configs[self.XML_PATH_KEY] = xml_path
        self.configs[self.LOG_PATH_KEY] = log_path
        self.configs[self.BINATY_PATH_KEY] = join(join(self.folder,'XML_finalResult_lht'),'GMEMfinalResult_frame????.svb')
        time_ini = self.configs[self.TIME_INI_KEY]
        time_end = self.configs[self.TIME_END_KEY]
        self.n_frames = time_end - time_ini + 1
        self.pos = readXMLAmat(xml_path, time_ini, time_end, symbol = '?')

        self.manual_tracks = readManualTrackFile(mtrack_filename)

        # variable empty initialization
        self.index_filter = []
        self._filter_config = {}

        # track the cells
        self.trackCells()

    def getLogPath(self, folder):
        """ 
        Get the path of the log file inside the results folder
        """
        path = join(self.folder,'experimentLog_0001.txt')
        for f_path in os.listdir(folder):
            if re.search('experimentLog_[0-9]*.txt', f_path):
                path = join(self.folder,f_path)
                break

        return path

    def readInputImage(self, frame, symbol = '?'):
        """
        Wrap the functions to read the input image file
        """
        time_ini = self.configs[self.TIME_INI_KEY] 
        t = time_ini + frame
        image_path = corrTIFPath(self.configs[self.IMAGE_PATH_KEY], symbol, t)

        return readTIFImage(image_path)

    def readSVFile(self, frame, symbol = '?'):
        """
        Wrap the functions to read the supervoxel file
        """
        time_ini = self.configs[self.TIME_INI_KEY] 
        t = time_ini + frame
        binary_path = corrTIFPath(self.configs[self.BINATY_PATH_KEY], symbol, t)

        return readSuperVoxelFromFile(binary_path)

    def printTrackData(self, path, filtered=True):
        """ 
        Write a text file with all the track numbers, the frame it starts
        and how long it lasts
        """

        f = open(path, 'w')
        for i, t in enumerate(self.t_appearance):
            if not filtered:
                f.write('{id}\t{time}\t{length}\n'.format(id = i, time = t, length=len(self.id_seq[i])))
            else:
                if i in self.index_filter:
                    f.write('{id}\t{time}\t{length}\n'.format(id = i, time = t, length=len(self.id_seq[i])))

        f.close()
        return True

    def minFrameFilter(self, min_frames, keep_previous = True):
        """
        For each time frame we include only the ids that
        satisfy the condition of lasting for at least min_frames
        """

        # In case of no filter give warning and stop
        if not self.index_filter:
            print("WARNING! Cells not tracked or all cells filtered. No min_frames condition applied.")
            return None

        if not keep_previous:
        # reset variables if not keeping the old values
            self.index_filter = list(range(len(self.id_seq)))
            self._filter_config = {}
        else:
        # check whether this was still done
            if self.MIN_FRAMES_KEY in self._filter_config:
                # if less restrictive condition, do nothing
                if self._filter_config[self.MIN_FRAMES_KEY] <= min_frames:
                    return self.index_filter 
                    
        # check conditions
        did_not_pass = []
        for idx, id_seq in enumerate(self.id_seq):
            if len(id_seq) < min_frames:
                did_not_pass.append(idx)

        # Apply changes
        self.index_filter = list(set(self.index_filter) - set(did_not_pass))

        # save filter configuration
        self._filter_config[self.MIN_FRAMES_KEY] = min_frames


        if not self.index_filter:
            print("WARNING! ALL CELLS FILTERED, consider changing the parameter min_frames")
        else:
            print("%d tracks from a total of %d met the min_frames condition"%(len(self.index_filter), len(self.id_seq)))

        return self.index_filter

    def blackListFilter(self, black_list, keep_previous = True):
        """
        Remove the black list of track indexes from the filtered indexes
        """
        
        # In case of no filter give warning and stop
        if not self.index_filter:
            print("WARNING! Cells not tracked or all cells filtered. No black list applied.")
            return None

        if keep_previous:
            # if already filtered by black_list, merge both lists
            if self.BLACK_LIST_KEY in self._filter_config:
                print("WARNING! This was already filtered for black_list and the results will be combined.")
                black_list = list(set(self._filter_config[self.BLACK_LIST_KEY].append(black_list)))
        else:
            # reinitialize self.index_filter
            self.index_filter = list(range(len(self.id_seq)))
            self._filter_config = {}

        # Apply changes
        self.index_filter = list(set(self.index_filter) - set(black_list))

        # save filter configuration
        self._filter_config[self.BLACK_LIST_KEY] = black_list

        return self.index_filter

    def getIDsInTime(self, filtered = True):
        """
        Get a list, in time, of lists of the IDs (in the XML) of the cells
        that met the filter conditions imposed by the filters
        """

        n_time = len(self.pos)
        output = [[],]*n_time
        for t in range(n_time):
            if (not filtered) or (not self._filter_config):
                # get all ids in time
                output[t] = self.pos[t][4]
            else:
                for idx, id_seq in enumerate(self.id_seq):
                    # check if the track passed the filter
                    if idx in self.index_filter:
                        # now check if there is a track for this time
                        id_ = self.Track2ID(idx, t)
                        if id_:
                            output[t].append(id_)

        return output

    def getIDsInFrame(self, frame, filtered = True):
        """ 
        Get a list of the IDs (ID in the XML) of the cells in the frame
        that meet the filter conditions imposed by the filters
        """

        if (not filtered) or (not self._filter_config):
             # get all ids in frame
            output = self.pos[frame][4]
        else:
            output = []
            for idx, id_seq in enumerate(self.id_seq):
                # check if the track passed the filter
                if idx in self.index_filter:
                    # now check if there is a track for this time
                    id_ = self.Track2ID(idx, frame)
                    if id_:
                        output.append(id_)

        return output

    def getSvIDsInFrame(self, frame, filtered = True):
        """ 
        Get a list of the supervoxel IDs of the cells in the frame
        that meet the filter conditions imposed by the filters
        """
        ids = self.getIDsInFrame(frame, filtered)
        if (not filtered) or (not self._filter_config):
            svIDs = self.pos[frame][3]
        else:
            svIDs = [[],]*len(ids)
            for i, id_num in enumerate(ids):
                idx = self.pos[frame][4].index(id_num)
                svIDs[i] = self.pos[frame][3][idx]

        return ids, svIDs

    def getAllPositions(self, frame, filtered = True):
        """
        Get the position of all the particles that have a
        sequence bigger or equal than min_frames

        ---
        PARAMETERS

        frame: Frame for which we want to get the positions
        min_frames: Minimum number of frames that the track lasts
        to be considered OK. Any negative number means no filter.
        black_list: Indexes that cannot be included in the positions.
        keep_previous: If previously applied filters will remain

        OUTPUT

        x,y,z: coordinates of all the points in frame 
        """

        # get all positions in a numpy array
        pos_arr = np.asarray(self.pos[frame][0:3])

        if (not filtered) or (not self._filter_config):   
            # get all the points
            x = pos_arr[0,:]
            y = pos_arr[1,:]
            z = pos_arr[2,:]
        else:

            # get all the ids in a numpy array
            ids = np.asarray(self.pos[frame][4])

            # now get only the IDs we want (mask of boolean in numpy)
            ok_ids = np.asarray(self.getIDsInFrame(frame))
            to_include = np.in1d(ids, ok_ids)

            # finally only the positions we want
            x = pos_arr[0,to_include]
            y = pos_arr[1,to_include]
            z = pos_arr[2,to_include]

        return x,y,z

    def getCenterOfMass(self, filtered = True):
        """ 
        Get the center of mass coordinates of the points
        in time. The output is [x, y, z] with x,y,z the
        size of the time
        """
        n_time = len(self.pos)
        x_mean = [0.0,]*n_time
        y_mean = [0.0,]*n_time
        z_mean = [0.0,]*n_time      
        for frame in range(n_time):
            # get all the positions of the filtered points
            x,y,z = self.getAllPositions(frame, filtered)
            x_mean[frame] = np.asarray(x).mean() if len(x) > 0 else None
            y_mean[frame] = np.asarray(y).mean() if len(y) > 0 else None
            z_mean[frame] = np.asarray(z).mean() if len(z) > 0 else None

        return x_mean, y_mean, z_mean

    def getWholeMovement(self, track_index):
        """
        Get all the positions in time of a track denominated
        by the value track_index
        """
        if self._n_cell == 0:
        # if not yet run
            self.trackCells()

        if track_index < len(self.id_seq):
            # initialize variables
            t_ini = self.t_appearance[track_index]
            id_seq = self.id_seq[track_index]
            seq_len = len(id_seq)
            t = [0,]*seq_len
            x = [0.0,]*seq_len
            y = [0.0,]*seq_len
            z = [0.0,]*seq_len

            for dt, id_ in enumerate(id_seq):
                time = t_ini+dt
                t[dt] = time
                all_ids = self.pos[time][4]
                idx = all_ids.index(id_)
                x[dt] = self.pos[time][0][idx]
                y[dt] = self.pos[time][1][idx]
                z[dt] = self.pos[time][2][idx]

        else:
            print("Required track does not exist.")
            return None

        return t, x, y, z

    def ID2Track(self, id_num, frame):
        """
        Return the number of the track ID
        given the ID of the particle and the time frame
        """
        if id_num in self.dict_track[frame]:
            return self.dict_track[frame][id_num]

        return None

    def Track2ID(self, track, frame):
        """
        Return the ID of the particle
        given the track ID and the time frame
        """
        t_ini = self.t_appearance[track]
        id_seq = self.id_seq[track]
        if (frame >= t_ini) and (frame < len(id_seq) + t_ini):
            return id_seq[frame-t_ini]

        return None

    def _addTrack(self, t, id_num):
        """
        Add new track to data
        """
        # Add a new sequence
        self.id_seq.append([])
        self.id_seq[self._n_cell].append(id_num)

        # Include the time it was added
        self.t_appearance.append(t)

        # Insert it in control variables
        self.dict_track[t][id_num] = self._n_cell
        self._n_cell += 1

    def _addDivision(self, t, child2_id, parent_index):
        """
        Add new division
        """
        # First get the data to save
        parent_id = self.id_seq[parent_index][-2]
        child1_id = self.id_seq[parent_index][-1]

        # Remove previously added id in parent sequence
        self.id_seq[parent_index] = self.id_seq[parent_index][:-1]

        # Remove parent from control lists
        del self.dict_track[t][child1_id]

        # Add childs to new indexes
        self._addTrack(t, child1_id)
        self._addTrack(t, child2_id)

        # Add data to division variable
        self.division.append({'t': t, 'parent_id': parent_id, 
            'child1_id': child1_id, 'child2_id': child2_id})


    def trackCells(self):
        """
        The nuclei are indexed as they appear, and by
        verifying the parenting we check if the cell continues
        to exist in each frame.

        The variable id_seq carries the id sequence followed by
        this cell. The variable t_appearance states the frame the
        nucleus appeared.

        For easieness, we store the last ID of each tracked cell
        in the variables last_id and last_id_index
        """        
        # variable initialization
        self.t_appearance = []
        self.id_seq = []
        self._n_cell = 0
        self.division = []
        self.dict_track = {}

        t_ini = self.configs[self.TIME_INI_KEY]

        # Initialize points with first frame
        self.dict_track[0] = {}
        for id_num in self.pos[0][4]:
            self._addTrack(0, id_num)

        # From frame=1 on...
        for t, data_t in enumerate(self.pos[1:]):
            self.dict_track[t+1] = {}
            # check all the cells in this frame
            for cell, id_num in enumerate(data_t[4]):
                parent = data_t[5][cell]
                if parent == -1:
                    # new track
                    self._addTrack(t+1, id_num)
                elif parent in self.dict_track[t]:
                    # check if parent is in the previous list
                    index = self.dict_track[t][parent]
                    if index in self.dict_track[t+1].values():
                        # then we have cell division, and we monitor the child separarely
                        self._addDivision(t+1, id_num, index)
                    else:
                        # cell continues in the same track
                        self.id_seq[index].append(id_num)
                        self.dict_track[t+1][id_num] = index
                else:
                    # weird things happened!
                    print("Warning! Time %s, Cell ID %s lost track"%(str(t+t_ini), str(id_num)))


        # all track indexes are included, no filter (yet)
        self.index_filter = list(range(len(self.id_seq)))

        return self.id_seq, self.t_appearance
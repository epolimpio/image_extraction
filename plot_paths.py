import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from mpl_toolkits.mplot3d import Axes3D
import re
from math import *
from track_utils import TrackingAnalysis
from os.path import join

def get_cmap(N):
    '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct 
    RGB color.'''
    color_norm  = colors.Normalize(vmin=0, vmax=N-1)
    scalar_map = cm.ScalarMappable(norm=color_norm, cmap='hsv') 
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color

def plotTracks3D(track, frame_ini, frame_end):

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    anisotropy = track.configs[track.ANISOTROPY_KEY]

    for track_index in track.index_filter:
        # mov is an array (4, time), where 4 is:
        # 0 -> frame, 1-3 -> x,y,z
        mov = np.asarray(track.getWholeMovement(track_index))
        to_include = np.logical_and(
                     np.greater_equal(mov[0,:], frame_ini),
                     np.less_equal(mov[0,:], frame_end))
        if to_include.sum() > 0:
            ax.plot(mov[1, to_include], mov[2, to_include], mov[3, to_include])

    plt.show()

def plotManualTracks(track, frame_ini, frame_end):

    # set up figure
    fig = plt.figure()

    t_ini = track.configs[track.TIME_INI_KEY]
    anisotropy = track.configs[track.ANISOTROPY_KEY]

    cartesian = True
    annotate = False
    center_of_mass = np.asarray(track.getCenterOfMass())
    frames = np.arange(center_of_mass.shape[1])
    c_map = get_cmap(len(track.manual_tracks))

    if not cartesian:
        ax = fig.add_subplot(111, projection='3d')
    else:
        ax = fig.add_subplot(111)

    for cnt, track_index in enumerate(track.manual_tracks):
        mov = np.zeros((4,len(track.manual_tracks[track_index])))
        for i, t in enumerate(sorted(track.manual_tracks[track_index])):
            mov[0,i] = t - t_ini
            mov[1:4,i] = track.manual_tracks[track_index][t]

        to_include = np.logical_and(
                     np.greater_equal(mov[0,:], frame_ini),
                     np.less_equal(mov[0,:], frame_end))
        
        if to_include.sum() > 0:
            if not cartesian:
                ax.plot(mov[1, to_include], mov[2, to_include], anisotropy*mov[3, to_include])
            else:
                n_points = to_include.sum()
                # get the center of mass for the desired time frames
                com = center_of_mass[:, np.in1d(frames,mov[0,:])]

                # subtract the center of mass
                coord_com = mov[1:4, :] - com

                # it needs to be float32 for arctan to work
                coord_com = coord_com[:,to_include].astype(np.float32)

                # convert coordinates to cartesian projection
                angles = np.zeros((2,n_points))
             
                # use arctan2 to make arctan in the range we want [-pi, pi]
                angles[0,:] = np.arctan2(coord_com[1,:],coord_com[0,:])

                # azimuthal angle is between [-pi/2, pi/2]
                rho = np.sqrt(coord_com[0,:]**2 + coord_com[1,:]**2)
                angles[1,:] = np.arctan(coord_com[2,:]/rho)

                breaks = []
                # if the particle cross the graph boundaries, break in two lines
                for i in range(1, n_points, 1):
                    if abs(angles[0,i]-angles[0,i-1]) > pi:
                        breaks.append(i)
                    elif abs(angles[1,i]-angles[1,i-1]) > pi/2:
                        breaks.append(i)

                color = c_map(cnt)
                if not breaks:
                    # plot normally
                    ax.plot(angles[0,:], angles[1,:], c = color)
                else:
                    aux = 0
                    # plot breaking
                    for break_point in breaks:
                        ax.plot(angles[0,aux:break_point], angles[1,aux:break_point], c = color)
                        aux = break_point
                    # plot last
                    ax.plot(angles[0,aux:], angles[1,aux:], c = color)
                
                if annotate:
                    ax.annotate(str(track_index), xy=(angles[0,-1], angles[1,-1]), color = color)

    plt.show()


def plotTracksCartesian(track, frame_ini, frame_end, annotate = False):

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111)

    center_of_mass = np.asarray(track.getCenterOfMass())
    frames = np.arange(center_of_mass.shape[1])
    c_map = get_cmap(len(track.index_filter))
    
    for cnt, track_index in enumerate(track.index_filter):
        # mov is an array (4, time), where 4 is:
        # 0 -> frame, 1-3 -> x,y,z
        mov = np.asarray(track.getWholeMovement(track_index))
        
        # to get only the frames of interest
        to_include = np.logical_and(
                     np.greater_equal(mov[0,:], frame_ini),
                     np.less_equal(mov[0,:], frame_end))

        n_points = to_include.sum()
        if n_points > 0:
            # get the center of mass for the desired time frames
            com = center_of_mass[:, np.in1d(frames,mov[0,:])]

            # subtract the center of mass
            coord_com = mov[1:4, :] - com

            # it needs to be float32 for arctan to work
            coord_com = coord_com[:,to_include].astype(np.float32)

            # convert coordinates to cartesian projection
            angles = np.zeros((2,n_points))
         
            # use arctan2 to make arctan in the range we want [-pi, pi]
            angles[0,:] = np.arctan2(coord_com[1,:],coord_com[0,:])

            # azimuthal angle is between [-pi/2, pi/2]
            rho = np.sqrt(coord_com[0,:]**2 + coord_com[1,:]**2)
            angles[1,:] = np.arctan(coord_com[2,:]/rho)

            breaks = []
            # if the particle cross the graph boundaries, break in two lines
            for i in range(1, n_points, 1):
                if abs(angles[0,i]-angles[0,i-1]) > pi:
                    breaks.append(i)
                elif abs(angles[1,i]-angles[1,i-1]) > pi/2:
                    breaks.append(i)

            color = c_map(cnt)
            if not breaks:
                # plot normally
                ax.plot(angles[0,:], angles[1,:], c = color)
            else:
                aux = 0
                # plot breaking
                for break_point in breaks:
                    ax.plot(angles[0,aux:break_point], angles[1,aux:break_point], c = color)
                    aux = break_point
                # plot last
                ax.plot(angles[0,aux:], angles[1,aux:], c = color)
            
            if annotate:
                ax.annotate(str(track_index), xy=(angles[0,-1], angles[1,-1]), color = color)

    plt.show()    

def main(*args):

    date = "2015_6_22_15_33_43"
    frame_ini = 1
    frame_end = 20
    back = True
    if len(args) == 3:
        frame_ini = int(args[0])
        frame_end = int(args[1])
        date = str(args[2])
    elif len(args) > 3:
        if (args[3].lower() == 'false') or (str(args[3]) == '0'):
            back = False
    else:
        print('Provide the arguments for the function')
        print('Call must be: py plot_all_path_3d.py <frame_ini> <frame_end> <results_date>')
        return None

    # Define filenames
    ini_config = readConfigFile(join('ini_files', 'ini_config.ini'))
    results_folder = ini_config['results_folder']
    folder =  join(results_folder,"GMEMtracking3D_" + date)

    # read positions and apply filter
    track = TrackingAnalysis(folder)
    track.minFrameFilter(10)

    plotManualTracks(track, frame_ini, frame_end)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
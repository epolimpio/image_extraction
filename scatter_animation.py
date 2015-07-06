import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import re
from math import *
from read_amat_xml import readXML

def update_scatter(num, pos, points):
    print('frame->'+str(num))
    pos_arr = np.asarray(pos[num+1][0:3])
    points._offsets3d = (pos_arr[0,:], pos_arr[1,:],1.58*pos_arr[2,:])
    return points

def main(*args):

    n_time = 20
    date = "2015_6_22_15_33_43"
    if len(args) >= 2:
        n_time = int(args[0])
        date = str(args[1])

    # Define filenames
    xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"

    # read positions from XML
    pos = readXML(xml_path, n_time)
    pos_arr = np.asarray(pos[0][0:3])

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    points = ax.scatter(pos_arr[0,:], pos_arr[1,:], 1.58*pos_arr[2,:], animated=True)

    ani = animation.FuncAnimation(fig, update_scatter, frames=n_time-1, fargs = (pos, points),
                              interval=20, blit=False)

    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
        comment='Movie support!')
    writer = FFMpegWriter(fps=15, metadata=metadata)
    ani.save('basic_animation.mp4', fps=30, writer=writer)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
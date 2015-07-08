import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import re
from math import *
from track_utils import TrackingAnalysis

def update_scatter(num, track, points):
    print('frame->'+str(num))
    x, y, z = track.getPositions(num+1)
    points._offsets3d = (x, y, z)
    return points

def main(*args):

    n_time = 20
    date = "2015_7_8_8_12_50"
    if len(args) >= 2:
        n_time = int(args[0])
        date = str(args[1])

    # Define filenames
    xml_path = "D:\\image_software\\results\\GMEMtracking3D_"+date+"\\XML_finalResult_lht_bckgRm\\GMEMfinalResult_frame????.xml"

    # read positions
    track = TrackingAnalysis(xml_path, n_time)
    x, y, z = track.getPositions(0)

    f = open('test_data.dat', 'w+')
    track.trackCells()
    for i, id_seq in enumerate(track.id_seq):
        f.write('%d %d %d \n'%(i, track.t_appearance[i], len(id_seq)))
    f.write('\nDivisions:\n')
    for division in track.division:
        f.write('%d %d \n'%(division['t'], division['parent_id']))
    f.close

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    points = ax.scatter(x, y, z, animated=True)

    ani = animation.FuncAnimation(fig, update_scatter, frames=n_time-1, fargs = (track, points),
                              interval=20, blit=False)

    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
        comment='Movie support!')
    writer = FFMpegWriter(fps=5, metadata=metadata)
    ani.save('basic_animation.mp4', writer=writer)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
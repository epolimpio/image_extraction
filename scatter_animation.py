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

def update_scatter(num, track, points, line, frame_ini, mov):
    print('frame->'+str(num))
    x, y, z = track.getAllPositions(num+frame_ini+1, filtered = False)
    points._offsets3d = (x, y, z)

    line.set_data(mov[1, :num], mov[2, :num])
    line.set_3d_properties(mov[3,:num])

    return points, line

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

    min_frames = 5

    # Define filenames
    folder = "D:\\image_software\\results\\GMEMtracking3D_"+date

    # read positions and apply filter
    track = TrackingAnalysis(folder)
    track.minFrameFilter(min_frames)

    x, y, z = track.getAllPositions(frame_ini, filtered = False)
    
    # mov is an array (4, time), where 4 is:
    # 0 -> frame, 1-3 -> x,y,z
    mov = np.asarray(track.getWholeMovement(track.index_filter[0]))

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    points = ax.scatter(x, y, z, animated=True)
    line, = ax.plot(mov[1, 0:1], mov[2, 0:1], mov[3, 0:1])
    ani = animation.FuncAnimation(fig, update_scatter, frames=frame_end-frame_ini, fargs = (track, points, line, frame_ini, mov),
                              interval=20, blit=False)

    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
        comment='Moving cells')
    writer = FFMpegWriter(fps=5, metadata=metadata)
    ani.save('basic_animation.mp4', writer=writer)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
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

def update_scatter(num, track, points, line, min_frames, mov):
    print('frame->'+str(num))
    x, y, z = track.getAllPositions(num+1, filtered = False)
    points._offsets3d = (x, y, z)

    line.set_data(mov[1, :num], mov[2, :num])
    line.set_3d_properties(mov[3,:num])

    return points, line

def main(*args):

    n_time = 20
    date = "2015_7_8_8_12_50"
    if len(args) >= 2:
        n_time = int(args[0])
        date = str(args[1])

    min_frames = 10

    # Define filenames
    folder = "D:\\image_software\\results\\GMEMtracking3D_"+date

    # read positions and apply filter
    track = TrackingAnalysis(folder)
    track.minFrameFilter(min_frames)

    x, y, z = track.getAllPositions(0, filtered = False)

    mov = np.asarray(track.getWholeMoviment(45))
    print(mov.shape)

    # set up figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    points = ax.scatter(x, y, z, animated=True)
    line, = ax.plot(mov[1, 0:1], mov[2, 0:1], mov[3, 0:1])
    ani = animation.FuncAnimation(fig, update_scatter, frames=n_time-1, fargs = (track, points, line, min_frames, mov),
                              interval=20, blit=False)

    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Movie Test', artist='Matplotlib',
        comment='Movie support!')
    writer = FFMpegWriter(fps=5, metadata=metadata)
    ani.save('basic_animation.mp4', writer=writer)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
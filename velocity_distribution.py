import numpy as np
import matplotlib.pyplot as plt
from track_utils import TrackingAnalysis, readConfigFile
from os.path import join

def main(*args):
    """
    Main function to run from outside
    """

    n_frameslst = [31, 40, 25]
    dtlst = [2.0/3, 0.5, 0.5]  # time between frames in hours
    dxlst = [0.67, 0.67, 0.67]  # XY resolution in microns
    dzlst = [10, 1, 1]       # Z resolution in microns

    datelst = ['2015_8_26_15_56_12','2015_8_27_10_8_37', '2015_8_27_10_28_52']
    labels = ['Uninfected', 'Infected\nnon-rotating', 'Infected\nrotating']

    fig_av_speed = plt.figure(1)
    ax_av_speed = fig_av_speed.add_subplot(1,1,1)

    fig_res_speed = plt.figure(2)
    ax_res_speed = fig_res_speed.add_subplot(1,1,1)

    boxes_av_speed = []
    boxes_res_speed = []

    for i, date in enumerate(datelst):

        n_frames = n_frameslst[i]
        dt = dtlst[i]
        dx = dxlst[i]
        dz = dzlst[i]

        ini_config = readConfigFile(join('ini_files', 'ini_config.ini'))
        results_folder = ini_config['results_folder']
        folder =  join(results_folder,"GMEMtracking3D_" + date)

        filename = 'ini_files/track_ids_{0}.ini'.format(date)
        f = open(filename, 'r')
        track_ids = [int(x) for x in f.readlines()]
        f.close()

        track = TrackingAnalysis(folder)
        N = len(track_ids)

        vx = np.zeros((N, n_frames-1))
        vy = np.zeros((N, n_frames-1))
        vz = np.zeros((N, n_frames-1))

        for cell,track_id in enumerate(track_ids):

            data = np.array(track.getWholeMovement(track_id))

            if date == '2015_8_27_10_28_52':
                test = np.logical_and(
                    np.greater_equal(data[0,:], 4),
                    np.less(data[0,:], 4 + n_frames)
                    )
                data = data[:,test]
                print(data.shape    )

            vx[cell,:] = dx*(data[1,1:n_frames] - data[1,0:n_frames-1])/dt
            vy[cell,:] = dx*(data[2,1:n_frames] - data[2,0:n_frames-1])/dt
            vz[cell,:] = dz*(data[3,1:n_frames] - data[3,0:n_frames-1])/dt

        v = np.sqrt(vx**2+vy**2+vz**2)
        res_v = np.sqrt(np.sum(vx,0)**2 + np.sum(vy,0)**2 + np.sum(vz,0)**2)/N

        boxes_av_speed.append(v.reshape(-1))
        boxes_res_speed.append(res_v.reshape(-1))

    
    ax_av_speed.boxplot(boxes_av_speed, showfliers=False, labels=labels)
    ax_res_speed.boxplot(boxes_res_speed, showfliers=False, labels=labels)
    plt.show()

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

from track_utils import *

def main(*args):

    if len(args) >= 1:
        date = str(args[0])
    else:
        print('Provide the arguments for the function')
        print('Call must be: py print_all_tracks.py <results_date>')
        return None
    
    min_frames = 0
    if len(args) > 1:
    	min_frames = int(args[1])

    folder = "D:\\image_software\\results\\GMEMtracking3D_"+date
    filepath = folder + "\\tracks.txt"

    track = TrackingAnalysis(folder)
    if min_frames > 0:
    	track.minFrameFilter(min_frames, keep_previous = False)

    # Write the file
    track.printTrackData(filepath, filtered = True)

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
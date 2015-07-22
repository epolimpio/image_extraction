#!/usr/bin/env python
import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
from track_utils import corrTIFPath, TrackingAnalysis, ensure_dir
import os.path

class ManualTrackWindow(object):

    def __init__(self, parent, track, image_path_pattern):
        """
        Constructor
        """
        # initialize class variables
        self.z = 1
        self.t = track.configs[track.TIME_INI_KEY]
        self.track_num = -1
        self.track = track
        self.path = image_path_pattern
        self.parent = parent
        self.parent.title("Manual Track")
        self.__track_mov = np.array([])

        # set up the main canvas
        self.__initImageCanvas()
        # initialize all interface widgets
        self.__initInterfaceWidgets()
        # place widgets in the window
        self.__placeWidgets()


    def __initImageCanvas(self):
        """
        Set up the initial Canvas that handles the eye check images.
        It also initializes all the required binds for events in the image.
        """
        # open the first eye check image to set up the canvas
        path_aux = corrTIFPath(corrTIFPath(self.path,'?',self.t), '@', self.z)
        image = Image.open(path_aux)

        # get image size
        width, height = image.size

        # set up canvas
        self.canvas = tk.Canvas(self.parent, width=width, height=height)

        self.canvas.focus() # initialize with canvas selected
        self.canvas.focus_set() # to get keyboard events

        # bind of arrow events
        self.canvas.bind("<Up>", self.arrowEvent)
        self.canvas.bind("<Down>", self.arrowEvent)
        self.canvas.bind("<Right>", self.arrowEvent)
        self.canvas.bind("<Left>", self.arrowEvent)

        # bind of mouse events
        self.canvas.bind("<Button-1>", self.focusOnCanvas)

        # set up first image
        self.img = ImageTk.PhotoImage(image)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor = 'nw', image = self.img)

        # set up calibration elements on canvas (3 points) and related coordinates
        self.calibration_draws = {}
        self.calibration_coords = {}
        self.calibration_image_coord = {}
        if self.readCalibrationFile():
            for point in self.calibration_coords:
                [x,y] = self.calibration_coords[point]
                self.calibration_draws[point] = self.drawCalibrationMark(x,y, 'P{num}'.format(num=point+1))
            self.__hideCalibrationMarks()

    def __initInterfaceWidgets(self):
        """
        Set up the rest of the interface widgets
        besides the image.
        """
        self.to_disable = [] # contains the list of all the elements disabled when waiting for action
        
        # First initialize all the widgets
        # Entries for time, stack and track number
        self.track_str = tk.StringVar()
        self.track_entry = tk.Entry(self.parent, textvariable=self.track_str, width=5)
        self.track_entry.bind("<FocusOut>", self.changeTrackEvent)
        self.track_entry.bind("<Return>", self.changeTrackEvent)
        self.track_label = tk.Label(self.parent, text = "Track #")
        self.to_disable.append(self.track_entry)

        self.time_str = tk.StringVar()
        self.time_entry = tk.Entry(self.parent, textvariable=self.time_str, width=5)
        self.time_entry.bind("<FocusOut>", self.changeFrameEvent)
        self.time_entry.bind("<Return>", self.changeFrameEvent)
        self.time_label = tk.Label(self.parent, text = "Time Frame")
        self.time_str.set(self.t)
        self.to_disable.append(self.time_entry)

        self.stack_str = tk.StringVar()
        self.stack_entry = tk.Entry(self.parent, textvariable=self.stack_str, width=5)
        self.stack_entry.bind("<FocusOut>", self.changeStackEvent)
        self.stack_entry.bind("<Return>", self.changeStackEvent)
        self.stack_label = tk.Label(self.parent, text = "Stack #")
        self.stack_str.set(self.z)
        self.to_disable.append(self.stack_entry)

        # Buttons for following, delete and merge tracks
        self.follow_button = tk.Button(self.parent, text = "Follow", 
            command = self.followButtonCallback)
        self.following = False
        self.to_disable.append(self.follow_button)
        self.merge_button = tk.Button(self.parent, text = "Merge", 
            command = self.mergeButtonCallback)
        self.to_disable.append(self.merge_button)
        self.delete_button = tk.Button(self.parent, text = "Delete/Include", 
            command = self.deleteButtonCallback)
        self.to_disable.append(self.delete_button)

        # Create the calibration interface
        self.calibrate_button = tk.Button(self.parent, text = "Calibrate", 
            command = self.calibrateButtonCallback)
        self.to_disable.append(self.calibrate_button)

        self.calibration_table = [] # all widgets of the calibration table
        # Calibration table titles
        self.x_label = tk.Label(self.parent, text = "X")
        self.y_label = tk.Label(self.parent, text = "Y")
        self.point1_button = tk.Button(self.parent, text = "Point 1", 
            command = self.point1ButtonCallback)
        self.point2_button = tk.Button(self.parent, text = "Point 2", 
            command = self.point2ButtonCallback)
        self.point3_button = tk.Button(self.parent, text = "Point 3", 
            command = self.point3ButtonCallback)
        self.calibration_table.append(self.x_label)
        self.calibration_table.append(self.y_label)
        self.calibration_table.append(self.point1_button)
        self.calibration_table.append(self.point2_button)
        self.calibration_table.append(self.point3_button)

        # Calibration table entries
        self.point1x_str = tk.StringVar()
        self.point1x_entry = tk.Entry(self.parent, 
            textvariable = self.point1x_str, width=5)
        self.point1y_str = tk.StringVar()
        self.point1y_entry = tk.Entry(self.parent,
            textvariable = self.point1y_str, width=5)
        self.calibration_table.append(self.point1x_entry)
        self.calibration_table.append(self.point1y_entry)

        self.point2x_str = tk.StringVar()
        self.point2x_entry = tk.Entry(self.parent,
            textvariable = self.point2x_str, width=5)
        self.point2y_str = tk.StringVar()
        self.point2y_entry = tk.Entry(self.parent,
            textvariable = self.point2y_str, width=5)
        self.calibration_table.append(self.point2x_entry)
        self.calibration_table.append(self.point2y_entry)

        self.point3x_str = tk.StringVar()
        self.point3x_entry = tk.Entry(self.parent,
            textvariable = self.point3x_str, width=5)
        self.point3y_str = tk.StringVar()
        self.point3y_entry = tk.Entry(self.parent, 
            textvariable = self.point3y_str, width=5)
        self.calibration_table.append(self.point3x_entry)
        self.calibration_table.append(self.point3y_entry)

        # if the configuration file was read, set up the text entry
        if self.calibration_image_coord:
            self.point1x_str.set(self.calibration_image_coord[0][0])
            self.point1y_str.set(self.calibration_image_coord[0][1])
            self.point2x_str.set(self.calibration_image_coord[1][0])
            self.point2y_str.set(self.calibration_image_coord[1][1])
            self.point3x_str.set(self.calibration_image_coord[2][0])
            self.point3y_str.set(self.calibration_image_coord[2][1])

    def __placeWidgets(self):
        """
        Place widgets in the window.
        All the created widgets must be placed somewhere to show up.
        """
        self.canvas.grid(row=0, column=0, rowspan=11)
        self.track_label.grid(row=0, column=1)
        self.track_entry.grid(row=0, column=2, columnspan=2)
        self.time_label.grid(row=1, column=1)
        self.time_entry.grid(row=1, column=2, columnspan=2)
        self.stack_label.grid(row=2, column=1)
        self.stack_entry.grid(row=2, column=2, columnspan=2)
        self.follow_button.grid(row=3, column=1, columnspan=3)
        self.merge_button.grid(row=4, column=1, columnspan=3)
        self.delete_button.grid(row=5, column=1, columnspan=3)
        self.calibrate_button.grid(row=6, column=1, columnspan=3)
        self.x_label.grid(row=7, column=2, stick='s')
        self.y_label.grid(row=7, column=3, stick='s')
        self.point1_button.grid(row=8, column=1)
        self.point1x_entry.grid(row=8, column=2)
        self.point1y_entry.grid(row=8, column=3)
        self.point2_button.grid(row=9, column=1)
        self.point2x_entry.grid(row=9, column=2)
        self.point2y_entry.grid(row=9, column=3)
        self.point3_button.grid(row=10, column=1)
        self.point3x_entry.grid(row=10, column=2)
        self.point3y_entry.grid(row=10, column=3)

        # Hide the calibration table initially
        self.iscalibrating = False
        self.__hideCalibrationTable()

    def __showCalibrationTable(self):
        """
        Enable all the widgets in the calibration table
        """
        for widget in self.calibration_table:
            widget.config(state = 'normal')

    def __hideCalibrationTable(self):
        """
        Disable all the widgets in the calibration table
        """
        for widget in self.calibration_table:
            widget.config(state = 'disabled')

    def __enableAll(self, calibration = True):
        """
        Enable all the widgets in the list self.to_disable
        """
        for widget in self.to_disable:
            widget.config(state = 'normal')
        
        if calibration:
            self.__showCalibrationTable()

    def __disableAll(self, calibration = True):
        """
        Disable all the widgets in the list self.to_disable
        """
        for widget in self.to_disable:
            widget.config(state = 'disabled')

        if calibration:
            self.__hideCalibrationTable()

    def __changeImageOnCanvas(self, z_temp, t_temp):
        """
        Change the image on canvas to new z and t if
        file exists. Otherwise just warning.
        """        
        # check if file exists, if so changes the image
        path_aux = corrTIFPath(corrTIFPath(self.path,'?',t_temp), '@', z_temp)
        if os.path.isfile(path_aux):
            self.img = ImageTk.PhotoImage(Image.open(path_aux))
            self.canvas.itemconfig(self.image_on_canvas, image = self.img)
            self.z = z_temp
            self.stack_str.set(self.z)
            self.t = t_temp
            self.time_str.set(self.t)
        else:
            print('File {path} do not exist'.format(path = path_aux))
            return False

        return True

    def __showCalibrationMarks(self):
        """
        Show the marks used for calibration in the canvas
        """
        for draw in self.calibration_draws:
            for x in self.calibration_draws[draw]:
                self.canvas.itemconfig(x, state= 'normal')

    def __hideCalibrationMarks(self):
        """
        Hide the marks used for calibration in the canvas
        """
        for draw in self.calibration_draws:
            for x in self.calibration_draws[draw]:
                self.canvas.itemconfig(x, state= 'hidden')

    def warningWindow(self, warning):
        """
        Opens a warning pop-up with the given message
        """
        otherFrame = tk.Toplevel()
        otherFrame.title("otherFrame")
        label = tk.Label(otherFrame, text = warning)
        label.pack()
        handler = lambda: self.onCloseOtherFrame(otherFrame)
        btn = tk.Button(otherFrame, text="OK", command=handler)
        btn.pack()
        # make sure widget instances are deleted
        otherFrame.protocol("WM_DELETE_WINDOW", otherFrame.destroy)

    def onCloseOtherFrame(self, otherFrame):
        """
        Close warning window properly
        """
        otherFrame.destroy()

    def convertCoords(self, x, y):
        """
        Converts the XY of the click to the coordinates in the image
        according to calibration. If the calibration is not done
        properly a warning pops up.
        It assumes no rotation in the image. The requirement of
        3 points is to make it easier to calibrate.
        """
        # First check whether the calibration was done
        for key in range(3):
            if ((not key in self.calibration_coords) or 
               (not key in self.calibration_image_coord)):
                self.warningWindow("You must do the calibration.")
                return None

        # Then check whether they are colinear, if not the factors are calculated
        alfa = 0
        beta = 0
        dist_im = [0, 0]
        [x0, y0] = self.calibration_coords[0]
        [x0_im, y0_im] = self.calibration_image_coord[0]
        for key in range(1,3,1):
            coord = self.calibration_coords[key]
            image_coord = self.calibration_image_coord[key]
            # check for x and get the maximum distance for better precision
            if abs(coord[0]-x0)>0:
                dist_temp = (image_coord[0]-x0_im)
                if abs(dist_temp) > dist_im[0]:
                    dist_im[0] = abs(dist_temp)
                    alfa = (1.0*dist_temp)/(coord[0]-x0)
            
            # check for y and get the maximum distance for better precision
            if abs(coord[1]-y0)>0:
                dist_temp = (image_coord[1]-y0_im)
                if abs(dist_temp) > dist_im[1]:
                    dist_im[1] = abs(dist_temp)
                    beta = (1.0*dist_temp)/(coord[1]-y0)

        if (alfa == 0) or (beta == 0):
            self.warningWindow("Calibration points are colinear, redo the calibration")
            return None

        # If passed the requirements, then calculate the transformation
        x_out = x0_im + alfa*(x-x0)
        y_out = y0_im + beta*(y-y0)

        return x_out, y_out


    def followButtonCallback(self):

        if self.track_num >= 0:
            self.following = not self.following
            if self.following:
                self.canvas.focus_set()
                self.__disableAll()
                self.follow_button.config(state = 'normal', relief = 'sunken')
                t_ini = self.track.configs[self.track.TIME_INI_KEY]
                t_temp = self.__track_mov[0,0] + t_ini
                z_temp = round(self.__track_mov[3,0])
                self.__changeImageOnCanvas(z_temp, t_temp)
            else:
                self.__enableAll(False)
                self.follow_button.config(relief = 'raised')
        else:
            self.warningWindow("Select a Track to follow")


    def mergeButtonCallback(self):
        print("Merge")

    def deleteButtonCallback(self):
        print("Delete")

    def calibrateButtonCallback(self):

        self.iscalibrating = not self.iscalibrating
        
        if self.iscalibrating:
            self.__showCalibrationTable()
            self.__showCalibrationMarks()
        else:
            self.getImageCalibration()
            self.__hideCalibrationTable()
            self.__hideCalibrationMarks()


    def writeCalibrationFile(self):

        if self.calibration_image_coord and (len(self.calibration_coords)==3):
            filename = self.track.folder + "\\manual_track_config\\calibration.conf"
            ensure_dir(filename)
            f = open(filename, 'w')
            f.write('# Pixel Coordinates:\n')
            for point in self.calibration_coords:
                [x, y] = self.calibration_coords[point]
                f.write('{x}\t{y}\n'.format(x = x, y = y))
            f.write('# Real Coordinates:\n')
            for point in self.calibration_image_coord:
                [x, y] = self.calibration_image_coord[point]
                f.write('{x}\t{y}\n'.format(x = x, y = y))
            f.close()

    def readCalibrationFile(self):

        filename = self.track.folder + "\\manual_track_config\\calibration.conf"
        if os.path.isfile(filename):
            try: # in case the file was corrupted
                f = open(filename, 'r')
                f.readline() # jump first comment
                for point in range(3):
                    self.calibration_coords[point] = [int(x) for x in f.readline().strip().split('\t')]
                f.readline() # jump second comment
                for point in range(3):
                    self.calibration_image_coord[point] = [int(x) for x in f.readline().strip().split('\t')]
                f.close()
                return True
            except:
                return False
        else:
            return False

    def getImageCalibration(self):

        string_var = [[self.point1x_str, self.point1y_str],
                      [self.point2x_str, self.point2y_str],
                      [self.point3x_str, self.point3y_str]]

        aux = [0,0]
        for point, str_var in enumerate(string_var):
            x = str_var[0].get()
            y = str_var[1].get()
            if ((not x) or (not y)):
                self.calibration_image_coord = {}
                return False
            else:
                self.calibration_image_coord[point] = [int(x),int(y)]

        self.writeCalibrationFile()

        return True

    def deleteCalibrationMark(self, calibration_draw):

        for x in calibration_draw:
            self.canvas.delete(x)           

    def drawCalibrationMark(self, x, y, text):

        color = 'red'
        offset = 6
        x1 = self.canvas.create_line(x-offset, y-offset, x+offset, y+offset, fill = color, width = 2)
        x2 = self.canvas.create_line(x-offset, y+offset, x+offset, y-offset, fill = color, width = 2)
        label = self.canvas.create_text(x+offset+5, y+offset+5, text = text, fill = color)
        return x1, x2, label

    def getCalibrationXY(self, event):

        x = event.x
        y = event.y

        if self.__caller in self.calibration_draws:
            self.deleteCalibrationMark(self.calibration_draws[self.__caller])
        self.calibration_draws[self.__caller] = self.drawCalibrationMark(x,y, 'P{num}'.format(num=self.__caller+1))
        self.calibration_coords[self.__caller] = [x,y]

        self.writeCalibrationFile()

        self.canvas.unbind('<Double-Button-1>')
        self.canvas.bind("<Button-1>", self.focusOnCanvas)
        self.__enableAll()

    def getCalibrationPointOnCanvas(self):

        # Wait for the choice of the point
        self.canvas.bind('<Double-Button-1>', self.getCalibrationXY)
        self.canvas.unbind("<Button-1>")
        self.__disableAll()

    def point1ButtonCallback(self):
        
        self.__caller = 0
        self.getCalibrationPointOnCanvas()
        
    def point2ButtonCallback(self):
        
        self.__caller = 1
        self.getCalibrationPointOnCanvas()

    def point3ButtonCallback(self):
        
        self.__caller = 2
        self.getCalibrationPointOnCanvas()

    def changeStackEvent(self, event):

        z_temp = int(self.stack_str.get())
        if not self.__changeImageOnCanvas(z_temp, self.t):
            self.stack_str.set(self.z)

        if event.type == 2:
            self.focusOnCanvas()

    def changeFrameEvent(self, event):

        t_temp = int(self.time_str.get())
        if not self.__changeImageOnCanvas(self.z, t_temp):
            self.time_str.set(self.t)

        if event.type == 2:
            self.focusOnCanvas()

    def changeTrackEvent(self, event):

        track_temp = int(self.track_str.get())

        if track_temp < len(self.track.id_seq):
            track_mov = np.array(self.track.getWholeMovement(track_temp))
            if track_mov.size > 0:
                track_mov = np.ceil(track_mov)
                t_ini = self.track.configs[self.track.TIME_INI_KEY]
                t_temp = track_mov[0,0] + t_ini
                z_temp = round(track_mov[3,0])

                if self.__changeImageOnCanvas(z_temp, t_temp):
                    self.track_num = track_temp
                    self.__track_mov = track_mov

        self.track_str.set(self.track_num if self.track_num >= 0 else "")

        if event.type == 2:
            self.focusOnCanvas()

    def focusOnCanvas(self, event):

        self.canvas.focus()
        self.canvas.focus_set()

    def arrowEvent(self, event):
        """
        Handle the arrow events in the main canvas.
        """

        if event.keysym.lower() == 'up':
            z_temp = self.z + 1
            t_temp = self.t
        elif event.keysym.lower() == 'down':
            z_temp = self.z - 1
            t_temp = self.t
        elif event.keysym.lower() == 'right':
            z_temp = self.z
            t_temp = self.t + 1
        elif event.keysym.lower() == 'left':                   
            z_temp = self.z
            t_temp = self.t - 1

        if self.following and (t_temp != self.t):
            t_ini = self.track.configs[self.track.TIME_INI_KEY]
            check_time = np.equal(self.__track_mov[0,:], t_temp - t_ini)
            if check_time.sum() > 0:
                z_temp = self.__track_mov[3,check_time][0]
            else:
                print('Not tracked in the next time')
                return None
        self.__changeImageOnCanvas(z_temp, t_temp)

def main(*args):

    if len(args) >= 1:
        date = str(args[0])
    else:   
        date = input("Results date string:")

    folder = "D:\\image_software\\results\\GMEMtracking3D_" + date
    if os.path.exists(folder+"\\eye_check"):
        root = tk.Tk()
        track = TrackingAnalysis(folder)
        image_path_pattern = track.folder + "\\eye_check\\T?????\\Z@@@.png"
        window = ManualTrackWindow(root, track, image_path_pattern)
        root.mainloop()
    else:
        print("Run the file write_eye_check.py first")

    return None

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

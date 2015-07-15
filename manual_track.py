#!/usr/bin/env python
import tkinter as tk
from PIL import ImageTk, Image
from track_utils import corrTIFPath, TrackingAnalysis
import os.path

class ManualTrackWindow(object):

    def __init__(self, parent, track, image_path_pattern):
        """
        Constructor
        """
        # initialize class variables
        self.z = 1
        self.t = track.configs[track.TIME_INI_KEY]
        self.path = image_path_pattern
        self.parent = parent

        # set up the main canvas
        self.__initImageCanvas()

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
        self.canvas.pack()

        self.canvas.focus_set() # to get keyboard events

        # bind of arrow events
        self.canvas.bind("<Up>", self.arrowEvent)
        self.canvas.bind("<Down>", self.arrowEvent)
        self.canvas.bind("<Right>", self.arrowEvent)
        self.canvas.bind("<Left>", self.arrowEvent)

        # set up first image
        self.img = ImageTk.PhotoImage(image)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor = 'nw', image = self.img)

    def __initInterfaceWidgets(self):
        """
        Set up the rest of the interface widgets
        besides the image.
        """
        # First initialize all the widgets


        # Now place them in grid

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

        # check if file exists, if so changes the image
        path_aux = corrTIFPath(corrTIFPath(self.path,'?',t_temp), '@', z_temp)
        if os.path.isfile(path_aux):
            self.img = ImageTk.PhotoImage(Image.open(path_aux))
            self.canvas.itemconfig(self.image_on_canvas, image = self.img)
            self.z = z_temp
            self.t = t_temp
        else:
            print('File {path} do not exist'.format(path = path_aux))



folder = "D:\\image_software\\results\\GMEMtracking3D_2015_7_14_12_55_10"
root = tk.Tk()
track = TrackingAnalysis(folder)
image_path_pattern = track.folder + "\\eye_check\\T?????\\Z@@@.png"
window = ManualTrackWindow(root, track, image_path_pattern)
root.mainloop()

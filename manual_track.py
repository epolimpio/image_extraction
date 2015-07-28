#!/usr/bin/env python
import tkinter as tk
import numpy as np
import lxml.etree as etree
from PIL import ImageTk, Image
from track_utils import corrTIFPath, TrackingAnalysis, ensure_dir
import os.path

class ManualTrackWindow(object):

    SIZE_HISTORY_LINE = 10

    def __init__(self, parent, track):
        """
        Constructor
        """
        # initialize class variables
        self.z = 1
        self.t = track.configs[track.TIME_INI_KEY]
        self.track_num = None
        self.track = track
        self.tracking = False
        self.path = track.folder + "\\eye_check\\T?????\\Z@@@.png"
        
        # parent window parameters
        self.parent = parent
        self.parent.title("Manual Track")
        
        # Auxiliary variable with the followed track
        self.__track_mov = np.array([])

        # Auxiliary variable that keeps track of all the manual
        # tracks drawn in canvas
        self.__manual_draws = []

        # set up the main canvas
        self.__initImageCanvas()
        # initialize all interface widgets
        self.__initInterfaceWidgets()
        # place widgets in the window
        self.__placeWidgets()

        # Attribute that keeps all the manual tracks
        self.all_manualtracks = self.readManualTrackFile()
        self.__updateManualTrackOption()

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
        Set up the rest of the interface widgets besides the image canvas.
        Many widgets are placed inside frames for modularity
        of their positioning within the main window.
        """
        self.to_disable = [] # contains the list of all the elements disabled when waiting for action
        
        # First initialize all the widgets
        # Entries for time, stack and track number
        self.track_frame = tk.Frame(self.parent)
        self.track_str = tk.StringVar()
        self.track_label = tk.Label(self.track_frame, text = "Track #", width=12, anchor='w')
        self.track_entry = tk.Entry(self.track_frame, textvariable=self.track_str, width=5)
        self.track_entry.bind("<FocusOut>", self.changeTrackEvent)
        self.track_entry.bind("<Return>", self.changeTrackEvent)
        self.to_disable.append(self.track_entry)
        self.track_label.grid(row=0, column=0)
        self.track_entry.grid(row=0, column=1)

        self.time_entry_frame = tk.Frame(self.parent)
        self.time_str = tk.StringVar()
        self.time_label = tk.Label(self.time_entry_frame, text = "Time Frame", width=12, anchor='w')
        self.time_entry = tk.Entry(self.time_entry_frame, textvariable=self.time_str, width=5)
        self.time_entry.bind("<FocusOut>", self.changeFrameEvent)
        self.time_entry.bind("<Return>", self.changeFrameEvent)
        self.time_str.set(int(self.t))
        self.to_disable.append(self.time_entry)
        self.time_label.grid(row=0, column=0)
        self.time_entry.grid(row=0, column=1)

        self.stack_frame = tk.Frame(self.parent)
        self.stack_str = tk.StringVar()
        self.stack_label = tk.Label(self.stack_frame, text = "Stack #", width=12, anchor='w')
        self.stack_entry = tk.Entry(self.stack_frame, textvariable=self.stack_str, width=5)
        self.stack_entry.bind("<FocusOut>", self.changeStackEvent)
        self.stack_entry.bind("<Return>", self.changeStackEvent)
        self.stack_str.set(int(self.z))
        self.to_disable.append(self.stack_entry)
        self.stack_label.grid(row=0, column=0)
        self.stack_entry.grid(row=0, column=1)

        # Following button
        self.follow_button = tk.Button(self.parent, text = "Follow", 
            command = self.followButtonCallback, width=14)
        self.following = False
        self.to_disable.append(self.follow_button)

        # Merge Button and Entries
        self.merge_frame = tk.Frame(self.parent)
        self.merge_button = tk.Button(self.merge_frame, text = "Merge", 
            command = self.mergeButtonCallback, width=14)
        self.to_disable.append(self.merge_button)

        self.merge_label1 = tk.Label(self.merge_frame, text="Tr #1")
        self.merge_label2 = tk.Label(self.merge_frame, text="Tr #2")

        self.merge_str1 = tk.StringVar()
        self.merge_entry1 = tk.Entry(self.merge_frame, textvariable=self.merge_str1, width=5)
        self.to_disable.append(self.merge_entry1)

        self.merge_str2 = tk.StringVar()
        self.merge_entry2 = tk.Entry(self.merge_frame, textvariable=self.merge_str2, width=5)
        self.to_disable.append(self.merge_entry2)

        self.merge_label1.grid(row=0,column=0, padx=2)
        self.merge_label2.grid(row=0,column=1, padx=2)
        self.merge_entry1.grid(row=1,column=0, padx=2)
        self.merge_entry2.grid(row=1,column=1, padx=2)
        self.merge_button.grid(row=1,column=2, padx=40)

        # Delete Button and Entry
        self.delete_frame = tk.Frame(self.parent)
        self.delete_button = tk.Button(self.delete_frame, text = "Delete", 
            command = self.deleteButtonCallback, width=14)
        self.to_disable.append(self.delete_button)

        self.delete_str = tk.StringVar()
        self.delete_label = tk.Label(self.delete_frame, text = "Tr #", width=4)
        self.delete_entry = tk.Entry(self.delete_frame, textvariable=self.delete_str, width=5)
        self.to_disable.append(self.delete_entry)
        self.delete_label.grid(row=0, column=0, padx=2)
        self.delete_entry.grid(row=0, column=1, padx=2) 
        self.delete_button.grid(row=0, column=2, padx=40)

        # Division Button and Entries
        self.division_frame = tk.Frame(self.parent)
        self.division_button = tk.Button(self.division_frame, text = "Add division", 
            command = self.divisionButtonCallback, width=14)
        self.to_disable.append(self.division_button)

        self.division_parent_label = tk.Label(self.division_frame, text="Par", width=4)
        self.division_child1_label = tk.Label(self.division_frame, text="Ch1", width=4)
        self.division_child2_label = tk.Label(self.division_frame, text="Ch2", width=4)

        self.division_parent_str = tk.StringVar()
        self.division_parent_entry = tk.Entry(self.division_frame, textvariable=self.division_parent_str, width=5)
        self.to_disable.append(self.division_parent_entry)

        self.division_child1_str = tk.StringVar()
        self.division_child1_entry = tk.Entry(self.division_frame, textvariable=self.division_child1_str, width=5)
        self.to_disable.append(self.division_child1_entry)

        self.division_child2_str = tk.StringVar()
        self.division_child2_entry = tk.Entry(self.division_frame, textvariable=self.division_child2_str, width=5)
        self.to_disable.append(self.division_child2_entry)

        self.division_parent_label.grid(row=0,column=0, padx=2)
        self.division_parent_entry.grid(row=1,column=0, padx=2)
        self.division_child1_label.grid(row=0,column=1, padx=2)
        self.division_child1_entry.grid(row=1,column=1, padx=2)
        self.division_child2_label.grid(row=0,column=2, padx=2)
        self.division_child2_entry.grid(row=1,column=2, padx=2)
        self.division_button.grid(row=1,column=3, padx=2)

        # Manual Track Button and Entry
        self.manualtrack_frame = tk.Frame(self.parent)
        self.manualtrack_button = tk.Button(self.manualtrack_frame, text = "Add track", 
            command = self.trackButtonCallback, width=14)
        self.to_disable.append(self.manualtrack_button)

        self.manualtrack_label = tk.Label(self.manualtrack_frame, text="Tr #", width=4)
        self.manualtrack_str = tk.StringVar()
        self.manualtrack_list = tk.OptionMenu(self.manualtrack_frame, self.manualtrack_str, ())
        self.manualtrack_list.config(width=5)
        self.to_disable.append(self.manualtrack_list)
        self.manualtrack_label.grid(row=0, column=0, padx=2)
        self.manualtrack_list.grid(row=0, column=1, padx=2)       
        self.manualtrack_button.grid(row=0, column=2, padx=35)

        # Image selection Radio Buttons
        self.radio_frame = tk.Frame(self.parent)
        MODES = [
            ("All info", "All"),
            ("SV only", "SV"),
            ("No info", "None"),
        ]
        self.radio_related_path = {
            "All": "\\eye_check\\T?????\\Z@@@.png",
            "SV": "\\eye_check\\T?????_allSV\\Z@@@.png",
            "None": "\\eye_check\\T?????_stackOnly\\Z@@@.png",
        }

        self.radio_frame_str = tk.StringVar()
        self.radio_frame_str.set("All")
        for text, mode in MODES:
            self.image_select_radio = tk.Radiobutton(self.radio_frame, text=text,
                variable=self.radio_frame_str, value=mode, command=self.imageRadioCallback)
            self.image_select_radio.pack(anchor = 'w')

        # Image options Check Buttons
        self.check_frame = tk.Frame(self.parent)
        self.show_division_var = tk.IntVar()
        self.show_division_check = tk.Checkbutton(self.check_frame,
            text="Mark Divisions", variable=self.show_division_var,
            command=self.showDivisionCallback)
        self.show_division_check.pack(anchor = 'w')

        self.show_manualtrack_var = tk.IntVar()
        self.show_manualtrack_check = tk.Checkbutton(self.check_frame,
            text="Manual Tracks", variable=self.show_manualtrack_var,
            command=self.showManualTrackCallback)
        self.show_manualtrack_check.pack(anchor = 'w')

        # Create the calibration interface
        self.calibrate_button = tk.Button(self.parent, text = "Calibrate", 
            command = self.calibrateButtonCallback, width=14)
        self.to_disable.append(self.calibrate_button)

        self.calibration_table = [] # all widgets of the calibration table
        self.calibration_frame = tk.Frame(self.parent)
        # Calibration table titles
        self.x_label = tk.Label(self.calibration_frame, text = "X")
        self.y_label = tk.Label(self.calibration_frame, text = "Y")
        self.point1_button = tk.Button(self.calibration_frame, text = "Point 1", 
            command = self.point1ButtonCallback)
        self.point2_button = tk.Button(self.calibration_frame, text = "Point 2", 
            command = self.point2ButtonCallback)
        self.point3_button = tk.Button(self.calibration_frame, text = "Point 3", 
            command = self.point3ButtonCallback)
        self.calibration_table.append(self.x_label)
        self.calibration_table.append(self.y_label)
        self.calibration_table.append(self.point1_button)
        self.calibration_table.append(self.point2_button)
        self.calibration_table.append(self.point3_button)

        # Calibration table entries
        self.point1x_str = tk.StringVar()
        self.point1x_entry = tk.Entry(self.calibration_frame, 
            textvariable = self.point1x_str, width=5)
        self.point1y_str = tk.StringVar()
        self.point1y_entry = tk.Entry(self.calibration_frame,
            textvariable = self.point1y_str, width=5)
        self.calibration_table.append(self.point1x_entry)
        self.calibration_table.append(self.point1y_entry)

        self.point2x_str = tk.StringVar()
        self.point2x_entry = tk.Entry(self.calibration_frame,
            textvariable = self.point2x_str, width=5)
        self.point2y_str = tk.StringVar()
        self.point2y_entry = tk.Entry(self.calibration_frame,
            textvariable = self.point2y_str, width=5)
        self.calibration_table.append(self.point2x_entry)
        self.calibration_table.append(self.point2y_entry)

        self.point3x_str = tk.StringVar()
        self.point3x_entry = tk.Entry(self.calibration_frame,
            textvariable = self.point3x_str, width=5)
        self.point3y_str = tk.StringVar()
        self.point3y_entry = tk.Entry(self.calibration_frame, 
            textvariable = self.point3y_str, width=5)
        self.calibration_table.append(self.point3x_entry)
        self.calibration_table.append(self.point3y_entry)

        # Position table in frame
        self.x_label.grid(row=0, column=1, stick='s')
        self.y_label.grid(row=0, column=2, stick='s')
        self.point1_button.grid(row=1, column=0, padx=2, pady=2)
        self.point1x_entry.grid(row=1, column=1, padx=2, pady=2)
        self.point1y_entry.grid(row=1, column=2, padx=2, pady=2)
        self.point2_button.grid(row=2, column=0, padx=2, pady=2)
        self.point2x_entry.grid(row=2, column=1, padx=2, pady=2)
        self.point2y_entry.grid(row=2, column=2, padx=2, pady=2)
        self.point3_button.grid(row=3, column=0, padx=2, pady=2)
        self.point3x_entry.grid(row=3, column=1, padx=2, pady=2)
        self.point3y_entry.grid(row=3, column=2, padx=2, pady=2)

        # if the configuration file was read, set up the text entry
        if self.calibration_image_coord:
            self.point1x_str.set(int(self.calibration_image_coord[0][0]))
            self.point1y_str.set(int(self.calibration_image_coord[0][1]))
            self.point2x_str.set(int(self.calibration_image_coord[1][0]))
            self.point2y_str.set(int(self.calibration_image_coord[1][1]))
            self.point3x_str.set(int(self.calibration_image_coord[2][0]))
            self.point3y_str.set(int(self.calibration_image_coord[2][1]))

    def __placeWidgets(self):
        """
        Place widgets in the window.
        All the created widgets or frames must be placed somewhere to show up.
        Many of the widgets are already placed inside a frame, then we only
        need to position the frame within the parent window
        """
        row = 0
        self.track_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.time_entry_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.stack_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.radio_frame.grid(row=row, column=1, columnspan=2, stick='nw', pady=2)
        self.check_frame.grid(row=row, column=3, columnspan=2, stick='nw', pady=2, padx=4)
        row += 1
        self.follow_button.grid(row=row, column=1, columnspan=4)
        row += 1
        self.merge_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.delete_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.division_frame.grid(row=row, column=1, columnspan=4, stick='w')
        row += 1
        self.manualtrack_frame.grid(row=row, column=1, columnspan=4, stick='w')        
        row += 1
        self.calibrate_button.grid(row=row, column=1, columnspan=4, stick='s')
        row += 1
        self.calibration_frame.grid(row=row, column=1, columnspan=4)

        self.canvas.grid(row=0, column=0, rowspan=row+1)

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
            self.z = int(z_temp)
            self.stack_str.set(int(self.z))
            self.t = int(t_temp)
            self.time_str.set(int(self.t))
            if bool(self.show_manualtrack_var.get()):
                self.__putManualTrackMarks(z_temp, t_temp)
        else:
            print('File {path} do not exist'.format(path = path_aux))
            return False

        return True

    def __deleteAllManualTrackMarks(self):
        """
        Delete all manual track marks in the canvas
        """

        if self.__manual_draws:
            for draw in self.__manual_draws:
                self.canvas.delete(draw)

    def __putManualTrackMarks(self, z_temp, t_temp):
        """
        Include the manual track marks in the canvas,
        deleting the old marks
        """
        max_diff = 10
        color_below = '#00ff00' # green
        color_same = '#deb887' # yellowish
        color_above = '#ee82ee' # purple
        offset = 2
        
        self.__deleteAllManualTrackMarks()

        if self.all_manualtracks:
            self.__manual_draws = []
            for id_ in self.all_manualtracks:
                if t_temp in self.all_manualtracks[id_]:
                    x, y, z = self.all_manualtracks[id_][t_temp]
                    z_diff = z - z_temp
                    if abs(z_diff)<=max_diff:
                        if z_diff == 0:
                            color = color_same
                        elif z_diff < 0:
                            color = color_below
                        else:
                            color = color_above
                        self.__manual_draws.append(
                            self.canvas.create_oval(x-offset, y-offset,
                            x+offset, y+offset, fill = color, outline=''))

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

    def __updateManualTrackOption(self):
        """
        Updates the manual track options list
        """
        # reset list
        menu = self.manualtrack_list["menu"]
        menu.delete(0, "end")

        # get all the tracks
        options = ['New']
        for id_ in self.all_manualtracks:
            options.append('M{id}'.format(id=id_))

        for string in options:
            handler = lambda value=string: self.manualTrackListChange(value)
            menu.add_command(label=string, command=handler)

        self.manualtrack_str.set('New')

    def manualTrackListChange(self, string):
        """
        Handle what happens when the element on the manual track option menu changes
        """
        self.manualtrack_str.set(string)
        if string.lower() == 'new':
            self.manualtrack_button.config(text='Add Track')
        else:
            self.manualtrack_button.config(text='Edit Track')

    def createListBoxFrame(self, parent):
        """
        Creates a listbox with a scrollbar inside a frame
        """
        frame = tk.Frame(parent)
        scrollbar = tk.Scrollbar(frame, orient='vertical')
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.pack(side='left', fill='both', expand=1)

        return frame, listbox, scrollbar

    def warningWindow(self, warning):
        """
        Opens a warning pop-up with the given message
        """
        otherFrame = tk.Toplevel()
        otherFrame.title("WARNING")
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

    def yesnoWindow(self, message='', execute_if_yes=None, execute_if_no = None, **kwargs):
        """
        Opens a pop-up with the given message and Yes or No options
        If yes, execute_if_yes is executed, if no execute_if_no is executed
        Both are executed with the same parameters **kwargs
        """
        otherFrame = tk.Toplevel()
        otherFrame.title("CONFIRM")
        label = tk.Label(otherFrame, text = message)
        handler_yes = lambda: self.closeYesNo(otherFrame, execute_if_yes, **kwargs)
        btn_yes = tk.Button(otherFrame, text="Yes", command=handler_yes)
        
        handler_no = lambda: self.closeYesNo(otherFrame, execute_if_no, **kwargs)
        btn_no = tk.Button(otherFrame, text="No", command=handler_no)
        label.grid(row=0, column=0, columnspan=2)
        btn_yes.grid(row=1, column=0, padx=2)
        btn_no.grid(row=1, column=1, padx=2)
        # make sure widget instances are deleted
        otherFrame.protocol("WM_DELETE_WINDOW", otherFrame.destroy)

    def closeYesNo(self, otherFrame, command, **kwargs):
        """
        Closes YesNo Window and execute function if needed
        """        
        if command:
            command(**kwargs)
        otherFrame.destroy()


    def convertCoords(self, x, y, inverse=False):
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
        if inverse:
            # Convert from coord to pixels (inverse)
            x_out = x0 + (x-x0_im)/alfa
            y_out = y0 + (y-y0_im)/beta
        else:
            # Convert from pixels to coord
            x_out = x0_im + alfa*(x-x0)
            y_out = y0_im + beta*(y-y0)

        return x_out, y_out

    def followButtonCallback(self):
        """
        Callback of the follow button
        When clicked enter or leave follow the track mode
        """     
        if self.track_num is not None:
            self.following = not self.following
            if self.following:
                if self.track_str.get()[:1].lower() == 'm':
                    self.show_manualtrack_var.set(1)
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
        """
        Callback of the merge button
        Used to merge different tracks
        """
        # --- TO BE IMPLEMENTED --- #
        print("Merge")

    def deleteButtonCallback(self):
        """
        Callback of the Delete button
        Used to insert track in black list
        """
        # --- TO BE IMPLEMENTED --- #
        print("Delete")

    def divisionButtonCallback(self):
        """
        Callback of the division button
        Used to insert, edit of delete a division mark
        """
        # --- TO BE IMPLEMENTED --- #
        print("Division")

    def trackButtonCallback(self):
        """
        Callback of the Manual Track button
        Enter or leave the manual track mode
        """
        self.tracking = not self.tracking

        if self.tracking:
            self.startManualTrack()
        else:
            if self.current_manualtrack:
                # Ask if will save
                self.yesnoWindow("Save the acquired track?", self.saveManualTrack)
            else:
                # Only stops the tracking mode
                self.cancelManualTrack()

    def writeManualTrackFile(self, id_in = None):
        """
        Write the current manual track to the XML file
        Return the id of the written track
        """   
        if self.current_manualtrack:
            filename = self.track.folder + "\\manual_track_config\\manual_track.xml"
            ensure_dir(filename)
            if os.path.isfile(filename):
                tree = etree.parse(filename)
                root = tree.getroot()
                if id_in is None:
                    # Find the maximum id
                    id_max = 0
                    for track in root.iter('track'):
                        aux = int(track.attrib['id'])
                        id_max = aux if aux > id_max else id_max
                    id_ = id_max + 1 
                else:
                    id_ = id_in
                    # delete the previous data
                    for old in root.xpath("//track[@id={id_}]".format(id_=id_)):
                        old.getparent().remove(old)
            else:
                root = etree.Element("document")
                id_ = 0
            doc = etree.ElementTree(root)
            element = etree.SubElement(root, "track")
            element.attrib['id'] = '%d'%(id_)
            for t in self.current_manualtrack:
                x_, y_, z = self.current_manualtrack[t]
                x, y = self.convertCoords(x_, y_)
                time = etree.SubElement(element, "point")
                time.attrib['time'] = '%d'%(t)
                time.attrib['x'] = '%d'%(round(x))
                time.attrib['y'] = '%d'%(round(y))
                time.attrib['z'] = '%d'%(z)
 
            doc.write(filename)
            return id_
        else:
            return None

    def readManualTrackFile(self):
        """
        Read XML file with all the manual tracks
        Returns a dictionary with all the data
        """  
        filename = self.track.folder + "\\manual_track_config\\manual_track.xml"
        out = {}
        
        # Test if there is calibration
        test_pass = self.convertCoords(1, 1, inverse = True)
        if not test_pass:
            self.warningWindow('No calibration found, could not load manual tracks')
            print('Redo the calibration and restart the program')
            return out    

        if os.path.isfile(filename):
            tree = etree.parse(filename)
            root = tree.getroot()
            for element in root.iter('track'):
                id_ = int(element.attrib['id'])
                out[id_] = {}
                for point in element.iter('point'):
                    time = int(point.attrib['time'])
                    x_ = int(point.attrib['x'])
                    y_ = int(point.attrib['y'])
                    z = int(point.attrib['z'])

                    [x,y] = self.convertCoords(x_, y_, inverse = True)
                    out[id_][time] = [round(x),round(y),z]

        return out

    def saveManualTrack(self):
        """
        Save the data acquired in the last manual track.
        This is the callback of the saving confirmation
        window.
        """
        string = self.manualtrack_str.get()
        if string.lower() == 'new':   
            id_ = self.writeManualTrackFile()
        else:
            id_ = self.writeManualTrackFile(int(string[1:]))
        
        if id_:
            self.all_manualtracks[id_] = self.current_manualtrack
            self.__updateManualTrackOption()
        self.cancelManualTrack()

    def getManualTrackPoint(self, event):
        """
        Double click callback when tracking, add point to track
        """
        x = event.x
        y = event.y
        coords = self.convertCoords(x,y)
        if coords:
            if self.t in self.current_manualtrack_draw:
                self.deleteManualTrackMark(self.current_manualtrack_draw[self.t])

            self.deleteHistoryLine()

            self.current_manualtrack[self.t] = [x, y, self.z]
            self.current_manualtrack_draw[self.t] = self.drawManualTrackMark(x, y, self.z)

            self.drawHistoryLine(10)

    def deleteManualTrackPoint(self, event):
        """
        Left click callback when tracking, delete point clicked
        """
        x = event.x
        y = event.y
        # check if the click was close to the point, if so delete
        if self.t in self.current_manualtrack:
            coord_actual = self.current_manualtrack[self.t]
            if (abs(x-coord_actual[0])<5) and (abs(y-coord_actual[1])<5):
                del self.current_manualtrack[self.t]
                self.deleteManualTrackMark(self.current_manualtrack_draw[self.t])
                del self.current_manualtrack_draw[self.t]

    def stopManualTrack(self, event):
        """
        Escape callback when tracking, confirm if cancel
        """
        self.yesnoWindow('Do you want to cancel?', self.cancelManualTrack)

    def startManualTrack(self):
        """
        Starts the manual track status in the window
        """          
        # Double click add point
        self.canvas.bind('<Double-Button-1>', self.getManualTrackPoint)
        # Left click on top of point delete it
        self.canvas.bind('<Button-3>', self.deleteManualTrackPoint)
        # Escape cancel the track after confirmation
        self.canvas.bind('<Escape>', self.stopManualTrack)
        self.canvas.unbind("<Button-1>")
        self.__disableAll()
        self.manualtrack_button.config(state='normal', relief='sunken')
        self.show_manualtrack_check.config(state='disabled')
        self.show_division_check.config(state='disabled')
        self.__putManualTrackMarks(self.z, self.t)
        self.show_manualtrack_var.set(1)
        self.canvas.focus_set()
        string = self.manualtrack_str.get()
        self.history_line_draw = None
        self.current_manualtrack_draw = {}
        if string.lower() == 'new':
            self.current_manualtrack = {}
        else:
            # load the previous for edition
            id_ = int(string[1:]) # remove the M
            self.current_manualtrack = self.all_manualtracks[id_]
            t = list(self.current_manualtrack.keys())[0]
            [x,y,z] = self.current_manualtrack[t]
            self.__changeImageOnCanvas(z, t)
            self.current_manualtrack_draw[self.t] = self.drawManualTrackMark(x, y, self.z)

    def cancelManualTrack(self):
        """
        Stops the manual track status in the window,
        returning it to normal
        """        
        self.canvas.unbind('<Double-Button-1>')
        self.canvas.unbind('<Button-3>')
        self.canvas.unbind('<Escape>')
        self.canvas.bind("<Button-1>", self.focusOnCanvas)
        self.__enableAll()
        self.manualtrack_button.config(state='normal', relief='raised')
        self.show_manualtrack_check.config(state='normal')
        self.show_division_check.config(state='normal')

        self.deleteHistoryLine()
        if self.t in self.current_manualtrack_draw:
            self.deleteManualTrackMark(self.current_manualtrack_draw[self.t])

        self.canvas.focus_set()
        self.current_manualtrack = {}
        self.current_manualtrack_draw = {}
        self.history_line_draw = None
        self.tracking = False

    def drawManualTrackMark(self, x, y, z):
        """
        Draw a new point in manual track to canvas
        """ 
        color = 'red'
        color_up = '#ff4500'
        color_down = '#1e90ff'
        color_flat = '#c0c0c0'
        offset = 2
        if (self.t-1) in self.current_manualtrack:
            previous = self.current_manualtrack[self.t-1]

            if previous[2]<z:
                color_line = color_up
            elif previous[2]>z:
                color_line = color_down
            else:
                color_line = color_flat

            line = self.canvas.create_line(previous[0], previous[1], x, y, fill = color_line)
        else:
            line = None

        oval = self.canvas.create_oval(x-offset, y-offset, x+offset, y+offset, fill = color, outline='')
        label = self.canvas.create_text(x+offset+5, y+offset+5, text = 'Z%d'%z, fill = color)
        return oval, line, label

    def drawHistoryLine(self, num_points=None):
        """
        Draw the history line of current manual track
        """
        if num_points is None:
            num_points = self.SIZE_HISTORY_LINE

        self.history_line_draw = None
        color_up = '#ff4500'
        color_down = '#1e90ff'
        color_flat = '#c0c0c0'
        color_oval = 'blue'
        offset = 2
        points = {}
        if self.current_manualtrack:

            for t in range(self.t-1, self.t-num_points+1, -1):
                if t in self.current_manualtrack:
                    points[t] = self.current_manualtrack[t]
                else:
                    break

            if len(points)>=1:
                lines = []
                for t in points:
                    if t == self.t-1:
                        x,y,z = points[t]
                        lines.append(self.canvas.create_oval(x-offset, y-offset, 
                            x+offset, y+offset, fill = color_oval, outline=''))
                    else:
                        point = points[t+1]
                        previous = points[t]
                        if previous[2]<point[2]:
                            color_line = color_up
                        elif previous[2]>point[2]:
                            color_line = color_down
                        else:
                            color_line = color_flat
                        lines.append(self.canvas.create_line(
                            previous[0], previous[1], point[0], point[1],
                            fill = color_line))
                
                self.history_line_draw = lines

    def deleteHistoryLine(self):
        """
        Delete the drawn history line for current manual track
        """  
        if self.history_line_draw:
            for x in self.history_line_draw:
                self.canvas.delete(x)        

    
    def deleteManualTrackMark(self, manualtrack_draw):
        """
        Delete the drawn last point in current manual track
        """  
        for x in manualtrack_draw:
            if x:
                self.canvas.delete(x)


    def showDivisionCallback(self):
        """
        Callback of the show division Checkbutton
        If true shows the division marks
        """ 
        print("Show Division")
        print(self.show_division_var.get())

    def showManualTrackCallback(self):
        """
        Callback of the show manual track Checkbutton
        If true shows the manual track points
        """ 
        if bool(self.show_manualtrack_var.get()):
            self.__putManualTrackMarks(self.z, self.t)
        else:
            self.__deleteAllManualTrackMarks()

    def calibrateButtonCallback(self):
        """
        Callback of the calibrate button
        When clicked enter or leave calibration mode
        """
        self.iscalibrating = not self.iscalibrating
        
        if self.iscalibrating:
            self.__showCalibrationTable()
            self.__showCalibrationMarks()
        else:
            self.getImageCalibration()
            self.__hideCalibrationTable()
            self.__hideCalibrationMarks()

    def imageRadioCallback(self):
        """
        Callback of the image options radiobuttons
        Choose which image will be shown
        """
        path_key = self.radio_frame_str.get()
        self.path = self.track.folder + self.radio_related_path[path_key]
        self.__changeImageOnCanvas(self.z, self.t)        

    def writeCalibrationFile(self):
        """
        Write the current calibration to a file for further use
        """
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
        """
        Read the calibration file previously saved
        """
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
        """
        Get calibration points from the entries of the calibration table
        """
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
        """
        Delete a calibration mark from canvas
        """
        for x in calibration_draw:
            self.canvas.delete(x)           

    def drawCalibrationMark(self, x, y, text):
        """
        Draw a calibration mark on canvas
        """        
        color = 'red'
        offset = 6
        x1 = self.canvas.create_line(x-offset, y-offset, x+offset, y+offset, fill = color, width = 2)
        x2 = self.canvas.create_line(x-offset, y+offset, x+offset, y-offset, fill = color, width = 2)
        label = self.canvas.create_text(x+offset+5, y+offset+5, text = text, fill = color)
        return x1, x2, label

    def getCalibrationXY(self, event):
        """
        Callback of Double Click on canvas when in calibration mode
        Get the position clicked, save it and draw mark
        """  
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
        """
        Enter the Calibration mode
        """ 
        # Wait for the choice of the point
        self.canvas.bind('<Double-Button-1>', self.getCalibrationXY)
        self.canvas.unbind("<Button-1>")
        self.__disableAll()

    def point1ButtonCallback(self):
        """
        Callback of Point 1 button.
        Used to get calibration point 1
        """        
        self.__caller = 0
        self.getCalibrationPointOnCanvas()
        
    def point2ButtonCallback(self):
        """
        Callback of Point 2 button.
        Used to get calibration point 2
        """           
        self.__caller = 1
        self.getCalibrationPointOnCanvas()

    def point3ButtonCallback(self):
        """
        Callback of Point 2 button.
        Used to get calibration point 2
        """           
        self.__caller = 2
        self.getCalibrationPointOnCanvas()

    def changeStackEvent(self, event):
        """
        Callback of stack number entry
        Used to change the stack when requested
        """ 
        z_temp = int(self.stack_str.get())
        if not self.__changeImageOnCanvas(z_temp, self.t):
            self.stack_str.set(int(self.z))

        if event.type == 2:
            self.focusOnCanvas()

    def changeFrameEvent(self, event):
        """
        Callback of time frame number entry
        Used to change the frame when requested
        """ 
        t_temp = int(self.time_str.get())
        if not self.__changeImageOnCanvas(self.z, t_temp):
            self.time_str.set(int(self.t))

        if event.type == 2:
            self.focusOnCanvas()

    def changeTrackEvent(self, event):
        """
        Callback of track number entry
        Used to go to the first point of a track
        """
        string = self.track_str.get()
        manual = False
        if string[:1].lower() == 'm':
            manual = True
            string = string[1:]
        track_temp = int(string)

        t_ini = self.track.configs[self.track.TIME_INI_KEY]

        if manual:
            if track_temp in self.all_manualtracks: 
                self.show_manualtrack_var.set(1)
                track = self.all_manualtracks[track_temp]
                track_mov = np.zeros((4,len(track)), dtype = np.int32)
                i = 0
                for t in track:
                    track_mov[0,i] = t - t_ini
                    track_mov[1:4, i] = np.asarray(track[t])
                    i+=1

                t_temp = track_mov[0,0] + t_ini
                z_temp = track_mov[3,0]
                if self.__changeImageOnCanvas(z_temp, t_temp):
                    self.track_num = 'M%d'%track_temp
                    self.__track_mov = track_mov
        else:
            if track_temp < len(self.track.id_seq):
                track_mov = np.array(self.track.getWholeMovement(track_temp))
                if track_mov.size > 0:
                    track_mov = np.ceil(track_mov)
                    t_temp = track_mov[0,0] + t_ini
                    z_temp = round(track_mov[3,0])

                    if self.__changeImageOnCanvas(z_temp, t_temp):
                        self.track_num = '%d'%track_temp
                        self.__track_mov = track_mov

        self.track_str.set(self.track_num if self.track_num is not None else "")

        if event.type == 2:
            self.focusOnCanvas()

    def focusOnCanvas(self, event):
        """
        Give focus on canvas when called
        """
        self.canvas.focus()
        self.canvas.focus_set()

    def arrowEvent(self, event):
        """
        Handle the arrow events in the main canvas.
        This is used to navigate in time frame and stack.
        """
        if event.keysym.lower() == 'up':
            z_temp = self.z + 1
            t_temp = self.t
            caller_event = 'stack+1'
        elif event.keysym.lower() == 'down':
            z_temp = self.z - 1
            t_temp = self.t
            caller_event = 'stack-1'
        elif event.keysym.lower() == 'right':
            z_temp = self.z
            t_temp = self.t + 1
            caller_event = 'time+1'
        elif event.keysym.lower() == 'left':                   
            z_temp = self.z
            t_temp = self.t - 1
            caller_event = 'time-1'

        # If following update according to the position of the tracking point
        if self.following and (caller_event[:4]=='time'):
            t_ini = self.track.configs[self.track.TIME_INI_KEY]
            check_time = np.equal(self.__track_mov[0,:], t_temp - t_ini)
            if check_time.sum() > 0:
                z_temp = self.__track_mov[3,check_time][0]
            else:
                print('Not tracked in the next time')
                return None

        # If editing a track, return to the correct stack
        if self.tracking and (caller_event[:4]=='time'):
            if t_temp in self.current_manualtrack:
                z_temp = self.current_manualtrack[t_temp][2]

        self.__changeImageOnCanvas(z_temp, t_temp)

        # If tracking, redraw tracking lines and points
        if self.tracking and (caller_event[:4]=='time'):
            self.deleteHistoryLine()
            self.drawHistoryLine(10)
            shift = int(caller_event[-2:])
            if self.t-shift in self.current_manualtrack_draw:
                self.deleteManualTrackMark(self.current_manualtrack_draw[self.t-shift])

            if self.t in self.current_manualtrack:
                x,y,z = self.current_manualtrack[self.t]
                self.current_manualtrack_draw[self.t] = self.drawManualTrackMark(x, y, z)

def main(*args):
    """
    Main function to run from outside
    """
    if len(args) >= 1:
        date = str(args[0])
    else:   
        date = input("Results date string:")

    folder = "D:\\image_software\\results\\GMEMtracking3D_" + date
    if os.path.exists(folder+"\\eye_check"):
        root = tk.Tk()
        track = TrackingAnalysis(folder)
        window = ManualTrackWindow(root, track)
        root.mainloop()
    else:
        print("Run the file write_eye_check.py first")

    return None

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

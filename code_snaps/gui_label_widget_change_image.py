#!/usr/bin/env python
import tkinter as tk
from PIL import ImageTk, Image
from track_utils import corrTIFPath, TrackingAnalysis

path = "D:\\image_software\\results\\GMEMtracking3D_2015_7_14_12_55_10\\eye_check\\T00016\\Z@@@.png"
root = tk.Tk()

def callback(event):
    global i
    i += 1
    path_aux = corrTIFPath(path,'@',i)
    img2 = ImageTk.PhotoImage(Image.open(path_aux))
    panel.configure(image = img2)
    panel.image = img2

i = 1
path_aux = corrTIFPath(path,'@',i)    
img = ImageTk.PhotoImage(Image.open(path_aux))
panel = tk.Label(root, image = img)
panel.image = img
panel.pack(side = "bottom", fill = "both", expand = "yes")
panel.bind("<Button-1>", callback)

root.mainloop()

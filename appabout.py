from tkinter import *
import config
from languages import _


class About(Frame):
    def __init__(self, master=None):
        super().__init__(master)

    def mainloop(self, **kwargs):
        self.pack()
        self.create_widgets()
        super().mainloop(**kwargs)

    def create_widgets(self):
        self.master.title(_("About"))
        self.master.geometry('300x200+600+200')
        self.master.iconbitmap(config.ICON)

from tkinter import *
import config
from language import _


class AboutDialog:
    def __init__(self, master):
        self.master = master
        self.root = Toplevel()

    def show(self):
        self.root.title(_("About"))
        self.root.geometry('300x200+600+200')
        self.root.iconbitmap(config.ICON)
        self.root.transient()
        self.root.grab_set()
        self.root.focus_set()
        self.master.wait_window(self.root)

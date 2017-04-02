from tkinter import Label, BOTH, Entry, W, Toplevel
from tkinter import ttk
import config


class Dialog(Toplevel):
    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.iconbitmap(config.ICON)
        self.transient()
        self.grab_set()
        self.focus_set()

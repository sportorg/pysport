from tkinter import *
from tkinter import ttk


class StatusBar(ttk.Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        self.pack(side=BOTTOM, fill=X)
        self.label = ttk.Label(self, relief=SUNKEN, anchor=W)
        self.label.pack(fill=X)

    def set(self, format, *args):
        self.label.config(text=format % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


class ToolBar(Frame):
    def __init__(self, master=None):
        super().__init__(master, relief=RAISED)
        self.pack(side=TOP, fill=X)

    def set_button(self, side=LEFT, **kw):
        button = Button(self, kw)
        button.pack(side=side, padx=2, pady=2)

        return button

    def set_label(self, side=LEFT, **kw):
        button = Label(self, kw)
        button.pack(side=side, padx=2, pady=2)

        return button

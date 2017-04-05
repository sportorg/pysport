from tkinter import *
from tkinter import ttk


class StatusBar(ttk.Frame):

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
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
        label = Label(self, kw)
        label.pack(side=side, padx=2, pady=2)

        return label

    def set_image(self, image, side=LEFT, command=None):
        button = Button(self, image=image, command=command, border=0)
        button.image = image
        button.pack(side=side, padx=2, pady=2)
        button.bind("<Enter>", lambda event: button.configure(bg="azure"))
        button.bind("<Leave>", lambda event: button.configure(bg="SystemButtonFace"))

        return button

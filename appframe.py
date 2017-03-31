from tkinter import Label
from tkinter import ttk
import applist
import model


class Sportident(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Sportident")
        text.pack()


class Event(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Event")
        text.pack()


class Course(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Course")
        text.pack()


class Person(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        self.main()

    def main(self):
        text = applist.Person(self)
        text.list()


class Start(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Start")
        text.pack()


class Finish(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Finish")
        text.pack()


class Live(ttk.Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Live")
        text.pack()
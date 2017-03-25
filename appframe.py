from tkinter import *
import applist
import model


class Sportident(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Sportident")
        text.pack()


class Event(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Event")
        text.pack()


class Course(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Course")
        text.pack()


class Person(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        self.main()

    def main(self):
        text = applist.Person(self)
        text.list()


class Start(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Start")
        text.pack()


class Finish(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Finish")
        text.pack()


class Live(Frame):
    def __init__(self, parent=None):
        super().__init__(parent.master)
        self.pack()
        text = Label(self, text="Live")
        text.pack()
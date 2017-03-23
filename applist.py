from tkinter import *
from tkinter import ttk


import table


class Result:
    pass


class Start:
    pass


class Course:
    pass


class Person:
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def list(self):
        person_header = ['Name', 'Team', 'Bib', 'Start', 'Result']
        person_list = []
        for i in range(100):
            person_list.append(['Ахтаров' + str(i), 'Абрис', i, '12:00:' + str(i), i + 5])
        table.ListBox(self.parent, person_header, person_list)


class Event:
    pass

from tkinter import *
from tkinter import ttk
from pandastable import Table
import model


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
        person_header = ['id', 'Family', 'Given']
        persons = model.PersonName.select()
        person_list = []
        for person in persons:
            person_list.append([person.id, person.family, person.given])
        # table.ListBox(self.parent, person_header, person_list)
        pt = Table(self.parent, rows=5, cols=5)
        pt.show()


class Event:
    pass

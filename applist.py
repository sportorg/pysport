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
        person_header = ['id', 'name', 'surname']
        self.t = table.Table(self.parent, person_header, ysb=True, popup=True)

    def list(self):
        persons = model.Person.select()
        self.t.pack(fill=BOTH, expand=True)
        for person in persons:
            self.t.create_row({'id': person.id, 'name': person.name, 'surname': person.surname})
        self.t.register_popup('add', command=self.add)

    def add(self):
        per = model.Person.create(name="name", surname='surname')
        self.t.create_row({'id': per.id, 'name': per.name, 'surname': per.surname})


class Event:
    pass

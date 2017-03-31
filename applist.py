from tkinter import Label, BOTH, Entry, W
from tkinter import ttk
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
        self.t.register_popup('Add', command=self.add)
        self.t.register_popup('Delete', command=self.delete)
        self.t.register_popup('Edit', command=self.edit)

    def add(self):
        per = model.Person.create(name="name", surname='surname')
        self.t.create_row({'id': per.id, 'name': per.name, 'surname': per.surname})

    def delete(self):
        item = self.t.getTree().focus()
        if item:
            id = self.t.getTree().item(item)['values'][0]
            person = model.Person.get(model.Person.id == id)
            person.delete_instance()      
            self.t.getTree().delete(item)

    def edit(self):
        item = self.t.getTree().focus()
        x,y,width,height = self.t.getTree().bbox(item, 'name')
        # y-axis offset
        pady = height // 2
        # place Entry popup properly         
        name = self.t.getTree().item(item, 'text')
        self.entryPopup = Entry(self.t.getTree(), text=name)
        self.entryPopup.place(x=0, y=y+pady, anchor=W, relwidth=1)


class Event:
    pass

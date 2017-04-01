from tkinter import Label, BOTH, Entry, W, Toplevel
from tkinter import ttk
import table
import model
from language import _
import config


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
        person_header = ['id', 'name', 'surname']
        self.t = table.Table(self, person_header, ysb=True, popup=True)
        self.main()

    def main(self):
        self.list()

    def list(self):
        persons = model.Person.select()
        self.t.pack(fill=BOTH, expand=True)
        for person in persons:
            self.t.create_row({'id': person.id, 'name': person.name, 'surname': person.surname})
        self.t.register_popup(_("Add"), command=self.add)
        self.t.register_popup(_("Delete"), command=self.delete)
        self.t.register_popup(_("Edit person"), command=self.edit)
        self.t.register_popup(_("Copy and insert"))

    def get_id(self, item):
        return self.t.getTree().item(item)['values'][0]

    def add(self):
        per = model.Person.create(name="", surname='')
        self.t.create_row({'id': per.id, 'name': per.name, 'surname': per.surname})

    def delete(self):
        item = self.t.getTree().focus()
        if item:
            id = self.get_id(item)
            person = model.Person.get(model.Person.id == id)
            person.delete_instance()
            self.t.getTree().delete(item)

    def edit(self):
        item = self.t.getTree().focus()
        if item:
            id = self.get_id(item)
            self.edit_modal(id)

    def edit_modal(self, person_id):
        root = Toplevel()
        root.title(_("Edit person ") + str(person_id))
        root.geometry('500x300+600+200')
        root.iconbitmap(config.ICON)
        root.transient()
        root.grab_set()
        root.focus_set()
        self.wait_window(root)


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
from tkinter import Label, BOTH
from tkinter import ttk
from so_gui import table
from models import model
from so_widget import dialog
from language import _


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
        self.parent = parent
        person_header = ["id", "name", "surname", "team", "year", "qual"]
        self.t = table.Table(self, person_header, ysb=True, popup=True)
        self._main()

    def _main(self):
        self.t.get_tree().bind("<Control-i>", lambda event: self.add())
        self.t.get_tree().bind("<Delete>", lambda event: self.delete())
        self.t.bind_open(lambda event: self.edit())
        self.list()

    def list(self):
        persons = model.Person.select()
        self.t.pack(fill=BOTH, expand=True)
        for person in persons:
            self.t.create_row({
                'id': person.id,
                'name': person.name,
                'surname': person.surname,
                'team': person.team.name if person.team is not None else '',
                'year': person.year,
                'qual': person.qual
            })
        self.t.register_popup(_("Add"), command=self.add, accelerator="Ctrl+I")
        self.t.register_popup(_("Edit person"), command=self.edit)
        self.t.register_popup(_("Copy and insert"))
        self.t.register_popup(_("Delete") + " Del", command=self.delete)

    def get_id(self, item):
        return self.t.get_tree().item(item)['values'][0]

    def add(self):
        self.edit_modal()

    def delete(self):
        item = self.t.get_tree().focus()
        if item:
            person_id = self.get_id(item)
            person = model.Person.get(model.Person.id == person_id)
            person.delete_instance()
            next_item = self.t.get_tree().next(item)
            self.t.get_tree().focus(next_item)
            self.t.get_tree().see(next_item)
            self.t.get_tree().delete(item)

    def edit(self):
        item = self.t.get_tree().focus()
        if item:
            id = self.get_id(item)
            self.edit_modal(id)

    def edit_modal(self, person_id=None):
        if person_id is None:
            title = _("Add person")
        else:
            title = _("Edit person ") + str(person_id)

        root = dialog.Dialog(self)
        root.title(title)
        ttk.Label(root, text=_("Name")).grid(row=0)
        ttk.Label(root, text=_("Surname")).grid(row=1)
        ttk.Label(root, text=_("Birthday")).grid(row=2)
        ttk.Label(root, text=_("Team")).grid(row=3)

        name = ttk.Entry(root)
        surname = ttk.Entry(root)
        birth_date = ttk.Entry(root)
        team = ttk.Entry(root)

        name.grid(row=0, column=1, padx=5, pady=5)
        name.focus_set()
        surname.grid(row=1, column=1, padx=5, pady=5)
        birth_date.grid(row=2, column=1, padx=5, pady=5)
        team.grid(row=3, column=1, padx=5, pady=5)

        if person_id is not None:
            per = model.Person.get(model.Person.id == person_id)
            name.insert(0, per.name)
            surname.insert(0, per.surname)

        def ok():
            if person_id is None:
                person = model.Person.create(name=name.get(), surname=surname.get())
                self.t.create_row({'id': person.id, 'name': person.name, 'surname': person.surname})
            else:
                person = model.Person.get(model.Person.id == person_id)
                person.name = name.get()
                person.surname = surname.get()
                person.save()
                self.t.update_row({"name": name.get(), "surname": surname.get()}, id=person_id)
            root.option_clear()
            root.destroy()

        root.bind("<Return>", lambda event: ok())
        root.bind("<Escape>", lambda event: root.destroy())
        ok_button = ttk.Button(root, text="ok", command=ok)
        ok_button.grid(row=7, column=2)
        cancel_button = ttk.Button(root, text="cancel", command=root.destroy)
        cancel_button.grid(row=7, column=3)

        root.resizable(False, False)
        root.center()
        root.show()
        # root.bind("<Enter>", ok)

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

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

import configparser

import model
from bar import StatusBar, ToolBar
from appabout import About
import appframe
import config
from language import _, get_languages, locale_current
import sportident
from apptime import Clock


class App(ttk.Frame):
    def __init__(self, master=None, file=None):
        """
        :param master:
        :type master: Tk
        :param file: Путь к файлу
        :type file: str
        """
        super().__init__(master)
        self.conf = configparser.ConfigParser()
        self.db = model.database_proxy
        self.file = file
        self.menubar = None
        self.toolbar = None
        self.nb = None
        self.current_tab = 0
        self.status = None

        self.create_db()
        self.pack()
        self._widget()
        self._menu()
        self._status_bar()
        self._toolbar()
        self._main_frame()
        self.set_bind()

        self.si_read = sportident.SIRead(self)

    def mainloop(self, **kwargs):
        super().mainloop(**kwargs)

    def _widget(self):
        """
        Конфигурация главного окна
        """
        self.conf.read(config.CONFIG_INI)
        geometry = self.conf.get('geometry', 'geometry', fallback='500x380+0+0')

        self.set_title(self.file)
        self.master.geometry(geometry)
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        self.master.iconbitmap(config.ICON)

    def set_title(self, text=None):
        app_name = _(config.NAME)
        if text is None:
            self.master.title(app_name + ' ' + config.__version__)
            return
        self.master.title("{} - {} {}".format(text, app_name, config.__version__))

    def _menu(self):
        self.menubar = Menu(self.master)

        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label=_("New") + "...", command=self.new_file)
        filemenu.add_command(label=_("New Event") + "...", command=self.new_event)
        filemenu.add_command(label=_("Open") + "...", command=self.open)
        filemenu.add_command(label=_("Save As") + "..", command=self.save_as)
        filemenu.add_command(label=_("Open Recent"))
        filemenu.add_separator()
        filemenu.add_command(label=_("Settings") + "...")
        filemenu.add_command(label=_("Settings Event") + "...")
        filemenu.add_separator()
        filemenu.add_command(label=_("Import"))
        filemenu.add_command(label=_("Export"))
        filemenu.add_separator()
        filemenu.add_command(label=_("Exit"), command=self.close)
        self.menubar.add_cascade(label=_("File"), menu=filemenu)

        editmenu = Menu(self.menubar, tearoff=0)
        editmenu.add_command(label=_("Undo"))
        editmenu.add_command(label=_("Redo"))
        self.menubar.add_cascade(label=_("Edit"), menu=editmenu)

        viewmenu = Menu(self.menubar, tearoff=0)
        viewmenu.add_command(label=_("Start list"))
        self.menubar.add_cascade(label=_("View"), menu=viewmenu)

        toolsmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Tools"), menu=toolsmenu)

        servicesmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Service"), menu=servicesmenu)

        optionsmenu = Menu(self.menubar, tearoff=0)
        lang_menu = Menu(self.menubar, tearoff=0)
        for lang in get_languages():
            lang_menu.add_command(label=_(lang), command=lambda l=lang: self.set_locale(l))
        optionsmenu.add_cascade(label=_("Languages"), menu=lang_menu)
        self.menubar.add_cascade(label=_("Options"), menu=optionsmenu)

        helpmenu = Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label=_("Help"))
        helpmenu.add_command(label=_("About"), command=self.about)
        self.menubar.add_cascade(label=_("Help"), menu=helpmenu)

        self.master.config(menu=self.menubar)

    def _toolbar(self):
        self.toolbar = ToolBar(self.master)
        self.toolbar.set_button(text="<", relief=FLAT, command=self.close)
        self.siread_button = self.toolbar.set_button(text="si", relief=FLAT, bg='red', command=self.si_read_run)
        self.refresh_button = self.toolbar.set_button(text='update', command=self.refresh)
        clock_toolbar = self.toolbar.set_label(side=RIGHT)
        # clock = Clock(clock_toolbar)
        # clock.start()

    def _main_frame(self):
        # self.main_frame = Frame(self.master)
        # self.main_frame.pack(fill=X)

        self.nb = ttk.Notebook(self.master)
        self.nb.pack(fill='both', expand=True)

        self.nb.add(appframe.Sportident(self), text=_("Sportident"))
        self.nb.add(appframe.Event(self), text=_("Event"))
        self.nb.add(appframe.Course(self), text=_("Course"))
        self.nb.add(appframe.Person(self), text=_("Person"))
        self.nb.add(appframe.Start(self), text=_("Start list"))
        self.nb.add(appframe.Finish(self), text=_("Finish list"))
        self.nb.add(appframe.Live(self), text=_("Live"))
        self.nb.select(self.current_tab)

    def _status_bar(self):
        """
        Инициализация статус бара
        """
        self.status = StatusBar(self.master)
        self.status.set("%s", _("Working"))

    def set_bind(self):
        self.master.bind('<Control-n>', self.new_file)
        self.master.bind('<Control-o>', self.open)
        self.master.bind('<<NotebookTabChanged>>', self.set_tab)

    def set_tab(self, event=None):
        self.current_tab = self.nb.index(self.nb.select())

    def close(self):
        try:
            self.conf['geometry'] = {}
            self.conf.set('geometry', 'geometry', self.master.winfo_geometry())
            with open(config.CONFIG_INI, 'w') as configfile:
                self.conf.write(configfile)
        finally:
            self.master.quit()

    def set_locale(self, locale):
        try:
            self.conf['locale'] = {}
            self.conf.set('locale', 'current', locale)
        except configparser.Error:
            self.master.quit()

    def _set_file(self, file):
        if file is None:
            return False
        if not len(file):
            return False
        self.set_title(file)
        self.file = file
        self.create_db()
        self.refresh()
        return True

    def new_file(self, event=None):
        file = filedialog.asksaveasfilename()
        return self._set_file(file)

    def new_event(self):
        pass

    def open(self, event=None):
        file = filedialog.askopenfilename()
        return self._set_file(file)

    def save_as(self):
        pass

    @staticmethod
    def about():
        root = Tk()
        about = About(root)
        about.mainloop()

    def si_read_run(self):
        if self.si_read.is_running:
            self.siread_button['bg'] = 'red'
            self.si_read.is_running = False
        else:
            self.siread_button['bg'] = 'green'
            self.si_read.is_running = True

    def refresh(self):
        if self.nb is None:
            return
        self.nb.destroy()
        self._main_frame()

    def create_file(self):
        file = filedialog.asksaveasfilename(defaultextension=".sportorg")
        if not len(file):
            return False
        self.file = file
        return True

    def create_db(self):
        if self.file is None:
            database = model.SqliteDatabase(":memory:")
        else:
            database = model.SqliteDatabase(self.file)
        self.db.initialize(database)
        self.db.connect()
        self.db.create_tables([
            model.Event,
            model.Person,
            model.Extensions,
            model.ControlCard,
            model.CourseControl,
            model.Course,
            model.EventStatus,
            model.ResultStatus,
            model.Country,
            model.Contact,
            model.Address,
            model.Start,
            model.SplitTime,
            model.Result
        ], safe=True)

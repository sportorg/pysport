from tkinter import *
from tkinter import ttk
import configparser

from model import *
from bar import StatusBar, ToolBar
from appabout import About
import appframe
import config
from languages import _, get_languages, locale_current
import sportident
from apptime import Clock


class App(Frame):
    def __init__(self, master=None, file=None):
        super().__init__(master)
        self.conf = configparser.ConfigParser()
        self.file = file

        self.pack()
        self._widget()
        self._menu()
        self._toolbar()
        self._status_bar()
        self._main_frame()

        self.si_read = sportident.SIRead(self)

    def mainloop(self, **kwargs):
        super().mainloop(**kwargs)

    def _widget(self):
        """
        Конфигурация главного окна
        """
        self.conf.read(config.CONFIG_INI)
        geometry = self.conf.get('geometry', 'geometry', fallback='500x380+0+0')

        self.master.title(_(config.NAME))
        self.master.geometry(geometry)
        self.master.protocol('WM_DELETE_WINDOW', self.close)
        self.master.iconbitmap(config.ICON)

    def _menu(self):
        menubar = Menu(self.master)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label=_("New"))
        filemenu.add_command(label=_("Save"))
        filemenu.add_command(label=_("Save As"))
        filemenu.add_separator()
        filemenu.add_command(label=_("Exit"), command=self.close)
        menubar.add_cascade(label=_("File"), menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label=_("Undo"))
        editmenu.add_command(label=_("Redo"))
        menubar.add_cascade(label=_("Edit"), menu=editmenu)

        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label=_("Start list"))
        menubar.add_cascade(label=_("View"), menu=viewmenu)

        toolsmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Tools"), menu=toolsmenu)

        servicesmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_("Service"), menu=servicesmenu)

        optionsmenu = Menu(menubar, tearoff=0)
        lang_menu = Menu(menubar, tearoff=0)
        for lang in get_languages():
            lang_menu.add_command(label=_(lang), command=lambda l=lang: self.set_locale(l))
        optionsmenu.add_cascade(label=_("Languages"), menu=lang_menu)
        menubar.add_cascade(label=_("Options"), menu=optionsmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label=_("Help"))
        helpmenu.add_command(label=_("About"), command=self.about)
        menubar.add_cascade(label=_("Help"), menu=helpmenu)

        self.master.config(menu=menubar)

    def _toolbar(self):
        toolbar = ToolBar(self.master)
        toolbar.set_button(text="<", relief=FLAT, command=self.close)
        self.siread_button = toolbar.set_button(text="si", relief=FLAT, bg='red', command=self.si_read_run)
        clock_toolbar = toolbar.set_label(side=RIGHT)
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

    def _status_bar(self):
        """
        Инициализация статус бара
        """
        self.status = StatusBar(self.master)
        self.status.set("%s", _("Working"))

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

    def create_db(self):
        pass
        # db.connect()
        # db.create_tables([
        #     Event,
        #     Person,
        #     Extensions,
        #     ControlCard,
        #     CourseControl,
        #     Course,
        #     EventStatus,
        #     ResultStatus,
        #     Country,
        #     Contact,
        #     Address,
        #     PersonName,
        #     Start,
        #     SplitTime,
        #     Result
        # ], safe=True)

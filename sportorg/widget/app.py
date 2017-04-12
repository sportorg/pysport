from tkinter import *
from tkinter import ttk
from tkinter import filedialog, messagebox

import configparser

from sportorg.models import model
from sportorg.ttk.bar import StatusBar, ToolBar
from sportorg.widget import frame
from sportorg.widget import dialog
import config
from sportorg.language import _, get_languages

from sportorg.so_import.winorient.csv_import import WinOrientCSV
from sportorg.so_import.winorient.wdb_import import WinOrientBinary


class App(ttk.Frame):
    def __init__(self, master=None, file=None):
        """
        :type master: Tk
        :type file: str
        """
        super().__init__(master)
        self.conf = configparser.ConfigParser()
        self.db = model.database_proxy
        self.file = file
        self.menubar = None
        self.toolbar = None
        self.nb = None
        self.current_tab = 3
        self.status = None

    def mainloop(self, **kwargs):
        self.initialize_db()
        self.create_db()
        self.pack()
        self._widget()
        self._menu()
        self._status_bar()
        self._toolbar()
        self._main_frame()
        self.set_bind()
        super().mainloop(**kwargs)

    def _widget(self):
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
        if self.menubar is not None:
            self.menubar.destroy()
        self.menubar = Menu(self.master)

        filemenu = Menu(self.menubar, tearoff=0)
        filemenu.add_command(label=_("New") + "...", command=self.new_file, accelerator="Ctrl+N")
        filemenu.add_command(label=_("New Race") + "...", command=self.new_event)
        filemenu.add_command(label=_("Open") + "...", command=self.open, accelerator="Ctrl+O")
        filemenu.add_command(label=_("Save"), command=self.save)
        filemenu.add_command(label=_("Save As") + "..", command=self.save_as)
        filemenu.add_command(label=_("Open Recent"))
        filemenu.add_separator()
        filemenu.add_command(label=_("Settings") + "...")
        filemenu.add_command(label=_("Settings Event") + "...")
        filemenu.add_separator()
        import_menu = Menu(self.menubar, tearoff=0)
        import_menu.add_command(label=_("WinOrient CSV"), command=self.import_csv)
        import_menu.add_command(label=_("WinOrient WDB"), command=self.import_wdb)
        filemenu.add_cascade(label=_("Import"), menu=import_menu)
        filemenu.add_command(label=_("Export"))
        filemenu.add_separator()
        filemenu.add_command(label=_("Exit"), command=self.close)
        self.menubar.add_cascade(label=_("File"), menu=filemenu)

        editmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=_("Edit"), menu=editmenu)

        viewmenu = Menu(self.menubar, tearoff=0)
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
        helpmenu.add_command(label=_("About"), command=self.about, accelerator="F2")
        self.menubar.add_cascade(label=_("Help"), menu=helpmenu)

        self.master.config(menu=self.menubar)

    def _toolbar(self):
        if self.toolbar is not None:
            self.toolbar.destroy()
        self.toolbar = ToolBar(self.master)
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("file.png")), command=self.new_file)
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("save.png")), command=self.save)
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("folder.png")), command=self.open)
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("print.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("csv.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("doc.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("html.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("pdf.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("sportident.png")))
        self.toolbar.set_image(PhotoImage(file=config.icon_dir("refresh.png")), command=self.refresh)

    def _main_frame(self):
        if self.nb is not None:
            self.nb.destroy()
        self.nb = ttk.Notebook(self.master)
        self.nb.pack(fill='both', expand=True)

        self.nb.add(frame.Sportident(self), text=_("Sportident"))
        self.nb.add(frame.Event(self), text=_("Event"))
        self.nb.add(frame.Course(self), text=_("Course"))
        self.nb.add(frame.Person(self), text=_("Person"))
        self.nb.add(frame.Start(self), text=_("Start list"))
        self.nb.add(frame.Finish(self), text=_("Finish list"))
        self.nb.add(frame.Live(self), text=_("Live"))
        self.nb.select(self.current_tab)

    def _status_bar(self):
        if self.status is not None:
            self.status.destroy()
        self.status = StatusBar(self.master)
        self.status.set("%s", _("Working"))

    def set_bind(self):
        self.master.bind('<Control-n>', lambda event: self.new_file())
        self.master.bind('<Control-o>', lambda event: self.open())
        self.master.bind('<<NotebookTabChanged>>', lambda event: self.set_tab())
        self.master.bind('<F2>', lambda event: self.about())

    def set_tab(self):
        self.current_tab = self.nb.index(self.nb.select())

    def close(self):
        try:
            self.conf['geometry'] = {}
            self.conf.set('geometry', 'geometry', "{}x{}+{}+{}".format(
                self.master.winfo_width(),
                self.master.winfo_height()+20,
                self.master.winfo_x(),
                self.master.winfo_y(),
            ))
            with open(config.CONFIG_INI, 'w') as configfile:
                self.conf.write(configfile)
        finally:
            self.master.quit()

    def set_locale(self, loc):
        try:
            self.conf['locale'] = {}
            self.conf.set('locale', 'current', loc)
            self.status.set("%s", _("Do refresh"))
        except configparser.Error:
            self.master.quit()

    def new_file(self):
        is_create = self.create_file()
        if is_create:
            self.set_title(self.file)
            self.initialize_db()
            self.create_db()
            self.refresh()

    def new_event(self):
        pass

    def open(self):
        is_open = self.open_file()
        if is_open:
            self.set_title(self.file)
            self.initialize_db()
            self.refresh()

    def save(self):
        if self.file is not None:
            messagebox.showinfo(_("Info"), _("Don`t worry, file already exist"))
            return
        is_create = self.create_file()
        if is_create:
            pass

    def save_as(self):
        pass

    def about(self):
        about = dialog.Dialog()
        about.overrideredirect(1)
        about.title(_("About"))
        about.geometry("500x300+600+200")
        about.center()
        close = Button(about, text=_("Ok"), command=lambda: about.destroy(), border=1, pady=2)
        close.pack(side=BOTTOM, fill=X)
        about.show()
        self.wait_window(about)

    def refresh(self):
        print('refresh')
        self._menu()
        self._toolbar()
        self._status_bar()
        self._main_frame()

    def create_file(self):
        ftypes = [(config.NAME + ' files', '*.sportorg'), ('SQLITE', '*.sqlite')]
        file = filedialog.asksaveasfilename(defaultextension=".sportorg", filetypes=ftypes)
        if not len(file):
            return False
        self.file = file
        return True

    def open_file(self):
        ftypes = [(config.NAME + ' files', '*.sportorg'), ('SQLITE', '*.sqlite'), ('All files', '*')]
        file = filedialog.askopenfilename(filetypes=ftypes)
        if not len(file):
            return False
        self.file = file
        return True

    def import_csv(self):
        ftypes = [('Winorient csv file', '*.csv'), ('All files', '*')]
        file = filedialog.askopenfilename(filetypes=ftypes)
        if not len(file):
            return
        wo_csv = WinOrientCSV(file=file)
        wo_csv.run()
        if wo_csv.is_complete:
            self.refresh()

    def import_wdb(self):
        ftypes = [('Winorient file', '*.wdb'), ('All files', '*')]
        file = filedialog.askopenfilename(filetypes=ftypes)
        if not len(file):
            return
        wo_bin_import = WinOrientBinary(file=file)
        wo_bin_import.run()
        if wo_bin_import.is_complete:
            self.refresh()

    def initialize_db(self):
        if self.file is None:
            database = model.SqliteDatabase(":memory:")
        else:
            database = model.SqliteDatabase(self.file)
        self.db.initialize(database)
        self.db.connect()

    def create_db(self):
        with self.db.atomic():
            self.db.create_tables([
                model.Qualification,
                model.Fee,
                model.RelayTeam,
                model.RaceStatus,
                model.Race,
                model.Course,
                model.CoursePart,
                model.CourseControl,
                model.ResultStatus,
                model.Country,
                model.Contact,
                model.Address,
                model.Organization,
                model.Person,
                model.Entry,
                model.ControlCard,
                model.Group,
                model.Participation,
                model.Result,
                model.RelayTeamLeg,
                model.LegCoursePart,
                model.OnlineControlTime
            ], safe=True)

import logging
import webbrowser

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QPushButton,
        QTabWidget,
        QWidget,
        QHBoxLayout,
        QCommandLinkButton,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QPushButton,
        QTabWidget,
        QWidget,
        QHBoxLayout,
        QCommandLinkButton,
    )

from sportorg import config
from sportorg.common.audio import get_sounds
from sportorg.common.template import get_templates
from sportorg.gui.dialogs.file_dialog import get_existing_directory
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox, AdvSpinBox
from sportorg.language import get_languages, translate
from sportorg.models.memory import (
    add_race,
    copy_race,
    del_race,
    get_current_race_index,
    move_down_race,
    move_up_race,
    races,
    set_current_race_index,
)
from sportorg.modules.configs.configs import Config


class Tab:
    def save(self):
        pass


class MainTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.widget.setLayout(self.layout)

        self.label_lang = QLabel(translate("Languages"))
        self.item_lang = AdvComboBox()
        self.item_lang.addItems(get_languages())
        self.item_lang.setCurrentText(
            Config().configuration.get("current_locale", "ru_RU")
        )
        self.layout.addRow(self.label_lang, self.item_lang)

        self.item_auto_save = AdvSpinBox(
            maximum=3600 * 24, value=Config().configuration.get("autosave_interval")
        )
        self.item_auto_save.setMinimum(5)
        self.layout.addRow(translate("Auto save") + " (sec)", self.item_auto_save)

        self.item_show_toolbar = QCheckBox(translate("Show toolbar"))
        self.item_show_toolbar.setChecked(Config().configuration.get("show_toolbar"))
        self.layout.addRow(self.item_show_toolbar)

        self.item_open_recent_file = QCheckBox(translate("Open recent file"))
        self.item_open_recent_file.setChecked(
            Config().configuration.get("open_recent_file")
        )
        self.layout.addRow(self.item_open_recent_file)

        self.item_use_birthday = QCheckBox(translate("Use birthday"))
        self.item_use_birthday.setChecked(Config().configuration.get("use_birthday"))
        self.layout.addRow(self.item_use_birthday)

        self.item_check_updates = QCheckBox(translate("Check updates"))
        self.item_check_updates.setChecked(Config().configuration.get("check_updates"))
        # self.layout.addRow(self.item_check_updates)

        self.item_save_in_utf8 = QCheckBox(translate("Save in UTF-8 encoding"))
        self.item_save_in_utf8.setChecked(
            Config().configuration.get("save_in_utf8", False)
        )
        self.layout.addRow(self.item_save_in_utf8)

        self.item_save_in_gzip = QCheckBox(translate("Compress files to gzip"))
        self.item_save_in_gzip.setChecked(
            Config().configuration.get("save_in_gzip", False)
        )
        self.layout.addRow(self.item_save_in_gzip)

    def save(self):
        Config().configuration.set("current_locale", self.item_lang.currentText())
        Config().configuration.set("autosave_interval", self.item_auto_save.value())
        Config().configuration.set(
            "open_recent_file", self.item_open_recent_file.isChecked()
        )

        if (
            bool(Config().configuration.get("show_toolbar"))
            != self.item_show_toolbar.isChecked()
        ):
            if self.item_show_toolbar.isChecked():
                mw = GlobalAccess().get_main_window()
                if hasattr(mw, "toolbar"):
                    mw.toolbar.show()
                else:
                    mw._setup_toolbar()
            else:
                mw = GlobalAccess().get_main_window()
                mw.toolbar.hide()
        Config().configuration.set("show_toolbar", self.item_show_toolbar.isChecked())
        Config().configuration.set("use_birthday", self.item_use_birthday.isChecked())
        Config().configuration.set("check_updates", self.item_check_updates.isChecked())
        Config().configuration.set("save_in_utf8", self.item_save_in_utf8.isChecked())
        Config().configuration.set("save_in_gzip", self.item_save_in_gzip.isChecked())


class SoundTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.widget.setLayout(self.layout)

        self.sounds = get_sounds()

        self.item_enabled = QCheckBox(translate("Enabled"))
        self.item_enabled.setChecked(Config().sound.get("enabled"))
        self.layout.addRow(self.item_enabled)

        self.label_successful = QLabel(translate("Successful result"))
        self.item_successful = AdvComboBox()
        self.item_successful.addItems(self.sounds)
        self.item_successful.setCurrentText(
            Config().sound.get("successful") or config.sound_dir("ok.wav")
        )
        self.layout.addRow(self.label_successful, self.item_successful)

        self.label_unsuccessful = QLabel(translate("Unsuccessful result"))
        self.item_unsuccessful = AdvComboBox()
        self.item_unsuccessful.addItems(self.sounds)
        self.item_unsuccessful.setCurrentText(
            Config().sound.get("unsuccessful") or config.sound_dir("failure.wav")
        )
        self.layout.addRow(self.label_unsuccessful, self.item_unsuccessful)

        self.item_enabled_rented_card = QCheckBox(translate("Enable rented card sound"))
        self.item_enabled_rented_card.setChecked(
            Config().sound.get("enabled_rented_card", Config().sound.get("enabled"))
        )
        self.layout.addRow(self.item_enabled_rented_card)

        self.label_rented_card = QLabel(translate("Rented card sound"))
        self.item_rented_card = AdvComboBox()
        self.item_rented_card.addItems(self.sounds)
        self.item_rented_card.setCurrentText(
            Config().sound.get("rented_card") or config.sound_dir("rented_card.wav")
        )
        self.layout.addRow(self.label_rented_card, self.item_rented_card)

        self.label_enter_number = QLabel(translate("Enter number sound"))
        self.item_enter_number = AdvComboBox()
        self.item_enter_number.addItems(self.sounds)
        self.item_enter_number.setCurrentText(
            Config().sound.get("enter_number") or config.sound_dir("enter_number.wav")
        )
        self.layout.addRow(self.label_enter_number, self.item_enter_number)

    def save(self):
        Config().sound.set("enabled", self.item_enabled.isChecked())
        Config().sound.set("successful", self.item_successful.currentText())
        Config().sound.set("unsuccessful", self.item_unsuccessful.currentText())
        Config().sound.set(
            "enabled_rented_card", self.item_enabled_rented_card.isChecked()
        )
        Config().sound.set("rented_card", self.item_rented_card.currentText())
        Config().sound.set("enter_number", self.item_enter_number.currentText())


class MultidayTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.buttons_layout = QHBoxLayout()
        self.button_container = QWidget()
        self.button_container.setLayout(self.buttons_layout)

        self.widget.setLayout(self.layout)

        self.item_races = AdvComboBox()
        self.fill_race_list()

        def select_race():
            index = self.item_races.currentIndex()
            set_current_race_index(index)
            GlobalAccess().get_main_window().init_model()
            GlobalAccess().get_main_window().set_title()

        self.item_races.currentIndexChanged.connect(select_race)
        self.layout.addRow(self.item_races)

        def add_race_function():
            add_race()
            self.fill_race_list()

        self.item_new = QPushButton(translate("New"))
        self.item_new.clicked.connect(add_race_function)
        self.buttons_layout.addWidget(self.item_new)

        def copy_race_function():
            copy_race()
            self.fill_race_list()

        self.item_copy = QPushButton(translate("Copy"))
        self.item_copy.clicked.connect(copy_race_function)
        self.buttons_layout.addWidget(self.item_copy)

        def move_up_race_function():
            move_up_race()
            self.fill_race_list()

        self.item_move_up = QPushButton(translate("Move up"))
        self.item_move_up.clicked.connect(move_up_race_function)
        self.buttons_layout.addWidget(self.item_move_up)

        def move_down_race_function():
            move_down_race()
            self.fill_race_list()

        self.item_move_down = QPushButton(translate("Move down"))
        self.item_move_down.clicked.connect(move_down_race_function)
        self.buttons_layout.addWidget(self.item_move_down)

        def del_race_function():
            del_race()
            self.fill_race_list()

        self.item_del = QPushButton(translate("Delete"))
        self.item_del.clicked.connect(del_race_function)
        self.buttons_layout.addWidget(self.item_del)

        self.layout.addRow(self.button_container)

    def save(self):
        pass

    def fill_race_list(self):
        race_list = []
        index = get_current_race_index()

        self.item_races.clear()
        for cur_race in races():
            race_list.append(str(cur_race.data.get_start_datetime()))
        self.item_races.addItems(race_list)

        self.item_races.setCurrentIndex(index)


class TemplateTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.widget.setLayout(self.layout)

        self.item_download_description = QLabel()
        self.item_download_description.setText(
            translate(
                "Download the zipped templates file — Source code (zip/tar.gz),\nthen unzip it and choose your locale"
            )
        )
        self.layout.addRow(self.item_download_description)

        self.item_download = QCommandLinkButton(translate("Download templates"))

        def open_templates_page() -> None:
            webbrowser.open("https://github.com/sportorg/templates/releases", new=2)

        self.item_download.clicked.connect(open_templates_page)
        self.layout.addRow(self.item_download)

        self.item_custom_dir = QPushButton(translate("Select the templates directory"))

        def select_custom_dir() -> None:
            dirpath = get_existing_directory(
                translate("Open the templates directory"), config.template_dir()
            )
            if not dirpath:
                return

            self.item_custom_dirpath.setText(dirpath)
            Config().templates.set("directory", dirpath)
            config.set_template_dir(dirpath)
            self.item_template.clear()
            self.item_template.addItems(
                sorted(get_templates(config.template_dir("reports")))
            )

        self.item_custom_dir.clicked.connect(select_custom_dir)
        self.layout.addRow(self.item_custom_dir)

        self.item_custom_dirpath = QLabel()
        self.item_custom_dirpath.setText(config.template_dir())
        self.layout.addRow(self.item_custom_dirpath)

    def save(self):
        pass


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.widgets = [
            (MainTab(self), translate("Main settings")),
            (SoundTab(self), translate("Sounds")),
            (MultidayTab(self), translate("Multi day")),
            (TemplateTab(self), translate("Templates directory")),
        ]

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Settings"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        for tab, title in self.widgets:
            self.tab_widget.addTab(tab.widget, title)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        for tab, _ in self.widgets:
            tab.save()
        Config().save()

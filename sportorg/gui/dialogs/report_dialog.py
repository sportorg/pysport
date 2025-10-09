import codecs
import logging
import os
import webbrowser

from docxtpl import DocxTemplate

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QPushButton,
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
    )

from sportorg import config, settings
from sportorg.common.template import get_templates, get_text_from_file
from sportorg.gui.dialogs.file_dialog import (
    get_open_file_name,
    get_save_file_name,
)
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.constant import RentCards
from sportorg.models.memory import get_current_race_index, race, races
from sportorg.models.result.result_tools import recalculate_results

_settings = {
    "last_template": None,
    "open_in_browser": True,
    "last_file": None,
    "save_to_last_file": False,
    "selected": False,
}


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Report creating"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_template = QLabel(translate("Template"))
        self.item_template = AdvComboBox(min_width=250, min_context_length_symbols=60)
        self.item_template.addItems(
            sorted(get_templates(settings.template_dir("reports")))
        )
        self.layout.addRow(self.label_template, self.item_template)
        if _settings["last_template"]:
            self.item_template.setCurrentText(_settings["last_template"])

        self.item_custom_path = QPushButton(translate("Choose template"))

        def select_custom_path() -> None:
            file_name = get_open_file_name(
                translate("Open HTML template"), translate("HTML file (*.html)")
            )
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        self.item_open_in_browser = QCheckBox(translate("Open in browser"))
        self.item_open_in_browser.setChecked(_settings["open_in_browser"])
        self.layout.addRow(self.item_open_in_browser)

        self.item_save_to_last_file = QCheckBox(translate("Save to last file"))
        self.item_save_to_last_file.setChecked(_settings["save_to_last_file"])
        self.layout.addRow(self.item_save_to_last_file)
        if _settings["last_file"] is None:
            self.item_save_to_last_file.setDisabled(True)

        self.item_selected = QCheckBox(translate("Send selected"))
        self.item_selected.setChecked(_settings["selected"])
        self.layout.addRow(self.item_selected)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except FileNotFoundError as e:
                logging.error(str(e))
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
        self.button_ok.setFocus()

    def apply_changes_impl(self):
        obj = race()
        mw = GlobalAccess().get_main_window()

        template_path = self.item_template.currentText()

        _settings["last_template"] = template_path
        _settings["open_in_browser"] = self.item_open_in_browser.isChecked()
        _settings["save_to_last_file"] = self.item_save_to_last_file.isChecked()
        _settings["selected"] = self.item_selected.isChecked()

        recalculate_results(recheck_results=False)

        races_dict = []
        if _settings["selected"]:
            if mw.current_tab == 0:
                person_list = []
                for i in mw.get_selected_rows():
                    person_list.append(obj.persons[i])
                races_dict = [
                    r.to_dict_partial(
                        person_list=person_list,
                        result_list=[],
                        group_list=[],
                        orgs_list=[],
                        course_list=[],
                    )
                    for r in races()
                ]
            elif mw.current_tab == 1:
                result_list = []
                for i in mw.get_selected_rows():
                    result_list.append(obj.results[i])
                races_dict = [
                    r.to_dict_partial(
                        person_list=[],
                        result_list=result_list,
                        group_list=[],
                        orgs_list=[],
                        course_list=[],
                    )
                    for r in races()
                ]
            elif mw.current_tab == 2:
                group_list = []
                for i in mw.get_selected_rows():
                    group_list.append(obj.groups[i].name)
                races_dict = [
                    r.to_dict_partial(
                        person_list=[],
                        result_list=[],
                        group_list=group_list,
                        orgs_list=[],
                        course_list=[],
                    )
                    for r in races()
                ]
            elif mw.current_tab == 3:
                course_list = []
                for i in mw.get_selected_rows():
                    course_list.append(obj.courses[i])
                races_dict = [
                    r.to_dict_partial(
                        person_list=[],
                        result_list=[],
                        group_list=[],
                        orgs_list=[],
                        course_list=course_list,
                    )
                    for r in races()
                ]
            elif mw.current_tab == 4:
                orgs_list = []
                for i in mw.get_selected_rows():
                    orgs_list.append(obj.organizations[i])
                races_dict = [
                    r.to_dict_partial(
                        person_list=[],
                        result_list=[],
                        group_list=[],
                        orgs_list=orgs_list,
                        course_list=[],
                    )
                    for r in races()
                ]
        else:
            races_dict = [r.to_dict() for r in races()]

        # Remove sensitive data
        for race_data in races_dict:
            if race_data:
                race_data["settings"].pop("live_urls", None)

        template_path_items = template_path.split("/")[-1]
        template_path_items = ".".join(template_path_items.split(".")[:-1]).split("_")

        # remove tokens, containing only digits
        for i in template_path_items:
            if str(i).isdigit():
                template_path_items.remove(i)
        report_suffix = "_".join(template_path_items)

        if template_path.endswith(".docx"):
            # DOCX template processing
            full_path = settings.template_dir() + template_path
            doc = DocxTemplate(full_path)
            context = {}
            context["race"] = races_dict[get_current_race_index()]
            context["name"] = config.NAME
            context["version"] = str(config.VERSION)
            doc.render(context)

            if _settings["save_to_last_file"]:
                file_name = _settings["last_file"]
            else:
                file_name = get_save_file_name(
                    translate("Save As MS Word file"),
                    translate("MS Word file (*.docx)"),
                    "{}_{}".format(
                        obj.data.get_start_datetime().strftime("%Y%m%d"), report_suffix
                    ),
                )
            if file_name:
                doc.save(file_name)
                os.startfile(file_name)

        elif template_path.endswith(".csv"):
            template = get_text_from_file(
                template_path,
                race=races_dict[get_current_race_index()],
                races=races_dict,
                rent_cards=list(RentCards().get()),
                current_race=get_current_race_index(),
                selected={"persons": []},  # leave here for back compatibility
            )

            if _settings["save_to_last_file"]:
                file_name = _settings["last_file"]
            else:
                file_name = get_save_file_name(
                    translate("Save As CSV file"),
                    translate("CSV file (*.csv)"),
                    "{}_{}".format(
                        obj.data.get_start_datetime().strftime("%Y%m%d"), report_suffix
                    ),
                )
            if len(file_name):
                _settings["last_file"] = file_name
                with codecs.open(file_name, "w", "utf-8") as file:
                    file.write(template)
                    file.close()

        else:
            template = get_text_from_file(
                template_path,
                race=races_dict[get_current_race_index()],
                races=races_dict,
                rent_cards=list(RentCards().get()),
                current_race=get_current_race_index(),
                selected={"persons": []},  # leave here for back compatibility
            )

            if _settings["save_to_last_file"]:
                file_name = _settings["last_file"]
            else:
                file_name = get_save_file_name(
                    translate("Save As HTML file"),
                    translate("HTML file (*.html)"),
                    "{}_{}".format(
                        obj.data.get_start_datetime().strftime("%Y%m%d"), report_suffix
                    ),
                )
            if len(file_name):
                _settings["last_file"] = file_name
                with codecs.open(file_name, "w", "utf-8") as file:
                    file.write(template)
                    file.close()

                # Open file in your browser
                if _settings["open_in_browser"]:
                    webbrowser.open("file://" + file_name, new=2)

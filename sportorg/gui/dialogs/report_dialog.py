import codecs
import logging
import os
import time

import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QPushButton, QDialogButtonBox, QCheckBox
from docxtpl import DocxTemplate

from sportorg import config
from sportorg.core.template import get_templates, get_text_from_file
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.memory import race, races, get_current_race_index
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits

_settings = {
    'last_template': None,
    'open_in_browser': True,
    'last_file': None,
    'save_to_last_file': False,
    'selected': False,
}


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Report creating'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_template = QLabel(_('Template'))
        self.item_template = AdvComboBox()
        self.item_template.addItems(get_templates(config.template_dir('result')))
        self.layout.addRow(self.label_template, self.item_template)
        if _settings['last_template'] is not None:
            self.item_template.setCurrentText(_settings['last_template'])

        self.item_custom_path = QPushButton(_('Choose template'))

        def select_custom_path():
            file_name = get_open_file_name(_('Open HTML template'), _("HTML file (*.html)"))
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        self.item_open_in_browser = QCheckBox(_('Open in browser'))
        self.item_open_in_browser.setChecked(_settings['open_in_browser'])
        self.layout.addRow(self.item_open_in_browser)

        self.item_save_to_last_file = QCheckBox(_('Save to last file'))
        self.item_save_to_last_file.setChecked(_settings['save_to_last_file'])
        self.layout.addRow(self.item_save_to_last_file)
        if _settings['last_file'] is None:
            self.item_save_to_last_file.setDisabled(True)

        self.item_selected = QCheckBox(_('Send selected'))
        self.item_selected.setChecked(_settings['selected'])
        self.layout.addRow(self.item_selected)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except FileNotFoundError as e:
                logging.error(str(e))
            except Exception as e:
                logging.error(str(e))
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()
        self.button_ok.setFocus()

    def apply_changes_impl(self):
        obj = race()
        mw = GlobalAccess().get_main_window()
        map_items = [obj.persons, obj.results, obj.groups, obj.courses, obj.organizations]
        map_names = ['persons', 'results', 'groups', 'courses', 'organizations']
        selected_items = {
            'persons': [],
            'results': [],
            'groups': [],
            'courses': [],
            'organizations': [],
        }

        template_path = self.item_template.currentText()

        _settings['last_template'] = template_path
        _settings['open_in_browser'] = self.item_open_in_browser.isChecked()
        _settings['save_to_last_file'] = self.item_save_to_last_file.isChecked()
        _settings['selected'] = self.item_selected.isChecked()

        if _settings['selected']:
            cur_items = map_items[mw.current_tab]

            for i in mw.get_selected_rows():
                selected_items[map_names[mw.current_tab]].append(cur_items[i].to_dict())

        ResultCalculation(obj).process_results()
        RaceSplits(obj).generate()
        ScoreCalculation(obj).calculate_scores()

        races_dict = [r.to_dict() for r in races()]

        if template_path.endswith('.docx'):
            # DOCX template processing
            full_path = config.template_dir() + template_path
            doc = DocxTemplate(full_path)
            context = {}
            context['race'] = races_dict[get_current_race_index()]
            context['name'] = config.NAME
            context['version'] = str(config.VERSION)
            doc.render(context)

            if _settings['save_to_last_file']:
                file_name = _settings['last_file']
            else:
                file_name = get_save_file_name(_('Save As MS Word file'), _("MS Word file (*.docx)"),
                                               '{}_official'.format(obj.data.get_start_datetime().strftime("%Y%m%d")))
            if file_name:
                doc.save(file_name)
                os.startfile(file_name)

        else:
            template = get_text_from_file(
                template_path,
                race=races_dict[get_current_race_index()],
                races=races_dict,
                current_race=get_current_race_index(),
                selected=selected_items
            )

            if _settings['save_to_last_file']:
                file_name = _settings['last_file']
            else:
                file_name = get_save_file_name(_('Save As HTML file'), _("HTML file (*.html)"),
                                               '{}_report'.format(obj.data.get_start_datetime().strftime("%Y%m%d")))
            if file_name:
                _settings['last_file'] = file_name
                with codecs.open(file_name, 'w', 'utf-8') as file:
                    file.write(template)
                    file.close()

                # Open file in your browser
                if _settings['open_in_browser']:
                    webbrowser.open('file://' + file_name, new=2)
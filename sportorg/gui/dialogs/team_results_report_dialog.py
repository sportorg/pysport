import codecs
import logging
import time
import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QPushButton, QDialogButtonBox, QCheckBox

from sportorg import config
from sportorg.core.template import get_templates, get_text_from_file
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.result.score_calculation import ScoreCalculation

_settings = {
    'last_template': None,
    'open_in_browser': True,
    'last_file': None,
    'save_to_last_file': False,
}


class TeamResultsReportDialog(QDialog):
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
        self.item_template.addItems(get_templates(config.template_dir('team_results')))
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

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except FileNotFoundError as e:
                logging.error(str(e))
            except Exception as e:
                logging.error(str(e))
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
        template_path = self.item_template.currentText()

        _settings['last_template'] = template_path
        _settings['open_in_browser'] = self.item_open_in_browser.isChecked()
        _settings['save_to_last_file'] = self.item_save_to_last_file.isChecked()

        ScoreCalculation.calculate_scores()
        template = get_text_from_file(template_path, **ScoreCalculation.get_team_results_data())

        if _settings['save_to_last_file']:
            file_name = _settings['last_file']
        else:
            file_name = get_save_file_name(_('Save As HTML file'), _("HTML file (*.html)"),
                                           '{}_team_results'.format(time.strftime("%Y%m%d")))
        if file_name:
            _settings['last_file'] = file_name
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(template)
                file.close()

            # Open file in your browser
            if _settings['open_in_browser']:
                webbrowser.open('file://' + file_name, new=2)

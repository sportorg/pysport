import codecs
import logging
import time
import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QDialog, QPushButton, QGroupBox, QRadioButton, QDialogButtonBox

from sportorg import config
from sportorg.core.template import get_templates, get_text_from_file
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.start.start_calculation import SortType


class BibReportDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Bib'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_template = QLabel(_('Template'))
        self.item_template = AdvComboBox()
        self.item_template.addItems(get_templates(config.template_dir('bib')))
        self.layout.addRow(self.label_template, self.item_template)

        self.item_custom_path = QPushButton(_('Choose template'))

        def select_custom_path():
            file_name = get_open_file_name(_('Open HTML template'), _("HTML file (*.html)"))
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        self.sorting_type_box = QGroupBox(_('Sorting by'))
        self.sorting_type_layout = QFormLayout()
        self.sorting_type_bib = QRadioButton(_('Bib'))
        self.sorting_type_bib.setChecked(True)
        self.sorting_type_layout.addRow(self.sorting_type_bib)
        self.sorting_type_org = QRadioButton(_('Team'))
        self.sorting_type_layout.addRow(self.sorting_type_org)
        self.sorting_type_group = QRadioButton(_('Group'))
        self.sorting_type_layout.addRow(self.sorting_type_group)
        self.sorting_type_box.setLayout(self.sorting_type_layout)
        self.layout.addRow(self.sorting_type_box)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
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
        sorting = SortType.BIB
        if self.sorting_type_org.isChecked():
            sorting = SortType.ORGANIZATION
        elif self.sorting_type_group.isChecked():
            sorting = SortType.GROUP

        template_path = self.item_template.currentText()
        # FIXME
        # template = get_text_from_file(template_path, **get_persons_data(sorting))
        template = ''

        file_name = get_save_file_name(_('Save As HTML file'), _("HTML file (*.html)"),
                                       '{}_bib'.format(time.strftime("%Y%m%d")))
        if file_name:
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(template)
                file.close()

            # Open file in your browser
            webbrowser.open('file://' + file_name, new=2)

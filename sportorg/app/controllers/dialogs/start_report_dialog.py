import codecs
import sys
import traceback

import time
import webbrowser

from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, QApplication, QDialog, QPushButton

from sportorg.app.models.start_calculation import get_start_data
from sportorg.app.modules.utils.custom_controls import AdvComboBox
from sportorg.core.template import get_templates, get_text_from_file

from sportorg.language import _
from sportorg import config


class StartReportDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Create start'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setToolTip(_('Creating of report'))

        self.layout = QFormLayout(self)

        self.label_template = QLabel(_('Template'))
        self.item_template = AdvComboBox()
        self.item_template.addItems(get_templates())
        self.layout.addRow(self.label_template, self.item_template)

        self.item_custom_path = QPushButton('...')

        def select_custom_path():
            file_name = QtWidgets.QFileDialog.getOpenFileName(self, _('Open HTML template'), '',
                                                              _("HTML file (*.html)"))[0]
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                traceback.print_exc()
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def apply_changes_impl(self):
        template_path = self.item_template.currentText()

        template = get_text_from_file(template_path, **get_start_data())

        file_name = QtWidgets.QFileDialog.getSaveFileName(self, _('Save As HTML file'),
                                                          '/start_' + str(time.strftime("%Y%m%d")),
                                                          _("HTML file (*.html)"))[0]
        with codecs.open(file_name, 'w', 'utf-8') as file:
            file.write(template)
            file.close()

        # Open file in your browser
        webbrowser.open('file://' + file_name, new=2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartReportDialog()
    sys.exit(app.exec_())

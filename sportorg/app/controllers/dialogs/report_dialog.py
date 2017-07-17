import codecs
import sys
import traceback

import time
import webbrowser

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QComboBox, QCompleter, QApplication, QDialog, \
    QPushButton

from sportorg.app.plugins.template.template import get_templates, get_text_from_file, get_result_data

from sportorg.language import _

class AdvComboBox(QComboBox):
    """
    Combo with autocomplete
    Found in Internet by Sergei
    """

    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_function(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited.connect(filter_function)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Report creating'))
        self.setWindowIcon(QIcon('sportorg.ico'))
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
                print(sys.exc_info())
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
        template = get_text_from_file(template_path, **get_result_data())
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, _('Save As HTML file'),
                                                          '/report_' + str(time.strftime("%Y%m%d")),
                                                          _("HTML file (*.html)"))[0]
        with codecs.open(file_name, 'w', 'utf-8') as file:
            file.write(template)
            file.close()

        # Open file in your browser
        webbrowser.open('file://' + file_name, new=2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReportDialog()
    sys.exit(app.exec_())

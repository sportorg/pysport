import codecs
import sys
import traceback

import time
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QComboBox, QCompleter, QApplication, QDialog, \
    QPushButton

from sportorg.app.plugins.template.template import get_templates, get_text_from_file, get_result_data


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
        self.setWindowTitle('Report creating')
        self.setWindowIcon(QIcon('sportorg.ico'))
        self.setGeometry(100, 100, 350, 500)
        self.setToolTip('Creating of report')

        self.layout = QFormLayout(self)

        self.label_template = QLabel('Template')
        self.item_template = AdvComboBox()
        self.item_template.addItems(get_templates())
        self.layout.addRow(self.label_template, self.item_template)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                print(sys.exc_info())
                traceback.print_exc()
            self.close()

        self.button_ok = QPushButton('OK')
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def apply_changes_impl(self):
        template_path = self.item_template.currentText()
        template = get_text_from_file(template_path, **get_result_data())
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save As HTML file',
                                                          '/report_' + str(time.strftime("%Y%m%d")),
                                                          "HTML file (*.html)")[0]
        with codecs.open(file_name, 'w', 'utf-8') as file:
            file.write(template)
            file.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReportDialog()
    sys.exit(app.exec_())

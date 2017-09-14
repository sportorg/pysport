import sys
import traceback

from PyQt5 import QtCore, QtWidgets, QtPrintSupport
from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QAbstractPrintDialog
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QComboBox, QCompleter, QApplication, QTableView, QDialog, \
    QPushButton, QTimeEdit, QRadioButton, QCheckBox

from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race, Organization, Result
from sportorg.app.models.result_calculation import ResultCalculation
from sportorg.app.plugins.utils.utils import datetime2qtime, qtime2datetime

from sportorg.language import _

class PrintPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Print properties'))
        self.setWindowIcon(QIcon('sportorg.ico'))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setToolTip(_('Print properties Window'))

        self.layout = QFormLayout(self)

        self.label_printer = QLabel(_('Default printer'))
        self.printer_selector = QPushButton(_('select'))

        def select_main_printer():
            printer = self.select_printer()
            self.selected_printer.setText(printer)

        self.printer_selector.clicked.connect(select_main_printer)

        self.label_split_printer = QLabel(_('Default split printer'))
        self.split_printer_selector = QPushButton(_('select'))

        def select_split_printer():
            printer = self.select_printer()
            self.selected_split_printer.setText(printer)

        self.split_printer_selector.clicked.connect(select_split_printer)

        self.selected_printer = QLabel()
        self.selected_split_printer = QLabel()

        printer_name = 'main printer' # TODO
        try:
            QPrinter.setPrinterName(printer_name)
        except:
            # traceback.print_stack()
            printer_name = QPrinter().printerName()
        self.selected_printer.setText(printer_name)

        printer_name = 'split printer' # TODO
        try:
            QPrinter.setPrinterName(printer_name)
        except:
            # traceback.print_stack()
            printer_name = QPrinter().printerName()
        self.selected_split_printer.setText(printer_name)

        self.layout.addRow(self.label_printer, self.printer_selector)
        self.layout.addRow(self.selected_printer)

        self.layout.addRow(self.label_split_printer, self.split_printer_selector)
        self.layout.addRow(self.selected_split_printer)

        self.print_splits_checkbox = QCheckBox(_('Print splits'))
        self.layout.addRow(self.print_splits_checkbox)

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

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index

        assert (isinstance(index, QModelIndex))
        orig_index_int = index.row()

        current_object = race().results[orig_index_int]
        assert (isinstance(current_object, Result))
        self.current_object = current_object

        if current_object.finish_time is not None:
            self.item_finish.setTime(datetime2qtime(current_object.finish_time))
        if current_object.start_time is not None:
            self.item_start.setTime(datetime2qtime(current_object.start_time))
        if current_object.result is not None:
            self.item_result.setText(str(current_object.result))
        if current_object.penalty_time is not None:
            self.item_penalty.setTime(datetime2qtime(current_object.penalty_time))

    def select_printer(self):
        try:
            printer = QtPrintSupport.QPrinter()
            pd = QPrintDialog(printer)
            pd.setOption(QAbstractPrintDialog.PrintSelection)
            pd.exec()
            return printer.printerName()
        except:
            traceback.print_exc()
        return None

    def apply_changes_impl(self):
        pass

    def get_parent_window(self):
        return GlobalAccess().get_main_window()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PrintPropertiesDialog()
    sys.exit(app.exec_())


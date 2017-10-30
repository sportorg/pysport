import sys
import logging

from PyQt5 import QtPrintSupport
from PyQt5.QtGui import QIcon
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QAbstractPrintDialog
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QApplication, QDialog, \
    QPushButton,  QCheckBox

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.memory import race

from sportorg.language import _
from sportorg import config


class PrintPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Printer settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

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

        self.layout.addRow(self.label_printer, self.printer_selector)
        self.layout.addRow(self.selected_printer)

        self.layout.addRow(self.label_split_printer, self.split_printer_selector)
        self.layout.addRow(self.selected_split_printer)

        self.print_splits_checkbox = QCheckBox(_('Print splits'))
        self.layout.addRow(self.print_splits_checkbox)

        self.set_values()

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def set_values(self):
        obj = race()
        printer_name = obj.get_setting('main_printer', QPrinter().printerName())
        try:
            QPrinter().setPrinterName(printer_name)
        except Exception as e:
            printer_name = QPrinter().printerName()
        self.selected_printer.setText(printer_name)

        printer_name = obj.get_setting('split_printer', QPrinter().printerName())
        try:
            QPrinter().setPrinterName(printer_name)
        except Exception as e:
            logging.exception(str(e))
            printer_name = QPrinter().printerName()
        self.selected_split_printer.setText(printer_name)

        self.print_splits_checkbox.setChecked(obj.get_setting('split_printout', False))

    def select_printer(self):
        try:
            printer = QtPrintSupport.QPrinter()
            pd = QPrintDialog(printer)
            pd.setOption(QAbstractPrintDialog.PrintSelection)
            pd.exec()
            return printer.printerName()
        except Exception as e:
            logging.exception(str(e))
        return None

    def apply_changes_impl(self):
        obj = race()
        main_printer = self.selected_printer.text()
        obj.set_setting('main_printer', main_printer)
        split_printer = self.selected_split_printer.text()
        obj.set_setting('split_printer', split_printer)
        obj.set_setting('split_printout', self.print_splits_checkbox.isChecked())

    def get_parent_window(self):
        return GlobalAccess().get_main_window()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PrintPropertiesDialog()
    sys.exit(app.exec_())

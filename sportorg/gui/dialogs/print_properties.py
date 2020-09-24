import logging

from PySide2 import QtPrintSupport
from PySide2.QtGui import QIcon
from PySide2.QtPrintSupport import QAbstractPrintDialog, QPrintDialog, QPrinter
from PySide2.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
)

from sportorg import config
from sportorg.common.template import get_templates
from sportorg.gui.dialogs.file_dialog import get_open_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.modules.configs.configs import Config


class PrintPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate('Printer settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_split_printer = QLabel(translate('Default split printer'))
        self.split_printer_selector = QPushButton(translate('select'))

        def select_split_printer():
            printer = self.select_printer()
            self.selected_split_printer.setText(printer)

        self.split_printer_selector.clicked.connect(select_split_printer)

        self.selected_printer = QLabel()
        self.selected_split_printer = QLabel()

        self.layout.addRow(self.label_split_printer, self.split_printer_selector)
        self.layout.addRow(self.selected_split_printer)

        self.label_template = QLabel(translate('Template'))
        self.item_template = AdvComboBox()
        self.item_template.setMaximumWidth(200)
        self.item_template.addItem(translate('Internal printing'))
        self.item_template.addItem(
            translate('Internal printing') + ' ' + translate('scale') + '=75'
        )
        self.item_template.addItems(get_templates(config.template_dir('split')))
        self.layout.addRow(self.label_template, self.item_template)

        self.item_custom_path = QPushButton(translate('Choose template'))

        def select_custom_path():
            file_name = get_open_file_name(
                translate('Open HTML template'), translate('HTML file (*.html)')
            )
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        self.print_splits_checkbox = QCheckBox(translate('Print splits'))
        self.layout.addRow(self.print_splits_checkbox)

        self.margin_group_box = QGroupBox(translate('Margins'))
        self.margin_layout = QFormLayout()
        self.item_margin_left = QDoubleSpinBox()
        self.margin_layout.addRow(QLabel(translate('Left')), self.item_margin_left)
        self.item_margin_top = QDoubleSpinBox()
        self.margin_layout.addRow(QLabel(translate('Top')), self.item_margin_top)
        self.item_margin_right = QDoubleSpinBox()
        self.margin_layout.addRow(QLabel(translate('Right')), self.item_margin_right)
        self.item_margin_bottom = QDoubleSpinBox()
        self.margin_layout.addRow(QLabel(translate('Bottom')), self.item_margin_bottom)
        self.margin_group_box.setLayout(self.margin_layout)
        self.layout.addRow(self.margin_group_box)

        self.set_values()

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
        self.button_ok.setText(translate('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def set_values(self):
        obj = race()
        default_printer_name = QPrinter().printerName()

        printer_name = Config().printer.get('split', default_printer_name)
        # try:
        #     QPrinter().setPrinterName(printer_name)
        # except Exception as e:
        #     logging.error(str(e))
        #     printer_name = default_printer_name
        self.selected_split_printer.setText(printer_name)

        self.print_splits_checkbox.setChecked(obj.get_setting('split_printout', False))

        template = obj.get_setting('split_template')
        if template:
            self.item_template.setCurrentText(template)

        self.item_margin_left.setValue(obj.get_setting('print_margin_left', 5.0))
        self.item_margin_top.setValue(obj.get_setting('print_margin_top', 5.0))
        self.item_margin_right.setValue(obj.get_setting('print_margin_right', 5.0))
        self.item_margin_bottom.setValue(obj.get_setting('print_margin_bottom', 5.0))

    def select_printer(self):
        try:
            printer = QtPrintSupport.QPrinter()
            pd = QPrintDialog(printer)
            pd.setOption(QAbstractPrintDialog.PrintSelection)
            pd.exec_()
            return printer.printerName()
        except Exception as e:
            logging.error(str(e))
        return None

    def apply_changes_impl(self):
        obj = race()
        split_printer = self.selected_split_printer.text()
        Config().printer.set('split', split_printer)
        obj.set_setting('split_printout', self.print_splits_checkbox.isChecked())
        obj.set_setting('split_template', self.item_template.currentText())

        obj.set_setting('print_margin_left', self.item_margin_left.value())
        obj.set_setting('print_margin_top', self.item_margin_top.value())
        obj.set_setting('print_margin_right', self.item_margin_right.value())
        obj.set_setting('print_margin_bottom', self.item_margin_bottom.value())

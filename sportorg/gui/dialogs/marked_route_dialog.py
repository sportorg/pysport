import logging

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QPushButton,
        QTextEdit,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QPushButton,
        QTextEdit,
    )

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race


class MarkedRouteDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def list_31_32(self):
        self.item_table.setPlainText("")
        for i in range(31, 100):
            if i % 2 > 0:
                self.item_table.append(str(i) + "," + str(i + 1))

    def list_31_131(self):
        self.item_table.setPlainText("")
        for i in range(31, 100):
            self.item_table.append(str(i) + "," + str(i + 100))

    def list_31(self):
        self.item_table.setPlainText("")
        for i in range(31, 100):
            self.item_table.append(str(i))

    def init_ui(self):
        self.setWindowTitle(translate("Marked route course generation"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.hint = QLabel(
            translate(
                "Specify in each row all control codes separated by comma, e.g. '31,32'"
            )
        )
        self.layout.addRow(self.hint)

        self.label_sample = QLabel("\n\n31,32\n33,34\n35,36\n37,38\n...")
        self.item_table = QTextEdit()
        self.item_table.setPlainText("")

        self.layout.addRow(self.label_sample, self.item_table)

        self.button_31_32 = QPushButton("31,32")
        self.button_31_32.setMaximumWidth(50)
        self.button_31_32.clicked.connect(self.list_31_32)
        self.button_31_131 = QPushButton("31,131")
        self.button_31_131.setMaximumWidth(50)
        self.button_31_131.clicked.connect(self.list_31_131)
        self.button_31 = QPushButton("31")
        self.button_31.setMaximumWidth(50)
        self.button_31.clicked.connect(self.list_31)

        self.layout.addRow(self.button_31_32)
        self.layout.addRow(self.button_31_131)
        self.layout.addRow(self.button_31)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
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

    def apply_changes_impl(self):
        text = self.item_table.toPlainText()
        code_dict = {}
        for line in text.split("\n"):
            for code in str(line).split(","):
                code_dict[code] = line
        for course in race().courses:
            for control in course.controls:
                code = control.code.split("(")[0]
                if code in code_dict.keys():
                    code_list = code_dict[code]
                    if code_list == code:
                        control.code = code
                    else:
                        control.code = code + "(" + code_list + ")"

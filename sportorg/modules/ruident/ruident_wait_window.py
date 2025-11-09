try:
    from PySide6.QtGui import QIcon, QFont
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QSpinBox,
    )
    from PySide6 import QtCore
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon, QFont
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QSpinBox, QPushButton,
    )
    from PySide2 import QtCore

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate

DURATION_INT = 10


class RuidentWaitDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.init_ui()

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Waiting..."))
        # self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)
        self.item_counter = QLabel()
        self.item_counter.setFont(QFont("Arial", 50))
        self.layout.addRow(self.item_counter)
        self.item_text = QLabel()
        self.item_text.setText(
            "You may need to  restart reader station as well  if nо connection with SportOrg within 1 minute."
        )
        self.layout.addRow(self.item_text)

        self.setMinimumWidth(400)

        self.timer_start()
        self.update_gui()

    def timer_start(self):
        self.time_left_int = DURATION_INT

        self.my_qtimer = QtCore.QTimer(self)
        self.my_qtimer.timeout.connect(self.timer_timeout)
        self.my_qtimer.start(1000)

        self.update_gui()

    def timer_timeout(self):
        self.time_left_int -= 1

        if self.time_left_int == -1:
            self.close()

        self.update_gui()

    def update_gui(self):
        self.item_counter.setText(str(self.time_left_int))

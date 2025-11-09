import os
from time import sleep

import pygetwindow

from sportorg.gui.dialogs.file_dialog import get_open_file_name

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


class RuidentRestartDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.init_ui()

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Question"))
        # self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.layout = QFormLayout(self)
        self.item_text = QLabel()
        self.item_text.setText(
            "Do you want to restart Ruident utility?"
        )
        self.layout.addRow(self.item_text)
        self.item_restart_service = QPushButton(text=translate("Restart Ruident service"))
        self.layout.addRow(self.item_restart_service)
        self.item_no_action = QPushButton(text=translate("Close"))
        self.layout.addRow(self.item_no_action)

        self.item_restart_service.clicked.connect(self.restart_service)
        self.item_no_action.clicked.connect(self.close)

        self.setMinimumWidth(400)

    def restart_service(self):
        cwd = os.getcwd()
        ruident_folder = cwd + os.path.sep + "ruident"
        if os.path.isdir(ruident_folder):
            ruident_exe = ruident_folder + os.path.sep + "RuidConnectRD.exe"
            if os.path.isfile(ruident_exe):
                try:
                    app_list = pygetwindow.getWindowsWithTitle('RuidConnectRD.exe')
                    if len(app_list) == 0:
                        self._logger.info(f"RUIDENT: starting RuidConnectRD.exe")
                        os.chdir(ruident_folder)
                        # os.system("start cmd /k " + ruident_exe)
                        os.startfile(ruident_exe)
                        os.chdir(cwd)
                    else:
                        self._logger.info(f"RUIDENT: RuidConnectRD.exe already started")
                except Exception as e:
                    self._logger.exception(e)

            self.get_data_filepath()

            if not os.path.exists(self.file_name):
                sleep(1)
                if not os.path.exists(self.file_name):
                    self.file_name = get_open_file_name()

            if not self.file_name:
                self.file_name = get_open_file_name()

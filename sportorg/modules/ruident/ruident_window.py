import os
import platform
from os.path import exists

import pygetwindow

from sportorg.modules.ruident.ruident import RuidentClient

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QSpinBox,
    )
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QSpinBox, QPushButton,
    )

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate


class RuidentDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.init_ui()

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Ruident mode"))
        # self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_restart_service = QPushButton(text=translate("Restart Ruident service"))
        self.layout.addRow(self.item_restart_service)

        self.item_monitor_log = QPushButton(text=translate("Monitor log"))
        self.layout.addRow(self.item_monitor_log)

        self.item_verify_connect = QPushButton(text=translate("Verify connect"))
        self.layout.addRow(self.item_verify_connect)

        self.item_verify_data = QPushButton(text=translate("Verify data.csv"))
        self.layout.addRow(self.item_verify_data)

        self.item_stop = QPushButton(text=translate("Stop service"))
        self.layout.addRow(self.item_stop)

        self.item_help = QPushButton(text=translate("Help"))
        self.layout.addRow(self.item_help)

        self.item_no_action = QPushButton(text=translate("No action"))
        self.layout.addRow(self.item_no_action)

        self.item_restart_service.clicked.connect(self.restart_service)
        self.item_monitor_log.clicked.connect(self.monitor_log)
        self.item_verify_connect.clicked.connect(self.maximize_service_win)
        self.item_verify_data.clicked.connect(self.verify_data)
        self.item_stop.clicked.connect(self.stop_service)
        self.item_help.clicked.connect(self.help)
        self.item_no_action.clicked.connect(self.close)

        self.setMinimumWidth(400)
        self.show()

    def start_service(self):
        ruident = RuidentClient()
        ruident.launch_reader_service()

    def restart_service(self):
        self.stop_service()
        self.start_service()

    def maximize_service_win(self):
        # Find the window by title (case-insensitive)
        list = pygetwindow.getWindowsWithTitle('RuidConnectRD.exe')
        if len(list) > 0:
            window = list[0]

            # Maximize the window
            window.restore()
            window.activate()

    def stop_service(self):
        service_name = "RuidConnectRD.exe"
        # Find the window by title (case-insensitive)
        for window in pygetwindow.getWindowsWithTitle(service_name):
            # Close the window
            window.close()
            RuidentClient().toggle()

    def monitor_log(self):
        GlobalAccess().get_main_window().select_tab(5)

    def verify_data(self):
        ruident = RuidentClient()
        ruident.get_data_filepath()
        filepath = ruident.file_name
        if filepath and exists(filepath):
            if platform.system() == 'Windows':
                os.startfile(filepath)

    def help(self):
        cwd = os.getcwd()
        ruident_folder = cwd + os.path.sep + "ruident"
        filepath = ruident_folder + os.path.sep + "help.pdf"
        os.startfile(filepath)

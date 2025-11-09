import os
import platform
from os.path import exists
from time import sleep

import pygetwindow
from PySide2 import QtCore

from sportorg.modules.ruident.ruident import RuidentClient
from sportorg.modules.ruident.ruident_wait_window import RuidentWaitDialog

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
    from PySide2.QtGui import QIcon, QFont
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
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_restart_service = QPushButton(text=translate("Start / Restart Ruident service"))
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

        self.item_counter = QLabel("0")
        self.item_counter.setFont(QFont("Arial", 40))
        self.item_counter.setMinimumWidth(200)
        self.layout.addRow(self.item_counter)

        self.item_restart_service.clicked.connect(self.restart_service)
        self.item_monitor_log.clicked.connect(self.monitor_log)
        self.item_verify_connect.clicked.connect(self.maximize_service_win)
        self.item_verify_data.clicked.connect(self.verify_data)
        self.item_stop.clicked.connect(self.stop_service)
        self.item_help.clicked.connect(self.help)

        self.setMinimumWidth(400)
        self.show()
        self.timer_start()

    def start_service(self):
        RuidentClient().start(timeout=10)

    def restart_service(self):
        self.stop_service()
        sleep(2)
        self.start_service()
        sleep(1)
        # RuidentWaitDialog().show()

    def maximize_service_win(self):
        # Find the window by title (case-insensitive)
        list = pygetwindow.getWindowsWithTitle('RuidConnectRD.exe')
        if len(list) > 0:
            window = list[0]

            # Maximize the window
            window.restore()
            try:
                window.activate()
            except Exception as e:
                print("Cannot open window, SportOrg is not active now")

    def stop_service(self):
        RuidentClient().stop_ruident_utility()
        RuidentClient().stop()
        # wait for 2 sec to terminate correctly
        # sleep(2)
        self.time_int = 3

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

    def timer_start(self):
        self.time_int = 15

        self.my_qtimer = QtCore.QTimer(self)
        self.my_qtimer.timeout.connect(self.timer_timeout)
        self.my_qtimer.start(1000)

        self.update_gui()

    def timer_timeout(self):
        self.time_int -= 1
        if self.time_int < 0:
            self.close()

        self.update_gui()

    def update_gui(self):
        self.item_counter.setText(str(self.time_int % 60))

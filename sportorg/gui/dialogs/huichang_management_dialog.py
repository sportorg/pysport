import functools
import logging

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QSpinBox,
        QStyle,
        QVBoxLayout,
    )
except ModuleNotFoundError:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QSpinBox,
        QStyle,
        QVBoxLayout,
    )

from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.libs.huichang.huichang import Huichang, HuichangException
from sportorg.modules.sportident.sireader import SIReaderClient


class HuichangManagementDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self._huichang = None

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def closeEvent(self, event):
        self._disconnect()

    def init_ui(self):
        self.setWindowTitle(translate("Huichang Management"))
        self.layout = QVBoxLayout(self)

        self.label_port = QLabel(translate("Port") + " 🛈")
        self.item_port = AdvComboBox()
        self.scan_port_button = QPushButton()
        pixmapi = QStyle.SP_BrowserReload
        icon = self.style().standardIcon(pixmapi)
        self.scan_port_button.setIcon(icon)
        self.scan_port_button.setToolTip(translate("Update list of available ports"))
        self.scan_port_button.clicked.connect(self.scan_ports)

        self.port_layout = QHBoxLayout()
        self.port_layout.addWidget(self.label_port)
        self.port_layout.addWidget(self.item_port)
        self.port_layout.addWidget(self.scan_port_button)
        self.layout.addLayout(self.port_layout)

        self.scan_ports()

        self.time_group_box = QGroupBox(translate("Time Calibration"))
        self.time_layout = QVBoxLayout(self.time_group_box)

        self.time_sync_button = QPushButton(translate("Time Sync") + " 🛈")
        self.time_sync_button.clicked.connect(self.time_sync)
        self.time_sync_button.setToolTip(
            translate("Send current system time to the connected station")
        )
        self.time_layout.addWidget(self.time_sync_button)

        self.layout.addWidget(self.time_group_box)

        self.station_number_group_box = QGroupBox(translate("Station Number"))
        self.station_number_layout = QVBoxLayout(self.station_number_group_box)

        self.station_clear_rb = QRadioButton(translate("Clear (6)"))
        self.station_superstart_rb = QRadioButton(translate("Superstart (11)"))
        self.station_start_rb = QRadioButton(translate("Start (16)"))
        self.station_finish_rb = QRadioButton(translate("Finish (21)"))
        self.station_check_rb = QRadioButton(translate("Check (27)"))
        self.station_master_rb = QRadioButton(translate("Master (250)"))
        self.station_manual_rb = QRadioButton(translate("Other (26-254)"))
        self.station_manual_rb.setChecked(True)

        self.station_spin = QSpinBox()
        self.station_spin.setRange(26, 254)
        self.station_spin.setValue(31)
        self.station_manual_rb.toggled.connect(self.station_spin.setEnabled)

        self.station_number_apply_button = QPushButton(translate("Apply") + " 🛈")
        self.station_number_apply_button.setToolTip(
            translate("Set new number for the connected station")
        )
        self.station_number_apply_button.clicked.connect(self.station_number_apply)

        self.station_number_layout.addWidget(self.station_clear_rb)
        self.station_number_layout.addWidget(self.station_superstart_rb)
        self.station_number_layout.addWidget(self.station_start_rb)
        self.station_number_layout.addWidget(self.station_finish_rb)
        self.station_number_layout.addWidget(self.station_check_rb)
        self.station_number_layout.addWidget(self.station_master_rb)
        self.station_number_layout.addWidget(self.station_manual_rb)
        self.station_number_layout.addWidget(self.station_spin)
        self.station_number_layout.addWidget(self.station_number_apply_button)

        self.layout.addWidget(self.station_number_group_box)

        self.show()

    def scan_ports(self):
        self.current_port = self.item_port.currentText()
        self.item_port.clear()
        ports = SIReaderClient().get_ports()
        self.item_port.addItems(ports)
        if ports and self.current_port in ports:
            self.item_port.setCurrentText(self.current_port)

    def _connect(self):
        self._huichang = None
        port = self.item_port.currentText()
        if not port:
            logging.info(translate("First select a valid port"))
            return None
        try:
            self._huichang = Huichang(port=port, logger=logging.root)
        except HuichangException:
            logging.error(translate("Could not connect to Huichang station"))
        return self._huichang

    def _disconnect(self):
        if self._huichang is not None:
            self._huichang.disconnect()
            self._huichang = None

    def connect_station(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            hc = self._connect()
            if hc:
                func(self, *args, **kwargs)
            self._disconnect()

        return wrapper

    def block_gui(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.setCursor(Qt.WaitCursor)
            try:
                return func(self, *args, **kwargs)
            finally:
                self.unsetCursor()

        return wrapper

    @block_gui
    @connect_station
    def time_sync(self):
        self._huichang.time_sync()

    @block_gui
    @connect_station
    def station_number_apply(self):
        station_number = self.station_spin.value()
        if self.station_clear_rb.isChecked():
            station_number = 6
        elif self.station_superstart_rb.isChecked():
            station_number = 11
        elif self.station_start_rb.isChecked():
            station_number = 16
        elif self.station_finish_rb.isChecked():
            station_number = 21
        elif self.station_check_rb.isChecked():
            station_number = 27
        elif self.station_master_rb.isChecked():
            station_number = 250

        self._huichang.set_station_number(station_number)

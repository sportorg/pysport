import logging
import uuid

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QRadioButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:
    from PySide2.QtCore import QTimer
    from PySide2.QtWidgets import (
        QAbstractItemView,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QRadioButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvSpinBox
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.modules.teamwork.teamwork import Teamwork


class TeamworkPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = "hh:mm:ss"
        self._clients_timer = None

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def closeEvent(self, event):
        self._stop_clients_timer()
        super().closeEvent(event)

    def init_ui(self):
        self.setWindowTitle(translate("Teamwork"))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        self.teamwork_tab = QWidget()
        self.teamwork_layout = QFormLayout()
        self.teamwork_item_host = QLineEdit()
        self.teamwork_item_port = AdvSpinBox(0, 65535)
        self.teamwork_item_token = QLineEdit()
        self.teamwork_groupbox = QGroupBox()
        self.teamwork_groupbox.setTitle(translate("Type connection"))
        self.teamwork_groupbox_layout = QFormLayout()
        self.teamwork_item_client = QRadioButton(translate("Client"))
        self.teamwork_item_server = QRadioButton(translate("Server"))
        self.teamwork_groupbox_layout.addRow(self.teamwork_item_client)
        self.teamwork_groupbox_layout.addRow(self.teamwork_item_server)
        self.teamwork_groupbox.setLayout(self.teamwork_groupbox_layout)

        self.teamwork_layout.addRow(QLabel(translate("Host")), self.teamwork_item_host)
        self.teamwork_layout.addRow(QLabel(translate("Port")), self.teamwork_item_port)
        self.teamwork_layout.addRow(self.teamwork_groupbox)
        self.teamwork_tab.setLayout(self.teamwork_layout)

        self.tab_widget.addTab(self.teamwork_tab, translate("Client/Server"))

        self.connections_tab = QWidget()
        self.connections_layout = QVBoxLayout()
        self.connections_status_label = QLabel("")
        self.connections_table = QTableWidget(0, 5)
        self.connections_table.setHorizontalHeaderLabels(
            [
                translate("ID"),
                translate("Address"),
                translate("Idle, s"),
                translate("Packets"),
                translate("Keepalive"),
            ]
        )
        self.connections_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connections_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.connections_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connections_table.verticalHeader().setVisible(False)
        self.connections_table.horizontalHeader().setStretchLastSection(True)

        self.connections_buttons = QHBoxLayout()
        self.connections_refresh_button = QPushButton(translate("Refresh"))
        self.connections_disconnect_button = QPushButton(translate("Disconnect client"))
        self.connections_buttons.addWidget(self.connections_refresh_button)
        self.connections_buttons.addWidget(self.connections_disconnect_button)

        self.connections_layout.addWidget(self.connections_status_label)
        self.connections_layout.addWidget(self.connections_table)
        self.connections_layout.addLayout(self.connections_buttons)
        self.connections_tab.setLayout(self.connections_layout)
        self.tab_widget.addTab(self.connections_tab, translate("Connected clients"))

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
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)
        self.layout.addRow(button_box)

        self.teamwork_item_client.toggled.connect(self._update_connections_controls)
        self.teamwork_item_server.toggled.connect(self._update_connections_controls)
        self.connections_refresh_button.clicked.connect(self.refresh_connected_clients)
        self.connections_disconnect_button.clicked.connect(
            self.disconnect_selected_client
        )

        self.set_values_from_model()
        self._update_connections_controls()
        self._start_clients_timer()
        self.refresh_connected_clients()

        self.show()

    def _start_clients_timer(self):
        self._clients_timer = QTimer(self)
        self._clients_timer.timeout.connect(self.refresh_connected_clients)
        self._clients_timer.start(1000)

    def _stop_clients_timer(self):
        if self._clients_timer is not None:
            self._clients_timer.stop()

    def _update_connections_controls(self):
        self.refresh_connected_clients()

    def _is_server_selected(self) -> bool:
        return self.teamwork_item_server.isChecked()

    def _is_server_running(self) -> bool:
        teamwork = Teamwork()
        return teamwork.is_alive() and teamwork.connection_type == "server"

    def refresh_connected_clients(self):
        server_selected = self._is_server_selected()
        server_running = self._is_server_running()

        if not server_selected:
            self.connections_status_label.setText(
                translate("Switch Teamwork mode to Server to manage clients")
            )
            clients = []
        elif not server_running:
            self.connections_status_label.setText(
                translate("Teamwork server is stopped")
            )
            clients = []
        else:
            clients = Teamwork().get_server_clients()
            self.connections_status_label.setText(
                translate("Connected clients: {}".format(len(clients)))
            )

        self.connections_table.setRowCount(len(clients))
        for row_index, client in enumerate(clients):
            self.connections_table.setItem(
                row_index,
                0,
                QTableWidgetItem(str(client.get("id", ""))),
            )
            self.connections_table.setItem(
                row_index,
                1,
                QTableWidgetItem(str(client.get("address", ""))),
            )
            self.connections_table.setItem(
                row_index,
                2,
                QTableWidgetItem(str(client.get("idle_seconds", ""))),
            )
            self.connections_table.setItem(
                row_index,
                3,
                QTableWidgetItem(str(client.get("packets", ""))),
            )
            self.connections_table.setItem(
                row_index,
                4,
                QTableWidgetItem(str(client.get("keepalive_packets", ""))),
            )

        self.connections_disconnect_button.setEnabled(server_running)
        self.connections_refresh_button.setEnabled(True)

    def disconnect_selected_client(self):
        if not self._is_server_running():
            return
        selected_rows = self.connections_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        for row in selected_rows:
            item = self.connections_table.item(row.row(), 0)
            if item is None:
                continue
            try:
                Teamwork().disconnect_server_client(int(item.text()))
            except ValueError:
                continue

        self.refresh_connected_clients()

    def set_values_from_model(self):
        obj = race()

        teamwork_host = obj.get_setting("teamwork_host", "localhost")
        teamwork_port = obj.get_setting("teamwork_port", 50010)
        teamwork_token = obj.get_setting("teamwork_token", str(uuid.uuid4())[:8])
        teamwork_type_connection = obj.get_setting("teamwork_type_connection", "client")

        self.teamwork_item_host.setText(teamwork_host)
        self.teamwork_item_port.setValue(teamwork_port)
        self.teamwork_item_token.setText(teamwork_token)
        if teamwork_type_connection == "client":
            self.teamwork_item_client.setChecked(True)
        elif teamwork_type_connection == "server":
            self.teamwork_item_server.setChecked(True)

    def apply_changes_impl(self):
        obj = race()

        teamwork_host = self.teamwork_item_host.text()
        teamwork_port = self.teamwork_item_port.value()
        teamwork_token = self.teamwork_item_token.text()
        teamwork_type_connection = "client"
        if self.teamwork_item_server.isChecked():
            teamwork_type_connection = "server"

        obj.set_setting("teamwork_host", teamwork_host)
        obj.set_setting("teamwork_port", teamwork_port)
        obj.set_setting("teamwork_token", teamwork_token)
        obj.set_setting("teamwork_type_connection", teamwork_type_connection)

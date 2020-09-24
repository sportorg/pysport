import logging
import uuid

from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QWidget,
)

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race


class TeamworkPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        # self.setFixedWidth(500)
        self.setWindowTitle(translate('Teamwork'))
        # self.setWindowIcon(QIcon(icon_dir('sportident.png')))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        # client/server
        self.teamwork_tab = QWidget()
        self.teamwork_layout = QFormLayout()
        self.teamwork_item_host = QLineEdit()
        self.teamwork_item_port = QSpinBox()
        self.teamwork_item_port.setMinimum(0)
        self.teamwork_item_port.setMaximum(65535)
        self.teamwork_item_token = QLineEdit()
        self.teamwork_groupbox = QGroupBox()
        self.teamwork_groupbox.setTitle(translate('Type connection'))
        self.teamwork_groupbox_layout = QFormLayout()
        self.teamwork_item_client = QRadioButton(translate('Client'))
        self.teamwork_item_server = QRadioButton(translate('Server'))
        self.teamwork_groupbox_layout.addRow(self.teamwork_item_client)
        self.teamwork_groupbox_layout.addRow(self.teamwork_item_server)
        self.teamwork_groupbox.setLayout(self.teamwork_groupbox_layout)

        self.teamwork_layout.addRow(QLabel(translate('Host')), self.teamwork_item_host)
        self.teamwork_layout.addRow(QLabel(translate('Port')), self.teamwork_item_port)
        # self.teamwork_layout.addRow(QLabel(translate('Token')), self.teamwork_item_token)
        self.teamwork_layout.addRow(self.teamwork_groupbox)
        self.teamwork_tab.setLayout(self.teamwork_layout)

        self.tab_widget.addTab(self.teamwork_tab, translate('Client/Server'))

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

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)
        self.layout.addRow(button_box)

        self.set_values_from_model()

        self.show()

    def set_values_from_model(self):
        obj = race()

        # teamwork
        teamwork_host = obj.get_setting('teamwork_host', 'localhost')
        teamwork_port = obj.get_setting('teamwork_port', 50010)
        teamwork_token = obj.get_setting('teamwork_token', str(uuid.uuid4())[:8])
        teamwork_type_connection = obj.get_setting('teamwork_type_connection', 'client')

        self.teamwork_item_host.setText(teamwork_host)
        self.teamwork_item_port.setValue(teamwork_port)
        self.teamwork_item_token.setText(teamwork_token)
        if teamwork_type_connection == 'client':
            self.teamwork_item_client.setChecked(True)
        elif teamwork_type_connection == 'server':
            self.teamwork_item_server.setChecked(True)

    def apply_changes_impl(self):
        obj = race()

        # teamwork
        teamwork_host = self.teamwork_item_host.text()
        teamwork_port = self.teamwork_item_port.value()
        teamwork_token = self.teamwork_item_token.text()
        teamwork_type_connection = 'client'
        if self.teamwork_item_server.isChecked():
            teamwork_type_connection = 'server'

        obj.set_setting('teamwork_host', teamwork_host)
        obj.set_setting('teamwork_port', teamwork_port)
        obj.set_setting('teamwork_token', teamwork_token)
        obj.set_setting('teamwork_type_connection', teamwork_type_connection)

import logging

try:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtGui import QIcon, Qt
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QPushButton
except ModuleNotFoundError:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtGui import QIcon, Qt
    from PySide2.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QPushButton

from sportorg import config
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox, AdvSpinBox
from sportorg.language import translate


class DialogFilter(QDialog):
    def __init__(self, table=None):
        super().__init__(GlobalAccess().get_main_window())
        if table:
            self.table = table

        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QGridLayout(self)

        model = self.table.model()
        headers = model.get_headers()

        for i in range(len(headers)):
            self.label = QtWidgets.QLabel(self)
            self.label.setText(headers[i])
            self.label.setObjectName("filter_label_" + str(i))
            self.label.setMaximumWidth(120)
            actions = [
                translate("equal to"),
                translate("contain"),
                translate("doesn't contain"),
                translate("in list"),
            ]
            default_action = actions[0]
            self.combo_action = AdvComboBox(self, actions, max_width=90)
            self.combo_action.setCurrentText(default_action)
            self.combo_action.setObjectName("filter_action_" + str(i))
            self.combo_value = AdvComboBox(self)
            self.combo_value.setMinimumWidth(150)
            self.combo_value.addItem("")
            self.combo_value.addItems(model.get_column_unique_values(i))
            self.combo_value.setObjectName("filter_value_" + str(i))

            self.layout.addWidget(self.label, i, 0, alignment=Qt.AlignRight)
            self.layout.addWidget(self.combo_action, i, 1)
            self.layout.addWidget(self.combo_value, i, 2)

        self.recover_filter()

        self.max_rows_count_label = QtWidgets.QLabel(self)

        self.max_rows_count_spin_box = AdvSpinBox(5000, 100000)
        self.layout.addWidget(self.max_rows_count_label, len(headers), 0)
        self.layout.addWidget(self.max_rows_count_spin_box, len(headers), 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.clicked.connect(self.reject)

        self.layout.addWidget(button_box, len(headers) + 1, 0)

        self.button_clear = QPushButton(text=translate("Clear"))
        self.button_clear.clicked.connect(self.clear_filter)
        self.layout.addWidget(self.button_clear, len(headers) + 1, 1)

        self.translate_ui()

    def exec_(self):
        self.show()
        return super().exec_()

    def accept(self, *args, **kwargs):
        try:
            # apply filter here
            if self.table:
                proxy_model = self.table.model()
                proxy_model.clear_filter()
                proxy_model.max_rows_count = self.max_rows_count_spin_box.value()

                headers = proxy_model.get_headers()
                for i in range(len(headers)):
                    value_combo = self.findChild(AdvComboBox, "filter_value_" + str(i))
                    assert isinstance(value_combo, AdvComboBox)
                    value = value_combo.currentText()
                    action_combo = self.findChild(
                        AdvComboBox, "filter_action_" + str(i)
                    )
                    assert isinstance(action_combo, AdvComboBox)
                    action = action_combo.currentText()
                    if len(value):
                        proxy_model.set_filter_for_column(i, value, action)
                        if headers[i] == translate("Group"):
                            PersonEditDialog.GROUP_NAME = value
                        elif headers[i] == translate("Team"):
                            PersonEditDialog.ORGANIZATION_NAME = value

                proxy_model.apply_filter()

        except Exception as e:
            logging.exception(e)

        super().accept(*args, **kwargs)

    def recover_filter(self):
        # show current filter settings
        for filter_key in self.table.model().filter.keys():
            value = self.table.model().filter.get(filter_key)[0]
            action = self.table.model().filter.get(filter_key)[1]
            value_combo = self.findChild(AdvComboBox, "filter_value_" + str(filter_key))
            assert isinstance(value_combo, AdvComboBox)
            value_combo.setCurrentText(value)
            action_combo = self.findChild(
                AdvComboBox, "filter_action_" + str(filter_key)
            )
            assert isinstance(action_combo, AdvComboBox)
            action_combo.setCurrentText(action)

    def clear_filter(self):
        headers = self.table.model().get_headers()
        for i in range(len(headers)):
            action_combo = self.findChild(AdvComboBox, "filter_value_" + str(i))
            assert isinstance(action_combo, AdvComboBox)
            action_combo.setCurrentText("")

    def translate_ui(self):
        self.setWindowTitle(translate("Filter Dialog"))
        self.max_rows_count_label.setText(translate("Max rows count"))
        self.button_ok.setText(translate("OK"))
        self.button_cancel.setText(translate("Cancel"))

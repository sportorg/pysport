import os
from typing import Any, Dict, List, Optional

try:
    from PySide6 import QtCore
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QHBoxLayout,
        QHeaderView,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
except ModuleNotFoundError:
    from PySide2 import QtCore
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import (
        QAbstractItemView,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QHBoxLayout,
        QHeaderView,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )

from sportorg import config, settings
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.modules.plugins import plugin_client


class PluginsDialog(QDialog):
    COLUMN_ENABLED = 0
    COLUMN_EXECUTABLE = 1
    COLUMN_ARGUMENTS = 2

    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self._plugin_ids: Dict[int, str] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle(translate("Plugins"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setModal(True)
        self.resize(760, 360)

        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(
            [
                translate("Enabled"),
                translate("Executable"),
                translate("Arguments"),
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(
            self.COLUMN_ENABLED, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COLUMN_EXECUTABLE, QHeaderView.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            self.COLUMN_ARGUMENTS, QHeaderView.Stretch
        )

        for plugin_config in settings.get_plugin_configs():
            self._add_row(plugin_config)

        self.button_add = QPushButton(translate("Add"))
        self.button_add.clicked.connect(lambda: self._add_row())
        self.button_remove = QPushButton(translate("Delete"))
        self.button_remove.clicked.connect(self._remove_selected_row)
        self.button_browse = QPushButton(translate("Select file"))
        self.button_browse.clicked.connect(self._browse_selected_row)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.button_add)
        self.buttons_layout.addWidget(self.button_remove)
        self.buttons_layout.addWidget(self.button_browse)
        self.buttons_layout.addStretch(1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate("OK"))
        self.button_ok.clicked.connect(self._apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(self.close)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.buttons_layout)
        self.layout.addWidget(button_box)

    def _add_row(self, plugin_config: Optional[Dict[str, Any]] = None) -> None:
        if plugin_config is None:
            plugin_config = {
                "enabled": False,
                "executable_path": "",
                "arguments": "",
                "plugin_id": "",
            }

        row = self.table.rowCount()
        self.table.insertRow(row)
        self._plugin_ids[row] = str(plugin_config.get("plugin_id", ""))

        enabled_item = QTableWidgetItem()
        enabled_item.setFlags(
            QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsUserCheckable
        )
        enabled_item.setCheckState(
            QtCore.Qt.Checked
            if bool(plugin_config.get("enabled", False))
            else QtCore.Qt.Unchecked
        )
        self.table.setItem(row, self.COLUMN_ENABLED, enabled_item)

        executable_item = QTableWidgetItem(
            str(plugin_config.get("executable_path", ""))
        )
        self.table.setItem(row, self.COLUMN_EXECUTABLE, executable_item)

        arguments_item = QTableWidgetItem(str(plugin_config.get("arguments", "")))
        self.table.setItem(row, self.COLUMN_ARGUMENTS, arguments_item)

    def _remove_selected_row(self) -> None:
        row = self._selected_row()
        if row is None:
            return

        self.table.removeRow(row)
        self._rebuild_plugin_ids_after_remove(row)

    def _browse_selected_row(self) -> None:
        row = self._selected_row()
        if row is None:
            self._add_row()
            row = self.table.rowCount() - 1

        current_path = self._item_text(row, self.COLUMN_EXECUTABLE)
        current_dir = os.path.dirname(current_path) if current_path else ""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            translate("Select plugin executable"),
            current_dir,
            translate("Executable files (*)"),
        )
        if file_name:
            self.table.item(row, self.COLUMN_EXECUTABLE).setText(file_name)

    def _apply_changes(self) -> None:
        plugin_configs: List[Dict[str, Any]] = []
        for row in range(self.table.rowCount()):
            executable_path = self._item_text(row, self.COLUMN_EXECUTABLE)
            arguments = self._item_text(row, self.COLUMN_ARGUMENTS)
            if not executable_path and not arguments:
                continue

            enabled_item = self.table.item(row, self.COLUMN_ENABLED)
            enabled = (
                enabled_item is not None
                and enabled_item.checkState() == QtCore.Qt.Checked
            )
            plugin_configs.append(
                {
                    "executable_path": executable_path,
                    "arguments": arguments,
                    "enabled": enabled,
                    "plugin_id": self._plugin_ids.get(row, ""),
                }
            )

        settings.set_plugin_configs(plugin_configs)
        settings.save_settings_to_file()
        plugin_client.reload()

        main_window = GlobalAccess().get_main_window()
        if main_window is not None:
            main_window.refresh_menu()

        self.close()

    def _selected_row(self) -> Optional[int]:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return int(rows[0].row())

    def _item_text(self, row: int, column: int) -> str:
        item = self.table.item(row, column)
        if item is None:
            return ""
        return item.text().strip()

    def _rebuild_plugin_ids_after_remove(self, removed_row: int) -> None:
        plugin_ids = {}
        for row, plugin_id in self._plugin_ids.items():
            if row < removed_row:
                plugin_ids[row] = plugin_id
            elif row > removed_row:
                plugin_ids[row - 1] = plugin_id
        self._plugin_ids = plugin_ids

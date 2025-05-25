import logging

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
        QSpinBox,
    )

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import translate
from sportorg.models.memory import race
from sportorg.models.result.result_tools import recalculate_results


class SplitDeleteDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Delete split"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_start_cp = QSpinBox()
        self.item_start_cp.setMaximum(999)
        self.layout.addRow(QLabel(translate("Start CP")), self.item_start_cp)

        self.item_end_cp = QSpinBox()
        self.item_end_cp.setMaximum(999)
        self.layout.addRow(QLabel(translate("End CP")), self.item_end_cp)

        self.item_max_intermediate = QSpinBox()
        self.item_max_intermediate.setValue(5)
        self.item_max_intermediate.setMaximum(999)
        self.layout.addRow(
            QLabel(translate("Max intermediate CP")), self.item_max_intermediate
        )

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(translate("Ok"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(translate("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        from_cp = str(self.item_start_cp.value())
        to_cp = str(self.item_end_cp.value())
        max_offset = self.item_max_intermediate.value()

        obj = race()

        results = obj.results
        for cur_res in results:
            from_index = -1
            to_index = -1
            for cur_split in cur_res.splits:
                if cur_split.code == from_cp and from_index < 0:
                    from_index = cur_split.index

                if cur_split.code == to_cp:
                    to_index = cur_split.index

            if from_index > -1 and 0 < to_index - from_index <= max_offset:
                delta = cur_res.splits[to_index].time - cur_res.splits[from_index].time

                for i in range(from_index + 1, to_index):
                    cur_res.splits[i].time = cur_res.splits[from_index].time

                for i in range(to_index, len(cur_res.splits)):
                    cur_res.splits[i].time = cur_res.splits[i].time - delta
                cur_res.finish_time = cur_res.finish_time - delta

        recalculate_results(race_object=obj)

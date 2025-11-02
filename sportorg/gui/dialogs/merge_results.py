import logging

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel
except ModuleNotFoundError:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel

from sportorg import config
from sportorg.common.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvSpinBox, AdvTimeEdit
from sportorg.language import translate
from sportorg.models.memory import ResultSportident, Split, race
from sportorg.models.result.result_tools import recalculate_results


class MergeResultsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(translate("Merge results"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_min_time_interval = AdvTimeEdit(time=OTime(minute=1))
        self.layout.addRow(
            QLabel(translate("Min. time interval")), self.item_min_time_interval
        )

        self.item_first_cp = AdvSpinBox(value=101, minimum=1, maximum=1024)
        self.layout.addRow(QLabel(translate("First CP")), self.item_first_cp)

        self.item_cp_increment = AdvSpinBox(value=1, minimum=0, maximum=100)
        self.layout.addRow(QLabel(translate("CP increment")), self.item_cp_increment)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
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
        min_time_interval = self.item_min_time_interval.getOTime()
        first_cp = self.item_first_cp.value()
        cp_increment = self.item_cp_increment.value()

        obj = race()

        bib_set = set()
        duplicated_set = set()
        for res in obj.results:
            cur_bib = res.get_bib()
            if cur_bib in bib_set:
                duplicated_set.add(cur_bib)
            else:
                bib_set.add(cur_bib)

        for cur_bib in duplicated_set:
            result_list = []
            for res in reversed(
                obj.results
            ):  # reversed order because of removing objects from iterated list
                if res.get_bib() == cur_bib:
                    result_list.append(res)
                    obj.results.remove(res)

            if len(result_list) < 1:
                continue

            result_list.sort(key=lambda c: c.finish_time)
            final_result = ResultSportident()
            final_result.bib = cur_bib
            final_result.person = result_list[0].person
            final_result.card_number = result_list[0].card_number
            cur_cp = first_cp

            for i in result_list:
                if (
                    len(final_result.splits) < 1
                    or (i.finish_time - final_result.splits[-1].time)
                    > min_time_interval
                ):
                    new_split = Split()
                    new_split.code = cur_cp
                    new_split.time = i.finish_time
                    final_result.splits.append(new_split)
                    cur_cp += cp_increment
                else:
                    logging.debug(
                        "skip time: %s for bib %s", str(i.finish_time), str(cur_bib)
                    )

            # append splits from existing objects
            append_splits = True
            if append_splits:
                for i in result_list:
                    for j in i.splits:
                        final_result.splits.append(j)
                final_result.sort_splits()
                final_result.remove_duplicated_splits()

            final_result.finish_time = final_result.splits[-1].time
            obj.results.append(final_result)

        recalculate_results(race_object=obj)

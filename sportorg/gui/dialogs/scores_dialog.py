import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton, QFormLayout, QRadioButton, QCheckBox, QSpinBox, QLineEdit, QLabel

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race


class ScoresDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Scores assign'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(False)
        self.setMinimumWidth(650)

        self.layout = QFormLayout(self)

        self.label_list = QRadioButton(_('Value list'))
        self.label_list.setChecked(True)
        self.item_list = QLineEdit()
        self.item_list.setText('40;37;35;33;32;31;30;29;28;27;26;25;24;23;22;21;20;19;18;17;16;15;14;13;12;11;10;9;8;7;6;5;4;3;2;1')
        self.layout.addRow(self.label_list, self.item_list)

        self.label_formula = QRadioButton(_('Formula'))
        self.item_formula = QLineEdit()
        self.layout.addRow(self.label_formula, self.item_formula)

        self.label_formula_hint = QLabel('Hint: You can use following variables: LeaderTime, Time, Year, Place, Length')
        self.layout.addRow(self.label_formula_hint)

        self.label_limit = QCheckBox(_('Limit per team'))
        self.item_limit = QSpinBox()
        self.item_limit.setMaximumWidth(50)
        self.layout.addRow(self.label_limit, self.item_limit)


        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(str(e))
            self.close()

        self.button_ok = QPushButton(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def apply_changes_impl(self):
        cur_race = race()
        cur_race.set_setting('score_list', self.item_list.text())
        cur_race.set_setting('score_formula', self.item_formula.text())
        cur_race.set_setting('score_team_limit', self.item_limit.value())
        cur_race.set_setting('score_use_team_limit', self.item_limit.value())

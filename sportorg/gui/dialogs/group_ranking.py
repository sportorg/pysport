import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QPushButton, QCheckBox, QSpinBox, QTimeEdit, QHBoxLayout

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.memory import RankingItem, Qualification
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import time_to_otime, time_to_qtime


class GroupRankingDialog(QDialog):
    def __init__(self, group=None):
        super().__init__(GlobalAccess().get_main_window())
        self.group = group

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Rank calculation'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        for i in self.group.ranking.rank:
            cur_item = self.group.ranking.rank[i]
            try:
                self.layout.addRow(get_widget_from_ranking(cur_item))
            except:
                logging.exception()

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
        for i in Qualification:
            name = i.name
            if i in self.group.ranking.rank:
                rank = self.group.ranking.rank[i]
                assert isinstance(rank, RankingItem)
                rank.is_active = self.findChild(QCheckBox, name + '_checkbox').isChecked()
                rank.max_place = self.findChild(QSpinBox, name + '_place').value()
                rank.max_time = time_to_otime(self.findChild(QTimeEdit, name + '_time').time())
                rank.use_scores = self.findChild(AdvComboBox, name + '_combo').currentText() == _('Rank')
        ResultCalculation().set_rank(self.group)


def get_widget_from_ranking(ranking):
    assert isinstance(ranking, RankingItem)
    qual = ranking.qual.name
    qual_checkbox = QCheckBox(ranking.qual.get_title())
    qual_checkbox.setFixedWidth(50)
    qual_checkbox.setObjectName(qual + '_checkbox')

    type_combo = AdvComboBox()
    type_combo.addItems({_('Rank'), _('Max place'), _('Result time')})
    type_combo.setFixedWidth(150)
    type_combo.setObjectName(qual + '_combo')

    max_place = QSpinBox()
    max_place.setValue(0)
    max_place.setFixedWidth(70)
    max_place.setObjectName(qual + '_place')

    max_time = QTimeEdit()
    max_time.setFixedWidth(70)
    max_time.setDisplayFormat("HH:mm:ss")
    max_time.setObjectName(qual + '_time')

    def select_type():
        text = type_combo.currentText()
        max_place.setVisible(text == _('Max place'))
        max_time.setVisible(text == _('Result time'))

    def set_enabled():
        flag = qual_checkbox.isChecked()
        type_combo.setEnabled(flag)
        max_place.setEnabled(flag)
        max_time.setEnabled(flag)

    type_combo.currentIndexChanged.connect(select_type)
    qual_checkbox.stateChanged.connect(set_enabled)

    if ranking.use_scores:
        type_combo.setCurrentText(_('Rank'))
    elif ranking.max_place:
        type_combo.setCurrentText(_('Max place'))
        max_place.setValue(ranking.max_place)
    else:
        type_combo.setCurrentText(_('Result time'))
        max_time.setTime(time_to_qtime(ranking.max_time))

    qual_checkbox.setChecked(ranking.is_active)
    select_type()
    set_enabled()

    layout = QHBoxLayout()
    layout.addWidget(qual_checkbox)
    layout.addWidget(type_combo)
    layout.addWidget(max_place)
    layout.addWidget(max_time)
    return layout

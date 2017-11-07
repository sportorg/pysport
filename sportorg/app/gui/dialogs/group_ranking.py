import sys
import logging

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, \
    QApplication, QDialog, \
    QPushButton, QCheckBox, QSpinBox, QTimeEdit, QHBoxLayout

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.memory import Group, RankingItem, Qualification
from sportorg.app.modules.utils.custom_controls import AdvComboBox
from sportorg.app.modules.utils.utils import qtime2otime, otime2qtime

from sportorg.language import _
from sportorg import config


class GroupRankingDialog(QDialog):
    def __init__(self, group=None):
        super().__init__()
        self.group = group
        self.init_ui()

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle(_('Rank calculation'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        for i in self.group.ranking.rank:
            cur_item = self.group.ranking.rank[i]
            self.layout.addRow(get_widget_from_ranking(cur_item))

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
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
                rank.max_time = qtime2otime(self.findChild(QTimeEdit, name + '_time').time())
                rank.use_scores = self.findChild(AdvComboBox, name + '_combo').currentText() == _('Rank')

    def get_parent_window(self):
        return GlobalAccess().get_main_window()


def get_widget_from_ranking(ranking):
    assert isinstance(ranking, RankingItem)
    qual = ranking.qual.name
    qual_checkbox = QCheckBox(_(ranking.qual.get_title()))
    qual_checkbox.setFixedWidth(50)
    qual_checkbox.setObjectName(qual + '_checkbox')

    type_combo = AdvComboBox()
    type_combo.addItems({_('Rank'), _('Max place'), _('Result time')})
    type_combo.setFixedWidth(150)
    type_combo.setObjectName(qual + '_combo')

    max_place = QSpinBox()
    max_place.setValue(1)
    max_place.setFixedWidth(50)
    max_place.setObjectName(qual + '_place')

    max_time = QTimeEdit()
    max_time.setFixedWidth(50)
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
        max_time.setTime(otime2qtime(ranking.max_time))

    qual_checkbox.setChecked(ranking.is_active)
    select_type()
    set_enabled()

    layout = QHBoxLayout()
    layout.addWidget(qual_checkbox)
    layout.addWidget(type_combo)
    layout.addWidget(max_place)
    layout.addWidget(max_time)
    return layout


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GroupRankingDialog(group=Group())
    sys.exit(app.exec_())

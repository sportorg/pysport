import codecs
import logging
import time
import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QTextEdit, QDialogButtonBox

from sportorg import config
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import get_race_groups, get_race_courses
from sportorg.models.memory import race


class StartChessDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        # FIXME
        # self.data = get_chess_list()
        self.data = []

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Start times'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.item_cols = AdvComboBox()
        self.item_cols.addItems([_('Start corridor'), _('Course'), _('Group')])
        self.item_cols.currentTextChanged.connect(self.set_text)
        self.layout.addRow(self.item_cols)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.NoWrap)
        self.text.setMinimumHeight(450)
        self.text.setMinimumWidth(450)
        self.text.setMaximumHeight(450)
        self.layout.addRow(self.text)

        self.set_text()

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
        self.button_ok.setText(_('Save As HTML file'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def get_html(self):
        index = self.item_cols.currentIndex()

        course = get_race_courses()
        course.sort()

        groups = get_race_groups()
        groups.sort()

        group_start_corridors = []
        for group in race().groups:
            if group.start_corridor not in group_start_corridors:
                group_start_corridors.append(group.start_corridor)
        group_start_corridors.sort()

        col_data = group_start_corridors
        col_text = 'group_start_corridor'

        if index == 1:
            col_data = course
            col_text = 'course'
        elif index == 2:
            col_data = groups
            col_text = 'group'

        data = self.data

        text = '<div><table>'
        text += '<tr><td></td>'
        for col_item in col_data:
            text += '<td>{}</td>'.format(col_item)
        text += '</tr>'

        for time_str in sorted(data):
            text += '<tr><td>{}</td>'.format(time_str)
            persons = {}
            for item in data[time_str]:
                if item[col_text] not in persons:
                    persons[item[col_text]] = [item]
                else:
                    persons[item[col_text]].append(item)
            for col_item in col_data:
                if col_item in persons:
                    text += '<td>'
                    for item in persons[col_item]:
                        text += '{} '.format(item['bib'])
                    text += '</td>'
                else:
                    text += '<td></td>'

            text += '</tr>'
        text += '</table></div>'
        return text

    def set_text(self):
        self.text.setHtml(self.get_html())

    def apply_changes_impl(self):
        file_name = get_save_file_name(_('Save As HTML file'), _("HTML file (*.html)"),
                                       '{}_start_times'.format(time.strftime("%Y%m%d")))
        if file_name:
            html = self.get_html()
            style = 'table {width:100%}' \
                    'td {border-bottom:1pt solid gray; text-align:center; padding-top:0.4em; font-weight:bold;}'
            html = '<html><head><meta charset="UTF-8"><style>{}</style></head><body>{}</body></html>'.format(style, html)
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(html)
                file.close()

            webbrowser.open('file://' + file_name, new=2)

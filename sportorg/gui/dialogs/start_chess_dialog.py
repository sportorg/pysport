import codecs
import logging
import time

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QDialog, QTextEdit, QDialogButtonBox

from sportorg import config
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.constant import get_race_groups, get_race_courses
from sportorg.models.start.start_calculation import get_chess_list


class StartChessDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('Start times'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.text = QTextEdit()
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
                logging.exception(str(e))
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

    def set_text(self):
        # course = get_race_courses()
        # course.sort()

        groups = get_race_groups()
        groups.sort()

        col_data = groups
        col_text = 'group'

        data = get_chess_list()

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

        self.text.setText(text)

    def apply_changes_impl(self):
        file_name = get_save_file_name(_('Save As HTML file'), _("HTML file (*.html)"),
                                       '{}_start_times'.format(time.strftime("%Y%m%d")))
        if file_name:
            with codecs.open(file_name, 'w', 'utf-8') as file:
                file.write(self.text.toHtml())
                file.close()

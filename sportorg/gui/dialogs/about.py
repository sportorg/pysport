import datetime
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QFormLayout, QDialog, QLabel, QTextEdit

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg import config


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec(self):
        self.init_ui()
        return super().exec()

    def init_ui(self):
        self.setWindowTitle(_('About'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setStyleSheet("background:white")
        self.setMinimumWidth(540)
        self.setMaximumWidth(640)
        self.layout = QFormLayout(self)

        title_font = QFont("Times", 24)
        title_text = QLabel()
        title_text.setText('{} {}'.format(config.NAME, config.VERSION))
        title_text.setFont(title_font)
        title_icon = QLabel()
        title_icon.setPixmap(QPixmap(config.ICON).scaled(75, 75))
        self.layout.addRow(title_icon, title_text)

        contributors_text = QLabel()
        contributors_text.setText('\n{}:{}'.format(
            _('Contributors'),
            '\n\t- Danil Akhtarov,\n\t- Sergei Kobelev,\n\t- Semyon Yakimov.'
        ))
        self.layout.addRow(contributors_text)

        home_page_text = QLabel()
        home_page_text.setText(
            '\n{0}: <a href="{1}">{1}</a>'.format(_('Home page'), 'https://sportorg.github.io/pysport/')
        )
        home_page_text.setOpenExternalLinks(True)

        self.layout.addRow(home_page_text)

        licence_title = QLabel()
        licence_title.setText(
            '\nMIT License'
        )
        licence_title.setAlignment(Qt.AlignCenter)
        self.layout.addRow(licence_title)

        licence_text = QTextEdit()
        licence_text.setStyleSheet("QScrollBar:vertical {background: #bfbfbf}")
        licence_text.setMinimumHeight(220)
        licence_text.setMaximumHeight(220)
        licence_text.setReadOnly(True)
        year = max(datetime.datetime.today().year, 2017)
        licence_text.setText("Copyright (c) " + str(year) + """ SportOrg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.""")
        self.layout.addRow(licence_text)
        self.show()

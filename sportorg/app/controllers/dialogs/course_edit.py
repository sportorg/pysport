import sys
import traceback

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QLabel, \
    QLineEdit, QComboBox, QCompleter, QApplication, QTableView, QDialog, \
    QPushButton, QSpinBox, QTextEdit

from sportorg.app.models.memory import race, Organization, Course, CourseControl


def get_course_types():
    return ['order', 'free', 'marked route']


class AdvComboBox(QComboBox):
    """
    Combo with autocomplete
    Found in Internet by Sergei
    """

    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_function(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited.connect(filter_function)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)


class CourseEditDialog(QDialog):
    def __init__(self, table=None, index=None):
        super().__init__()
        self.init_ui()
        if table is not None:
            self.set_values_from_table(table, index)

    def close_dialog(self):
        self.close()

    def init_ui(self):
        self.setWindowTitle('Course properties')
        self.setWindowIcon(QIcon('sportorg.ico'))
        self.setGeometry(100, 100, 350, 500)
        self.setToolTip('Course Edit Window')

        self.layout = QFormLayout(self)

        self.label_name = QLabel('Name')
        self.item_name = QLineEdit()
        self.layout.addRow(self.label_name, self.item_name)

        self.label_type = QLabel('Type')
        self.item_type = AdvComboBox()
        self.item_type.addItems(get_course_types())
        self.layout.addRow(self.label_type, self.item_type)

        self.label_length = QLabel('Length')
        self.item_length = QSpinBox()
        self.item_length.setMaximum(100000)
        self.item_length.setSingleStep(100)
        self.item_length.setValue(0)
        self.layout.addRow(self.label_length, self.item_length)

        self.label_climb = QLabel('Climb')
        self.item_climb = QSpinBox()
        self.item_climb.setValue(0)
        self.item_climb.setMaximum(10000)
        self.item_climb.setSingleStep(10)
        self.layout.addRow(self.label_climb, self.item_climb)

        self.label_control_qty = QLabel('Control count')
        self.item_control_qty = QSpinBox()
        self.layout.addRow(self.label_control_qty, self.item_control_qty)

        self.label_controls = QLabel('Controls')
        self.item_controls = QTextEdit()
        self.layout.addRow(self.label_controls, self.item_controls)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except:
                print(sys.exc_info())
                traceback.print_exc()
            self.close()

        self.button_ok = QPushButton('OK')
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = QPushButton('Cancel')
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(self.button_ok, self.button_cancel)

        self.show()

    def set_values_from_table(self, table, index):
        self.table = table
        self.current_index = index
        assert (isinstance(table, QTableView))
        model = table.model()
        assert (isinstance(model, QSortFilterProxyModel))
        orig_index = model.mapToSource(index)
        assert (isinstance(orig_index, QModelIndex))
        orig_index_int = orig_index.row()

        current_object = race().courses[orig_index_int]
        assert (isinstance(current_object, Course))
        self.current_object = current_object

        self.item_name.setText(current_object.name)

        if current_object.type is not None:
            self.item_type.setCurrentText(str(current_object.type))
        if current_object.length is not None:
            self.item_length.setValue(current_object.length)
        if current_object.climb is not None:
            self.item_climb.setValue(current_object.climb)
        if current_object.controls is not None:
            self.item_control_qty.setValue(len(current_object.controls))
        for i in current_object.controls:
            assert isinstance(i, CourseControl)
            self.item_controls.append(str(i.code) + ' ' + str(i.length))

    def apply_changes_impl(self):
        changed = False
        course = self.current_object
        assert (isinstance(course, Course))

        if course.name != self.item_name.text():
            course.name = self.item_name.text()
            changed = True

        if str(course.type) != self.item_type.currentText():
            course.type = self.item_type.currentText()
            changed = True

        if course.length != self.item_length.value():
            course.length = self.item_length.value()
            changed = True

        if course.climb != self.item_climb.value():
            course.climb = self.item_climb.value()
            changed = True

        text = self.item_controls.toPlainText()
        course.controls.clear()
        for i in text.split('\n'):
            control = CourseControl()
            control.code = i.split()[0]
            control.length = i.split()[1]
            course.controls.append(control)

        if changed:
            table = self.table
            # table.model().sourceModel().update_one_object(part, table.model().mapToSource(self.current_index).row())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CourseEditDialog()
    sys.exit(app.exec_())

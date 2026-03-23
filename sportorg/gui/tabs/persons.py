import logging

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    from PySide2 import QtCore, QtWidgets

from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import PersonMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race
from sportorg.models.start.relay import set_next_relay_number_to_person


class PersonsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []
        self._alt_pressed = False
        self._alt_input = ""

    def set_start_group(self, number):
        if -1 < self.currentIndex().row() < len(race().persons):
            person = race().persons[self.currentIndex().row()]
            person.start_group = number
            logging.debug("Set start group {} for person {}".format(number, person))

    def _get_numpad_value(self, event):
        """Check if event is a NumPad digit key and NumLock is enabled."""
        numpad_keys = {
            QtCore.Qt.Key_0: "0",
            QtCore.Qt.Key_1: "1",
            QtCore.Qt.Key_2: "2",
            QtCore.Qt.Key_3: "3",
            QtCore.Qt.Key_4: "4",
            QtCore.Qt.Key_5: "5",
            QtCore.Qt.Key_6: "6",
            QtCore.Qt.Key_7: "7",
            QtCore.Qt.Key_8: "8",
            QtCore.Qt.Key_9: "9",
        }

        if event.key() in numpad_keys:
            modifiers = event.modifiers()
            if modifiers & QtCore.Qt.KeypadModifier:
                return numpad_keys[event.key()]
        return None

    def keyPressEvent(self, event):
        """Handle Alt + digits for quick start_group input."""
        # Check if only Alt is pressed (without Ctrl, Shift, Meta)
        if event.key() == QtCore.Qt.Key_Alt:
            modifiers = event.modifiers()
            if (
                not (modifiers & QtCore.Qt.ControlModifier)
                and not (modifiers & QtCore.Qt.ShiftModifier)
                and not (modifiers & QtCore.Qt.MetaModifier)
            ):
                self._alt_pressed = True
                self._alt_input = ""
                return super().keyPressEvent(event)

        if self._alt_pressed:
            key = self._get_numpad_value(event) or event.text()

            if key.isdigit():
                # If Alt is held and a digit is pressed
                self._alt_input += key
                event.accept()  # Suppress the event
                return
            else:
                # If a non-digit key is pressed, cancel the input mode
                self._alt_pressed = False
                self._alt_input = ""
                return super().keyPressEvent(event)

        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Apply start_group when Alt is released."""
        if event.key() == QtCore.Qt.Key_Alt and self._alt_pressed:
            self._alt_pressed = False

            # Apply entered number if it exists and there is a selected row
            if self._alt_input and 0 <= self.currentIndex().row() < len(race().persons):
                try:
                    number = int(self._alt_input)
                    self.set_start_group(number)
                    GlobalAccess().get_main_window().refresh()
                except (ValueError, AttributeError):
                    pass

            self._alt_input = ""
            event.accept()
            return

        return super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        """Cancel input mode when focus is lost."""
        self._alt_pressed = False
        self._alt_input = ""
        return super().focusOutEvent(event)

    def selectionChanged(self, selected, deselected):
        """Cancel input mode when selection changes."""
        self._alt_pressed = False
        self._alt_input = ""
        return super().selectionChanged(selected, deselected)


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.person_table = PersonsTableView(self)
        self.entry_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.person_table.setObjectName("PersonTable")
        self.person_table.setModel(PersonMemoryModel())

        def entry_double_clicked(index):
            # show_edit_dialog(index)
            try:
                if index.row() < len(race().persons):
                    dialog = PersonEditDialog(race().persons[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
            except Exception as e:
                logging.exception(e)

        def entry_single_clicked(index):
            try:
                obj = race()
                if GlobalAccess().get_main_window().relay_number_assign:
                    if index.row() < len(obj.persons):
                        set_next_relay_number_to_person(obj.persons[index.row()])
                        GlobalAccess().get_main_window().refresh()

            except Exception as e:
                logging.error(str(e))

        self.person_table.activated.connect(entry_double_clicked)
        self.person_table.clicked.connect(entry_single_clicked)
        self.entry_layout.addWidget(self.person_table)

    def get_table(self):
        return self.person_table

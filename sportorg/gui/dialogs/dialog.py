from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from sportorg import config
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import translate
from sportorg.utils.time import qdate_to_date, time_to_otime, time_to_qtime


@dataclass
class Field:
    title: str = ''
    object: Optional[Any] = None
    key: str = ''
    id: str = ''
    q_item: Optional[Any] = None
    q_label: Optional[Any] = None


@dataclass
class LineField(Field):
    select_all: bool = False


@dataclass
class TextField(Field):
    pass


@dataclass
class NumberField(Field):
    maximum: Optional[int] = None
    minimum: Optional[int] = None
    single_step: Optional[int] = None
    is_disabled: Optional[bool] = None


@dataclass
class LabelField(Field):
    def set_text(self, text: str = '') -> None:
        if text:
            self.q_label.show()
            self.q_item.show()
        else:
            self.q_label.hide()
            self.q_item.hide()
        self.q_item.setText(text)


@dataclass
class ButtonField(Field):
    text: str = ''


@dataclass
class AdvComboBoxField(Field):
    items: List[str] = field(default_factory=list)


@dataclass
class CheckBoxField(Field):
    label: str = ''


@dataclass
class TimeField(Field):
    format: str = 'hh:mm:ss'


@dataclass
class DateField(Field):
    maximum: Optional[date] = None


class _Empty:
    pass


Empty = _Empty()


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title: str = translate('Dialog')
        self.ok_title: str = translate('Ok')
        self.cancel_title: str = translate('Cancel')
        self.is_modal: bool = True
        self.size = (400, 319)
        self.form = [
            LineField(),
            TextField(),
            NumberField(),
            LabelField(),
            AdvComboBoxField(),
            CheckBoxField(),
            TimeField(),
        ]
        self.fields = {}

    def exec_(self):
        self._init_ui()
        return super().exec_()

    def _init_ui(self) -> None:
        parent = self.parent()

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(config.ICON))
        self.setModal(self.is_modal)
        self.resize(*self.size)
        if self.is_modal and parent:
            self.setMaximumWidth(parent.size().width())
            self.setMaximumHeight(parent.size().height())

        vertical_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        content_widget = QWidget()

        form_layout = QFormLayout(content_widget)

        for field in self.form:
            label = QLabel(field.title)
            item = None
            value = Empty
            if field.object and field.key:
                value = getattr(field.object, field.key)
            convert_value = getattr(self, f'convert_{field.id}', None)
            if convert_value:
                value = convert_value(value)

            if isinstance(field, LineField):
                item = QLineEdit()
                if value is not Empty:
                    item.setText(value)
                callback = getattr(self, f'on_{field.id}_changed', None)
                if callback:
                    item.textChanged.connect(callback)
            if isinstance(field, NumberField):
                item = QSpinBox()
                if field.maximum is not None:
                    item.setMaximum(field.maximum)
                if field.minimum is not None:
                    item.setMinimum(field.minimum)
                if field.single_step is not None:
                    item.setSingleStep(field.single_step)
                if field.is_disabled is not None:
                    item.setDisabled(field.is_disabled)
                if value is not Empty:
                    item.setValue(value)
                callback = getattr(self, f'on_{field.id}_finished', None)
                if callback:
                    item.editingFinished.connect(callback)
                callback = getattr(self, f'on_{field.id}_changed', None)
                if callback:
                    item.valueChanged.connect(callback)
            if isinstance(field, LabelField):
                item = QLabel()
                item.hide()
                label.hide()
            if isinstance(field, CheckBoxField):
                item = QCheckBox(field.label)
                if value is not Empty:
                    item.setChecked(value)
                callback = getattr(self, f'on_{field.id}_changed', None)
                if callback:
                    item.stateChanged.connect(callback)
            if isinstance(field, AdvComboBoxField):
                item = AdvComboBox()
                item.addItems(field.items)
                if value is not Empty:
                    item.setCurrentText(value)
                callback = getattr(self, f'on_{field.id}_changed', None)
                if callback:
                    item.currentTextChanged.connect(callback)
            if isinstance(field, TextField):
                item = QTextEdit()
                item.setTabChangesFocus(True)
                if isinstance(value, str):
                    item.setText(value)
                elif value is not Empty:
                    for row in value:
                        item.append(row)
                callback = getattr(self, f'on_{field.id}_changed', None)
                if callback:
                    item.textChanged.connect(callback)
            if isinstance(field, TimeField):
                item = QTimeEdit()
                item.setDisplayFormat(field.format)
                item.setTime(time_to_qtime(value))
            if isinstance(field, DateField):
                item = QDateEdit()
                if field.maximum:
                    item.setMaximumDate(field.maximum)
                if value and value is not Empty:
                    item.setDate(value)
            if isinstance(field, ButtonField):
                item = QPushButton(field.text)
                callback = getattr(self, f'on_{field.id}_clicked', None)
                if callback:
                    item.clicked.connect(callback)

            form_layout.addRow(label, item)
            field.q_label = label
            field.q_item = item
            if field.id:
                self.fields[field.id] = field

        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        vertical_layout.addWidget(scroll_area)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.button_ok = self.button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(self.ok_title)
        self.button_ok.clicked.connect(self._apply)

        self.button_cancel = self.button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(self.cancel_title)
        self.button_cancel.clicked.connect(self.close)

        vertical_layout.addWidget(self.button_box)

        self.before_showing()
        self.show()
        for field in self.form:
            if isinstance(field, LineField):
                if field.select_all:
                    field.q_item.setFocus()
                    field.q_item.selectAll()
        self.after_showing()

    def _apply(self) -> None:
        for field in self.form:
            value = Empty

            if isinstance(field, LineField):
                value = field.q_item.text()
            if isinstance(field, NumberField):
                value = field.q_item.value()
            if isinstance(field, LabelField):
                pass
            if isinstance(field, CheckBoxField):
                value = field.q_item.isChecked()
            if isinstance(field, AdvComboBoxField):
                value = field.q_item.currentText()
            if isinstance(field, TextField):
                value = field.q_item.toPlainText()
            if isinstance(field, TimeField):
                value = time_to_otime(field.q_item.time())
            if isinstance(field, DateField):
                value = qdate_to_date(field.q_item.date())

            if value is Empty:
                continue

            parse_value = getattr(self, f'parse_{field.id}', None)
            if parse_value:
                value = parse_value(value)
            if field.object and field.key:
                setattr(field.object, field.key, value)

        self.apply()
        self.close()

    def before_showing(self) -> None:
        pass

    def after_showing(self) -> None:
        pass

    def apply(self) -> None:
        pass

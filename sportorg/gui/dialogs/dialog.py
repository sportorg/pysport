from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional

try:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import (
        QCheckBox,
        QDateEdit,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:
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
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

from sportorg import config
from sportorg.gui.utils.custom_controls import AdvComboBox, AdvSpinBox, AdvTimeEdit
from sportorg.language import translate
from sportorg.utils.time import qdate_to_date, time_to_otime


@dataclass
class Field:
    title: str = ""
    object: Optional[Any] = None
    key: str = ""
    id: str = ""
    q_item: Optional[Any] = None
    q_label: Optional[Any] = None
    tooltip: Optional[str] = None


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
    def set_text(self, text: str = "") -> None:
        if text:
            self.q_label.show()  # type:ignore
            self.q_item.show()  # type:ignore
        else:
            self.q_label.hide()  # type:ignore
            self.q_item.hide()  # type:ignore
        self.q_item.setText(text)  # type:ignore


@dataclass
class ButtonField(Field):
    text: str = ""


@dataclass
class AdvComboBoxField(Field):
    items: List[str] = field(default_factory=list)


@dataclass
class CheckBoxField(Field):
    label: str = ""


@dataclass
class TimeField(Field):
    format: str = "hh:mm:ss"


@dataclass
class DateField(Field):
    maximum: Optional[date] = None


class _Empty:
    pass


Empty = _Empty()


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title: str = translate("Dialog")
        self.ok_title: str = translate("Ok")
        self.cancel_title: str = translate("Cancel")
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
        # type:ignore
        parent = self.parent()

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(config.ICON))
        self.setModal(self.is_modal)
        self.resize(*self.size)  # type:ignore
        if self.is_modal and parent:  # type:ignore
            self.setMaximumWidth(parent.size().width())
            self.setMaximumHeight(parent.size().height())

        vertical_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        content_widget = QWidget()

        form_layout = QFormLayout(content_widget)

        for form_field in self.form:
            label = QLabel(form_field.title)
            item = None
            value = Empty
            if form_field.object and form_field.key:
                value = getattr(form_field.object, form_field.key)
            convert_value = getattr(self, f"convert_{form_field.id}", None)
            if convert_value:
                value = convert_value(value)

            if isinstance(form_field, LineField):
                item = QLineEdit()
                if value is not Empty:
                    item.setText(str(value))  # type:ignore
                callback = getattr(self, f"on_{form_field.id}_changed", None)  # type:ignore
                if callback:
                    item.textChanged.connect(callback)
            if isinstance(form_field, NumberField):
                item = AdvSpinBox()
                if form_field.maximum is not None:
                    item.setMaximum(form_field.maximum)
                if form_field.minimum is not None:
                    item.setMinimum(form_field.minimum)
                if form_field.single_step is not None:
                    item.setSingleStep(form_field.single_step)
                if form_field.is_disabled is not None:
                    item.setDisabled(form_field.is_disabled)
                if value is not Empty:
                    item.setValue(value)  # type:ignore
                callback = getattr(self, f"on_{form_field.id}_finished", None)  # type:ignore
                if callback:
                    item.editingFinished.connect(callback)
                callback = getattr(self, f"on_{form_field.id}_changed", None)
                if callback:
                    item.valueChanged.connect(callback)
            if isinstance(form_field, LabelField):
                item = QLabel()
                item.hide()
                label.hide()
            if isinstance(form_field, CheckBoxField):
                item = QCheckBox(form_field.label)
                if value is not Empty:
                    item.setChecked(value)  # type:ignore
                callback = getattr(self, f"on_{form_field.id}_changed", None)
                if callback:
                    item.stateChanged.connect(callback)
            if isinstance(form_field, AdvComboBoxField):
                item = AdvComboBox()
                item.addItems(form_field.items)
                if value is not Empty:
                    item.setCurrentText(value)  # type:ignore
                callback = getattr(self, f"on_{form_field.id}_changed", None)
                if callback:
                    item.currentTextChanged.connect(callback)
            if isinstance(form_field, TextField):
                item = QTextEdit()
                item.setTabChangesFocus(True)
                if isinstance(value, str):
                    item.setText(value)
                elif value is not Empty:
                    for row in value:  # type:ignore
                        item.append(row)
                callback = getattr(self, f"on_{form_field.id}_changed", None)
                if callback:
                    item.textChanged.connect(callback)
            if isinstance(form_field, TimeField):
                item = AdvTimeEdit(display_format=form_field.format, time=value)
            if isinstance(form_field, DateField):
                item = QDateEdit()
                if form_field.maximum:
                    item.setMaximumDate(form_field.maximum)  # type:ignore
                if value and value is not Empty:
                    item.setDate(value)  # type:ignore
            if isinstance(form_field, ButtonField):
                item = QPushButton(form_field.text)
                callback = getattr(self, f"on_{form_field.id}_clicked", None)
                if callback:
                    item.clicked.connect(callback)

            form_layout.addRow(label, item)  # type:ignore
            form_field.q_label = label
            form_field.q_item = item

            if form_field.id:
                self.fields[form_field.id] = form_field

            if form_field.tooltip:
                form_field.q_item.setToolTip(form_field.tooltip)
                if hasattr(form_field.q_item, "setToolTip"):
                    form_field.q_item.setToolTip(form_field.tooltip)

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
        for form_field in self.form:
            if isinstance(form_field, LineField):
                if form_field.select_all:
                    form_field.q_item.setFocus()  # type:ignore
                    form_field.q_item.selectAll()  # type:ignore
        self.after_showing()

    def _apply(self) -> None:
        for form_field in self.form:
            value = Empty

            if isinstance(form_field, LineField):
                value = form_field.q_item.text()  # type:ignore
            if isinstance(form_field, NumberField):
                value = form_field.q_item.value()  # type:ignore
            if isinstance(form_field, LabelField):
                pass
            if isinstance(form_field, CheckBoxField):
                value = form_field.q_item.isChecked()  # type:ignore
            if isinstance(form_field, AdvComboBoxField):
                value = form_field.q_item.currentText()  # type:ignore
            if isinstance(form_field, TextField):
                value = form_field.q_item.toPlainText()  # type:ignore
            if isinstance(form_field, TimeField):
                value = time_to_otime(form_field.q_item.time())  # type:ignore
            if isinstance(form_field, DateField):
                value = qdate_to_date(form_field.q_item.date())  # type:ignore

            if value is Empty:
                continue

            parse_value = getattr(self, f"parse_{form_field.id}", None)
            if parse_value:
                value = parse_value(value)
            if form_field.object and form_field.key:
                setattr(form_field.object, form_field.key, value)

        self.apply()
        self.close()

    def before_showing(self) -> None:
        pass

    def after_showing(self) -> None:
        pass

    def apply(self) -> None:
        pass

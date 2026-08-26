from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout , QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox
from sportorg.models.memory import race

class ImpinjSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        group_box = QGroupBox("Настройки RFID-контроллера Impinj")
        form = QFormLayout(group_box)
        
        # 1. Выбор COM-порта
        self.port_combo = QComboBox()
        self.port_combo.addItem("Автопоиск (Автодетекция)", "auto")
        for i in range(1, 30):
            self.port_combo.addItem(f"Порт COM{i}", f"COM{i}")
        
        self.port_combo.setCurrentIndex(self.port_combo.findData(race().get_setting("impinj_port", "auto")))
        form.addRow("Последовательный порт:", self.port_combo)
        
        # 2. Выбор скорости порта (Baud Rate)
        self.baud_combo = QComboBox()
        self.baud_combo.addItem("9600 bps", 3)
        self.baud_combo.addItem("19200 bps", 4)
        self.baud_combo.addItem("38400 bps", 5)
        self.baud_combo.addItem("57600 bps (Стандарт)", 6)
        self.baud_combo.addItem("115200 bps", 7)
        
        self.baud_combo.setCurrentIndex(self.baud_combo.findData(race().get_setting("impinj_baud_rate_idx", 6)))
        form.addRow("Скорость соединения:", self.baud_combo)
        
        # 3. Динамический контейнер для чекбоксов активных антенн
        self.antenna_group_box = QGroupBox("Доступные антенны RFID-контроллера")
        
        # ИЗМЕНЕНИЕ: Меняем QHBoxLayout на QGridLayout для табличного вывода
        self.antenna_layout = QGridLayout(self.antenna_group_box)
        self.antenna_checkboxes = []
        
        # При первичной загрузке восстанавливаем сохраненное ранее количество портов
        saved_ports_count = race().get_setting("impinj_hardware_ports", 0)
        if saved_ports_count > 0:
            self.rebuild_antenna_checkboxes(saved_ports_count)
        form.addRow(self.antenna_group_box)
        
        # 4. Мощность излучения ридера (0-30 dBm)
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 30)
        self.power_spin.setSuffix(" dBm")
        self.power_spin.setValue(int(race().get_setting("impinj_rf_power", 26)))
        form.addRow("Мощность излучения:", self.power_spin)
        
        # 5. Чекбокс защиты (Детекция антенны)
        self.check_ant_box = QCheckBox("Защитный режим выключения не подключенной антенны")
        self.check_ant_box.setChecked(bool(race().get_setting("impinj_check_ant", True)))
        form.addRow(self.check_ant_box)
        
        layout.addWidget(group_box)

    def rebuild_antenna_checkboxes(self, count):
        """Динамически перестраивает сетку чекбоксов строго по 4 штуки в ряд"""
        # Удаляем старые элементы разметки
        while self.antenna_layout.count():
            item = self.antenna_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.antenna_checkboxes.clear()
        
        # Загружаем сохраненную битовую маску из БД (по умолчанию 0 — все выключены)
        saved_mask = race().get_setting("impinj_antenna_mask", 0)
        
        # Генерируем новый набор чекбоксов в зависимости от переданного count
        for i in range(1, count + 1):
            cb = QCheckBox(f"Ант. {i}")
            
            # Извлекаем бит состояния для текущей антенны из общей маски
            is_checked = bool(saved_mask & (1 << (i - 1)))
            cb.setChecked(is_checked)
            
            # ВАЖНО: Вычисляем строку и колонку для размещения (по 4 антенны в ряд)
            # Индекс в цикле идет от 0 до count-1, поэтому берем (i - 1)
            idx = i - 1
            row = idx // 4     # Каждые 4 элемента переносим на новую строку
            column = idx % 4   # Остаток от деления определяет колонку (0, 1, 2, 3)
            
            # Добавляем виджет в сетку на вычисленную позицию
            self.antenna_layout.addWidget(cb, row, column)
            self.antenna_checkboxes.append(cb)


    def save_settings(self):
        """Вызывается автоматически при нажатии кнопки ОК в главном окне"""
        obj = race()
        
        # Считаем битовую маску на основе проставленных галочек
        antenna_mask = 0
        for idx, cb in enumerate(self.antenna_checkboxes):
            if cb.isChecked():
                antenna_mask |= (1 << idx) # Выставляем соответствующий бит в 1
                
        # Сохраняем вычисленные значения в настройки гонки SportOrg
        obj.set_setting("impinj_port", self.port_combo.currentData())
        obj.set_setting("impinj_baud_rate_idx", self.baud_combo.currentData())
        obj.set_setting("impinj_antenna_mask", antenna_mask)
        obj.set_setting("impinj_hardware_ports", len(self.antenna_checkboxes))
        obj.set_setting("impinj_rf_power", self.power_spin.value())
        obj.set_setting("impinj_check_ant", self.check_ant_box.isChecked())

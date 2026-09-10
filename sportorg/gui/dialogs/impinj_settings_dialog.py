from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox
from sportorg.models.memory import race
from sportorg.language import translate

class ImpinjSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        group_box = QGroupBox(translate("Impinj RFID controller settings"))
        form = QFormLayout(group_box)
        
        # 1. COM port selection
        self.port_combo = QComboBox()
        self.port_combo.addItem(translate("Autodetect"), "auto")
        for i in range(1, 30):
            # В po-файле: msgid "Open port {}" -> msgstr "Открываю порт {}"
            # Для сохранения оригинального вида "Порт COM1" используется явный формат
            self.port_combo.addItem(translate("Port") + f" COM{i}", f"COM{i}")
        
        self.port_combo.setCurrentIndex(self.port_combo.findData(race().get_setting("impinj_port", "auto")))
        form.addRow(translate("COM port"), self.port_combo)
        
        # 2. Connection speed selection (Baud Rate)
        self.baud_combo = QComboBox()
        self.baud_combo.addItem("9600 bps", 3)
        self.baud_combo.addItem("19200 bps", 4)
        self.baud_combo.addItem("38400 bps", 5)
        # Слово (Стандарт) заменено на системное "System" из po-файла
        self.baud_combo.addItem(f"57600 bps ({translate('System')})", 6)
        self.baud_combo.addItem("115200 bps", 7)
        
        self.baud_combo.setCurrentIndex(self.baud_combo.findData(race().get_setting("impinj_baud_rate_idx", 6)))
        form.addRow(translate("Baud Rate"), self.baud_combo)
        
        # 3. Dynamic container for active antenna checkboxes
        self.antenna_group_box = QGroupBox(translate("Available RFID Antennas"))
        
        # Changed QHBoxLayout to QGridLayout for grid layout display
        self.antenna_layout = QGridLayout(self.antenna_group_box)
        self.antenna_checkboxes = []
        
        # Restore previously saved hardware ports count during initial load
        saved_ports_count = race().get_setting("impinj_hardware_ports", 0)
        if saved_ports_count > 0:
            self.rebuild_antenna_checkboxes(saved_ports_count)
        form.addRow(self.antenna_group_box)
        
        # 4. Reader RF power output (0-30 dBm)
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 30)
        self.power_spin.setSuffix(" dBm")
        self.power_spin.setValue(int(race().get_setting("impinj_rf_power", 26)))
        form.addRow(translate("RF Power:"), self.power_spin)
        
        # 5. Safe mode checkbox (Antenna detection protection)
        self.check_ant_box = QCheckBox(translate("Safe antenna mode"))
        self.check_ant_box.setChecked(bool(race().get_setting("impinj_check_ant", True)))
        form.addRow(self.check_ant_box)

        #beeper check-box
        self.beep_en_box = QCheckBox(translate("Enable buzzer / beep sound")) # Ключ для бипера в UI
        # reed from base , default is Enable
        self.beep_en_box.setChecked(bool(race().get_setting("impinj_beep_en", True)))
        form.addRow(self.beep_en_box)

        layout.addWidget(group_box)


    def rebuild_antenna_checkboxes(self, count):
        """Dynamically rebuilds the checkboxes grid layout strictly into 4 items per row"""
        # Remove old layout items
        while self.antenna_layout.count():
            item = self.antenna_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.antenna_checkboxes.clear()
        
        # Load the saved antenna bitmask from the database (default 0 — all disabled)
        saved_mask = race().get_setting("impinj_antenna_mask", 0)
        
        # Generate a new set of checkboxes depending on the provided count
        for i in range(1, count + 1):
            cb = QCheckBox(translate("Ant. {}").format(i))
            
            # Extract the state bit for the current antenna from the shared bitmask
            is_checked = bool(saved_mask & (1 << (i - 1)))
            cb.setChecked(is_checked)
            
            # Calculate row and column indices for layout distribution (4 antennas per row)
            idx = i - 1
            row = idx // 4     # Moves to a new row every 4 items
            column = idx % 4   # Remainder defines the column index (0, 1, 2, 3)
            
            # Add widget to the grid layout at calculated position
            self.antenna_layout.addWidget(cb, row, column)
            self.antenna_checkboxes.append(cb)

    def save_settings(self):
        """Triggered automatically when clicking the OK button in the main window"""
        obj = race()
        
        # Compute the antenna bitmask based on checked boxes
        antenna_mask = 0
        for idx, cb in enumerate(self.antenna_checkboxes):
            if cb.isChecked():
                antenna_mask |= (1 << idx) # Set corresponding bit to 1
                
        # Save calculated values to SportOrg race settings
        obj.set_setting("impinj_port", self.port_combo.currentData())
        obj.set_setting("impinj_baud_rate_idx", self.baud_combo.currentData())
        obj.set_setting("impinj_antenna_mask", antenna_mask)
        obj.set_setting("impinj_hardware_ports", len(self.antenna_checkboxes))
        obj.set_setting("impinj_rf_power", self.power_spin.value())
        obj.set_setting("impinj_check_ant", self.check_ant_box.isChecked())

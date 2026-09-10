import logging
import os
import ctypes
import configparser
from sportorg.language import translate
from queue import Empty, Queue
from random import randint
from threading import Event, main_thread
from time import sleep

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:
    from PySide6.QtCore import QThread, Signal

from sportorg.common.otime import OTime
from sportorg.common.singleton import singleton
from sportorg.models import memory
from sportorg.models.memory import race

BYTE = ctypes.c_ubyte

class ImpinjCommand:
    def __init__(self, command, data=None):
        self.command = command
        self.data = data

class ImpinjThread(QThread):
    def __init__(self, port, queue, stop_event, logger, debug=False):
        self.port = port
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue = queue
        self._stop_event = stop_event
        self._logger = logger
        self._debug = debug
        self.timeout_list = {}
        self.timeout = race().get_setting("readout_duplicate_timeout", 15000)
        
        self.dll = None
        self.frm_handle = ctypes.c_int(-1)
        self.com_adr = BYTE(0xFF)
        self._logger.info(f"[RFID-DEBUG] Thread initialized. Assigned port from configurations: {self.port}")

    def _init_dll(self):
        try:
            # 1. Define portable path relative to the current script file location
            base_dir = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.abspath(os.path.join(base_dir, "..", "..", "libs", "rfid_impinj", "UHFReader288.dll"))
            
            self._logger.info(f"[RFID-DEBUG] Attempting to load DLL at path: {dll_path}")
            
            # 2. Add folder to Windows search paths for linked DLL dependencies (required for Python 3.8+)
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(os.path.dirname(dll_path))
                except Exception:
                    pass
            
            # 3. Load the library context structure
            self.dll = ctypes.WinDLL(dll_path, winmode=0)
            self._logger.info("[RFID-DEBUG] Library UHFReader288.dll successfully loaded into memory.")
            return True
        except Exception as e:
            self._logger.error(f"[RFID-DEBUG] CRITICAL ERROR loading UHFReader288.dll: {e}")
            return False

    def _connect_reader(self):
        # 1. Extract parameters from the SportOrg race memory database
        port_num = int("".join(filter(str.isdigit, str(self.port)))) if self.port and "".join(filter(str.isdigit, str(self.port))) else 0
        
        # Dynamic baud rate configuration
        saved_baud_idx = race().get_setting("impinj_baud_rate_idx", 6)
        baud_rate = BYTE(int(saved_baud_idx))
        
        # Safe antenna mode configuration
        check_ant_val = BYTE(1 if bool(race().get_setting("impinj_check_ant", True)) else 0)
        
        # --- NEW BLOCK: Fetch RF radiation power mapping state (defaults to 26 dBm) ---
        saved_power = race().get_setting("impinj_rf_power", 26)
        rf_power_val = BYTE(int(saved_power))
        
        if port_num > 0:
            self._logger.info(f"[RFID-DEBUG] Attempting to open specific target port: COM{port_num} (Baud: {baud_rate.value})")
            try:
                res = self.dll.OpenComPort(ctypes.c_int(port_num), ctypes.byref(self.com_adr), baud_rate, ctypes.byref(self.frm_handle))
                self._logger.info(f"[RFID-DEBUG] OpenComPort execution response payload: {res}, retrieved FrmHandle: {self.frm_handle.value}")
                if res == 0 and self.frm_handle.value >= 0:
                    self._logger.info(f"[RFID-DEBUG] Connection successfully established on target port COM{port_num}!")
                    
                    # Apply antenna validation protection context profiles
                    try: self.dll.SetCheckAnt(ctypes.byref(self.com_adr), check_ant_val, self.frm_handle)
                    except Exception: pass
                    
                    # --- NEW BLOCK: Transmit RF power calibration payload parameters to controller ---
                    try:
                        pow_res = self.dll.SetRfPower(ctypes.byref(self.com_adr), rf_power_val, self.frm_handle)
                        self._logger.info(f"[RFID-DEBUG] Power initialization (SetRfPower={rf_power_val.value} dBm) returned code: {pow_res}")
                    except Exception as e:
                        self._logger.warning(f"[RFID-DEBUG] Failed to call SetRfPower via DLL: {e}")
                        
                    return True
            except Exception as e:
                self._logger.error(f"[RFID-DEBUG] Failed to call OpenComPort: {e}")
                
        self._logger.info("[RFID-DEBUG] The specific port did not respond or is not specified. Launching AutoOpenComPort...")
        try:
            auto_port = ctypes.c_int(0)
            res = self.dll.AutoOpenComPort(ctypes.byref(auto_port), ctypes.byref(self.com_adr), baud_rate, ctypes.byref(self.frm_handle))
            self._logger.info(f"[RFID-DEBUG] AutoOpenComPort execution response payload: {res}. Autodetected port: COM{auto_port.value}, FrmHandle: {self.frm_handle.value}")
            if res == 0 and self.frm_handle.value >= 0:
                self._logger.info(f"[RFID-DEBUG] Connection successfully established via autodetected port COM{auto_port.value}!")
                
                # Apply antenna validation protection context profiles
                try: self.dll.SetCheckAnt(ctypes.byref(self.com_adr), check_ant_val, self.frm_handle)
                except Exception: pass
                
                # --- NEW BLOCK: Transmit RF power calibration payload parameters during auto connection setup ---
                try:
                    pow_res = self.dll.SetRfPower(ctypes.byref(self.com_adr), rf_power_val, self.frm_handle)
                    self._logger.info(f"[RFID-DEBUG] Power initialization (SetRfPower={rf_power_val.value} dBm) returned code: {pow_res}")
                except Exception as e:
                    self._logger.warning(f"[RFID-DEBUG] Error calling SetRfPower by DLL: {e}")
                    
                return True
        except Exception as e:
            self._logger.error(f"[RFID-DEBUG] Error calling AutoOpenComPort: {e}")
            
        self._logger.error("[RFID-DEBUG] Error connect to RFID controller")
        return False
    def run(self):
        self._logger.info("[RFID-DEBUG] run() method invoked. Initializing tracking pipeline...")
        
        if not self._init_dll():
            self._logger.error("[RFID-DEBUG] Error calling DLL from start")
            return
            
        if not self._connect_reader():
            self._logger.error("[RFID-DEBUG] Not startig , controller not connect")
            return
            
        self._logger.info("[RFID-DEBUG] Start SingleTagInventory_G2...")
        
        loop_counter = 0
        while main_thread().is_alive() and not self._stop_event.is_set():
            loop_counter += 1
            
            try:
                # Guaranteed allocation and zeroing out of memory buffer blocks before every DLL invocation context
                epc_buffer = (BYTE * 2000)()
                epc_length = ctypes.c_int(0)
                card_num = ctypes.c_int(0)

                # Calling the polling function from the DLL
                res = self.dll.SingleTagInventory_G2(
                    ctypes.byref(self.com_adr), 
                    epc_buffer, 
                    ctypes.byref(epc_length), 
                    ctypes.byref(card_num), 
                    self.frm_handle
                )
                
                # If a card is physically present in the buffer, process it!
                if card_num.value > 0 and epc_length.value > 0:
                    
                    # epc_buffer[0]— antenna number (skip it)
                    antenna_num = epc_buffer[0]
                    
                    # The actual EPC number goes from index 1 to epc_length.value inclusive
                    actual_epc_bytes = [epc_buffer[i] for i in range(1, epc_length.value + 1)]
                    raw_hex = "".join(f"{b:02X}" for b in actual_epc_bytes)
                    
                    # The last byte in the structure is the RSSI signal level
                    rssi_val = epc_buffer[epc_length.value + 1]
                    
                    self._logger.info(
                        f'[RFID-INFO] {translate("TAG READ:")}: {raw_hex} | '
                        f'{translate("Antenna :")}: {antenna_num} | '
                        f'RSSI: {rssi_val} | '
                        f'{translate("HW DLL response:")}: {res}'
                    )
                    
                    # Formatting the data structure with spaces for ResultThread
                    card_data = {
                        "epc": " ".join(raw_hex[i:i+2] for i in range(0, len(raw_hex), 2)), 
                        "time": OTime.now(),
                        "antenna": int(antenna_num)  # <-- Pass the hardware antenna ID forward
                    }
                    
                    # Filtering duplicates based on the competition program timeout
                    if card_data["epc"] not in self.timeout_list or card_data["time"] - self.timeout_list[card_data["epc"]] >= OTime(msec=self.timeout):
                        self.timeout_list[card_data["epc"]] = card_data["time"]
                        self._queue.put(ImpinjCommand("card_data", card_data), timeout=1)
                        self._logger.info(f"[RFID-DEBUG] Tag {card_data['epc']} successfully dispatched to Sportorg routing queue.")
                        
                else:
                    # Periodic idle log to show that the thread is alive
                    if loop_counter % 150 == 0:
                        self._logger.info(f"[RFID-DEBUG] Polling active. DLL response: {res}, Cards found: {card_num.value}")
                        
            except Exception as e:
                self._logger.error(f"[RFID-DEBUG] Error inside the polling loop: {e}")
                
            sleep(0.02)
            
        self._logger.info("[RFID-DEBUG] Exiting the polling loop. Shutting down.")
        if self.frm_handle.value >= 0:
            self.dll.CloseSpecComPort(self.frm_handle)
            self._logger.info("[RFID-DEBUG] COM-port closed")
class ResultThread(QThread):
    data_sender = Signal(object)
    def __init__(self, queue, stop_event, logger):
        super().__init__()
        self.setObjectName(self.__class__.__name__)
        self._queue, self._stop_event, self._logger = queue, stop_event, logger

    def run(self):
        sleep(1)
        while main_thread().is_alive() and not self._stop_event.is_set():
            try:
                cmd = self._queue.get(timeout=5)
                if cmd.command == "card_data":
                    self.data_sender.emit(self._get_result(cmd.data))
            except Empty:
                pass
            except Exception as e:
                self._logger.exception(e)

  
    @staticmethod
    def _get_result(card_data):
        result = memory.race().new_result(memory.ResultRfidImpinj)
        
        epc = str(card_data["epc"]).replace(" ", "").upper()
        
        if epc.isdecimal():
            result.card_number = int(epc)
        else:
            result.card_number = (int(epc, 16) + 5000000) % 10**8
        
        logging.root.info(f"[RFID-DEBUG] >>> Final processed chip card number in Sportorg: {result.card_number} <<<")
        
        result.finish_time = card_data["time"]
        

        return result


@singleton
class ImpinjClient:
    def __init__(self):
        self._queue, self._stop_event, self._impinj_thread, self._result_thread, self.port, self._logger, self._call_back = Queue(), Event(), None, None, None, logging.root, None

    def set_call(self, value):
        if self._call_back is None:
            self._call_back = value
        return self

    def start(self):
        self.port = memory.race().get_setting("system_port", None)
        self._stop_event.clear()
        
        self._logger.info(f"[RFID-DEBUG] Impinj Client - START button pressed. Current port:{self.port}")
        
        if not self._impinj_thread or self._impinj_thread.isFinished():
            self._logger.info("[RFID-DEBUG] Initializing and launching ImpinjThread execution sequence...")
            self._impinj_thread = ImpinjThread(self.port, self._queue, self._stop_event, self._logger, debug=True)
            self._impinj_thread.start()
        else:
            self._logger.warning("[RFID-DEBUG] Start attempt rejected: ImpinjThread is already up and running.")
            
        if not self._result_thread or self._result_thread.isFinished():
            self._result_thread = ResultThread(self._queue, self._stop_event, self._logger)
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()

    def stop(self):
        self._logger.info("[RFID-DEBUG] Impinj Client - STOP button pressed..")
        self._stop_event.set()

    def toggle(self):
        self.stop() if (self._impinj_thread and self._result_thread and not self._impinj_thread.isFinished() and not self._result_thread.isFinished()) else self.start()

    def is_alive(self):
        return bool(
            self._impinj_thread 
            and self._result_thread 
            and not self._impinj_thread.isFinished() 
            and not self._result_thread.isFinished()
        )

def detect_impinj_hardware(port_str, baud_idx):
    """
    Connection check and controller port auto-detection based on 
    the external reader_types.ini configuration file.
    """
    try:
        # Base directory where the current script is located
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Move up to the project root (3 levels up to sportorg)
        # root_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
        # Target folder in the root directory
        # libs_dir = os.path.join(root_dir, "libs", "rfid_impinj")
        libs_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "libs", "rfid_impinj"))

        # 1. Initializing the UHFReader288 DLL from the libs folder.
        # Loading the external ReaderType.ini configuration file from the libs folder.
        ini_path = os.path.join(libs_dir, "ReaderType.ini")
        dll_path = os.path.join(libs_dir, "UHFReader288.dll")
        
        config = configparser.ConfigParser(comment_prefixes=';')
        if os.path.exists(ini_path):
            config.read(ini_path, encoding='utf-8')
        else:
            logging.root.warning(f"[RFID-WARNING] External file {ini_path} not found! Fallback mode enabled.")

        if not os.path.exists(dll_path):
            logging.root.error(f"[RFID-ERROR] DLL library not found at path: {dll_path}")
            return None
            
        # Add subfolder to Windows search paths for dependent libraries
        if hasattr(os, 'add_dll_directory'):
            try: 
                os.add_dll_directory(os.path.dirname(dll_path))
            except Exception: 
                pass
                
        dll = ctypes.WinDLL(dll_path, winmode=0)
        
        # Check if the port number is valid
        port_num = int("".join(filter(str.isdigit, str(port_str)))) if port_str else 0
        if port_num == 0:
            return None
            
        com_adr = ctypes.c_ubyte(0xFF)
        baud_rate = ctypes.c_ubyte(baud_idx)
        frm_handle = ctypes.c_int(0)
        
        # Opening COM port
        result = dll.OpenComPort(ctypes.c_int(port_num), ctypes.byref(com_adr), baud_rate, ctypes.byref(frm_handle))
        if result != 0:
            return None
            
        # Allocate memory for SDK response variables
        version_info = (ctypes.c_ubyte * 2)()
        reader_type = ctypes.c_ubyte(0)
        tr_type = ctypes.c_ubyte(0)
        dmaxfre = ctypes.c_ubyte(0)
        dminfre = ctypes.c_ubyte(0)
        power_dbm = ctypes.c_ubyte(0)
        scan_time = ctypes.c_ubyte(0)
        ant_cfg0 = ctypes.c_ubyte(0)
        beep_en = ctypes.c_ubyte(0)
        ant_cfg1 = ctypes.c_ubyte(0)
        check_ant = ctypes.c_ubyte(0)
        
        info_res = dll.GetReaderInformation(
            ctypes.byref(com_adr), version_info, ctypes.byref(reader_type),
            ctypes.byref(tr_type), ctypes.byref(dmaxfre), ctypes.byref(dminfre),
            ctypes.byref(power_dbm), ctypes.byref(scan_time), ctypes.byref(ant_cfg0),
            ctypes.byref(beep_en), ctypes.byref(ant_cfg1), ctypes.byref(check_ant),
            frm_handle
        )
        
        hardware_ports = 4
        firmware_version = "0.0"
        reader_type_hex = "00"
        chip_type = "Unknown"
        model_name = "Unknown"
        
        if info_res == 0:
            type_code = reader_type.value
            reader_type_hex = f"0x{type_code:02X}"
            firmware_version = f"{version_info[0]}.{version_info[1]}"
            
            # Looking for a section in the INI file
            section_name = reader_type_hex
            if config.has_section(section_name):
                hardware_ports = config.getint(section_name, "AntennaNum", fallback=4)
                chip_type = config.get(section_name, "ChipType", fallback="EX10")
                model_name = config.get(section_name, "RDVersion", fallback="UHF-Reader")
            else:
                # Fallback parsing by bitmask
                hardware_ports = 16 if ant_cfg1.value > 0 else (8 if ant_cfg0.value > 0x0F else 4)
                model_name = f"Generic (Type {reader_type_hex})"
                chip_type = "EX10/R2000"
                
            logging.root.info(f"[RFID-INFO] INI parsing successful. Section: {section_name} | Ports: {hardware_ports} | Chip: {chip_type}")
        else:
            logging.root.error(f"[RFID-INFO] GetReaderInformation error: {info_res}")
            
        dll.CloseSpecComPort(frm_handle.value)
        
        return {
            "port": port_str,
            "ports_count": hardware_ports,
            "version": firmware_version,
            "type": reader_type_hex,
            "chip": chip_type,
            "model": model_name
        }
        
    except Exception as e:
        logging.root.error(f"[RFID-ERROR] Critical detector error due to INI/DLL: {e}")
        return None

def check_impinj_connection(self):
        """RFID reader communication check (UI wrapper over the hardware detector)"""
        current_port = self.impinj_settings_widget.port_combo.currentData()
        current_baud_idx = self.impinj_settings_widget.baud_combo.currentData()
        
        # Prepare the list of COM ports for validation scanning
        ports_to_check = [f"COM{i}" for i in range(1, 21)] if current_port == "auto" else [current_port]
        
        if current_port == "auto":
            self.lbl_connect_status.setText(translate("Scaninig COM ports..."))
            self.lbl_connect_status.setStyleSheet("color: orange;")
        else:
            self.lbl_connect_status.setText(f"{translate('Checking')} {current_port}...")
            self.lbl_connect_status.setStyleSheet("color: gray;")
            
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        device_info = None
        
        # Iterate over ports and invoke the standalone hardware detection function
        for port_str in ports_to_check:
            res = detect_impinj_hardware(port_str, current_baud_idx)
            if res is not None:
                device_info = res
                break
                
        if device_info:
            # Reader detected! Lock the respective port inside the user interface combo box context
            idx = self.impinj_settings_widget.port_combo.findData(device_info["port"])
            if idx >= 0:
                self.impinj_settings_widget.port_combo.setCurrentIndex(idx)
                
            # Rebuild checkbox grid configuration layouts matching actual physical reader antenna counts
            self.impinj_settings_widget.rebuild_antenna_checkboxes(device_info["ports_count"])
            
            # Format and display the synchronized reader operational metrics text payload layout
            status_text = (
                f"{translate('STATUS: OK')} ("
                f"{device_info['port']} | "
                f"{translate('Type')}: 0x{device_info['type']} | "
                f"FW: v{device_info['version']} | "
                f"{translate('Ports')}: {device_info['ports_count']})"
            )
            self.lbl_connect_status.setText(status_text)
            self.lbl_connect_status.setStyleSheet("color: green;")
        else:
            # Device hardware controller handshake interface response timed out or not found
            if current_port == "auto":
                self.lbl_connect_status.setText(translate("STATUS: Impinj Reader not found on COM1-COM20"))
            else:
                self.lbl_connect_status.setText(f"{translate('STATUS: Connection error to')} {current_port}")
            self.lbl_connect_status.setStyleSheet("color: red;")

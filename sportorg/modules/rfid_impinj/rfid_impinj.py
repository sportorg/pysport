import logging
import os
import ctypes
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
        self._logger.info(f"[RFID-DEBUG] Поток инициализирован. Заданный порт из настроек: {self.port}")

    def _init_dll(self):
        try:
            # 1. Задаем переносимый путь относительно текущего файла скрипта
            base_dir = os.path.dirname(os.path.abspath(__file__))
            dll_path = os.path.abspath(os.path.join(base_dir, "..", "..", "libs", "rfid_impinj", "UHFReader288.dll"))
            
            self._logger.info(f"[RFID-DEBUG] Попытка загрузки DLL по пути: {dll_path}")
            
            # 2. Добавляем папку в поиск Windows для связанных зависимостей DLL (актуально для Python 3.8+)
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(os.path.dirname(dll_path))
                except Exception:
                    pass
            
            # 3. Загружаем библиотеку
            self.dll = ctypes.WinDLL(dll_path, winmode=0)
            self._logger.info("[RFID-DEBUG] Библиотека UHFReader288.dll успешно загружена в память.")
            return True
        except Exception as e:
            self._logger.error(f"[RFID-DEBUG] КРИТИЧЕСКАЯ ОШИБКА загрузки UHFReader288.dll: {e}")
            return False


    def _connect_reader(self):
        # 1. Извлекаем параметры из базы данных гонки SportOrg
        port_num = int("".join(filter(str.isdigit, str(self.port)))) if self.port and "".join(filter(str.isdigit, str(self.port))) else 0
        
        # Динамическая скорость (исправление из прошлого шага)
        saved_baud_idx = race().get_setting("impinj_baud_rate_idx", 6)
        baud_rate = BYTE(int(saved_baud_idx))
        
        # Безопасный режим (исправление из прошлого шага)
        check_ant_val = BYTE(1 if bool(race().get_setting("impinj_check_ant", True)) else 0)
        
        # --- НОВЫЙ БЛОК: Получаем мощность из виджета (по умолчанию 26 dBm) ---
        saved_power = race().get_setting("impinj_rf_power", 26)
        rf_power_val = BYTE(int(saved_power))
        
        if port_num > 0:
            self._logger.info(f"[RFID-DEBUG] Пробуем открыть конкретный порт: COM{port_num} (Baud: {baud_rate.value})")
            try:
                res = self.dll.OpenComPort(ctypes.c_int(port_num), ctypes.byref(self.com_adr), baud_rate, ctypes.byref(self.frm_handle))
                self._logger.info(f"[RFID-DEBUG] Результат OpenComPort: {res}, полученный FrmHandle: {self.frm_handle.value}")
                if res == 0 and self.frm_handle.value >= 0:
                    self._logger.info(f"[RFID-DEBUG] Успешное подключение к COM{port_num}!")
                    
                    # Передаем безопасный режим антенн
                    try: self.dll.SetCheckAnt(ctypes.byref(self.com_adr), check_ant_val, self.frm_handle)
                    except Exception: pass
                    
                    # --- НОВЫЙ БЛОК: Передаем мощность излучения в контроллер ---
                    try:
                        pow_res = self.dll.SetRfPower(ctypes.byref(self.com_adr), rf_power_val, self.frm_handle)
                        self._logger.info(f"[RFID-DEBUG] Установка мощности (SetRfPower={rf_power_val.value} dBm) вернула код: {pow_res}")
                    except Exception as e:
                        self._logger.warning(f"[RFID-DEBUG] Не удалось вызвать SetRfPower через DLL: {e}")
                        
                    return True
            except Exception as e:
                self._logger.error(f"[RFID-DEBUG] Сбой при вызове OpenComPort: {e}")
                
        self._logger.info("[RFID-DEBUG] Конкретный порт не ответил или не задан. Запуск AutoOpenComPort...")
        try:
            auto_port = ctypes.c_int(0)
            res = self.dll.AutoOpenComPort(ctypes.byref(auto_port), ctypes.byref(self.com_adr), baud_rate, ctypes.byref(self.frm_handle))
            self._logger.info(f"[RFID-DEBUG] Результат AutoOpenComPort: {res}. Найден порт: COM{auto_port.value}, FrmHandle: {self.frm_handle.value}")
            if res == 0 and self.frm_handle.value >= 0:
                self._logger.info(f"[RFID-DEBUG] Успешное авто-подключение к COM{auto_port.value}!")
                
                # Передаем безопасный режим антенн
                try: self.dll.SetCheckAnt(ctypes.byref(self.com_adr), check_ant_val, self.frm_handle)
                except Exception: pass
                
                # --- НОВЫЙ БЛОК: Передаем мощность при автоподключении ---
                try:
                    pow_res = self.dll.SetRfPower(ctypes.byref(self.com_adr), rf_power_val, self.frm_handle)
                    self._logger.info(f"[RFID-DEBUG] Установка мощности (SetRfPower={rf_power_val.value} dBm) вернула код: {pow_res}")
                except Exception as e:
                    self._logger.warning(f"[RFID-DEBUG] Не удалось вызвать SetRfPower через DLL: {e}")
                    
                return True
        except Exception as e:
            self._logger.error(f"[RFID-DEBUG] Сбой при вызове AutoOpenComPort: {e}")
            
        self._logger.error("[RFID-DEBUG] Не удалось подключиться к RFID-считывателю ни одним из способов.")
        return False


    def run(self):
        self._logger.info("[RFID-DEBUG] Метод run() запущен. Начинаем инициализацию...")
        
        if not self._init_dll():
            self._logger.error("[RFID-DEBUG] Поток остановлен: ошибка инициализации DLL.")
            return
            
        if not self._connect_reader():
            self._logger.error("[RFID-DEBUG] Поток остановлен: устройство не подключено.")
            return
            
        self._logger.info("[RFID-DEBUG] Входим в бесконечный цикл опроса антенны (SingleTagInventory_G2)...")
        
        loop_counter = 0
        while main_thread().is_alive() and not self._stop_event.is_set():
            loop_counter += 1
            
            try:
                # Гарантированно выделяем и ОБНУЛЯЕМ память перед каждым опросом к DLL
                epc_buffer = (BYTE * 2000)()
                epc_length = ctypes.c_int(0)
                card_num = ctypes.c_int(0)

                # Вызываем функцию опроса из DLL
                res = self.dll.SingleTagInventory_G2(
                    ctypes.byref(self.com_adr), 
                    epc_buffer, 
                    ctypes.byref(epc_length), 
                    ctypes.byref(card_num), 
                    self.frm_handle
                )
                
                # Если в буфере физически появилась карта — обрабатываем её!
                if card_num.value > 0 and epc_length.value > 0:
                    
                    # epc_buffer[0] — номер антенны (пропускаем его)
                    antenna_num = epc_buffer[0]
                    
                    # Сам EPC-номер идет с 1-го индекса по epc_length.value включительно
                    actual_epc_bytes = [epc_buffer[i] for i in range(1, epc_length.value + 1)]
                    raw_hex = "".join(f"{b:02X}" for b in actual_epc_bytes)
                    
                    # Последний байт в структуре — уровень сигнала RSSI
                    rssi_val = epc_buffer[epc_length.value + 1]
                    
                    self._logger.info(
                        f"[RFID-DEBUG] МЕТКА НАЙДЕНА! Антенна: {antenna_num} | "
                        f"Чистый EPC: {raw_hex} | RSSI: {rssi_val} | Ответ DLL: {res}"
                    )
                    
                    # Формируем структуру данных с пробелами для ResultThread
                    card_data = {
                        "epc": " ".join(raw_hex[i:i+2] for i in range(0, len(raw_hex), 2)), 
                        "time": OTime.now(),
                        "antenna": int(antenna_num)  # <-- Передаем номер антенны дальше
                    }
                    
                    # Фильтрация дубликатов по таймауту программы соревнований
                    if card_data["epc"] not in self.timeout_list or card_data["time"] - self.timeout_list[card_data["epc"]] >= OTime(msec=self.timeout):
                        self.timeout_list[card_data["epc"]] = card_data["time"]
                        self._queue.put(ImpinjCommand("card_data", card_data), timeout=1)
                        self._logger.info(f"[RFID-DEBUG] Метка {card_data['epc']} отправлена в очередь Sportorg.")
                        
                else:
                    # Периодический лог холостого хода, чтобы видеть, что поток живет
                    if loop_counter % 150 == 0:
                        self._logger.info(f"[RFID-DEBUG] Опрос активен. Ответ DLL: {res}, Найдено карт: {card_num.value}")
                        
            except Exception as e:
                self._logger.error(f"[RFID-DEBUG] Ошибка внутри цикла опроса: {e}")
                
            sleep(0.02)
            
        self._logger.info("[RFID-DEBUG] Выход из цикла опроса. Завершаем работу.")
        if self.frm_handle.value >= 0:
            self.dll.CloseSpecComPort(self.frm_handle)
            self._logger.info("[RFID-DEBUG] COM-порт считывателя закрыт.")



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
        
        logging.root.info(f"[RFID-DEBUG] >>> Итоговый чистый номер чипа в Sportorg: {result.card_number} <<<")
        
        result.finish_time = card_data["time"]
        
        # # --- ЗАПИСЬ НОМЕРА АНТЕННЫ В КОММЕНТАРИЙ ОТМЕТКИ ---
        # if "antenna" in card_data:
        #     result.comment = f"Антенна {card_data["antenna"]}"  # Текст, который появится в сплитах
        #                 # Если антенна 1 -> станция 101, если антенна 2 -> 102 и т.д.
        #     result.station = 100 + int(card_data["antenna"])
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
        
        self._logger.info(f"[RFID-DEBUG] Нажата кнопка СТАРТ в клиенте ImpinjClient. Текущий порт: {self.port}")
        
        if not self._impinj_thread or self._impinj_thread.isFinished():
            self._logger.info("[RFID-DEBUG] Создаем и запускаем поток ImpinjThread...")
            self._impinj_thread = ImpinjThread(self.port, self._queue, self._stop_event, self._logger, debug=True)
            self._impinj_thread.start()
        else:
            self._logger.warning("[RFID-DEBUG] Попытка старта отклонена: ImpinjThread уже запущен и работает.")
            
        if not self._result_thread or self._result_thread.isFinished():
            self._result_thread = ResultThread(self._queue, self._stop_event, self._logger)
            if self._call_back:
                self._result_thread.data_sender.connect(self._call_back)
            self._result_thread.start()

    def stop(self):
        self._logger.info("[RFID-DEBUG] Нажата кнопка СТОП в клиенте ImpinjClient.")
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
import os
import ctypes
import logging

import os
import ctypes
import logging
import configparser

import os
import ctypes
import logging
import configparser

def detect_impinj_hardware(port_str, baud_idx):
    """
    Проверка связи и автоопределение портов контроллера на основе 
    внешнего конфигурационного файла reader_types.ini
    """
    try:
        # Базовая директория, где лежит текущий скрипт
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Поднимаемся к корню проекта (на 3 уровня вверх до sportorg)
       # root_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
        # Целевая папка в корне
        #libs_dir = os.path.join(root_dir, "libs", "rfid_impinj")
        libs_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "libs", "rfid_impinj"))

        # 1. Инициализация DLL UHFReader288 из папки libsЗагружаем внешний файл конфигурации ReaderType.ini из папки libs
        ini_path = os.path.join(libs_dir, "ReaderType.ini")
        dll_path = os.path.join(libs_dir, "UHFReader288.dll")
        
        config = configparser.ConfigParser(comment_prefixes=';')
        if os.path.exists(ini_path):
            config.read(ini_path, encoding='utf-8')
        else:
            logging.root.warning(f"[RFID-WARNING] Внешний файл {ini_path} не найден! Включен фолбэк-режим.")


        
        if not os.path.exists(dll_path):
            logging.root.error(f"[RFID-ERROR] DLL библиотека не найдена по пути: {dll_path}")
            return None
            
        # Добавляем подпапку в пути поиска Windows для зависимых библиотек
        if hasattr(os, 'add_dll_directory'):
            try: 
                os.add_dll_directory(os.path.dirname(dll_path))
            except Exception: 
                pass
                
        dll = ctypes.WinDLL(dll_path, winmode=0)
        
        # Валидация номера порта
        port_num = int("".join(filter(str.isdigit, str(port_str)))) if port_str else 0
        if port_num == 0:
            return None
            
        com_adr = ctypes.c_ubyte(0xFF)
        baud_rate = ctypes.c_ubyte(baud_idx)
        frm_handle = ctypes.c_int(0)
        
        # Открываем COM-порт
        result = dll.OpenComPort(ctypes.c_int(port_num), ctypes.byref(com_adr), baud_rate, ctypes.byref(frm_handle))
        if result != 0:
            return None
            
        # Аллоцируем память под переменные ответа SDK
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
            
            # Ищем секцию в INI файле
            section_name = reader_type_hex
            if config.has_section(section_name):
                hardware_ports = config.getint(section_name, "AntennaNum", fallback=4)
                chip_type = config.get(section_name, "ChipType", fallback="EX10")
                model_name = config.get(section_name, "RDVersion", fallback="UHF-Reader")
            else:
                # Резервный разбор по маске бит
                hardware_ports = 16 if ant_cfg1.value > 0 else (8 if ant_cfg0.value > 0x0F else 4)
                model_name = f"Generic (Type {reader_type_hex})"
                chip_type = "EX10/R2000"
                
            logging.root.info(f"[RFID-INFO] Парсинг INI успешен. Секция: {section_name} | Портов: {hardware_ports} | Чип: {chip_type}")
        else:
            logging.root.error(f"[RFID-INFO] Ошибка GetReaderInformation: {info_res}")
            
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
        logging.root.error(f"[RFID-ERROR] Критическая ошибка детектора из-за INI/DLL: {e}")
        return None

# sfrwriter.py
import logging
import platform
from datetime import datetime
from time import sleep

if platform.system() == "Windows":
    from pywinusb.hid import HidDevice, HidDeviceFilter


class SFRWriter:
    """Класс для записи данных на SFR-карты"""
    
    # Настройки устройства (аналогично SFRReader)
    VENDOR_ID = 0x2047
    PRODUCT_ID = 0x301
    HID_REPORT_COUNT = 64
    
    # Команды протокола
    CMD_INIT = 0x3F
    CMD_START = 0xFD
    CMD_END = 0xFE
    CMD_WRITE_CODE = 0x02
    
    def __init__(self, debug=False, logger=None):
        self._device = None
        self._debug = debug
        self._logger = logger
        self._block = False
        
        self._connect_writer()
    
    def is_device_connected(self):
        if self._device and isinstance(self._device, HidDevice):
            if self._device.is_plugged() and self._device.is_opened():
                return True
        return False
    
    def _connect_writer(self):
        """Подключение к SFR-станции"""
        if platform.system() != "Windows":
            raise SFRWriterException("Unsupported platform: %s" % platform.system())
        
        hid_filter = HidDeviceFilter(
            vendor_id=self.VENDOR_ID, product_id=self.PRODUCT_ID
        )
        devices = hid_filter.get_devices()
        
        if devices:
            device = devices[0]
            device.open()
            self._device = device
            
            if self._logger:
                self._logger.debug("SFR station connected for writing")
                
            # Устанавливаем обработчик данных
            device.set_raw_data_handler(self._data_handler)
        else:
            if self._logger:
                self._logger.debug("SFR station not found or unavailable")
            raise SFRWriterException("SFR station not found")
    
    def _data_handler(self, data):
        """Обработчик ответов от устройства"""
        if self._debug:
            logging.debug("sfrwriter.data_handler: Raw data: %s", str(data))
        
        self._block = False
    
    def _send_command(self, command, wait_response=True):
        """Отправка команды на устройство"""
        if self._debug:
            logging.debug("sfrwriter.send_command: ==>> command '%s'", str(command))
        
        buffer = self._get_hid_buffer(command)
        
        if self.is_device_connected():
            if wait_response:
                self._block = True
                try:
                    self._device.send_output_report(buffer)
                    
                    # Ждем ответа
                    count = 0
                    while self._block and count < 100:  # timeout
                        sleep(0.01)
                        count += 1
                        
                except Exception as e:
                    if self._debug:
                        logging.debug("sfrwriter.send_command: device disconnected")
                    self._logger.error(str(e))
                    self.disconnect()
                
                self._block = False
            else:
                self._device.send_output_report(buffer)
    
    def _get_hid_buffer(self, command):
        """Подготовка буфера для HID-отчета"""
        buffer = [0x00] * self.HID_REPORT_COUNT
        for i in range(len(command)):
            buffer[i] = command[i]
        return buffer
    
    @staticmethod
    def _calculate_checksum(data):
        """Расчет контрольной суммы"""
        checksum = 0
        for byte in data:
            checksum = (checksum + byte) & 0xFF
        return checksum
    
    def write_card_data(self, card_data):
        """
        Запись данных на SFR-карту
        card_data: словарь с данными для записи
        """
        try:
            # Команда инициализации записи
            init_command = [self.CMD_INIT, 0x05, self.CMD_START, self.CMD_WRITE_CODE, 0x01, 0x00, self.CMD_END]
            init_command[5] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x01])
            self._send_command(init_command)
            
            # Запись номера карты (если указан)
            if 'card_number' in card_data and card_data['card_number']:
                self._write_card_number(card_data['card_number'])
            
            # Запись номера участника
            if 'bib' in card_data and card_data['bib']:
                self._write_bib(card_data['bib'])
            
            # Запись времени старта
            if 'start_time' in card_data and card_data['start_time']:
                self._write_start_time(card_data['start_time'])
            
            # Запись отметок на КП
            if 'punches' in card_data:
                for punch in card_data['punches']:
                    self._write_punch(punch['code'], punch['time'])
            
            # Запись времени финиша
            if 'finish_time' in card_data and card_data['finish_time']:
                self._write_finish_time(card_data['finish_time'])
            
            # Финальная команда
            final_command = [self.CMD_INIT, 0x05, self.CMD_START, self.CMD_WRITE_CODE, 0x02, 0x00, self.CMD_END]
            final_command[5] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x02])
            self._send_command(final_command, wait_response=False)
            
            return True
            
        except Exception as e:
            logging.error("Error writing card data: %s", str(e))
            return False
    
    def _write_card_number(self, card_number):
        """Запись номера карты"""
        # Преобразование номера карты в байты
        card_bytes = self._number_to_bytes(card_number, 4)
        command = [self.CMD_INIT, 0x08, self.CMD_START, self.CMD_WRITE_CODE, 0x10] + card_bytes + [0x00, self.CMD_END]
        command[7] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x10] + card_bytes)
        self._send_command(command)
    
    def _write_bib(self, bib):
        """Запись номера участника"""
        bib_bytes = self._number_to_bytes(bib, 3)
        command = [self.CMD_INIT, 0x07, self.CMD_START, self.CMD_WRITE_CODE, 0x11] + bib_bytes + [0x00, self.CMD_END]
        command[6] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x11] + bib_bytes)
        self._send_command(command)
    
    def _write_start_time(self, start_time):
        """Запись времени старта"""
        if isinstance(start_time, datetime):
            time_bytes = self._time_to_bytes(start_time)
            command = [self.CMD_INIT, 0x07, self.CMD_START, self.CMD_WRITE_CODE, 0x20] + time_bytes + [0x00, self.CMD_END]
            command[6] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x20] + time_bytes)
            self._send_command(command)
    
    def _write_finish_time(self, finish_time):
        """Запись времени финиша"""
        if isinstance(finish_time, datetime):
            time_bytes = self._time_to_bytes(finish_time)
            command = [self.CMD_INIT, 0x07, self.CMD_START, self.CMD_WRITE_CODE, 0x21] + time_bytes + [0x00, self.CMD_END]
            command[6] = self._calculate_checksum([self.CMD_WRITE_CODE, 0x21] + time_bytes)
            self._send_command(command)
    
    def _write_punch(self, code, punch_time):
        """Запись отметки на КП"""
        if isinstance(punch_time, datetime):
            time_bytes = self._time_to_bytes(punch_time)
            code_byte = int(code) & 0xFF
            
            command = [self.CMD_INIT, 0x07, self.CMD_START, self.CMD_WRITE_CODE, code_byte] + time_bytes + [0x00, self.CMD_END]
            command[6] = self._calculate_checksum([self.CMD_WRITE_CODE, code_byte] + time_bytes)
            self._send_command(command)
    
    @staticmethod
    def _number_to_bytes(number, num_bytes):
        """Преобразование числа в массив байт"""
        result = []
        for i in range(num_bytes):
            result.append(number & 0xFF)
            number >>= 8
        return result
    
    @staticmethod
    def _time_to_bytes(dt):
        """Преобразование времени в байты формата SFR"""
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        
        # Преобразование в BCD-формат
        h1 = hour // 10
        h2 = hour % 10
        m1 = minute // 10
        m2 = minute % 10
        s1 = second // 10
        s2 = second % 10
        
        return [
            (h1 << 4) | h2,
            (m1 << 4) | m2,
            (s1 << 4) | s2
        ]
    
    def disconnect(self):
        """Отключение от устройства"""
        if self._device:
            self._device.close()
    
    def __del__(self):
        self.disconnect()


class SFRWriterException(Exception):
    pass


def write_to_sfr_card(card_data, station_debug=False):
    """
    Функция для записи данных на SFR-карту
    card_data: словарь с данными:
        - card_number: номер карты
        - bib: номер участника
        - start_time: время старта (datetime)
        - finish_time: время финиша (datetime)
        - punches: список отметок [{'code': '31', 'time': datetime}, ...]
    """
    try:
        writer = SFRWriter(debug=station_debug)
        success = writer.write_card_data(card_data)
        writer.disconnect()
        return success
    except Exception as e:
        logging.error("Failed to write SFR card: %s", str(e))
        return False
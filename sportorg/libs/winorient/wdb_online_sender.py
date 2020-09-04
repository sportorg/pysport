import logging
import os
import threading
import time

from pip._vendor import requests

from sportorg.common.otime import OTime
from sportorg.libs.winorient.wdb import WDB, WDBFinish, parse_wdb
from sportorg.utils.time import int_to_otime, time_to_hhmmss

ONLINE_NUMBER = 'num'
ONLINE_RESULT = 'r'
ONLINE_TIME = 't'
ONLINE_FLAG = 'fl'
ONLINE_LAP = 'dubl'
ONLINE_SPLIT = 's'
ONLINE_PARAM1 = 'lis'
ONLINE_SCORE = 'ochki'
ONLINE_FINISH_TIME = 'tfin'
ONLINE_SI = 'si'
ONLINE_COMMENT = 'com'


class WdbOnlineSender(object):
    def __init__(self):
        self.url = ''
        self.file_path = ''
        self.send_splits = True
        self.check_interval = 1000  # ms
        self.is_running = False
        self.last_modification_time = None
        self.current_wdb = None
        self.tr = None

    def start(self):
        self.tr = threading.Thread(target=self.run)
        self.tr.start()

    def run(self):
        while True:
            logging.info('thread iteration')
            mod_time = time.ctime(os.path.getmtime(self.file_path))
            if self.last_modification_time:
                if mod_time != self.last_modification_time:
                    self.read()
            else:
                self.read()
            self.last_modification_time = mod_time
            time.sleep(float(self.check_interval) / 1000)

    def read(self):
        wdb = parse_wdb(self.file_path)
        new_finishes = self.get_new_finishes(wdb)
        self.current_wdb = wdb
        for finish in new_finishes:
            self.send(finish)

    def get_new_finishes(self, wdb):
        ret = []
        if wdb and isinstance(wdb, WDB):
            for new_finish in wdb.fin:
                if isinstance(new_finish, WDBFinish):
                    bib = new_finish.number
                    if bib:
                        if self.current_wdb and isinstance(self.current_wdb, WDB):
                            old_finish = self.current_wdb.find_finish_by_number(bib)

                            if old_finish and isinstance(old_finish, WDBFinish):

                                if old_finish.time != new_finish.time:
                                    # result changed
                                    ret.append(new_finish)
                                    continue

                                old_person = self.current_wdb.find_man_by_number(
                                    old_finish.number
                                )
                                new_person = wdb.find_man_by_number(new_finish.number)

                                if old_person and new_person:
                                    if old_person.status != new_person.status:
                                        # status changed
                                        ret.append(new_finish)
                                        continue

                            else:
                                # new finish
                                ret.append(new_finish)
                                continue
                        else:
                            # first run, empty previous base
                            ret.append(new_finish)
                            continue
        return ret

    def send(self, finish):
        if finish and isinstance(finish, WDBFinish):
            man = self.current_wdb.find_man_by_number(finish.number)
            ret = self.url
            ret += ONLINE_NUMBER + '=' + str(finish.number)
            ret += '&' + ONLINE_RESULT + '=' + time_to_hhmmss(int_to_otime(man.result))
            ret += '&' + ONLINE_FLAG + '=' + str(man.status)
            ret += (
                '&' + ONLINE_TIME + '=' + str(OTime.now().to_sec() * 100)
            )  # WO-compatible time in sec * 100
            if self.send_splits:
                splits = self.get_splits(self.current_wdb, man)
                ret += '&' + ONLINE_SPLIT + '=' + splits

            logging.info(ret)
            res = requests.get(ret)

    def get_splits(self, wdb, man):
        """
        строка со сплитами. WinOrient передает её в закодированном бинарном формате
        Формат: [SSSSSSTTTTTTCC]*
        SSSSSS - номер чипа в 16-чной системе
        TTTTTT - время в 16-чной системе
        СС - номер КП в 16-чной системе
        """

        chip = man.get_chip()
        separator = ''
        ret = ''
        for cur_punch in chip.punch:
            if cur_punch.code:
                split = '{:06x}{:06x}{:02x}'.format(
                    chip.id, int(cur_punch.time / 100), cur_punch.code
                )
                ret += split + separator
        return ret

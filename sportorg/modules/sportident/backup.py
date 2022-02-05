import logging
import sys
from datetime import datetime
from multiprocessing import Process

from sportorg import config
from sportorg.common.fake_std import FakeStd
from sportorg.common.otime import OTime
from sportorg.models import memory
from sportorg.models.memory import ResultSportident, race
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.utils.time import time_to_hhmmss, time_to_otime, hhmmss_to_time


class BackupProcess(Process):
    def __init__(self, text):
        super().__init__()
        self.data = text

    def run(self):
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            with open(
                    config.log_dir('si{}.log'.format(datetime.now().strftime('%Y%m%d'))),
                    'a',
            ) as f:
                f.write(self.data)
        except Exception as e:
            logging.error(str(e))


def backup_data(card_data):
    text = 'start\n{}\n{}\n{}\n'.format(
        card_data['card_number'],
        time_to_hhmmss(card_data['start']) if 'start' in card_data else '',
        time_to_hhmmss(card_data['finish']) if 'finish' in card_data else '',
    )
    text += 'split_start\n'
    for i in range(len(card_data['punches'])):
        text += '{} {}\n'.format(
            card_data['punches'][i][0], time_to_hhmmss(card_data['punches'][i][1])
        )

    text += 'split_end\n'
    text += 'end\n'

    BackupProcess(text).start()


def load_backup(file_name):
    def parse_time(hhmmss_time):
        if hhmmss_time == "":
            return OTime()
        return time_to_otime(hhmmss_to_time(hhmmss_time))

    obj = race()

    def find_person(card_number):
        for p in obj.persons:
            if p.card_number == card_number:
                return p
        return None

    state = 0
    result = {
        "card_number": 0,
        "start-time": 0,
        "finish-time": 0,
        "splits": []
    }

    for line in open(file_name):
        line = " ".join(line.split())
        if state == 0 and line == "start":
            state = 1
            result['splits'] = []
        elif state == 1:
            state = 2
            result['card_number'] = line
        elif state == 2:
            state = 3
            result['start-time'] = parse_time(line)
        elif state == 3:
            state = 4
            result['finish-time'] = parse_time(line)
        elif state == 4 and line == "split_start":
            state = 5
        elif state == 5 and line != "split_end":
            control, time = line.split()
            result['splits'].append((int(control), parse_time(time)))
        elif state == 5 and line == "split_end":
            state = 6
        elif state == 6 and line == "end":
            mem_result = memory.race().new_result(ResultSportident)
            card_number = int(result['card_number'])
            person = find_person(card_number)
            mem_result.card_number = card_number
            mem_result.person = person

            if result['start-time'] != 0:
                mem_result.start_time = result['start-time']
            if result['finish-time'] != 0:
                mem_result.finish_time = result['finish-time']

            for leg in result['splits']:
                split = memory.Split()
                split.code = leg[0]
                split.time = leg[1]
                split.days = 0
                mem_result.splits.append(split)

            ResultSportidentGeneration(mem_result).add_result()
            logging.debug("Import result with card_number=" + result['card_number'])
            state = 0

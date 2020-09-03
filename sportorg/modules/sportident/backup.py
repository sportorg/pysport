import logging
import sys
from datetime import datetime
from multiprocessing import Process

from sportorg import config
from sportorg.common.fake_std import FakeStd
from sportorg.utils.time import time_to_hhmmss


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
        time_to_hhmmss(card_data['start']) if card_data['start'] else '',
        time_to_hhmmss(card_data['finish']) if card_data['finish'] else '',
    )
    text += 'split_start\n'
    for i in range(len(card_data['punches'])):
        text += '{} {}\n'.format(
            card_data['punches'][i][0], time_to_hhmmss(card_data['punches'][i][1])
        )

    text += 'split_end\n'
    text += 'end\n'

    BackupProcess(text).start()

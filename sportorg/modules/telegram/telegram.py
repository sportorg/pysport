import logging
import sys
from threading import Thread

from sportorg.common.fake_std import FakeStd
from sportorg.common.singleton import singleton
from sportorg.libs.telegram.telegram import Telegram
from sportorg.models.memory import race


class TelegramSendThread(Thread):
    def __init__(self, token, chat_id, text, parse_mode=''):
        super().__init__()
        self.setName(TelegramSendThread.__class__.__name__)
        self.token = token
        self.chat_id = chat_id
        self.text = text
        self.parse_mode = parse_mode

    def run(self):
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            Telegram(self.token).send_message(self.chat_id, self.text, self.parse_mode)
        except Exception as e:
            logging.error(str(e))


class BotOption:
    def __init__(self, token, chat_id, template, parse_mode, enabled=False):
        self.token = token
        self.chat_id = chat_id
        self.template = template
        self.parse_mode = parse_mode
        self.enabled = enabled


@singleton
class TelegramClient:
    @staticmethod
    def get_options():
        obj = race()
        return BotOption(
            obj.get_setting('telegram_token', ''),
            obj.get_setting('telegram_chat_id', ''),
            obj.get_setting('telegram_template', ''),
            obj.get_setting('telegram_parse_mode', ''),
            obj.get_setting('telegram_enabled', False),
        )

    def send_result(self, result):
        if result.person:
            self.send(
                {
                    'group': result.person.group.name if result.person.group else '',
                    'name': result.person.full_name,
                    'bib': result.person.bib,
                    'result': result.get_result(),
                    'place': result.place,
                    'penalty_time': result.penalty_time,
                    'penalty_laps': result.penalty_laps,
                }
            )

    def send(self, data_dict):
        options = self.get_options()
        if not options.enabled or not options.token or not options.chat_id:
            return
        text = options.template
        try:
            for key, val in data_dict.items():
                text = text.replace('{' + str(key) + '}', str(val))
        except Exception as e:
            logging.error(str(e))
        logging.info('Telegram {}'.format(text))
        TelegramSendThread(
            options.token, options.chat_id, text, options.parse_mode
        ).start()

import logging
import sys
from threading import Thread

from sportorg import settings
from sportorg.common.fake_std import FakeStd
from sportorg.libs.max.max import Max
from sportorg.models.memory import race


class MaxSendThread(Thread):
    def __init__(self, token, chat_id, text, parse_mode=""):
        super().__init__(daemon=True)
        self.setName("MaxSendThread")
        self.token = token
        self.chat_id = chat_id
        self.text = text
        self.parse_mode = parse_mode

    def run(self):
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            Max(self.token).send_message(self.chat_id, self.text, self.parse_mode)
        except Exception as e:
            logging.error(str(e))


class BotOption:
    def __init__(self, token, chat_id, template, parse_mode, enabled=False):
        self.token = token
        self.chat_id = chat_id
        self.template = template
        self.parse_mode = parse_mode
        self.enabled = enabled


class MaxClient:
    @staticmethod
    def get_options():
        obj = race()
        return BotOption(
            settings.SETTINGS.max_token,
            obj.get_setting("max_chat_id", ""),
            obj.get_setting("max_template", ""),
            obj.get_setting("max_parse_mode", ""),
            obj.get_setting("max_enabled", False),
        )

    def send_result(self, result):
        if result.person:
            self.send(
                {
                    "group": result.person.group.name if result.person.group else "",
                    "name": result.person.full_name,
                    "bib": result.person.bib,
                    "result": result.get_result(),
                    "place": result.place,
                    "penalty_time": result.penalty_time,
                    "penalty_laps": result.penalty_laps,
                }
            )

    def send(self, data_dict):
        options = self.get_options()
        if not options.enabled or not options.token or not options.chat_id:
            return
        text = options.template
        try:
            for key, val in data_dict.items():
                text = text.replace("{" + str(key) + "}", str(val))
        except Exception as e:
            logging.error(str(e))
        logging.info("MAX {}".format(text))
        MaxSendThread(
            options.token,
            options.chat_id,
            text,
            options.parse_mode,
        ).start()


max_client = MaxClient()

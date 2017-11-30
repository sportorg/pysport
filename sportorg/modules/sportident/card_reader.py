import datetime
import logging

from sportorg import config
from sportorg.core.event import add_event
from sportorg.gui.dialogs.bib_dialog import BibDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.models import memory
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.sportident import sireader
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.utils.time import time_to_otime


def read():
    return start()


def get_result(card_data):
    result = memory.ResultSportident()
    result.sportident_card = memory.race().new_sportident_card(card_data['card_number'])

    for i in range(len(card_data['punches'])):
        time = card_data['punches'][i][1]
        if time:
            split = memory.Split()
            split.code = card_data['punches'][i][0]
            split.time = time_to_otime(time)
            result.splits.append(split)

    result.start_time = time_to_otime(card_data['start'])
    result.finish_time = time_to_otime(card_data['finish'])

    return result


def start():
    port = sireader.choose_port()

    def event_finish(card_data):
        assignment_mode = memory.race().get_setting('sportident_assignment_mode', False)
        if not assignment_mode:
            ResultSportidentGeneration(get_result(card_data)).add_result()
            ResultCalculation().process_results()
        else:
            try:
                bib_dialog = BibDialog()
                bib_dialog.exec()
                person = bib_dialog.get_person()
                memory.race().person_sportident_card(person, card_data['card_number'])
            except Exception as e:
                logging.exception(str(e))
        GlobalAccess().get_main_window().init_model()

    if port is not None:
        reader = sireader.SIReaderThread(
            port,
            func=event_finish,
            debug=config.DEBUG
        )
        start_time = memory.race().get_setting('sportident_zero_time', (8, 0, 0))
        reader.start_time = datetime.datetime.today().replace(
            hour=start_time[0],
            minute=start_time[1],
            second=start_time[2],
            microsecond=0
        )
        reader.start()

        add_event('close', lambda: stop(reader))

        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    reader.stop()

from sportorg.app.gui.global_access import GlobalAccess
from sportorg.app.models.result_calculation import ResultCalculation
from . import sireader
from sportorg.core.event import event, add_event
from sportorg.app.models import memory


def read():
    return start()


def get_result(card_data):
    result = memory.Result()
    result.card_number = card_data['card_number']
    result.punches = card_data['punches']
    result.start_time = card_data['start']
    result.finish_time = card_data['finish']
    result.person = None

    return result


def start():
    port = sireader.choose_port()

    def event_finish(card_data):
        event('finish', 'sportident', get_result(card_data))

        ResultCalculation().process_results()
        GlobalAccess().get_main_window().init_model()

    if port is not None:
        """
        :event: 'finish' 'sportident', result
        """
        reader = sireader.SIReaderThread(
            port,
            func=event_finish
        )
        reader.start()

        add_event('close', lambda: stop(reader))

        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    reader.stop()

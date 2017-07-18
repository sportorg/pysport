from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.app.models.memory import race
from sportorg.app.models.result_calculation import ResultCalculation
from . import sireader
from sportorg.app.models import memory


def read():
    return start(PersonPredetermined.card_reading)


def start(card_reader=lambda card_data: card_data):
    port = sireader.choose_port()
    if port is not None:
        reader = sireader.SIReaderThread(port, func=card_reader)
        reader.start()
        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    print('close', reader)
    reader.stop()


class PersonCardData:
    def __init__(self, card_data):
        self.card_data = card_data
        self._person = None

    @classmethod
    def card_reading(cls, card_data):
        pass

    @property
    def person(self):
        if self._person is None:
            self._person = self.get_person_by_card()

        return self._person

    @person.setter
    def person(self, person: memory.Person):
        self._person = person

    def get_person_by_card(self):
        return memory.find(memory.race().persons, card_number=str(self.card_data['card_number']))

    def check_punches(self):
        if self.person is None:
            return False
        i = 0
        controls = self.person.group.course.controls
        if len(controls) == 0:
            return False
        for punch in self.card_data['punches']:
            if punch[0] == controls[i].code:
                i += 1

        if i == len(controls):
            return True

        return False

    def set_status(self, status):
        self.person.result.status = status

    def set_result(self):
        if self.person is None:
            return self

        data = self.card_data
        result = memory.Result.create(
            card_number=data['card_number'],
            start_time=data['start'],
            finish_time=data['finish'],
            punches=list()
        )
        for punch in data['punches']:
            result.punches.append(list(punch))

        race().results.append(result) # add new object to the list
        if self.person.result is not None:
            race().results.remove(self.person.result)

        self.person.result = result
        result.person = self.person

        ResultCalculation().process_results()
        GlobalAccess().get_main_window().refresh()

        return self

    def get_text_result(self):
        # use templates
        pass

    def print_result(self, printer):
        pass

    def get_person_by_user_input(self):
        card_number = self.card_data['card_number']

        return memory.Person()

    def persons_dialog(self):
        pass


class PersonPredetermined(PersonCardData):
    @classmethod
    def card_reading(cls, card_data):
        print('from card_reader.py PersonPredetermined', card_data)
        person_card = cls(card_data)
        if person_card.person is None:
            print('Not person')
            # person_card.person = person_card.get_person_by_user_input()
            # if person_card.person is None:
            return
        person_card.set_result()

        if not person_card.check_punches():
            person_card.set_status(memory.ResultStatus.DISQUALIFIED)

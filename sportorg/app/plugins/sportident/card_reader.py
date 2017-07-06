from . import sireader
from . import settings
from sportorg.app.models import memory


def start(cls):
    port = sireader.choose_port()
    if port is not None:
        reader = sireader.SIReaderThread(port, func=cls.card_reading)
        reader.start()
        return reader

    return None


def stop(reader: sireader.SIReaderThread):
    print('close', reader)
    reader.reading = False


class PersonCardData:
    def __init__(self, card_data):
        self.card_data = card_data
        self._person = None

    @classmethod
    def card_reading(cls, card_data):
        print(card_data)

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

        self.person.result = result

        return self


class PersonPredetermined(PersonCardData):
    @classmethod
    def card_reading(cls, card_data):
        person_card = cls(card_data)
        if person_card.person is None:
            print('Not person')
            # person_card.person =
            return
        # if not person_card.check_punches():
        #     person_card.set_status(memory.ResultStatus.DISQUALIFIED)

        person_card.set_result()

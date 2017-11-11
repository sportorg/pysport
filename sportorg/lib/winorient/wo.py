import csv

from sportorg.app.models.memory import Qualification


class CSVReader:
    def __init__(self, data=None):
        self._data = [] if data is None else data

        self._groups = set()
        self._teams = set()
        self._cards = set()

    def parse(self, source):
        try:
            with open(source) as csv_file:
                spam_reader = csv.reader(csv_file, delimiter=';')
                for row in spam_reader:
                    self.append(row)
        except FileNotFoundError:
            raise FileNotFoundError("Not found " + source)

        return self

    @property
    def data(self):
        return self._data

    def append(self, person):
        def ifempty(o, default=None):
            if len(o):
                return 0
            if default is not None:
                return default
            return None

        person_dict = {
            'group_name': person[0],
            'team_name': person[2],
            'qual': Qualification(person[3]),
            'bib': ifempty(person[4]),
            'year': int(person[5]) if len(person[5]) else None,
            'card_number': int(person[6]) if len(person[6]) else None,
            'comment': person[7]
        }
        if len(str(person[1]).split(' ')) == 2:
            person_dict['name'] = str(person[1]).split(' ')[1]
            person_dict['surname'] = str(person[1]).split(' ')[0]
        elif len(str(person[1]).split(' ')) > 2:
            person_dict['name'] = str(person[1]).split(' ', 1)[1]
            person_dict['surname'] = str(person[1]).split(' ', 1)[0]
        else:
            person_dict['name'] = person[1]
            person_dict['surname'] = ''
        self._data.append(person_dict)

    @property
    def groups(self):
        if not len(self._groups):
            for row in self.data:
                self._groups.add(row['group_name'])

        return self._groups

    @property
    def cards(self):
        if not len(self._cards):
            for row in self.data:
                self._cards.add(row['card_number'])

        return self._cards

    @property
    def teams(self):
        if not len(self._teams):
            for row in self.data:
                self._teams.add(row['team_name'])

        return self._teams


def parse_csv(source):
    csv_reader = CSVReader()

    return csv_reader.parse(source)

import csv


class CSVReader:
    qual = {
        '0': 'б/р',
        '3': 'IIIю',
        '2': 'IIю',
        '1': 'Iю',
        '6': 'III',
        '5': 'II',
        '4': 'I',
        '7': 'КМС',
        '8': 'МС',
        '9': 'МСМК',
        '*': 'ЗМС'
    }

    def __init__(self, data=None):
        self._data = [] if data is None else data

        self._groups = set()
        self._teams = set()
        self._card = set()

    def parse(self, source):
        try:
            with open(source) as csv_file:
                spam_reader = csv.reader(csv_file, delimiter=';')
                for row in spam_reader:
                    self.append(row)
        except FileNotFoundError:
            raise FileNotFoundError("Not fount " + source)

        return self

    @property
    def data(self):
        return self._data

    def append(self, person):
        person_dict = {
            'group': person[0],
            'team': person[2],
            'qual': self.qual[person[3]],
            'bib': person[4],
            'year': person[5],
            'card': person[6],
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
                self._groups.add(row['group'])

        return self._groups

    @property
    def cards(self):
        if not len(self._card):
            for row in self.data:
                self._card.add(row['card'])

        return self._card

    @property
    def teams(self):
        if not len(self._teams):
            for row in self.data:
                self._teams.add(row['team'])

        return self._teams


def parse_csv(source):
    csv_reader = CSVReader()

    return csv_reader.parse(source)

import csv


class CSVReader:
    def __init__(self, data=None):
        self._data = [] if data is None else data

        self._groups = set()
        self._teams = set()
        self._cards = set()

    def parse(self, source):
        with open(source, encoding='cp1251') as csv_file:
            spam_reader = csv.reader(csv_file, delimiter=';')
            for row in spam_reader:
                self.append(row)

        return self

    @property
    def data(self):
        return self._data

    def append(self, person):
        if not person or len(person) < 8:
            return

        if str(person[3]).isdigit():
            # support of old WO format, without representative, emulate it
            person.insert(3, '')

        person_dict = {
            'group_name': person[0],
            'team_name': person[2],
            'representative': person[3],
            'qual_id': person[4],
            'bib': int(person[5]) if len(person[5]) else 0,
            'year': int(person[6]) if len(person[6]) else 0,
            'sportident_card': int(person[7]) if str(person[7]).isdigit() else 0,
            'comment': person[8],
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
                self._cards.add(row['sportident_card'])

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

import csv
import model


class WinOrientCSV:
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

    def __init__(self, file=None, data=None):
        self._file = file
        self._data = [] if data is None else data
        self._groups = set()
        self._teams = set()
        self._card = set()
        self._is_complete = False

    @property
    def is_complete(self):
        return self._is_complete

    @property
    def data(self):
        if not len(self._data):
            self._read_file()

        return self._data

    def append(self, person):
        """
        
        :type person: list
        """
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

    def _read_file(self):
        try:
            with open(self._file) as csv_file:
                spam_reader = csv.reader(csv_file, delimiter=';')
                for row in spam_reader:
                    self.append(row)

        except FileNotFoundError:
            pass

    def run(self):
        print(self.groups)
        print(self.teams)
        print(self.data)

        data_group = [{'name': group, 'long_name': group} for group in self.groups]
        model_group = {}
        for data_dict in data_group:
            org = model.Group.create(**data_dict)
            model_group[org.name] = org.id

        data_team = [{'name': team} for team in self.teams]
        model_team = {}
        for data_dict in data_team:
            org = model.Organization.create(**data_dict)
            model_team[org.name] = org.id

        data_person = [{
            'name': row['name'],
            'surname': row['surname'],
            'team': model_team[row['team']],
            'year': row['year'],
            'qual': row['qual'],
        } for row in self.data]
        with model.database_proxy.atomic():
            model.Person.insert_many(data_person).execute()

        self._is_complete = True
        # TODO: from data to sql

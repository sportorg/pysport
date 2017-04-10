import csv
import model
from wdb import WDB


class WinOrientBinary:
    qual = {
        '': 'б/р',
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

    def __init__(self, file=None):
        self._file = file
        self.wdb_object = WDB()
        self._is_complete = False
        self._read_file()

    @property
    def is_complete(self):
        return self._is_complete


    def _read_file(self):
        try:
            with open(self._file, 'rb') as wdb_file:
                byte_array = wdb_file.read()
                self.wdb_object = WDB()
                self.wdb_object.parse_bytes(byte_array)
        except FileNotFoundError:
            pass

    def run(self):

        data_group = [{'name': group.name, 'long_name': group.name} for group in self.wdb_object.group]
        model_group = {}
        with model.database_proxy.atomic():
            for data_dict in data_group:
                org = model.Group.create(**data_dict)
                model_group[org.name] = org.id

        data_team = [{'name': team.name} for team in self.wdb_object.team]
        model_team = {}
        with model.database_proxy.atomic():
            for data_dict in data_team:
                org = model.Organization.create(**data_dict)
                model_team[org.name] = org.id

        data_person = [{
                           'name': str.split(man.name, ' ')[0],
                           'surname': str.split(man.name, ' ')[-1],
                           'team': man.team,
                           'year': man.year,
                           'qual': self.qual[str(man.qualification)],
                       } for man in self.wdb_object.man]
        with model.database_proxy.atomic():
            for idx in range(0, len(data_person), 100):
                model.Person.insert_many(data_person[idx:idx + 100]).execute()

        self._is_complete = True


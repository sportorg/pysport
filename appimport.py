import csv
import model


class WinOrientCSV:
    def __init__(self, file):
        self._file = file
        self._data = []
        self._groups = set()
        # TODO: добавить свойства _teams as _groups

    @property
    def data(self):
        if not len(self._data):
            self._read_file()

        return self._data

    def append(self, person):
        # TODO: добавить доп поля, pydoc - что принмает
        """
        
        :param arr: 
        """
        person_dict = {'group': person[0], 'name': person[1]}
        self._data.append(person_dict)

    @property
    def groups(self):
        if not len(self._groups):
            for row in self.data:
                self._groups.add(row['group'])

        return self._groups

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
        print(self.data)
        # TODO: from data to sql

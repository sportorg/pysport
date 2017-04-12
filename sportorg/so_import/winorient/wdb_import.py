from sportorg.models import model
from sportorg.models.model import RaceStatus
from sportorg.winorient.wdb import WDB


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

        self.create_race(self.wdb_object)
        self.create_organizations(self.wdb_object)

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

    def create_race(self, wdb):

        assert isinstance(wdb, WDB)

        name = 'wdb imported race'
        discipline = wdb.info.type
        start_time = wdb.info.date_str
        end_time = wdb.info.date_str
        status_text = 'Applied'
        status_obj = model.RaceStatus.get_or_create(value=status_text)[0]
        status = status_obj.id
        url = ''
        information = wdb.info.title

        data = {
            'name': name,
            'discipline': discipline,
            'start_time': start_time,
            'end_time': end_time,
            'status': status,
            'url': url,
            'information': information,
        }

        model.Race.create(
                          name=name,
                          discipline=discipline,
                          start_time=start_time,
                          end_time=end_time,
                          status = status, # TODO: write foreign key of status
                          url=url,
                          information=information
                          )

    def create_organizations(self, wdb):

        assert isinstance(wdb, WDB)

        for team in wdb.team:

            name = team.name
            address = None
            contact = None
            if len(team.refferent) > 0:
                contact = model.Contact.get_or_create({'name': 'team contact', 'value': team.refferent})
            country = None  # TODO: decode from WDB byte

            data = {
                'name': name,
                'address': address,
                'contact': contact,
                'country': country,
            }

            model.Organization.create(**data)

import datetime

from sportorg.app.models import model
from sportorg.app.models.memory import Race, Organization, Group, Person, Result, race, find, Course, \
    CourseControl, Country, Contact, Address
from sportorg.app.models.result_calculation import ResultCalculation
from sportorg.lib.winorient.wdb import WDB, WDBMan, WDBTeam, WDBGroup, WDBDistance, WDBPunch


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

        with model.database_proxy.atomic():
            for man in self.wdb_object.man:
                assert (isinstance(man, WDBMan))
                data_person = {
                    'name': str.split(man.name, ' ')[0],
                    'surname': str.split(man.name, ' ')[-1],
                    'team': man.team,
                    'year': man.year,
                    'qual': self.qual[str(man.qualification)]
                }
                person = model.Person.create(**data_person)

                card = None
                if man.si_card != 0:
                    card = model.ControlCard.create(
                        name="SPORTIDENT",
                        value=str(man.si_card),
                        person=person
                    )

                data_participation = {
                    'group': model_group[str(man.get_group().name)],
                    'person': person,
                    'bib_number': int(man.number),
                    'comment': man.comment,
                    'start_time': self.int_to_time(man.start),
                    'control_card': card
                }
                participation = model.Participation.create(**data_participation)

                finish = man.get_finish()

                if finish is not None:
                    finish_time = finish.time

                    data_result = {
                        'participation': participation,
                        'control_card': card,
                        'start_time': self.int_to_time(man.start),
                        'finish_time': self.int_to_time(finish_time)
                    }
                    model.Result.create(**data_result)

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

        model.Race.create(
                          name=name,
                          discipline=discipline,
                          start_time=start_time,
                          end_time=end_time,
                          status=status,  # TODO: write foreign key of status
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
                params = {'name': 'team contact', 'value': team.refferent}
                contact = model.Contact.get_or_create(**params)[0]
            country = None  # TODO: decode from WDB byte

            data = {
                'name': name,
                'address': address,
                'contact': contact,
                'country': country,
            }

            model.Organization.create(**data)

    def int_to_time(self, value):
        """ convert value from 1/100 s to time """
        # ret = datetime(1970, 1, 1) + timedelta(seconds= value/100, milliseconds=value*10%1000)
        # ret = datetime.datetime.fromtimestamp(int(value)/100.0)
        # TODO Find more simple solution!!!
        # ret = datetime.time(value // 360000, (value % 360000) // 6000, (value % 6000) // 100, (value % 100) * 10000)
        today = datetime.datetime.now()
        assert (isinstance(today, datetime.datetime))
        ret = datetime.datetime(today.year, today.month, today.day, value // 360000 % 24, (value % 360000) // 6000,
                                (value % 6000) // 100, (value % 100) * 10000)

        return ret

    def create_objects(self):
        """Create objects in memory, according to model"""
        my_race = race()
        assert(isinstance(my_race, Race))

        my_race.set_setting('sub_title', '\n'.join(self.wdb_object.info.title))
        my_race.set_setting('location', self.wdb_object.info.place)
        my_race.set_setting('chief_referee', self.wdb_object.info.referee)
        my_race.set_setting('secretary', self.wdb_object.info.secretary)


        for team in self.wdb_object.team:
            assert (isinstance(team, WDBTeam))
            new_team = Organization()
            new_team.name = team.name
            new_team.region = str(team.region)
            new_team.country = Country()
            new_team.address = Address()
            new_team.contact = Contact()
            new_team.country.name = str(team.country)
            my_race.organizations.append(new_team)

        for course in self.wdb_object.dist:
            assert (isinstance(course, WDBDistance))
            new_course = Course()
            new_course.controls = []
            new_course.name = course.name
            new_course.climb = course.elevation
            new_course.length = course.length
            new_course.type = self.wdb_object.info.type  # TODO parse type

            # controls
            for i in range(course.point_quantity):
                control = CourseControl()
                control.code = course.point[i]
                if i > len(course.leg):
                    control.length = course.leg[i]
                new_course.controls.append(control)

            my_race.courses.append(new_course)

        for group in self.wdb_object.group:
            assert (isinstance(group, WDBGroup))
            new_group = Group()
            new_group.name = group.name
            new_group.price = group.owner_cost
            course = group.get_course()
            if course is not None:
                new_group.course = find(race().courses, name=course.name)
            my_race.groups.append(new_group)

        for man in self.wdb_object.man:
            assert (isinstance(man, WDBMan))
            new_person = Person()
            new_person.surname = man.name.split(" ")[0]
            new_person.name = man.name.split(" ")[-1]
            new_person.bib = man.number
            new_person.qual = self.qual[str(man.qualification)]
            new_person.year = man.year
            new_person.card_number = man.si_card
            new_person.is_out_of_competition = man.is_not_qualified
            new_person.comment = man.comment
            group_name = man.get_group().name
            new_person.group = find(race().groups, name=group_name)
            team_name = man.get_team().name
            new_person.organization = find(race().organizations, name=team_name)

            my_race.persons.append(new_person)

            new_person.start_time = self.int_to_time(man.start)

            # result
            fin = man.get_finish()
            if fin is not None:
                result = Result()
                result.person = new_person
                new_person.result = result

                result.card_number = man.si_card
                result.start_time = self.int_to_time(man.start)
                result.finish_time = self.int_to_time(fin.time)
                result.status = man.status
                result.result = man.result

                my_race.results.append(result)

                # punches
                chip = man.get_chip()
                if chip is not None:
                    result.punches = []
                    for i in range(chip.quantity):
                        p = chip.punch[i]
                        assert isinstance(p, WDBPunch)
                        code = p.code
                        time = self.int_to_time(p.time)
                        punch = (code, time)
                        if code > 0:
                            result.punches.append(punch)

        ResultCalculation().process_results()

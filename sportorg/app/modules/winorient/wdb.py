import traceback

from PyQt5.QtWidgets import QMessageBox

from sportorg.app.models import model
from sportorg.app.models.memory import Race, Organization, Group, Person, Result, race, find, Course, \
    CourseControl, Country, Contact, Address, ResultStatus
from sportorg.app.models.result.result_calculation import ResultCalculation
from sportorg.app.modules.utils.utils import int_to_time, time_to_int
from sportorg.language import _
from sportorg.lib.winorient.wdb import WDB, WDBMan, WDBTeam, WDBGroup, WDBDistance, WDBPunch, WDBFinish, WDBChip


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
        '10': 'ЗМС'
    }

    qual_reverse = {
        '':     0,
        ' ':    0,
        'б/р':  0,
        'IIIю': 3,
        'IIю':  2,
        'Iю':   1,
        'III':  6,
        'II':   5,
        'I':    4,
        'КМС':  7,
        'МС':   8,
        'МСМК': 9,
        'ЗМС':  10
    }

    status = {
        0: ResultStatus.OK,
        1: ResultStatus.DISQUALIFIED,
        2: ResultStatus.OVERTIME,
        7: ResultStatus.DID_NOT_FINISH,
        8: ResultStatus.DID_NOT_START
    }

    status_reverse = {
        ResultStatus.OK: 0,
        ResultStatus.DISQUALIFIED: 1,
        ResultStatus.OVERTIME: 2,
        ResultStatus.DID_NOT_FINISH: 7,
        ResultStatus.DID_NOT_START: 8
    }

    def __init__(self, file=None):
        self._file = file
        self.wdb_object = WDB()
        if file:
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
        except:
            traceback.print_exc()
            QMessageBox.question(None,
                                 _('Error'),
                                 _('Import error') + ': ' + self._file)

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
                    'start_time': int_to_time(man.start),
                    'control_card': card
                }
                participation = model.Participation.create(**data_participation)

                finish = man.get_finish()

                if finish is not None:
                    finish_time = finish.time

                    data_result = {
                        'participation': participation,
                        'control_card': card,
                        'start_time': int_to_time(man.start),
                        'finish_time': int_to_time(finish_time)
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
                if i < len(course.leg):
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
            if str(man.qualification) in self.qual.keys():
                new_person.qual = self.qual[str(man.qualification)]
            new_person.year = man.year
            new_person.card_number = man.si_card
            new_person.is_out_of_competition = man.is_not_qualified
            new_person.comment = man.comment
            new_person.start_group = man.start_group

            found_group = man.get_group()
            if found_group:
                group_name = found_group.name
                new_person.group = find(race().groups, name=group_name)
            
            found_team = man.get_team()
            if found_team:
                team_name = found_team.name
                new_person.organization = find(race().organizations, name=team_name)

            my_race.persons.append(new_person)

            new_person.start_time = int_to_time(man.start)

            # result
            fin = man.get_finish()
            if fin is not None:
                result = Result()
                result.person = new_person
                new_person.result = result

                result.card_number = man.si_card
                result.start_time = int_to_time(man.start)
                result.finish_time = int_to_time(fin.time)
                if man.status in self.status:
                    result.status = self.status[man.status]
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
                        time = int_to_time(p.time)
                        punch = (code, time)
                        if code > 0:
                            result.punches.append(punch)

        ResultCalculation().process_results()

    def export(self):
        wdb_object = WDB()
        my_race = race()

        title = my_race.get_setting('sub_title')
        wdb_object.info.title = title.split('\n')
        wdb_object.info.place = my_race.get_setting('location')
        wdb_object.info.referee = my_race.get_setting('chief_referee')
        wdb_object.info.secretary = my_race.get_setting('secretary')

        for team in my_race.organizations:
            new_team = WDBTeam()
            new_team.name = team.name
            if team.region:
                if isinstance(team.region, int):
                    new_team.region = team.region

            # TODO decode country id
            new_team.country = 0
            wdb_object.team.append(new_team)
            new_team.id = len(wdb_object.team)

        for course in my_race.courses:
            new_course = WDBDistance()
            new_course.name = course.name
            new_course.elevation = int(course.climb)
            new_course.length = int(course.length)

            # controls
            for i in range(len(course.controls)):

                if len(new_course.point) >= i:
                    new_course.point.append(0)
                    new_course.leg.append(0)

                new_course.point[i] = int(course.controls[i].code)
                leg = course.controls[i].length

                if leg:
                    if str(leg).find('.') > -1:
                        new_course.leg[i] = int(float(leg) * 1000)
                    else:
                        new_course.leg[i] = int(leg)

            wdb_object.dist.append(new_course)
            new_course.id = len(wdb_object.dist)

        for group in my_race.groups:
            new_group = WDBGroup()
            new_group.name = group.name

            if group.price:
                new_group.owner_cost = int(group.price)

            if group.course:
                course_found = wdb_object.find_course_by_name(group.course.name)
                if course_found:
                    new_group.distance_id = course_found.id

            wdb_object.group.append(new_group)
            new_group.id = len(wdb_object.group)

        for man in my_race.persons:
            assert isinstance(man, Person)
            new_person = WDBMan(wdb_object)
            new_person.name = str(man.surname) + " " + str(man.name)
            if man.bib:
                new_person.number = int(man.bib)

            # decode qualification
            if man.qual:
                new_person.qualification = WinOrientBinary.qual_reverse[man.qual]

            if man.year:
                new_person.year = int(man.year)
            if man.card_number:
                new_person.si_card = int(man.card_number)
                new_person.is_own_card = 2
            new_person.is_not_qualified = man.is_out_of_competition
            new_person.comment = man.comment
            if man.group:
                group_found = wdb_object.find_group_by_name(man.group.name)
                if group_found:
                    new_person.group = group_found.id
            if man.organization:
                team_found = wdb_object.find_team_by_name(man.organization.name)
                if team_found:
                    new_person.team = team_found.id

            wdb_object.man.append(new_person)
            new_person.id = len(wdb_object.man)

            new_person.start = time_to_int(man.start_time)
            new_person.start_group = man.start_group

            # result
            result = man.result
            if result is not None:
                new_finish = WDBFinish()

                new_finish.time = time_to_int(result.finish_time)
                new_finish.number = man.bib

                if result.status in self.status_reverse:
                    new_person.status = self.status_reverse[result.status]
                new_person.result = result.result

                wdb_object.fin.append(new_finish)

                # punches

                if result.punches:
                    new_chip = WDBChip()
                    new_chip.id = man.card_number
                    new_chip.start = WDBPunch(time=time_to_int(result.start_time))
                    new_chip.finish = WDBPunch(time=time_to_int(result.finish_time))

                    new_chip.quantity = len(result.punches)
                    for i in result.punches:
                        new_punch = WDBPunch()
                        new_punch.code = i[0]
                        new_punch.time = time_to_int(i[1])
                        new_chip.punch.append(new_punch)

                    wdb_object.chip.append(new_chip)

        return wdb_object

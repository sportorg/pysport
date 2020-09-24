from sportorg.common.otime import OTime
from sportorg.libs.winorient.wdb import (
    WDB,
    WDBChip,
    WDBDistance,
    WDBFinish,
    WDBGroup,
    WDBMan,
    WDBPunch,
    WDBTeam,
)
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Organization,
    Person,
    Qualification,
    ResultSportident,
    ResultStatus,
    Split,
    find,
    race,
)
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.utils.time import int_to_otime, time_to_int


class WDBImportError(Exception):
    pass


class WinOrientBinary:
    status = {
        0: ResultStatus.OK,
        1: ResultStatus.DISQUALIFIED,
        2: ResultStatus.OVERTIME,
        7: ResultStatus.DID_NOT_FINISH,
        8: ResultStatus.DID_NOT_START,
    }

    status_reverse = {
        ResultStatus.OK: 0,
        ResultStatus.RESTORED: 0,
        ResultStatus.MISSING_PUNCH: 1,
        ResultStatus.DISQUALIFIED: 1,
        ResultStatus.OVERTIME: 2,
        ResultStatus.DID_NOT_FINISH: 7,
        ResultStatus.DID_NOT_START: 8,
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
        except Exception as e:
            raise WDBImportError(e)

    def create_objects(self):
        """Create objects in memory, according to model"""
        my_race = race()

        my_race.data.title = '\n'.join(self.wdb_object.info.title)
        my_race.data.location = self.wdb_object.info.place
        my_race.data.chief_referee = self.wdb_object.info.referee
        my_race.data.secretary = self.wdb_object.info.secretary

        for team in self.wdb_object.team:
            new_team = Organization()
            new_team.name = team.name
            my_race.organizations.append(new_team)

        for course in self.wdb_object.dist:
            new_course = Course()
            new_course.controls = []
            new_course.name = course.name
            new_course.climb = course.elevation
            new_course.length = course.length
            # new_course.type = self.wdb_object.info.type  # TODO parse type

            # controls
            for i in range(course.point_quantity):
                control = CourseControl()
                control.code = str(course.point[i])
                if control.code == '0':
                    break
                if i < len(course.leg):
                    control.length = course.leg[i]
                new_course.controls.append(control)

            my_race.courses.append(new_course)

        for group in self.wdb_object.group:
            new_group = Group()
            new_group.name = group.name
            new_group.price = group.owner_cost
            course = group.get_course()
            if course:
                new_group.course = find(race().courses, name=course.name)
            my_race.groups.append(new_group)

        for man in self.wdb_object.man:
            new_person = Person()
            new_person.surname = man.name.strip().split(' ')[0]
            new_person.name = man.name.strip().split(' ')[-1]
            new_person.bib = man.number
            if man.qualification:
                if man.qualification == 10:
                    man.qualification = Qualification.MSMK.value  # Convert ZMS to MSMK
                new_person.qual = Qualification.get_qual_by_code(man.qualification)
            new_person.set_year(man.year)
            race().person_card_number(new_person, man.si_card)
            new_person.is_out_of_competition = man.is_not_qualified
            new_person.comment = man.comment
            new_person.start_group = man.start_group
            new_person.is_rented_card = not (man.is_own_card >> 1)
            new_person.is_personal = man.is_without_team

            found_group = man.get_group()
            if found_group:
                group_name = found_group.name
                new_person.group = find(race().groups, name=group_name)

            found_team = man.get_team()
            if found_team:
                team_name = found_team.name
                new_person.organization = find(race().organizations, name=team_name)

            my_race.persons.append(new_person)

            new_person.start_time = int_to_otime(man.start)

        # result
        for fin in self.wdb_object.fin:
            result = ResultSportident()
            result.finish_time = int_to_otime(fin.time)
            result.bib = fin.number

            person = find(my_race.persons, bib=result.bib)
            if person:
                result.person = person
                wdb_person = find(self.wdb_object.man, number=result.bib)
                if wdb_person.status in self.status:
                    result.status = self.status[wdb_person.status]
                result.penalty_time = OTime(sec=wdb_person.penalty_second)

            my_race.add_result(result)

        # punches
        for chip in self.wdb_object.chip:

            person = find(my_race.persons, card_number=chip.id)
            if person:
                result = find(my_race.results, person=person)
                if not result:
                    result = ResultSportident()
                    result.person = person
                    my_race.add_result(result)
            else:
                result = ResultSportident()
                my_race.add_result(result)

            result.card_number = chip.id
            result.splits = []
            for i in range(chip.quantity):
                p = chip.punch[i]
                code = p.code
                time = int_to_otime(p.time)
                split = Split()
                split.code = str(code)
                split.time = time
                if code > 0:
                    result.splits.append(split)

        ResultCalculation(race()).process_results()

    def export(self):
        wdb_object = WDB()
        my_race = race()

        title = my_race.data.description
        wdb_object.info.title = title.replace('<br>', '').split('\n')
        wdb_object.info.place = my_race.data.location
        wdb_object.info.referee = my_race.data.chief_referee
        wdb_object.info.secretary = my_race.data.secretary

        for team in my_race.organizations:
            new_team = WDBTeam()
            new_team.name = team.name

            wdb_object.team.append(new_team)
            new_team.id = len(wdb_object.team)

        for course in my_race.courses:
            new_course = WDBDistance()
            new_course.name = course.name
            new_course.elevation = int(course.climb)
            new_course.length = int(course.length)
            new_course.point_quantity = len(course.controls)

            # controls
            for i in range(len(course.controls)):

                if len(new_course.point) >= i:
                    new_course.point.append(0)
                    new_course.leg.append(0)

                if str(course.controls[i].code).isdigit():
                    new_course.point[i] = int(course.controls[i].code)
                else:
                    new_course.point[i] = 0
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
            new_person = WDBMan(wdb_object)
            new_person.name = str(man.surname) + ' ' + str(man.name)
            if man.bib:
                new_person.number = int(man.bib)

            # decode qualification
            if man.qual:
                new_person.qualification = Qualification(int(man.qual.value))

            if man.get_year():
                new_person.year = man.get_year()
            if man.card_number:
                new_person.si_card = int(man.card_number)
            new_person.is_not_qualified = man.is_out_of_competition
            if not man.is_rented_card:
                new_person.is_own_card = 2
            new_person.is_without_team = man.is_personal

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
            result = race().find_person_result(man)

            if result:
                new_finish = WDBFinish()

                new_finish.time = time_to_int(result.get_finish_time())
                new_finish.number = man.bib

                if result.status in self.status_reverse:
                    new_person.status = self.status_reverse[result.status]

                wdb_object.fin.append(new_finish)

                if result.penalty_time:
                    new_person.penalty_second = result.penalty_time.to_sec()

                # splits

                if result.splits:
                    new_chip = WDBChip()
                    if man.card_number:
                        new_chip.id = int(man.card_number)
                    new_chip.start = WDBPunch(time=time_to_int(result.start_time))
                    new_chip.finish = WDBPunch(time=time_to_int(result.finish_time))

                    new_chip.quantity = len(result.splits)
                    for split in result.splits:
                        new_punch = WDBPunch()
                        new_punch.code = int(split.code)
                        new_punch.time = time_to_int(split.time)
                        new_chip.punch.append(new_punch)

                    wdb_object.chip.append(new_chip)

        return wdb_object

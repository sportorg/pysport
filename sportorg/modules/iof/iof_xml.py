import logging
from datetime import datetime

import dateutil.parser

from sportorg import config
from sportorg.language import translate
from sportorg.libs.iof.iof import ResultList
from sportorg.libs.iof.parser import parse
from sportorg.models.memory import (
    Course,
    CourseControl,
    Group,
    Organization,
    Person,
    Qualification,
    create,
    find,
    race,
)


def export_result_list(file):
    obj = race()
    result_list = ResultList()
    result_list.iof.creator = config.NAME
    result_list.iof.create_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    result_list.event.name.value = obj.data.name
    if obj.data.start_time:
        result_list.event.start_time.date.value = obj.data.start_time.strftime(
            '%Y-%m-%d'
        )
        result_list.event.start_time.time.value = obj.data.start_time.strftime(
            '%H:%M:%S'
        )
    # TODO
    result_list.write(open(file, 'wb'), xml_declaration=True, encoding='UTF-8')


def import_from_iof(file):
    results = parse(file)
    if not len(results):
        return

    for result in results:
        if result.name == 'EntryList':
            import_from_entry_list(result.data)
        elif result.name == 'CourseData':
            import_from_course_data(result.data)


def import_from_course_data(courses):
    obj = race()
    for course in courses:
        if find(obj.courses, name=course['name']) is None:
            c = create(
                Course,
                name=course['name'],
                length=course['length'],
                climb=course['climb'],
            )
            controls = []
            i = 1
            for control in course['controls']:
                if control['type'] == 'Control':
                    controls.append(
                        create(
                            CourseControl,
                            code=control['control'],
                            order=i,
                            length=control['leg_length'],
                        )
                    )
                    i += 1
            c.controls = controls
            obj.courses.append(c)


def import_from_entry_list(entries):
    obj = race()
    for person_entry in entries:
        name = person_entry['group']['name']
        if 'short_name' in person_entry['group']:
            name = person_entry['group']['short_name']
        group = find(obj.groups, name=name)
        if group is None:
            group = Group()
            group.long_name = person_entry['group']['name']
            if 'short_name' in person_entry['group']:
                group.name = person_entry['group']['short_name']
            else:
                group.name = group.long_name
            obj.groups.append(group)

        org = find(obj.organizations, name=person_entry['organization']['name'])
        if org is None:
            org = Organization()
            org.name = person_entry['organization']['name']
            if 'role_person' in person_entry['organization']:
                org.contact = person_entry['organization']['role_person']
            obj.organizations.append(org)

    for person_entry in entries:
        person = Person()
        person.surname = person_entry['person']['family']
        person.name = person_entry['person']['given']
        name = person_entry['group']['name']
        if 'short_name' in person_entry['group']:
            name = person_entry['group']['short_name']
        person.group = find(obj.groups, name=name)
        person.organization = find(
            obj.organizations, name=person_entry['organization']['name']
        )
        if 'birth_date' in person_entry['person']:
            person.birth_date = dateutil.parser.parse(
                person_entry['person']['birth_date']
            ).date()
        if len(person_entry['race_numbers']):
            person.comment = 'C:' + ''.join(person_entry['race_numbers'])
        if person_entry['control_card']:
            person.card_number = int(person_entry['control_card'])
        if (
            'bib' in person_entry['person']['extensions']
            and person_entry['person']['extensions']['bib']
        ):
            person.bib = int(person_entry['person']['extensions']['bib'])
        if (
            'qual' in person_entry['person']['extensions']
            and person_entry['person']['extensions']['qual']
        ):
            person.qual = Qualification.get_qual_by_name(
                person_entry['person']['extensions']['qual']
            )
        obj.persons.append(person)

    persons_dupl_cards = obj.get_duplicate_card_numbers()
    persons_dupl_names = obj.get_duplicate_names()

    if len(persons_dupl_cards):
        logging.info(
            '{}'.format(translate('Duplicate card numbers (card numbers are reset)'))
        )
        for person in persons_dupl_cards:
            logging.info(
                '{} {} {} {}'.format(
                    person.full_name,
                    person.group.name if person.group else '',
                    person.organization.name if person.organization else '',
                    person.card_number,
                )
            )
            person.card_number = 0
    if len(persons_dupl_names):
        logging.info('{}'.format(translate('Duplicate names')))
        for person in persons_dupl_names:
            person.card_number = 0
            logging.info(
                '{} {} {} {}'.format(
                    person.full_name,
                    person.get_year(),
                    person.group.name if person.group else '',
                    person.organization.name if person.organization else '',
                )
            )

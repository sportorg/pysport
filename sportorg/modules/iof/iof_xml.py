import logging
from datetime import datetime

import dateutil.parser

from sportorg import config
from sportorg.language import _
from sportorg.libs.iof.iof import ResultList
from sportorg.libs.iof.parser import parse
from sportorg.models.memory import race, Group, find, Organization, Person, Qualification


def export_result_list(file):
    obj = race()
    result_list = ResultList()
    result_list.iof.creator = config.NAME
    result_list.iof.create_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    result_list.event.name.value = obj.data.name
    if obj.data.start_time is not None:
        result_list.event.start_time.date.value = obj.data.start_time.strftime("%Y-%m-%d")
        result_list.event.start_time.time.value = obj.data.start_time.strftime("%H:%M:%S")
    # TODO
    result_list.write(open(file, 'wb'), xml_declaration=True, encoding='UTF-8')


def import_entry_list(file):
    entries = parse(file)
    if not entries:
        return

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
            org.contact.name = 'name'
            if 'role_person' in person_entry['organization']:
                org.contact.value = person_entry['organization']['role_person']
            obj.organizations.append(org)

    for person_entry in entries:
        person = Person()
        person.surname = person_entry['person']['family']
        person.name = person_entry['person']['given']
        name = person_entry['group']['name']
        if 'short_name' in person_entry['group']:
            name = person_entry['group']['short_name']
        person.group = find(obj.groups, name=name)
        person.organization = find(obj.organizations, name=person_entry['organization']['name'])
        if 'birth_date' in person_entry['person']:
            person.birth_date = dateutil.parser.parse(person_entry['person']['birth_date']).date()
        if len(person_entry['race_numbers']):
            person.comment = 'C:' + ''.join(person_entry['race_numbers'])
        if person_entry['control_card']:
            person.card_number = int(person_entry['control_card'])
        if 'bib' in person_entry['person']['extensions'] and person_entry['person']['extensions']['bib']:
            person.bib = int(person_entry['person']['extensions']['bib'])
        if 'qual' in person_entry['person']['extensions'] and person_entry['person']['extensions']['qual']:
            person.qual = Qualification.get_qual_by_name(person_entry['person']['extensions']['qual'])
        obj.persons.append(person)

    persons_dupl_cards = obj.get_duplicate_card_numbers()
    persons_dupl_names = obj.get_duplicate_names()

    if len(persons_dupl_cards):
        logging.info('{}'.format(_('Duplicate card numbers (card numbers are reset)')))
        for person in persons_dupl_cards:
            logging.info('{} {} {} {}'.format(
                person.full_name,
                person.group.name if person.group else '',
                person.organization.name if person.organization else '',
                person.card_number
            ))
            person.card_number = 0
    if len(persons_dupl_names):
        logging.info('{}'.format(_('Duplicate names')))
        for person in persons_dupl_names:
            person.card_number = 0
            logging.info('{} {} {} {}'.format(
                person.full_name,
                person.get_year(),
                person.group.name if person.group else '',
                person.organization.name if person.organization else ''
            ))

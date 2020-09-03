import logging

from sportorg.language import translate
from sportorg.libs.winorient import wo
from sportorg.models import memory
from sportorg.models.memory import Qualification
from sportorg.modules.winorient.wdb import WinOrientBinary


def import_csv(source):
    wo_csv = wo.parse_csv(source)
    obj = memory.race()

    old_lengths = obj.get_lengths()

    for group_name in wo_csv.groups:
        group = memory.find(obj.groups, name=group_name)
        if group is None:
            group = memory.Group()
            group.name = group_name
            group.long_name = group_name
            obj.groups.append(group)

    for team_name in wo_csv.teams:
        org = memory.find(obj.organizations, name=team_name)
        if org is None:
            org = memory.Organization()
            org.name = team_name
            obj.organizations.append(org)

    for person_dict in wo_csv.data:
        if person_dict['qual_id'] and person_dict['qual_id'].isdigit():
            qual_id = int(person_dict['qual_id'])
        else:
            qual_id = 0
        person_org = memory.find(obj.organizations, name=person_dict['team_name'])
        person_org.contact = person_dict['representative']

        person = memory.Person()
        person.name = person_dict['name']
        person.surname = person_dict['surname']
        person.bib = person_dict['bib']
        person.set_year(person_dict['year'])
        person.card_number = int(person_dict['sportident_card'])
        person.group = memory.find(obj.groups, name=person_dict['group_name'])
        person.organization = person_org
        person.qual = Qualification(qual_id)
        person.comment = person_dict['comment']
        obj.persons.append(person)

    new_lengths = obj.get_lengths()

    logging.info(translate('Import result'))
    logging.info('{}: {}'.format(translate('Persons'), new_lengths[0] - old_lengths[0]))
    # logging.info('{}: {}'.format(translate('Race Results'), new_lengths[1]-old_lengths[1]))
    logging.info('{}: {}'.format(translate('Groups'), new_lengths[2] - old_lengths[2]))
    # logging.info('{}: {}'.format(translate('Courses'), new_lengths[3]-old_lengths[3]))
    logging.info('{}: {}'.format(translate('Teams'), new_lengths[4] - old_lengths[4]))

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


def import_wo_wdb(file_name):
    wb = WinOrientBinary(file=file_name)
    # wb.run()
    wb.create_objects()

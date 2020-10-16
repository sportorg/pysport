import xml.etree.ElementTree as ET


class IOFParseResult(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data


def parse(file):
    ns = {
        'iof': 'http://www.orienteering.org/datastandard/3.0',
        'orgeo': 'http://orgeo.ru/iof-xml-extensions/3.0',
    }
    tree = ET.parse(file)

    results = [
        IOFParseResult('EntryList', entry_list(tree, ns)),
        IOFParseResult('CourseData', course_data(tree, ns)),
        IOFParseResult('ResultList', result_list(tree, ns)),
        IOFParseResult('Event', event(tree, ns)),
    ]

    return [result for result in results if result.data is not None]


def course_data(tree, ns):
    root = tree.getroot()
    if 'CourseData' not in root.tag:
        return
    courses = []
    for course_el in root.find('iof:RaceCourseData', ns).findall('iof:Course', ns):
        course = {
            'name': course_el.find('iof:Name', ns).text,
            'length': int(course_el.find('iof:Length', ns).text),
            'climb': int(course_el.find('iof:Climb', ns).text),
            'controls': []
        }

        for course_control_el in course_el.findall('iof:CourseControl', ns):
            leg_length = 0
            if course_control_el.find('iof:LegLength', ns) is not None:
                leg_length = int(course_control_el.find('iof:LegLength', ns).text)
            course['controls'].append({
                'type': course_control_el.attrib['type'],  # Start, Control, Finish
                'control': course_control_el.find('iof:Control', ns).text,
                'leg_length': leg_length,
            })
        courses.append(course)
    return courses


def entry_list(tree, ns):
    root = tree.getroot()
    if 'EntryList' not in root.tag:
        return
    groups = {}
    for group_el in root.findall('iof:Class', ns):
        group_id = group_el.find('iof:Id', ns).text
        groups[group_id] = {
            'id': group_id,
            'name': group_el.find('iof:Name', ns).text,
            'short_name': group_el.find('iof:ShortName', ns).text
        }
    person_entries = []
    for person_entry_el in root.findall('iof:PersonEntry', ns):
        person_el = person_entry_el.find('iof:Person', ns)
        birth_date_el = person_el.find('iof:BirthDate', ns)
        id_el = person_el.find('iof:Id', ns)
        person = {
            'family': person_el.find('iof:Name', ns).find('iof:Family', ns).text,
            'given': person_el.find('iof:Name', ns).find('iof:Given', ns).text,
            'extensions': {}
        }
        if birth_date_el is not None:
            person['birth_date'] = birth_date_el.text
        if id_el is not None:
            person['id'] = id_el.text

        extensions_el = person_el.find('iof:Extensions', ns)
        if extensions_el:
            qual_el = extensions_el.find('orgeo:Qual', ns)
            if qual_el is not None:
                person['extensions']['qual'] = qual_el.text
            bib_el = extensions_el.find('orgeo:BibNumber', ns)
            if bib_el is not None:
                person['extensions']['bib'] = bib_el.text

        org_el = person_entry_el.find('iof:Organisation', ns)
        organization = None
        if org_el:
            organization = {
                'id': org_el.find('iof:Id', ns).text,
                'name': org_el.find('iof:Name', ns).text
            }
            role = org_el.find('iof:Role', ns)
            if role:
                role_person = role.find('iof:Person', ns)
                organization['role_person'] = '{} {}'.format(
                    role_person.find('iof:Name', ns).find('iof:Family', ns).text,
                    role_person.find('iof:Name', ns).find('iof:Given', ns).text
                )

        group_el = person_entry_el.find('iof:Class', ns)
        if group_el:

            group = {
                'id': group_el.find('iof:Id', ns).text,
                'name': group_el.find('iof:Name', ns).text
            }
            groups[group['id']] = {
                'id': group['id'],
                'name': group['name']
            }

        control_card_el = person_entry_el.find('iof:ControlCard', ns)
        control_card = ''
        if control_card_el is not None:
            control_card = control_card_el.text

        race_numbers = []
        for race_num_el in person_entry_el.findall('iof:RaceNumber', ns):
            race_numbers.append(race_num_el.text)

        person_entries.append({
            'person': person,
            'organization': organization,
            'group': groups[group['id']] if group['id'] in groups else group,
            'control_card': control_card,
            'race_numbers': race_numbers,
        })

    return person_entries


def result_list(tree, ns):
    root = tree.getroot()
    if 'ResultList' not in root.tag:
        return
    groups = {}

    person_results = []

    for class_result in root.findall('iof:ClassResult', ns):
        """Group of results for class"""
        group_el = class_result.find('iof:Class', ns)
        group_id = group_el.find('iof:Id', ns).text
        groups[group_id] = {
            'id': group_id,
            'name': group_el.find('iof:Name', ns).text,
            'short_name': group_el.find('iof:ShortName', ns).text if group_el.find('iof:ShortName', ns) else ''
        }

        for person_result_el in class_result.findall('iof:PersonResult', ns):
            person_el = person_result_el.find('iof:Person', ns)
            birth_date_el = person_el.find('iof:BirthDate', ns)
            id_el = person_el.find('iof:Id', ns)
            person = {
                'family': person_el.find('iof:Name', ns).find('iof:Family', ns).text,
                'given': person_el.find('iof:Name', ns).find('iof:Given', ns).text,
                'extensions': {}
            }
            if birth_date_el is not None:
                person['birth_date'] = birth_date_el.text
            if id_el is not None:
                person['id'] = id_el.text

            org_el = person_result_el.find('iof:Organisation', ns)
            organization = None
            if org_el:
                organization = {
                    'id': org_el.find('iof:Id', ns).text,
                    'name': org_el.find('iof:Name', ns).text
                }
                role = org_el.find('iof:Role', ns)
                if role:
                    role_person = role.find('iof:Person', ns)
                    organization['role_person'] = '{} {}'.format(
                        role_person.find('iof:Name', ns).find('iof:Family', ns).text,
                        role_person.find('iof:Name', ns).find('iof:Given', ns).text
                    )

            result_el = person_result_el.find('iof:Result', ns)
            bib_el = result_el.find('iof:BibNumber', ns)
            control_card_el = result_el.find('iof:ControlCard', ns)
            finish_time_el = result_el.find('iof:FinishTime', ns)

            splits = []
            for split in result_el .findall('iof:SplitTime', ns):
                split_time_el = split.find('iof:Time', ns)
                if split_time_el is not None:
                    control_code = split.find('iof:ControlCode', ns)
                    split_obj = {
                        'control_code': control_code.text,
                        'time': split_time_el.text
                    }
                    splits.append(split_obj)

            result = {
                'bib': result_el.find('iof:BibNumber', ns).text if bib_el is not None else '',
                'start_time': result_el.find('iof:StartTime', ns).text,
                'finish_time': finish_time_el.text if finish_time_el is not None else '',
                'status': result_el.find('iof:Status', ns).text,
                'control_card': control_card_el.text if control_card_el is not None else '',
                'splits': splits
            }

            person_results.append({
                'person': person,
                'organization': organization,
                'group': groups[group_id],
                'result': result,
            })

    return person_results


def event(tree, ns):
    root = tree.getroot()
    event_obj = {'races': []}
    event_el = root.find('iof:Event', ns)

    if event_el is None:
        return

    if event_el.find('iof:Name', ns) is not None:
        event_obj['name'] = event_el.find('iof:Name', ns).text
    if event_el.find('iof:StartTime', ns) is not None:
        event_obj['start_time'] = event_el.find('iof:StartTime', ns).text
    if event_el.find('iof:URL', ns) is not None:
        event_obj['url'] = event_el.find('iof:URL', ns).text

    if event_el is not None:
        for race_el in event_el.findall('iof:Race', ns):
            race_obj = {'name': race_el.find('iof:Name', ns).text if race_el.find('iof:Name', ns) is not None else ''}
            start_time_el = race_el.find('iof:StartTime', ns)
            if start_time_el:
                if start_time_el.find('iof:Date', ns) is not None:
                    race_obj['date'] = start_time_el.find('iof:Date', ns).text
                if start_time_el.find('iof:Time', ns) is not None:
                    race_obj['time'] = start_time_el.find('iof:Time', ns).text

            event_obj['races'].append(race_obj)

    return event_obj

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
    ]

    return [result for result in results if result.data]


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
            'controls': [],
        }

        for course_control_el in course_el.findall('iof:CourseControl', ns):
            leg_length = 0
            if course_control_el.find('iof:LegLength', ns):
                leg_length = int(course_control_el.find('iof:LegLength', ns).text)
            course['controls'].append(
                {
                    'type': course_control_el.attrib['type'],  # Start, Control, Finish
                    'control': course_control_el.find('iof:Control', ns).text,
                    'leg_length': leg_length,
                }
            )
        courses.append(course)
    return courses


def entry_list(tree, ns):
    root = tree.getroot()
    if 'EntryList' not in root.tag:
        return
    groups = {}
    for group_el in root.find('iof:Event', ns).findall('iof:Class', ns):
        group_id = group_el.find('iof:Id', ns).text
        groups[group_id] = {
            'id': group_id,
            'name': group_el.find('iof:Name', ns).text,
            'short_name': group_el.find('iof:ShortName', ns).text,
        }
    person_entries = []
    for person_entry_el in root.findall('iof:PersonEntry', ns):
        person_el = person_entry_el.find('iof:Person', ns)
        birth_date_el = person_el.find('iof:BirthDate', ns)
        person = {
            'family': person_el.find('iof:Name', ns).find('iof:Family', ns).text,
            'given': person_el.find('iof:Name', ns).find('iof:Given', ns).text,
            'extensions': {},
        }
        if birth_date_el:
            person['birth_date'] = birth_date_el.text
        extensions_el = person_el.find('iof:Extensions', ns)
        if extensions_el:
            qual_el = extensions_el.find('orgeo:Qual', ns)
            if qual_el:
                person['extensions']['qual'] = qual_el.text
            bib_el = extensions_el.find('orgeo:BibNumber', ns)
            if bib_el:
                person['extensions']['bib'] = bib_el.text

        org_el = person_entry_el.find('iof:Organisation', ns)
        organization = {
            'id': org_el.find('iof:Id', ns).text,
            'name': org_el.find('iof:Name', ns).text,
        }
        role = org_el.find('iof:Role', ns)
        if role:
            role_person = role.find('iof:Person', ns)
            organization['role_person'] = '{} {}'.format(
                role_person.find('iof:Name', ns).find('iof:Family', ns).text,
                role_person.find('iof:Name', ns).find('iof:Given', ns).text,
            )

        group_el = person_entry_el.find('iof:Class', ns)
        group = {
            'id': group_el.find('iof:Id', ns).text,
            'name': group_el.find('iof:Name', ns).text,
        }

        control_card_el = person_entry_el.find('iof:ControlCard', ns)
        control_card = ''
        if control_card_el:
            control_card = control_card_el.text

        race_numbers = []
        for race_num_el in person_entry_el.findall('iof:RaceNumber', ns):
            race_numbers.append(race_num_el.text)

        person_entries.append(
            {
                'person': person,
                'organization': organization,
                'group': groups[group['id']] if group['id'] in groups else group,
                'control_card': control_card,
                'race_numbers': race_numbers,
            }
        )

    return person_entries

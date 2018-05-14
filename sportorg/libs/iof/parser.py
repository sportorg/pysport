import xml.etree.ElementTree as ET


def parse(file):
    ns = {
        'iof': 'http://www.orienteering.org/datastandard/3.0',
        'orgeo': 'http://orgeo.ru/iof-xml-extensions/3.0',
    }
    tree = ET.parse(file)
    root = tree.getroot()
    if 'EntryList' not in root.tag:
        return
    groups = {}
    for group_el in root.find('iof:Event', ns).findall('iof:Class', ns):
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
        person = {
            'family': person_el.find('iof:Name', ns).find('iof:Family', ns).text,
            'given': person_el.find('iof:Name', ns).find('iof:Given', ns).text,
            'extensions': {}
        }
        if birth_date_el is not None:
            person['birth_date'] = birth_date_el.text
        extensions_el = person_el.find('iof:Extensions', ns)
        if extensions_el:
            qual_el = extensions_el.find('orgeo:Qual', ns)
            if qual_el is not None:
                person['extensions']['qual'] = qual_el.text
            bib_el = extensions_el.find('orgeo:BibNumber', ns)
            if bib_el is not None:
                person['extensions']['bib'] = bib_el.text

        org_el = person_entry_el.find('iof:Organisation', ns)
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
        group = {
            'id': group_el.find('iof:Id', ns).text,
            'name': group_el.find('iof:Name', ns).text
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

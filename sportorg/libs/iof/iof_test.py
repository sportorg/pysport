import json

import xmlschema


iof_schema = xmlschema.XMLSchema('data/IOF.xsd')


files = [
    # 'data/Examples/CompetitorList.xml',
    # 'data/Examples/CourseData.xml',
    # 'data/Examples/EntryList1.xml',
    # 'data/Examples/EntryList2.xml',
    # 'data/Examples/OrganisationList.xml',
    # 'data/Examples/ResultList1.xml',
    # 'data/Examples/ResultList2.xml',
    # 'data/Examples/StartList1.xml',
    # 'data/Examples/StartList2.xml',
]

for file in files:
    try:
        print('{} {}'.format(file, iof_schema.is_valid(file)))
        print(json.dumps(iof_schema.to_dict(file, decimal_type=str), indent=4))
    except Exception as e:
        print('{} {}'.format(file, str(e)))

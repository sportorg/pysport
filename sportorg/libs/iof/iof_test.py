import json

import xmlschema


iof_schema = xmlschema.XMLSchema('data/IOF.xsd')


files = []

for file in files:
    try:
        print('{} {}'.format(file, iof_schema.is_valid(file)))
        print(json.dumps(iof_schema.to_dict(file, decimal_type=str), indent=4))
    except Exception as e:
        print('{} {}'.format(file, str(e)))

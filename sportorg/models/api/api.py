import uuid

from sportorg.models.memory import Person, Result, Course, Organization, Group, ResultManual, ResultSportident


class Api:
    support_obj = {
        'Person': Person,
        'Result': Result,
        'ResultManual': ResultManual,
        'ResultSportident': ResultSportident,
        'Group': Group,
        'Course': Course,
        'Organization': Organization,
    }

    def __init__(self, r):
        self.race = r
        self.list_obj = {
            'Person': self.race.persons,
            'Result': self.race.results,
            'ResultManual': self.race.results,
            'ResultSportident': self.race.results,
            'Group': self.race.groups,
            'Course': self.race.courses,
            'Organization': self.race.organizations,
        }

    def get_obj(self, obj_name, obj_id):
        for item in self.list_obj[obj_name]:
            if str(item.id) == obj_id:
                return item

    def update(self, dict_obj):
        if 'object' not in dict_obj:
            return
        if dict_obj['object'] not in self.support_obj:
            return

        obj = self.get_obj(dict_obj['object'], dict_obj['id'])
        if obj is None:
            self.create_obj(dict_obj)
        else:
            self.update_obj(obj, dict_obj)

    def update_obj(self, obj, dict_obj):
        obj.update_data(dict_obj)
        if dict_obj['object'] == 'Person':
            obj.group = self.get_obj('Group', dict_obj['group_id'])
            obj.organization = self.get_obj('Organization', dict_obj['organization_id'])
        elif dict_obj['object'] in ['Result', 'ResultManual', 'ResultSportident']:
            obj.person = self.get_obj('Person', dict_obj['person_id'])
        elif dict_obj['object'] == 'Group':
            obj.course = self.get_obj('Course', dict_obj['course_id'])

    def create_obj(self, dict_obj):
        obj = self.support_obj[dict_obj['object']]()
        obj.id = uuid.UUID(dict_obj['id'])
        self.update_obj(obj, dict_obj)
        self.list_obj[dict_obj['object']].insert(0, obj)

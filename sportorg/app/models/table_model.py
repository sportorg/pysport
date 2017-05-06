import sys

import logging

import time
from PyQt5 import QtCore

from PyQt5.QtCore import QVariant, QAbstractTableModel
from peewee import prefetch

from sportorg.app.models import model
from sportorg.app.models.model import Person, Participation, Group, Organization, ControlCard


class AbstractSportOrgTableModel (QAbstractTableModel):
    """
    Used to specify common table behavior
    """


class PersonTableModel(AbstractSportOrgTableModel):
    def __init__(self):
        super().__init__()
        self.model = None
        self.data = None
        self.count = None

    def rowCount(self, parent=None, *args, **kwargs):

        # calculate quantity only 1 time
        if self.count is None:
            try:
                m = model.Person
                if m.table_exists():
                    query = m.select()
                    self.count = query.count()

            except:
                print("Unexpected error:", sys.exc_info()[0])
                self.count = 300

        return self.count

    def columnCount(self, parent=None, *args, **kwargs):
        return 13

    def data(self, index, role=None):
        if role == QtCore.Qt.DisplayRole:
            answer = str(index.row()) + ' ' + str(index.column())

            try:
                answer = self.get_participation_data(index.row()-1)[index.column()]
            except:
                print(sys.exc_info())

            return QVariant(answer)

        return QVariant()

    def get_person_data(self, position):

        # create data only at first call - do only 1 select
        if self.data is None:
            person = Person.select()
            self.data = []
            for i in person:
                self.data.append([i.name, i.surname, i.year, i.qual, ])

        current_person = self.data[position]
        return current_person

    def get_participation_data(self, position):

        # create data only at first call - do only 1 select
        if self.data is None:
            start = time.time()
            # participation = Participation.select()
            #
            # query = (
            #     Participation
            #     .select(Participation, Person, Organization, Group, ControlCard)
            #     .join(Person)
            #     .join(Organization, JOIN_LEFT_OUTER)
            #     .switch(Participation)
            #     .join(Group, JOIN_LEFT_OUTER)
            #     .switch(Participation)
            #     .join(ControlCard, JOIN_LEFT_OUTER)
            #     .aggregate_rows()
            # )

            query = prefetch(
                Participation.select(),
                Person.select(),
                Organization.select(),
                Group.select(),
                ControlCard.select()
            )

            participation = query

            self.data = []
            for i in participation:
                assert (isinstance(i, Participation))
                person = i.person
                group = i.group
                group_name = ''
                if group is not None:
                    assert (isinstance(group, Group))
                    group_name = group.name
                team = person.team
                team_name = ''
                if team is not None:
                    assert (isinstance(team, Organization))
                    team_name = team.name
                card = i.control_card
                card_value = ''
                card_is_rented = ''
                if card is not None:
                    assert (isinstance(card, ControlCard))
                    card_value = card.value
                    card.is_rented = card.is_rented
                assert (isinstance(person, Person))

                self.data.append([
                    person.surname,
                    person.name,
                    person.sex,
                    person.qual,
                    group_name,
                    team_name,
                    person.year,
                    i.bib_number,
                    card_value,
                    card_is_rented,
                    i.comment,
                    person.world_code,
                    person.national_code
                ])
            end = time.time()
            logging.info('Entry structure was created in ' + str(end - start) + ' s')

        ret = self.data[position]
        return ret

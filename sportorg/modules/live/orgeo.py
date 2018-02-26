import logging
from queue import Queue
from threading import Thread, main_thread
import time

import requests
from requests.exceptions import MissingSchema, ConnectionError

from sportorg import config
from sportorg.core.singleton import Singleton
from sportorg.models.memory import race, Person, Result, RaceType


class OrgeoCommand:
    def __init__(self, command, url='', data=None):
        self.command = command
        self.url = url
        self.data = data


class Orgeo:
    def __init__(self, url, user_agent=None, logger=None):
        if not user_agent:
            user_agent = 'Orgeo client'
        self._url = url
        self._headers = {
            'User-Agent': user_agent
        }
        self._logger = logger

    def _get_url(self, text=''):
        return '{}{}'.format(self._url, text)

    def send(self, data):
        response = requests.post(
            self._get_url(),
            headers=self._headers,
            json=data
        )
        return response


class OrgeoThread(Thread):
    def __init__(self, queue, user_agent=None, logger=None):
        super().__init__(name='Orgeo')
        self._queue = queue
        self._user_agent = user_agent
        self._logger = logger

    def run(self):
        while True:
            try:
                while True:
                    if not main_thread().is_alive():
                        return
                    if not self._queue.empty():
                        break
                    time.sleep(0.5)

                command = self._queue.get()

                if command.command == 'stop':
                    break

                try:
                    orgeo = Orgeo(command.url, self._user_agent, self._logger)
                    response = orgeo.send(command.data)
                    self._logger.info('status {}'.format(response.status_code))
                    self._logger.info(response.text)
                except ConnectionError as e:
                    self._logger.error(str(e))
                    time.sleep(10)
                except MissingSchema as e:
                    self._logger.error(str(e))

                # if not self._queue.qsize():
                #     break
            except Exception as e:
                self._logger.error(str(e))


class OrgeoClient(metaclass=Singleton):
    def __init__(self):
        self._queue = Queue()
        self._thread = None
        self._result_ids = []

    @staticmethod
    def is_enabled():
        obj = race()
        live_enabled = obj.get_setting('live_enabled', False)
        url = obj.get_setting('live_url', '')
        return live_enabled and bool(url)

    @staticmethod
    def get_url():
        obj = race()
        url = obj.get_setting('live_url', '')
        return url

    @staticmethod
    def get_data(person, result=None):
        assert person, Person
        data = {
            'id': str(person.id),
            'ref_id': str(person.id),
            'bib': person.bib,
            'group_name': person.group.name if person.group else '',
            'name': person.full_name,
            'organization': person.organization.name if person.organization else '',
            # 'country_code': 'RUS',
            'card_number': person.sportident_card,
            'national_code': None,
            'world_code': None,
            'out_of_competition': person.is_out_of_competition,
            'start': person.start_time.to_sec() if person.start_time else 0
        }

        if race().is_relay():
            # send relay fields only for relay events (requested by Ivan Churakoff)
            data['relay_team'] = person.bib % 1000
            data['lap'] = max(person.bib // 1000, 1)

        if result is not None:
            assert result, Result
            data['start'] = result.get_start_time().to_sec()
            data['result_ms'] = round(result.get_result_for_sort() / 10)
            data['result_status'] = str(result.status)
            if result.is_sportident():
                if len(result.splits):
                    data['splits'] = []
                    splits = race().get_course_splits(result)
                    for i in range(len(splits)):
                        """
                        Orgeo Splits format: 
                        Option 	Type 	Description
                        code 	string 	CP code
                        time 	int 	seconds of current split - time from previous CP to this CP
                        """
                        current_split = {}
                        current_split['code'] = str(splits[i].code)
                        end_time = splits[i].time
                        if i > 0:
                            start_time = splits[i - 1].time
                        else:
                            start_time = result.get_start_time()
                        current_split['time'] = (end_time - start_time).to_sec()
                        data['splits'].append(current_split)

        return data

    def get_result_data(self):
        obj = race()
        persons = []
        for result in obj.results:
            if not result.person:
                continue
            person = result.person
            if person.group and person.group.name and result.id not in self._result_ids:
                persons.append(self.get_data(person, result))
                self._result_ids.append(result.id)
        return {'persons': persons}

    def get_start_list_data(self):
        obj = race()
        persons = []
        for person in obj.persons:
            if person.group and person.group.name:
                persons.append(self.get_data(person))
        self.clear()
        return {
            'params': {
                'start_list': True
            },
            'persons': persons
        }

    def _start_thread(self):
        if self._thread is None:
            self._thread = OrgeoThread(
                self._queue,
                '{} {}'.format(config.NAME, config.VERSION),
                logging.root
            )
            self._thread.start()
        elif not self._thread.is_alive():
            self._thread = None
            self._start_thread()

    def send_results(self):
        if self.is_enabled():
            self._start_thread()
            data = self.get_result_data()
            if len(data['persons']):
                self._queue.put(OrgeoCommand('result', self.get_url(), data))

    def send_start_list(self):
        if self.is_enabled():
            self._start_thread()
            data = self.get_start_list_data()
            self._queue.put(OrgeoCommand('start_list', self.get_url(), data))

    def clear(self):
        self._result_ids.clear()

    def stop(self):
        self._queue.put(OrgeoCommand('stop'))

"""
Parse finish CSV from online-service orgeo.ru (2023)

-- Format:
CSV, separator ";"
SPLITS: [hh:mm:ss|code|]*
П/п;Группа;Фамилия, имя участника;Команда;№;Номер чипа;Место;Результат;Отст.;Время старта;[TV;90cp;]Сплиты;

-- Example:
1;Ж10;Лимонникова Анна;72_СШ №2 Кобелева;39;8510418;1;00:09:10;+00:00;12:33:00;00:01:41|59|00:00:55|60|00:01:14|61|
2;Ж10;Глухарева Светлана;72_СШ №2 Глухарева;35;2102481;2;00:11:06;+01:56;12:29:00;00:01:30|59|00:00:43|60|00:01:28|61|
18;Ж10;Радченко Милана;72_СШ №2 Кобелева;37;9111137;;не старт;;12:37:00;
33;Ж12;Аристова Надежда;55_Омская обл.;162;8517947;;непр.отмет.;;13:09:00;00:03:00|70|
"""

import csv

from sportorg.models.memory import (
    Group,
    Organization,
    Person,
    Race,
    ResultSportident,
    ResultStatus,
    Split,
)
from sportorg.utils.time import hhmmss_to_time

POS_GROUP = 1
POS_NAME = 2
POS_TEAM = 3
POS_BIB = 4
POS_CARD = 5
POS_RES = 7
POS_START = 9
POS_SPLITS = -1

DNS_STATUS = ["DNS", "не старт"]
DSQ_STATUS = ["DSQ", "непр.отмет."]


def recovery(file_name: str, race: Race) -> None:
    encoding = "cp1251"
    separator = ";"
    spl_separator = "|"

    with open(file_name, encoding=encoding) as csv_file:
        spam_reader = csv.reader(csv_file, delimiter=separator)
        for tokens in spam_reader:
            if len(tokens) <= POS_START:
                continue

            bib = tokens[POS_BIB]
            if bib == "" or not bib.isdigit():
                continue

            name = tokens[POS_NAME]
            person = Person()
            spl_pos = name.find(" ")
            if spl_pos > 0:
                person.surname = name[:spl_pos]
                person.name = name[spl_pos + 1 :]
            else:
                person.name = name
            person.set_bib(int(bib))

            team_name = tokens[POS_TEAM]
            team = race.find_team(team_name)
            if not team:
                team = Organization()
                team.name = team_name
                race.organizations.append(team)
            person.organization = team

            group_name = tokens[POS_GROUP]
            group = race.find_group(group_name)
            if not group:
                group = Group()
                group.name = group_name
                race.groups.append(group)
            person.group = group

            if len(tokens[POS_START]) > 0:
                person.start_time = hhmmss_to_time(tokens[POS_START])

            res = ResultSportident()
            res.person = person
            if tokens[POS_CARD].isdigit():
                res.card_number = int(tokens[POS_CARD])
            res.start_time = person.start_time
            result = tokens[POS_RES]
            if result.find(":") > 0:
                result_value = hhmmss_to_time(result)
                res.finish_time = res.start_time + result_value
            else:
                if result in DNS_STATUS:
                    res.status = ResultStatus.DID_NOT_START
                elif result in DSQ_STATUS:
                    res.status = ResultStatus.DISQUALIFIED

            splits = tokens[POS_SPLITS]
            if len(splits) > 1:
                splits_array = splits.split(spl_separator)
                cur_time = person.start_time
                for i in range(len(splits_array) // 2):
                    split = Split()
                    cur_time += hhmmss_to_time(splits_array[i * 2])
                    split.time = cur_time
                    split.code = int(splits_array[i * 2 + 1])
                    res.splits.append(split)

            race.persons.append(person)
            race.results.append(res)

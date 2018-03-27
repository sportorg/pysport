import logging

from sportorg.core.singleton import singleton
from sportorg.models.memory import race


def get_countries():
    return [
        '',
        'Abkhazia',
        'Australia',
        'Austria',
        'Azerbaijan',
        'Aland Islands',
        'Albania',
        'Algeria',
        'Anguilla',
        'Angola',
        'Andorra',
        'Argentina',
        'Armenia',
        'Aruba',
        'Afghanistan',
        'Bahamas',
        'Bangladesh',
        'Barbados',
        'Bahrain',
        'Belarus',
        'Belize',
        'Belgium',
        'Benin',
        'Bulgaria',
        'Bolivia',
        'Bosnia & Herzegovina',
        'Botswana',
        'Brazil',
        'Brunei Darussalam',
        'Burundi',
        'Bhutan',
        'Vatican City',
        'United Kingdom',
        'Hungary',
        'Venezuela',
        'Timor, East',
        'Viet Nam',
        'Gabon',
        'Haiti',
        'Gambia',
        'Ghana',
        'Guadeloupe',
        'Guatemala',
        'Guinea',
        'Guinea-Bissau',
        'Germany',
        'Gibraltar',
        'Hong Kong',
        'Honduras',
        'Grenada',
        'Greenland',
        'Greece',
        'Georgia',
        'Guam',
        'Denmark',
        'Dominica',
        'Dominican Republic',
        'Egypt',
        'Zambia',
        'Western Sahara',
        'Zimbabwe',
        'Israel',
        'India',
        'Indonesia',
        'Jordan',
        'Iraq',
        'Iran',
        'Ireland',
        'Iceland',
        'Spain',
        'Italy',
        'Yemen',
        'Kazakhstan',
        'Cambodia',
        'Cameroon',
        'Canada',
        'Qatar',
        'Kenya',
        'Cyprus',
        'Kyrgyzstan',
        'Kiribati',
        'China',
        'Colombia',
        'Korea, D.P.R.',
        'Korea',
        'Costa Rica',
        'Cote d\'Ivoire',
        'Cuba',
        'Kuwait',
        'Lao P.D.R.',
        'Latvia',
        'Lesotho',
        'Liberia',
        'Lebanon',
        'Libyan Arab Jamahiriya',
        'Lithuania',
        'Liechtenstein',
        'Luxembourg',
        'Mauritius',
        'Mauritania',
        'Madagascar',
        'Macedonia',
        'Malawi',
        'Malaysia',
        'Mali',
        'Maldives',
        'Malta',
        'Morocco',
        'Mexico',
        'Mozambique',
        'Moldova',
        'Monaco',
        'Mongolia',
        'Namibia',
        'Nepal',
        'Niger',
        'Nigeria',
        'Netherlands',
        'Nicaragua',
        'New Zealand',
        'Norway',
        'United Arab Emirates',
        'Oman',
        'Pakistan',
        'Panama',
        'Paraguay',
        'Peru',
        'Poland',
        'Portugal',
        'Russia',
        'Romania',
        'San Marino',
        'Saudi Arabia',
        'Senegal',
        'Serbia',
        'Singapore',
        'Syrian Arab Republic',
        'Slovakia',
        'Slovenia',
        'Somalia',
        'Sudan',
        'USA',
        'Tajikistan',
        'Thailand',
        'Tanzania',
        'Togo',
        'Tunisia',
        'Turkmenistan',
        'Turkey',
        'Uganda',
        'Uzbekistan',
        'Ukraine',
        'Uruguay',
        'Micronesia',
        'Fiji',
        'Philippines',
        'Finland',
        'France',
        'Croatia',
        'Chad',
        'Montenegro',
        'Czech Republic',
        'Chile',
        'Switzerland',
        'Sweden',
        'Sri Lanka',
        'Ecuador',
        'Eritrea',
        'Estonia',
        'Ethiopia',
        'South Africa',
        'Jamaica',
        'Japan'
    ]


def get_regions():
    return ['', 'Тюменская обл.', 'Курганская обл.', 'Свердловская обл.', 'Челябинская обл.', 'Республика Коми',
            'г.Москва', 'ХМАО-Югра']


def get_groups():
    return ['', 'M12', 'M14', 'M16', 'M21', 'D12', 'D14', 'M16', 'D21']


def get_race_groups():
    ret = ['']
    try:
        for i in race().groups:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return get_groups()


def get_teams():
    return ['', 'Тюменская обл.', 'Курганская обл.', 'Челябинская обл.', 'Республика Коми', 'г.Москва',
            'ХМАО-Югра']


def get_race_teams():
    ret = ['']
    try:
        for i in race().organizations:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return get_teams()


def get_race_courses():
    ret = ['']
    try:
        for i in race().courses:
            if i.name:
                ret.append(i.name)
        return ret
    except Exception as e:
        logging.error(str(e))
        return []


def get_names():
    return [
        '',
        'Адик',
        'Азамат',
        'Александр',
        'Александра',
        'Алексей',
        'Алена',
        'Алина',
        'Альберт',
        'Анастасия',
        'Андрей',
        'Анна',
        'Антон',
        'Арина',
        'Аркадий',
        'Артем',
        'Артём',
        'Артур',
        'Боймат',
        'Вадим',
        'Валентина',
        'Валерий',
        'Валерия',
        'Варвара',
        'Василий',
        'Василина',
        'Вениамин',
        'Вера',
        'Вероника',
        'Виктор',
        'Виктория',
        'Виталий',
        'Влада',
        'Владимир',
        'Владислав',
        'Всеволод',
        'Вячеслав',
        'Галина',
        'Георгий',
        'Григорий',
        'Даниил',
        'Данил',
        'Данила',
        'Данис',
        'Дания',
        'Дарья',
        'Денис',
        'Диана',
        'Дмитрий',
        'Евангелина',
        'Евгений',
        'Евгения',
        'Егор',
        'Екатерина',
        'Елена',
        'Елизавета',
        'Заур',
        'Иван',
        'Игорь',
        'Илья',
        'Ирина',
        'Карина',
        'Кирилл',
        'Константин',
        'Кристина',
        'Ксения',
        'Лариса',
        'Лев',
        'Леонид',
        'Лидия',
        'Любовь',
        'Людмила',
        'Макар',
        'Максим',
        'Маргарита',
        'Марина',
        'Мария',
        'Матвей',
        'Михаил',
        'Надежда',
        'Наталья',
        'Никит',
        'Никита',
        'Николай',
        'Нина',
        'Оксана',
        'Олег',
        'Олеся',
        'Ольга',
        'Павел',
        'Полина',
        'Равиль',
        'Раиса',
        'Рамзия',
        'Роман',
        'Руслан',
        'Савелий',
        'Светлана',
        'Святослав',
        'Семён',
        'Сергей',
        'Софья',
        'Станислав',
        'Степан',
        'Тамара',
        'Татьяна',
        'Тимофей',
        'Тимур',
        'Ульяна',
        'Филипп',
        'Шойра',
        'Эльза',
        'Юлия',
        'Юрий',
        'Ярослав',
        'Ярослава'
    ]


@singleton
class StatusComments(object):
    STATUS_COMMENTS = []

    def get_all(self):
        return self.STATUS_COMMENTS

    def get(self):
        for item in self.STATUS_COMMENTS:
            if item:
                return item
        return ''

    def set(self, items):
        if '' not in items:
            items.insert(0, '')
        self.STATUS_COMMENTS = items

    @staticmethod
    def remove_hint(full_str):
        return str(full_str).split('#')[0].strip()

import logging
import operator

from sportorg.common.singleton import singleton
from sportorg.models.memory import Qualification, race


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
        'Japan',
    ]


def get_regions():
    return Regions().get_all()


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
    return ['']


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
    return PersonNames().get_all()


@singleton
class PersonNames(object):
    NAMES = []

    def get_all(self):
        return self.NAMES

    def set(self, items):
        items.sort()
        if '' not in items:
            items.insert(0, '')
        self.NAMES = items


@singleton
class Regions(object):
    REGIONS = []

    def get_all(self):
        return self.REGIONS

    def set(self, items):
        items.sort()
        if '' not in items:
            items.insert(0, '')
        self.REGIONS = items


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


@singleton
class RentCards(object):
    CARDS = set()

    def exists(self, item):
        return item in self.CARDS

    def append(self, *items):
        for item in items:
            self.CARDS.add(item)

    def set(self, items):
        self.CARDS = set(items)

    def get(self):
        return self.CARDS

    def set_from_text(self, text, separator='\n'):
        self.CARDS = set()
        for item in text.split(separator):
            if not len(item):
                continue
            for n_item in item.split():
                if n_item.isdigit():
                    self.append(int(n_item))

    def to_text(self, separator='\n'):
        return separator.join([str(x) for x in self.CARDS])


@singleton
class RankingTable(object):
    """
    Ranking is read from configuration file called 'ranking_score.txt'
    Format: RANK;I;II;III;I_Y;II_Y[;III_Y[;KMS[;MS]]]
    e.g. 1000;136;151;169;;
    e.g. 850;133;148;166;;
    e.g. 5;;;;;100
    """

    RANKING = []
    column_mapping = {
        Qualification.I: 1,
        Qualification.II: 2,
        Qualification.III: 3,
        Qualification.I_Y: 4,
        Qualification.II_Y: 5,
        Qualification.III_Y: 6,
        Qualification.KMS: 7,
        Qualification.MS: 8,
    }

    def get_all(self):
        return self.RANKING

    def get_qual_table(self, qual):
        # get only 2 columns from whole table, corresponding to specified qualification
        try:
            columns = [0, self.column_mapping[qual]]
            my_items = operator.itemgetter(*columns)
            return [my_items(x) for x in self.RANKING]
        except Exception as e:
            # logging.exception(e)
            return [[0, 0]]

    def set(self, items):
        self.RANKING = []
        for i in items:
            row = []
            for j in i:
                if str(j).isdecimal():
                    row.append(int(j))
                else:
                    row.append(0)
            self.RANKING.append(row)

import codecs

from sportorg.models.memory import RaceType


class SFRXParser:
    def __init__(self, data=None):
        self._settings = {}
        self._dists = {}
        self._dists = {}
        self._groups = {}
        self._teams = {}

        self._data = [] if data is None else data
        self._splits = []

    def parse(self, source: str):
        f = codecs.open(source, "r", "UTF-8")

        for row in f:
            self.append(row.split("\t"))

        return self

    @property
    def data(self):
        return self._data

    def append(self, row):
        if not row or len(row) < 1:
            return
        if row[0].startswith("SFRx"):
            self._settings["title"] = row[1]
            self._settings["location"] = row[2]
            if row[7] == "Эстафета":
                self._settings["race_type"] = RaceType.RELAY
            else:
                self._settings["race_type"] = RaceType.INDIVIDUAL_RACE
        if row[0].startswith("d"):
            name = row[1]
            length = row[6]
            climb = row[7]
            bib = row[2]
            controls = []
            i = 9
            while i < len(row) - 1:
                controls.append({"code": row[i], "length": row[i + 1], "order": i - 8})
                i = i + 2
            dist_dict = {
                "bib": bib,
                "name": name,
                "length": length,
                "climb": climb,
                "controls": controls,
            }

            self._dists[str(int(row[0][1:]))] = dist_dict

        if row[0].startswith("g"):
            group = {"name": row[1], "course": int(row[7])}
            self._groups[str(int(row[0][1:]))] = group
        if row[0].startswith("t"):
            self._teams[str(int(row[0][1:]))] = row[1]

        if row[0].startswith("c"):
            person_dict = {
                "bib": int(row[1]),
                "group_id": row[2],
                "surname": row[3],
                "name": row[4].split(' ', 1)[0],
                "middle_name": row[4].split(' ', 1)[1] if len(row[4].split(' ', 1)) > 1 else "",
                "team_id": row[5],
                "year": int(row[6]) if len(row[6]) == 4 else 0,
                "birthday": row[6] if len(row[6]) == 10 else "",
                "qual_id": row[7],
                "comment": row[8],
                "start": row[13],
                "finish": row[14],
                "credit": row[15],
                "result": row[16],
            }
            self._data.append(person_dict)

        if row[0].startswith("s"):
            bib = row[1]
            splits = []
            i = 6
            while i < len(row) - 1:
                splits.append((row[i], row[i + 2]))
                i = i + 3

            split_dict = {"bib": bib, "split": splits}
            self._splits.append(split_dict)

    @property
    def groups(self):
        return self._groups

    @property
    def dists(self):
        return self._dists

    @property
    def splits(self):
        return self._splits

    @property
    def teams(self):
        return self._teams

    @property
    def settings(self):
        return self._settings


def parse(source: str) -> SFRXParser:
    parser = SFRXParser()
    return parser.parse(source)

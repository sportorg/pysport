from dataclasses import dataclass, field
from typing import IO
from xml.etree import ElementTree
from sportorg.utils.text import detect_encoding


class OcadImportException(Exception):
    pass


class CourseControlDict(dict):
    def __len__(self) -> int:
        if len(self.keys()) - 1 >= 0:
            return len(self.keys()) - 1

        return len(self.keys())


@dataclass
class CourseControl:
    order: str = ""
    code: str = ""
    length: str = ""


@dataclass
class Course:
    group: str = ""
    course: str = ""
    bib: str = ""
    climb: int = 0
    length: int = 0
    controls: CourseControlDict = field(default_factory=CourseControlDict)


class CourseList(list):
    def append(self, course: Course) -> None:
        super().append(course)


# fmt: off
class ClassesV8:
    """
    Example:

    ```
    M16;Normal Course;0;5.700;130;S1;0.219;117;0.412;150;0.502;107;0.155;63;0.113;93;0.176;99;0.183;97;0.488;98;0.659;64;0.661;140;0.191;52;0.198;87;0.391;132;0.249;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.1;3.300;205;S1;0.185;71;0.351;64;0.661;140;0.191;52;0.225;106;0.286;132;0.249;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.2;3.400;205;S1;0.219;117;0.246;64;0.733;70;0.207;52;0.198;87;0.341;56;0.281;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.3;3.400;205;S1;0.287;118;0.360;64;0.596;78;0.303;52;0.225;106;0.229;56;0.281;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    ```
    """
    # fmt: on

    def __init__(self, data=None):
        if data is None:
            data = []
        self._data = data
        self._courses = CourseList()
        self._groups = set()

    def clear(self):
        self._courses = CourseList()
        self._groups = set()

    def parse(self, file):
        if not isinstance(file, str) and not isinstance(file, IO):
            raise TypeError('file is not str or IO')
        if isinstance(file, str):
            try:
                enc = detect_encoding(file, default_encoding="windows-1251")
                with open(file, encoding=enc) as f:
                    content = f.readlines()
            except FileNotFoundError:
                raise FileNotFoundError('Not found ' + file)
        else:
            content = file.readlines()
        self._data = [x.strip() for x in content if x]
        self.clear()

        return self

    @property
    def data(self):
        if self._data is None:
            return []

        return self._data

    @property
    def courses(self) -> CourseList:
        if not len(self._courses):
            self._courses = CourseList()
            for item in self.data:
                self._courses.append(self.get_course(item))

        return self._courses

    @property
    def groups(self):
        if not len(self._groups):
            for course in self.courses:
                self._groups.add(course.group)

        return self._groups

    @staticmethod
    def get_courses(item):
        if not isinstance(item, str) and not isinstance(item, list):
            raise TypeError('item is not string or list')
        if isinstance(item, str):
            item = str(item).split(';')
        courses = CourseControlDict()
        courses_split = item[5:]
        courses_split.insert(0, '0')
        limit = len(courses_split)
        i = 0
        while (2 * i + 1) < limit:
            len_str = str(courses_split[2 * i]).replace(',', '.')
            if len_str and not len_str.replace('.', '').isdecimal():
                raise OcadImportException(
                    'Incorrect length:' + len_str + ' in row ' + str(item)
                )

            courses[i] = CourseControl(
                **{
                    'order': i,
                    'code': courses_split[2 * i + 1],
                    'length': float(len_str) if len(item[4]) else 0.0,
                }
            )
            i += 1

        return courses

    @staticmethod
    def get_course(item):
        def ifempty(o, default=None):
            if len(o):
                return 0
            if default:
                return default
            return None

        if not isinstance(item, str) and not isinstance(item, list):
            raise TypeError('item is not string or list')
        if isinstance(item, str):
            item = str(item).split(';')

        if len(item) < 5:
            raise OcadImportException('Too few fields: ' + str(item))

        len_str = str(item[3]).replace(',', '.')
        if len_str and not len_str.replace('.', '').isdecimal():
            raise OcadImportException(
                'Incorrect length:' + len_str + ' in row ' + str(item)
            )

        climb_str = str(item[4]).replace(',', '.')
        if climb_str and not climb_str.replace('.', '').isdecimal():
            raise OcadImportException(
                'Incorrect climb:' + climb_str + ' in row ' + str(item)
            )

        course = {
            'group': item[0],
            'course': item[1],
            'bib': item[2],
            'length': float(len_str) if len(item[3]) else 0.0,
            'climb': float(climb_str) if len(item[4]) else 0.0,
            'controls': ClassesV8.get_courses(item),
        }

        return Course(**course)


def parse_txt_v8(source):
    classes_v8 = ClassesV8()

    return classes_v8.parse(source)


class CoursesText:
    """
    Example:

    ```
    Normal Course	5.7	130	19	S1-117-150-107-63-93-99-97-98-64-140-52-87-132-95-116-90-47-120-115-F1
    Relay.1	3.3	 85	12	S1-(71/117/118)-64-(78/140/70)-52-(-(106-132/87-56))-95-116-90-47-120-115-F1
    ```
    """

    def __init__(self, file):
        self.file = file


class IofXMLv3:
    def __init__(self, tree=None):
        self._tree = tree

    def parse(self, source):
        self._tree = ElementTree.parse(source)

        return self


def parse_xml_v3(source):
    iof_xml_v3 = IofXMLv3()

    return iof_xml_v3.parse(source)

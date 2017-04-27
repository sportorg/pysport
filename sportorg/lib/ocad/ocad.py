from typing import IO
from xml.etree import ElementTree


class ClassesV8:
    """
    Example:
    
    M16;Normal Course;0;5.700;130;S1;0.219;117;0.412;150;0.502;107;0.155;63;0.113;93;0.176;99;0.183;97;0.488;98;0.659;64;0.661;140;0.191;52;0.198;87;0.391;132;0.249;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.1;3.300;205;S1;0.185;71;0.351;64;0.661;140;0.191;52;0.225;106;0.286;132;0.249;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.2;3.400;205;S1;0.219;117;0.246;64;0.733;70;0.207;52;0.198;87;0.341;56;0.281;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    Relay;Relay;1.3;3.400;205;S1;0.287;118;0.360;64;0.596;78;0.303;52;0.225;106;0.229;56;0.281;95;0.098;116;0.152;90;0.179;47;0.216;120;0.280;115;0.229;F1
    """

    def __init__(self, data=None):
        if data is None:
            data = []
        self._data = data
        self._courses = []
        self._groups = set()

    def clear(self):
        self._courses = []
        self._groups = set()

    def read_file(self, file):
        if not isinstance(file, str) and not isinstance(file, IO):
            raise TypeError("file is not str or IO")
        if isinstance(file, str):
            try:
                with open(file) as f:
                    content = f.readlines()
            except FileNotFoundError:
                raise FileNotFoundError("Not found " + file)
        else:
            content = file.readlines()
        self._data = [x.strip() for x in content]
        self.clear()

        return self

    @property
    def data(self):
        if self._data is None:
            return []

        return self._data

    @property
    def courses(self):
        if not len(self._courses):
            self._courses = []
            for item in self.data:
                self._courses.append(self.get_course(item))

        return self._courses

    @property
    def groups(self):
        if not len(self._groups):
            for course in self.courses:
                self._groups.add(course['group'])

        return self._groups

    @staticmethod
    def get_courses(item):
        if not isinstance(item, str) and not isinstance(item, list):
            raise TypeError("item is not string or list")
        if isinstance(item, str):
            item = str(item).split(';')
        courses = {}
        courses_split = item[5:]
        courses_split.insert(0, '0')
        limit = len(courses_split)
        i = 0
        while (2*i + 1) < limit:
            courses[i] = {"code": courses_split[2*i + 1], "length": courses_split[2*i]}
            i += 1

        return courses

    @staticmethod
    def get_course(item):
        if not isinstance(item, str) and not isinstance(item, list):
            raise TypeError("item is not string or list")
        if isinstance(item, str):
            item = str(item).split(';')
        course = {
            "group": item[0],
            "type": item[1],
            "bib": item[2],
            "length": item[3],
            "height": item[4],
            "course": ClassesV8.get_courses(item)
        }

        return course


class CoursesText:
    """
    Example:
    
    Normal Course	5.7	130	19	S1-117-150-107-63-93-99-97-98-64-140-52-87-132-95-116-90-47-120-115-F1
    Relay.1	3.3	 85	12	S1-(71/117/118)-64-(78/140/70)-52-(-(106-132/87-56))-95-116-90-47-120-115-F1
    """

    def __init__(self, file):
        self.file = file


class IofXMLv3:
    def __init__(self, tree=None):
        assert tree, ElementTree
        self._tree = tree

    def parse(self, source):
        self._tree = ElementTree.parse(source)

        return self

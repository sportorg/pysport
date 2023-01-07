from typing import List, Union
from sportorg.models.memory import ResultSportident, Person, Course, CourseControl, Split


def make_course(course: List[Union[int, str]]) -> Course:
    course_object = Course()
    course_object.controls = [make_course_control(code) for code in course]
    return course_object

def make_course_control(code: Union[int, str]) -> CourseControl:
    control = CourseControl()
    control.update_data({'code': code, 'length': 0})
    return control

def make_result(splits: List[int]) -> ResultSportident:
    result = ResultSportident()
    result.person = Person()
    result.splits = [make_split_control(code) for code in splits]
    return result

def make_split_control(code: int) -> Split:
    split = Split()
    split.update_data({'code': code, 'time': 0})
    return split

def check(course: List[Union[int, str]], splits: List[int]) -> bool:
    result = make_result(splits)
    course_object = make_course(course)
    return result.check(course_object)

def correct(course: List[Union[int, str]], splits: List[int]) -> bool:
    return check(course, splits)

def incorrect(course: List[Union[int, str]], splits: List[int]) -> bool:
    return not check(course, splits)


def test_specific_order_courses():
    '''Дистанция в заданном направлении. Спортсмену необходимо пройти 
    контрольные пункты в заданном порядке. Лишние КП не учитываются.
    '''    
    assert correct(course=[31, 32, 33],
                   splits=[31, 32, 33])

    # Лишний КП
    assert correct(course=[    31, 32, 33],
                   splits=[99, 31, 32, 33])

    assert correct(course=[31,     32, 33],
                   splits=[31, 99, 32, 33])

    assert correct(course=[31, 32, 33    ],
                   splits=[31, 32, 33, 99])

    # Пропущен КП
    assert incorrect(course=[31, 32, 33],
                     splits=[    32, 33])

    assert incorrect(course=[31, 32, 33],
                     splits=[31,     33])

    assert incorrect(course=[31, 32, 33],
                     splits=[31, 32    ])

    assert incorrect(course=[31, 32, 33],
                     splits=[99, 32, 33])

    # Взят не тот КП
    assert incorrect(course=[31, 32, 33],
                     splits=[51, 99, 33])

    assert incorrect(course=[31, 32, 33],
                     splits=[31, 32, 99])

    # КП взяты не в том порядке
    assert incorrect(course=[31, 32, 33],
                     splits=[31, 33, 32])


def test_free_order_course():
    '''Дистанция по выбору — спортсмену необходимо собрать определённое количество КП 
    в свободном порядке. Повторно взятые КП не засчитываются. Иногда на дистанции могут 
    быть обязательные первый и/или последний КП, обязательный КП в середине дистанции,
    переворот карты.
    '''    

    # Выбор — 3 различных КП
    c                 = ['*', '*', '*']
    assert   correct(c, [ 31,  32,  33])
    assert   correct(c, [ 71,  72,  73])
    assert   correct(c, [ 31,  32,  33,  34])
    assert incorrect(c, [ 31,  32     ])
    assert incorrect(c, [ 31,  31,  33])
    assert incorrect(c, [ 31,  32,  32])
    assert incorrect(c, [ 31,  32,  31])

    # Выбор: заданные номера КП
    c                 = ['*(31,32,33,34)', '*(31,32,33,34)', '*(31,32,33,34)']
    assert   correct(c, [ 31,               32,               33             ])
    assert   correct(c, [ 31, 31,           32,               33             ])
    
    assert incorrect(c, [ 31,               32,               73             ])
    assert incorrect(c, [ 31,               32,               31             ])
    assert incorrect(c, [ 31,               32                               ])

    # Выбор: заданные номера КП со сменой карты
    c                 = ['*(31,32,33,34)', '*(31,32,33,34)', '*(71,72,73,74)', '*(71,72,73,74)']
    assert   correct(c, [ 31,               34,               71,               74             ])
    assert   correct(c, [ 31, 31,           34,               71,               74             ])
    assert   correct(c, [ 31, 47,           34,               71,               74             ])
    assert   correct(c, [ 31,               32, 34,           71,               74             ])
    assert   correct(c, [ 31,               32,               71,               72, 74         ])
    
    assert incorrect(c, [ 31,               71,               34,               74             ])
    assert incorrect(c, [ 31,               34,               74                               ])
    assert incorrect(c, [ 31,               44,               71,               74             ])
    assert incorrect(c, [ 31,               34,               41,               74             ])

    # Выбор + заданные КП
    c                 = ['31', '*(32,33,34)', '*(32,33,34)', '70']
    assert   correct(c, [ 31,   32,            33,            70 ])
    assert   correct(c, [ 31,31,32,            33,            70 ])
    assert   correct(c, [ 31,   32,            33,            70, 71 ])
    assert   correct(c, [ 31,   32,            33, 34,        70 ])
    
    assert incorrect(c, [ 71,   32,            33,            70 ])
    assert incorrect(c, [ 31,   32,            33,            71 ])
    assert incorrect(c, [ 31,   32,            73,            70 ])
    assert incorrect(c, [ 31,   32,            32,            70 ])
    assert incorrect(c, [       32,            33,            70 ])
    assert incorrect(c, [ 31,   32,                           70 ])
    assert incorrect(c, [ 31,   32,            33,               ])

    # Выбор + заданные КП
    c                 = ['*(31,32,33)', '55', '*(31,32,33)']
    assert   correct(c, [ 31,            55,   33          ])
    assert   correct(c, [ 31, 32,        55,   33          ])
    assert   correct(c, [ 31,            55,   33, 31      ])
    assert   correct(c, [ 71, 31,        55,   33          ])
    
    assert incorrect(c, [ 31,            55,   31          ])
    assert incorrect(c, [ 71,            55,   33          ])
    assert incorrect(c, [ 31,            75,   33          ])
    assert incorrect(c, [ 31,            55,   73          ])
    assert incorrect(c, [                55,   33          ])
    assert incorrect(c, [ 31,                  33          ])
    assert incorrect(c, [ 31,            55                ])

    # Выбор + переворот карты + обязательные первый и последний КП на каждом круге
    c                 = [31, '*(33,34,35)', '*(33,34,35)', 39, 41, '*(43,44,45)', '*(43,44,45)', 49]
    assert   correct(c, [31,  33,            34,           39, 41,   45,           43,           49])
    assert   correct(c, [31,  33,            34,           39, 71, 41, 45,         43,           49])


def test_non_obvious_behavior():
    '''Неочевидное поведение при проверке дистанции. Не всегда это некорректная работа
    алгоритма, иногда может возникать из-за недочётов при составлении курсов.
    '''    
    # Выбор + заданные КП. Первый КП31 и последний КП34 включены в проверку выбора. 
    # Повторная отметка на этих КП может (ошибочно?) дать правильную отметку.
    c                 = [31, '*', '*', 34]
    assert   correct(c, [31,  31,  33, 34])
    assert   correct(c, [31,  32,  34, 34])
    c                 = [31, '*(31,32,33,34)', '*(31,32,33,34)', 34]
    assert   correct(c, [31,  31,               33,              34])
    assert   correct(c, [31,  32,               34,              34])

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

def ok(course: List[Union[int, str]], splits: List[int]) -> bool:
    '''Проверка отметки: результат засчитан

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции

    Returns
    -------
    bool
        Возвращает True если отметка признана правильной
    '''
    return check(course, splits)

def dsq(course: List[Union[int, str]], splits: List[int]) -> bool:
    '''Проверка отметки: результат не засчитан, нарушение порядка прохождения дистанции

    Parameters
    ----------
    course : List[Union[int, str]]
        Порядок прохождения дистанции
    splits : List[int]
        Отметки спортсмена на дистанции

    Returns
    -------
    bool
        Возвращает True если отметка признана неправильной
    '''
    return not check(course, splits)


def test_specific_order_courses():
    '''Дистанция в заданном направлении. Спортсмену необходимо пройти 
    контрольные пункты в заданном порядке. Лишние КП не учитываются.
    '''    
    assert ok(course=[31, 32, 33],
              splits=[31, 32, 33])

    # Лишний КП
    assert ok(course=[    31, 32, 33],
              splits=[99, 31, 32, 33])

    assert ok(course=[31,     32, 33],
              splits=[31, 99, 32, 33])

    assert ok(course=[31, 32, 33    ],
              splits=[31, 32, 33, 99])

    # Пропущен КП
    assert dsq(course=[31, 32, 33],
               splits=[    32, 33])

    assert dsq(course=[31, 32, 33],
               splits=[31,     33])

    assert dsq(course=[31, 32, 33],
               splits=[31, 32    ])

    assert dsq(course=[31, 32, 33],
               splits=[99, 32, 33])

    # Взят не тот КП
    assert dsq(course=[31, 32, 33],
               splits=[51, 99, 33])

    assert dsq(course=[31, 32, 33],
               splits=[31, 32, 99])

    # КП взяты не в том порядке
    assert dsq(course=[31, 32, 33],
               splits=[31, 33, 32])


def test_free_order_course():
    '''Дистанция по выбору — спортсмену необходимо собрать определённое количество КП 
    в свободном порядке. Повторно взятые КП не засчитываются. Иногда на дистанции могут 
    быть обязательные первый и/или последний КП, обязательный КП в середине дистанции,
    переворот карты.
    '''    

    # Выбор — 3 различных КП
    c           = ['*', '*', '*']
    assert  ok(c, [ 31,  32,  33])
    assert  ok(c, [ 71,  72,  73])
    assert  ok(c, [ 31,  32,  33,  34])
    assert dsq(c, [ 31,  32     ])
    assert dsq(c, [ 31,  31,  33])
    assert dsq(c, [ 31,  32,  32])
    assert dsq(c, [ 31,  32,  31])

    # Выбор: заданные номера КП
    c           = ['*(31,32,33,34)', '*(31,32,33,34)', '*(31,32,33,34)']
    assert  ok(c, [ 31,               32,               33             ])
    assert  ok(c, [ 31, 31,           32,               33             ])
    
    assert dsq(c, [ 31,               32,               73             ])
    assert dsq(c, [ 31,               32,               31             ])
    assert dsq(c, [ 31,               32                               ])

    # Выбор: заданные номера КП со сменой карты
    c           = ['*(31,32,33,34)', '*(31,32,33,34)', '*(71,72,73,74)', '*(71,72,73,74)']
    assert  ok(c, [ 31,               34,               71,               74             ])
    assert  ok(c, [ 31, 31,           34,               71,               74             ])
    assert  ok(c, [ 31, 47,           34,               71,               74             ])
    assert  ok(c, [ 31,               32, 34,           71,               74             ])
    assert  ok(c, [ 31,               32,               71,               72, 74         ])
    
    assert dsq(c, [ 31,               71,               34,               74             ])
    assert dsq(c, [ 31,               34,               74                               ])
    assert dsq(c, [ 31,               44,               71,               74             ])
    assert dsq(c, [ 31,               34,               41,               74             ])

    # Выбор + заданные КП
    c           = ['31', '*(32,33,34)', '*(32,33,34)', '70']
    assert  ok(c, [ 31,   32,            33,            70 ])
    assert  ok(c, [ 31,31,32,            33,            70 ])
    assert  ok(c, [ 31,   32,            33,            70, 71 ])
    assert  ok(c, [ 31,   32,            33, 34,        70 ])
    
    assert dsq(c, [ 71,   32,            33,            70 ])
    assert dsq(c, [ 31,   32,            33,            71 ])
    assert dsq(c, [ 31,   32,            73,            70 ])
    assert dsq(c, [ 31,   32,            32,            70 ])
    assert dsq(c, [       32,            33,            70 ])
    assert dsq(c, [ 31,   32,                           70 ])
    assert dsq(c, [ 31,   32,            33,               ])

    # Выбор + заданные КП
    c           = ['*(31,32,33)', '55', '*(31,32,33)']
    assert  ok(c, [ 31,            55,   33          ])
    assert  ok(c, [ 31, 32,        55,   33          ])
    assert  ok(c, [ 31,            55,   33, 31      ])
    assert  ok(c, [ 71, 31,        55,   33          ])
    
    assert dsq(c, [ 31,            55,   31          ])
    assert dsq(c, [ 71,            55,   33          ])
    assert dsq(c, [ 31,            75,   33          ])
    assert dsq(c, [ 31,            55,   73          ])
    assert dsq(c, [                55,   33          ])
    assert dsq(c, [ 31,                  33          ])
    assert dsq(c, [ 31,            55                ])

    # Выбор + переворот карты + обязательные первый и последний КП на каждом круге
    c           = [31, '*(33,34,35)', '*(33,34,35)', 39, 41, '*(43,44,45)', '*(43,44,45)', 49]
    assert  ok(c, [31,  33,            34,           39, 41,   45,           43,           49])
    assert  ok(c, [31,  33,            34,           39, 71, 41, 45,         43,           49])


def test_non_obvious_behavior():
    '''Неочевидное поведение при проверке дистанции. Не всегда это некорректная работа
    алгоритма, иногда может возникать из-за недочётов при составлении курсов.
    '''    
    
    # Выбор + заданные КП. Первый КП31 и последний КП34 включены в проверку выбора. 
    # Повторная отметка на этих КП может (ошибочно?) дать правильную отметку.
    c           = [31, '*', '*', 34]
    assert  ok(c, [31,  31,  33, 34])
    assert  ok(c, [31,  32,  34, 34])
    c           = [31, '*(31,32,33,34)', '*(31,32,33,34)', 34]
    assert  ok(c, [31,  31,               33,              34])
    assert  ok(c, [31,  32,               34,              34])

    # Классическая бабочка. Можно взять контрольные пункты не в том порядке, но отметка будет ок
    c           = [31, 32, '*(33,35)', '*(34,36)', 32, '*(33,35)', '*(34,36)', 32, 37]
    assert  ok(c, [31, 32,  33,         36,        32,  35,         34,        32, 37])


def test_butterfly_course():
    '''Рассев «бабочка» — спортсмен сначала пробегает одно крыло бабочки, затем другое
    '''    

    # Классическая бабочка — центральный КП32 необходимо взять три раза
    c           = [31, 32, '*(33,35)', '*(34,36)', 32, '*(33,35)', '*(34,36)', 32, 37]
    assert  ok(c, [31, 32,  33,         34,        32,  35,         36,        32, 37])
    assert  ok(c, [31, 32,  35,         36,        32,  33,         34,        32, 37])

    assert  ok(c, [70,31,32,33,         34,        32,  35,         36,        32, 37])
    assert  ok(c, [31, 32,  33, 70,     34,        32,  35,         36,        32, 37])
    assert  ok(c, [31, 32,  33,         34,        32,  35,         36,      32,37,70])

    assert dsq(c, [31, 32,  33,         34,        32,  33,         34,        32, 37])
    assert dsq(c, [31, 33,  32,         34,        32,  35,         36,        32, 37])
    assert dsq(c, [31, 32,  33,         34,        35,  36,         32,        32, 37])
    assert dsq(c, [    32,  33,         34,        32,  35,         36,        32, 37])
    assert dsq(c, [31, 32,  33,         34,        32,  35,         36,        32    ])
    assert dsq(c, [31, 32,              34,        32,  35,         36,        32, 37])
    assert dsq(c, [31, 32,  33,         34,             35,         36,        32, 37])
    assert dsq(c, [70, 32,  33,         34,        32,  35,         36,        32, 37])
    assert dsq(c, [31, 32,  33,         34,        32,  35,         36,        32, 70])
    assert dsq(c, [31, 32,  70,         34,        32,  35,         36,        32, 37])
    assert dsq(c, [31, 32,  33,         34,        70,  35,         36,        32, 37])

    # Модифицированная бабочка — перегон КП32 и КП34 необходимо посетить по два раза
    c           = [31, 32, '*(33,35)', 34, 32, '*(33,35)', 34, 36]
    assert  ok(c, [31, 32,  33,        34, 32,  35,        34, 36])
    assert  ok(c, [31, 32,  35,        34, 32,  33,        34, 36])

    assert  ok(c, [70,31,32,35,        34, 32,  33,        34, 36])
    assert  ok(c, [31, 32,  35, 70,    34, 32,  33,        34, 36])
    assert  ok(c, [31, 32,  35,        34, 32,  33,      34,36,70])

    assert dsq(c, [31, 32,  33,        34, 32,  33,        34, 36])
    assert dsq(c, [31, 33,  32,        34, 32,  35,        34, 36])
    assert dsq(c, [31, 32,  33, 35,    34, 32,             34, 36])
    assert dsq(c, [    32,  33,        34, 32,  35,        34, 36])
    assert dsq(c, [31, 32,             34, 32,  35,        34, 36])
    assert dsq(c, [31, 32,  33,        34, 32,  35,        34    ])
    assert dsq(c, [70, 32,  33,        34, 32,  35,        34, 36])
    assert dsq(c, [31, 32,  70,        34, 32,  35,        34, 36])
    assert dsq(c, [31, 32,  33,        34, 32,  35,        34, 70])

    # TODO: Классическая бабочка с неравными крыльями
    # TODO: Модифицированная бабочка с неравными крыльями

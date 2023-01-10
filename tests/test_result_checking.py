from typing import List, Union

from sportorg.models.memory import (
    Course,
    CourseControl,
    Person,
    ResultSportident,
    Split,
)


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


def test_controls_as_int():
    # Номера КП заданы числом
    assert ok(course=[31, 32, 33],
              splits=[31, 32, 33])

    assert dsq(course=[31, 32, 33],
              splits=[])


def test_controls_as_str():
    # Номера КП заданы строкой
    assert ok(course=['31', '32', '33'],
              splits=[ 31,   32,   33 ])

    assert dsq(course=['31', '32', '33'],
              splits=[])


def test_controls_with_optional_codes():
    # Возможность задать номера контрольных пунктов,
    # которые будут приняты как правильные
    assert  ok(course=['31(31,32,33)'],
               splits=[31])
    assert  ok(course=['31(31,32,33)'],
               splits=[32])
    assert dsq(course=['31(31,32,33)'],
               splits=[70])

    # Правильными считаются только КП, указанные в скобках
    assert dsq(course=['31(41,42,43)'],
               splits=[31])
    assert ok(course=['31(41,42,43)'],
              splits=[41])

    # КП31 — отметка ок, штрафа нет
    course_object = make_course(['31(31,32,33)'])
    result = make_result([31])
    assert result.check(course_object) == True
    assert result.splits[0].code == '31'
    assert result.splits[0].is_correct == True
    assert result.splits[0].has_penalty == False

    # КП32 — отметка ок, штраф есть
    course_object = make_course(['31(31,32,33)'])
    result = make_result([32])
    assert result.check(course_object) == True
    assert result.splits[0].code == '32'
    assert result.splits[0].is_correct == True
    assert result.splits[0].has_penalty == True

    # Другой КП — плохая отметка, штраф есть
    course_object = make_course(['31(31,32,33)'])
    result = make_result([70])
    assert result.check(course_object) == False
    assert result.splits[0].code == '70'
    assert result.splits[0].is_correct == False
    assert result.splits[0].has_penalty == True


def test_controls_with_optional_code_ranges():
    # Возможность задать номера контрольных пунктов, используя диапазон
    course = ['31(31-33)']
    assert  ok(course, splits=[31])
    assert  ok(course, splits=[32])
    assert  ok(course, splits=[33])
    assert dsq(course, splits=[34])

    # Возможность комбинировать отдельные КП и диапазоны
    course = ['31(31,41-43,51,61-64)']
    assert  ok(course, splits=[31])
    assert  ok(course, splits=[41])
    assert  ok(course, splits=[42])
    assert  ok(course, splits=[43])
    assert  ok(course, splits=[51])
    assert  ok(course, splits=[61])
    assert  ok(course, splits=[62])
    assert  ok(course, splits=[63])
    assert dsq(course, splits=[32])
    assert dsq(course, splits=[44])
    assert dsq(course, splits=[60])
    assert dsq(course, splits=[65])


def test_free_course_order_unique_controls():
    '''Возможность задать «любой контрольный пункт» ['*'] или
    «любой контрольный пункт из списка» ['*(31,32,33)'].
    Такие контрольные пункты будут приняты как правильные.
    Осуществляется проверка на уникальность.
    '''
    assert  ok(course=['*'], splits=[31])
    assert  ok(course=['*'], splits=[71])

    assert  ok(course=['*(31,32,33)'], splits=[31])
    assert  ok(course=['*(31,32,33)'], splits=[32])
    assert dsq(course=['*(31,32,33)'], splits=[34])

    course =                  ['*', '*', '*']
    assert  ok(course, splits=[ 31,  32,  33])
    assert  ok(course, splits=[ 31,  32,  33,  34])
    assert  ok(course, splits=[ 31,  32,  31,  33])
    assert dsq(course, splits=[ 31,  32,  31])
    assert dsq(course, splits=[ 31,  32     ])

    # Возможно комбинировать способы задания «любых» контрольных пунктов
    course =                  ['*(31-33)', '*(41-43)', '*(51-53)', '*']
    assert  ok(course, splits=[ 31,         41,         51,         32])
    assert  ok(course, splits=[ 31,         42,         53,         32])
    assert dsq(course, splits=[ 31,         42,         53,         31])

    course =                  [31, '*', '*(31-33)']
    # Возможно комбинировать заданные контрольные пункты и «любые»
    assert  ok(course, splits=[31,  32,  33])
    # Проверка уникальности производится только среди «любых»
    assert  ok(course, splits=[31,  31,  33])
    assert dsq(course, splits=[31,  33,  33])


def test_free_course_order_any_controls():
    # Возможность задать «любой контрольный пункт» ['%'] или
    # «любой контрольный пункт из списка» ['%(31,32,33)'].
    # Такие контрольные пункты будут приняты как правильные.
    # Проверка на уникальность не осуществляется.
    assert  ok(course=['%'], splits=[31])
    assert  ok(course=['%'], splits=[71])

    assert  ok(course=['%(31,32,33)'], splits=[31])
    assert  ok(course=['%(31,32,33)'], splits=[32])
    assert dsq(course=['%(31,32,33)'], splits=[34])

    course =                  ['%', '%', '%']
    assert  ok(course, splits=[ 31,  32,  33])
    assert  ok(course, splits=[ 31,  32,  33,  34])
    assert  ok(course, splits=[ 31,  32,  31,  33])
    assert  ok(course, splits=[ 31,  32,  31])
    assert  ok(course, splits=[ 31,  31,  31])
    assert dsq(course, splits=[ 31,  32])

    # Возможно комбинировать способы задания «любых» контрольных пунктов
    course =                  ['%(31-33)', '%(41-43)', '%(51-53)', '%'],
    assert  ok(course, splits=[ 31,         41,         51,         32])
    assert  ok(course, splits=[ 31,         42,         53,         32])
    assert  ok(course, splits=[ 31,         42,         53,         31])

    # Возможно комбинировать заданные контрольные пункты и «любые»
    course =                  [31, '%', '%(31-33)']
    assert  ok(course, splits=[31,  32,  33])
    assert  ok(course, splits=[31,  31,  31])

    # Возможно комбинировать «любые уникальные» и «любые не уникальные»
    course =                  [31, '*', '*', '%', '%']
    assert  ok(course, splits=[31,  32,  33,  34,  35])
    assert  ok(course, splits=[31,  31,  32,  31,  31])
    assert dsq(course, splits=[31,  32,  32,  34,  35])
    course =                  [31, '%', '%', '*', '*']
    assert  ok(course, splits=[31,  31,  31,  31,  32])


def test_course_pre_ordered():
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


def test_course_free_order():
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


def test_course_butterfly():
    '''Рассев «бабочка» — спортсмен сначала пробегает одно крыло бабочки, затем другое
    '''
    # Классическая бабочка — центральный КП32 необходимо взять три раза
    c           = [31, 32, '*(41,51)', '*(42,52)', 32, '*(51,41)', '*(52,42)', 32, 39]
    assert  ok(c, [31, 32,  41,         42,        32,  51,         52,        32, 39])
    assert  ok(c, [31, 32,  51,         52,        32,  41,         42,        32, 39])

    assert  ok(c, [70,31,32,41,         42,        32,  51,         52,        32, 39])
    assert  ok(c, [31, 32,  41, 70,     42,        32,  51,         52,        32, 39])
    assert  ok(c, [31, 32,  41,         42,        32,  51,         52,      32,39,70])

    assert dsq(c, [31, 32,  41,         42,        32,  41,         42,        32, 39])
    assert dsq(c, [31, 32,  51,         52,        35,  51,         52,        32, 39])
    assert dsq(c, [    32,  41,         42,        32,  51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,        32,  51,         52,        32    ])
    assert dsq(c, [31, 32,              42,        32,  51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,             51,         52,        32, 39])
    assert dsq(c, [70, 32,  41,         42,        32,  51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,        32,  51,         52,        32, 70])
    assert dsq(c, [31, 32,  70,         42,        32,  51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,        70,  51,         52,        32, 39])

    # Модифицированная бабочка — есть возвратный перегон; КП32 и КП33 надо взять по два раза
    c           = [31, 32, '*(41,51)', 33, 32, '*(51,41)', 33, 39]
    assert  ok(c, [31, 32,  41,        33, 32,  51,        33, 39])
    assert  ok(c, [31, 32,  51,        33, 32,  41,        33, 39])

    assert  ok(c, [70,31,32,41,        33, 32,  51,        33, 39])
    assert  ok(c, [31, 32,  41, 70,    33, 32,  51,        33, 39])
    assert  ok(c, [31, 32,  41,        33, 32,  51,      33,39,70])

    assert dsq(c, [31, 32,  41,        33, 32,  41,        33, 39])
    assert dsq(c, [31, 41,  32,        33, 32,  51,        33, 39])
    assert dsq(c, [31, 32,  41, 51,    33, 32,             33, 39])
    assert dsq(c, [    32,  41,        33, 32,  51,        33, 39])
    assert dsq(c, [31, 32,             33, 32,  51,        33, 39])
    assert dsq(c, [31, 32,  41,        33, 32,  51,        33    ])
    assert dsq(c, [70, 32,  41,        33, 32,  51,        33, 39])
    assert dsq(c, [31, 32,  70,        33, 32,  51,        33, 39])
    assert dsq(c, [31, 32,  41,        33, 32,  51,        33, 70])

    # Бабочка с неравными крыльями. КП32 включён в вариативную часть.
    c           = [31, 32, '*(41,51)', '*(42,52)', '*(43,32)', '*(32,41)', '*(51,42)', '*(52,43)', 32, 39]
    assert  ok(c, [31, 32,  41,         42,         43,         32,         51,         52,        32, 39])
    assert  ok(c, [31, 32,  51,         52,         32,         41,         42,         43,        32, 39])

    assert  ok(c, [70,31,32,41,         42,         43,         32,         51,         52,        32, 39])
    assert  ok(c, [31, 32,  41,         42, 70,     43,         32,         51,         52,        32, 39])
    assert  ok(c, [31, 32,  41,         42,         43,         32,         51,         52,      32,39,70])

    assert dsq(c, [31, 32,  41,         42,         43,         32,         41, 42,     43,        32, 39])
    assert dsq(c, [31, 32,  51,         52,         32,         51,         52,                    32, 39])
    assert dsq(c, [    32,  41,         42,         43,         32,         51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,                     43,         32,         51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,         43,                     51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,         43,         32,         51,         52,        32    ])
    assert dsq(c, [70, 32,  41,         42,         43,         32,         51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         70,         43,         32,         51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,         43,         70,         51,         52,        32, 39])
    assert dsq(c, [31, 32,  41,         42,         43,         32,         51,         52,        32, 70])

    # Модифицированная бабочка с неравными крыльями
    c           = [31, 32, '*(41,51)', '*(42,33)', '*(33,32)', '*(32,41)', '*(51,42)', 33, 39]
    assert  ok(c, [31, 32,  41,         42,         33,         32,         51,        33, 39])
    assert  ok(c, [31, 32,  51,         33,         32,         41,         42,        33, 39])

    assert  ok(c, [70,31,32,41,         42,         33,         32,         51,        33, 39])
    assert  ok(c, [31, 32,  41,         42, 70,     33,         32,         51,        33, 39])
    assert  ok(c, [31, 32,  41,         42,         33,         32,         51,      33,39,70])

    assert dsq(c, [31, 32,  41,         42,         33,         32,         41, 42,    33, 39])
    assert dsq(c, [31, 32,  51,         33,         32,         51,                    33, 39])
    assert dsq(c, [    32,  41,         42,         33,         32,         51,        33, 39])
    assert dsq(c, [31, 32,  41,         42,                     32,         51,        33, 39])
    assert dsq(c, [31, 32,  41,         42,         33,         32,         51,        33    ])
    assert dsq(c, [70, 32,  41,         42,         33,         32,         51,        33, 39])
    assert dsq(c, [31, 32,  41,         42,         70,         32,         51,        33, 39])
    assert dsq(c, [31, 32,  41,         42,         33,         32,         51,        33, 70])


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

    # Выбор со сменой карты, КП50 нарисован на обоих сторонах карты как доступный для выбора.
    # У спортсмена должна быть правильная отметка: на каждом круге решает задачу: взять 2 из 3 КП.
    c           = ['*(31,32,50)', '*(31,32,50)', 90, '*(50,71,72)', '*(50,71,72)']
    assert dsq(c, [ 31,            50,           90,  71,            50          ])

    # Классическая бабочка. Можно взять контрольные пункты не в том порядке, но отметка будет ок.
    # Должен быть дисквалифицирован: нарушение порядка прохождения дистанции.
    c           = [31, 32, '*(33,35)', '*(34,36)', 32, '*(33,35)', '*(34,36)', 32, 37]
    assert  ok(c, [31, 32,  33,         36,        32,  35,         34,        32, 37])

    # Бабочка с неравными крыльями. Нарисованные в картах варианты прохождения: 
    # 1) 31 -32- -41-42-43- -32- -51-52-    -32- 39
    # 2) 31 -32- -51-52-    -32- -41-42-43- -32- 39
    # Если КП32 взять не в том порядке, вернуться на КП41, а затем 
    # правильно взять КП32 — спортсмен будет дисквалифицирован.
    # У спортсмена должна быть правильная отметка: взятие лишнего КП допустимо.
    c           = [31, 32, '*(41,51)', '*(42,52)', '*(43,32)', '*(32,41)', '*(51,42)', '*(52,43)', 32, 39]
    assert dsq(c, [31, 32,  41,         42, 32,     43,         32,         51,         52,        32, 39])

    # При создании дистанции можно указывать КП не из списка.
    # При этом проверка осуществляется только по КП из списка.
    course = ['31(41,42,43)']
    assert dsq(course, splits=[31])
    assert ok(course, splits=[41])

    result = make_result([31])
    assert result.check(make_course(course)) == False
    assert result.splits[0].is_correct == False
    assert result.splits[0].has_penalty == True # Должно быть False так как 31 «правильный» КП

    result = make_result([41])
    assert result.check(make_course(course)) == True
    assert result.splits[0].is_correct == True
    assert result.splits[0].has_penalty == True

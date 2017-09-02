from . import memory


def find_person_by_result(system_id, result):
    assert result, memory.Result
    number = str(result.card_number)
    for person in memory.race().persons:
        if person.card_number == number:
            result.person = person

            return True

    return False


def add_result(system_id, result):
    """

    :type system_id: str
    :type result: memory.Result
    """
    assert result, memory.Result
    if isinstance(result.person, memory.Person):
        result.person.result = result
        memory.race().results.append(result)
    else:
        res = find_person_by_result(system_id, result)
        if res:
            add_result(system_id, result)

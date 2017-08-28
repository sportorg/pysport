from . import memory


def find_person_by_result(system_id, result):
    assert result, memory.Result
    # find

    return False


def add_result(system_id, result):
    """

    :type system_id: str
    :type result: memory.Result
    """
    assert result, memory.Result
    if isinstance(result.person, memory.Person):
        result.person.result = result
    else:
        res = find_person_by_result(system_id, result)

        if isinstance(res, memory.Result):
            add_result(system_id, res)

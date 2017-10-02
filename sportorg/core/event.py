_events = {}


def add_event(event_name, call):
    global _events

    if event_name not in _events:
        _events[event_name] = []

    _events[event_name].append(call)


def remove_event(event_name, call):
    pass


def event(event_name, *args, **kwargs):
    global _events

    if event_name not in _events:
        return None

    if not isinstance(_events[event_name], list):
        return None

    result = []
    for _event in _events[event_name]:
        if not isinstance(_event, tuple):
            r = _event(*args, **kwargs)
        else:
            cls = _event[0]
            method_name = _event[1]
            try:
                method = getattr(cls, method_name)
                r = method(*args, **kwargs)
            except AttributeError:
                print("Class `{}` does not implement `{}`".format(cls.__class__.__name__, method_name))
                r = None

        if r is not None:
            result.append(r)

    return result if len(result) else None


def event_list():
    return list(_events.keys())

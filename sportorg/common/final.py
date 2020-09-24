from abc import ABCMeta


def finalmethod(funcobj):
    funcobj.__isfinalmethod__ = True
    return funcobj


class Override(ABCMeta):
    def __init__(cls, name, bases, namespace):
        super(Override, cls).__init__(name, bases, namespace)
        finals = {
            name
            for name, value in list(namespace.items())
            if getattr(value, '__isfinalmethod__', False)
        }

        for base in bases:
            for name in getattr(base, '__finalmethods__', set()):
                value = getattr(cls, name, None)
                if getattr(value, '__isfinalmethod__', False):
                    finals.add(name)
                else:
                    raise TypeError(
                        "function '"
                        + str(value.__name__)
                        + "' in class '"
                        + str(cls.__name__)
                        + "' is final"
                    )
        cls.__finalmethods__ = frozenset(finals)


class _BaseABC(metaclass=ABCMeta):
    pass


# For finalmethod
class Base(_BaseABC, metaclass=Override):
    pass

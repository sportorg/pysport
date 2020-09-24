class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.

    >>>class SomeClass(metaclass=Singleton):
    >>>    pass
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


def singleton(cls, *args, **kw):
    """
    Decorator

    >>>@singleton
    >>>class SomeClass(object):
    >>>    pass
    """
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton

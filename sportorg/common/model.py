class Model(object):
    def __init__(self):
        self.cached_values = []

    def generate_cache(self):
        self.cached_values = []

    @classmethod
    def create(cls, **kwargs):
        o = cls()
        for key, value in kwargs.items():
            if hasattr(o, key):
                setattr(o, key, value)

        return o

    @classmethod
    def update(cls, **kwargs):
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        if hasattr(self, key):
            setattr(self, key, val)

class Version:
    def __init__(self, major=0, minor=0, patch=0, build=0, prefix='', suffix=''):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._build = build
        self._prefix = prefix
        self._suffix = suffix

    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def patch(self):
        return self._patch

    @property
    def build(self):
        return self._build

    @property
    def prefix(self):
        return self._prefix

    @property
    def suffix(self):
        return self._suffix

    @property
    def file(self):
        return '{major}.{minor}.{patch}.{build}'.format(
            major=self._major, minor=self._minor, patch=self._patch, build=self._build
        )

    def __str__(self):
        pattern = '{prefix}{major}.{minor}.{patch}'
        if self.build and self.suffix:
            pattern = '{prefix}{major}.{minor}.{patch}-{suffix}.{build}'
        elif self.build:
            pattern = '{prefix}{major}.{minor}.{patch}.{build}'
        elif self.suffix:
            pattern = '{prefix}{major}.{minor}.{patch}-{suffix}'

        return pattern.format(
            major=self._major,
            minor=self._minor,
            patch=self._patch,
            build=self._build,
            prefix=self._prefix,
            suffix=self._suffix,
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, o):
        return str(self) == str(o)

    def __gt__(self, o):
        return self.major > o.major

    def __ge__(self, o):
        return self.major >= o.major

    def is_compatible(self, o):
        return self.major == o.major

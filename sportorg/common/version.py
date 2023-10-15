from typing import Any


class Version:
    def __init__(
        self,
        major: int = 0,
        minor: int = 0,
        patch: int = 0,
        build: int = 0,
        prefix: str = '',
        suffix: str = '',
    ):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._build = build
        self._prefix = prefix
        self._suffix = suffix

    @property
    def major(self) -> int:
        return self._major

    @property
    def minor(self) -> int:
        return self._minor

    @property
    def patch(self) -> int:
        return self._patch

    @property
    def build(self) -> int:
        return self._build

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def suffix(self) -> str:
        return self._suffix

    @property
    def file(self) -> str:
        return '{major}.{minor}.{patch}.{build}'.format(
            major=self._major, minor=self._minor, patch=self._patch, build=self._build
        )

    def __str__(self) -> str:
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

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, o: Any) -> bool:
        if not isinstance(o, Version):
            return NotImplemented
        return str(self) == str(o)

    def __gt__(self, o: 'Version') -> bool:
        return self.major > o.major

    def __ge__(self, o: 'Version') -> bool:
        return self.major >= o.major

    def is_compatible(self, o) -> bool:
        return self.major == o.major

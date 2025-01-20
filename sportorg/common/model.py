from typing import Any, Dict


class Model:
    @classmethod
    def create(cls, **kwargs: Dict[str, Any]) -> Any:
        o = cls()
        for key, value in kwargs.items():
            if hasattr(o, key):
                setattr(o, key, value)

        return o

    @classmethod
    def update(cls, **kwargs: Dict[str, Any]) -> None:
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

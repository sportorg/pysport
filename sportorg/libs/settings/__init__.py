import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Type


def save_settings(settings: Any, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=4)


def load_settings(path: Path, cls: Type[Any]) -> Any:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Remove any keys from data that are not fields in the dataclass
    field_names = {f.name for f in cls.__dataclass_fields__.values()}
    data = {k: v for k, v in data.items() if k in field_names}

    return cls(**data)

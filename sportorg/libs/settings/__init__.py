import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Type


def save_settings(settings: Any, path: Path) -> None:
    old_data = _load_settings(path)
    data = asdict(settings)

    # Merge old data with new settings, preserving any existing keys
    if old_data:
        old_data.update(data)
        data = old_data

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_settings(path: Path, cls: Type[Any]) -> Optional[Any]:
    data = _load_settings(path)
    if not data:
        return None

    # Remove any keys from data that are not fields in the dataclass
    field_names = {f.name for f in cls.__dataclass_fields__.values()}
    data = {k: v for k, v in data.items() if k in field_names}

    try:
        return cls(**data)
    except Exception:
        return None


def _load_settings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

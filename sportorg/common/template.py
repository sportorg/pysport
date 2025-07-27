import os
from typing import Any, List

from sportorg import config, settings
from sportorg.libs.template import template


def get_templates(path: str = "", exclude_path: str = "") -> List[str]:
    if not path:
        path = settings.template_dir()
    if not exclude_path:
        exclude_path = settings.template_dir()
    files = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_templates(full_path)
            for f in fs:
                f = f.replace(exclude_path, "")
                f = f.replace("\\", "/")
                files.append(f)
        else:
            full_path = full_path.replace(exclude_path, "")
            full_path = full_path.replace("\\", "/")
            files.append(full_path)

    return files


def get_text_from_file(path: str, **kwargs: Any) -> str:
    kwargs["name"] = config.NAME
    kwargs["version"] = str(config.VERSION)
    if os.path.isfile(path):
        return template.get_text_from_path(path, **kwargs)

    return template.get_text_from_template(settings.template_dir(), path, **kwargs)

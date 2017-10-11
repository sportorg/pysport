import os

from sportorg.lib.template import template
from sportorg import config


def get_templates(path=None):
    if path is None:
        path = config.template_dir()
    files = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_templates(full_path)
            for f in fs:
                files.append(f)
        else:
            files.append(full_path)

    return files


def get_text_from_file(path, **kwargs):
    return template.get_text_from_file(path, **kwargs)

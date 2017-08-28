import os

from sportorg.lib.template import template
from sportorg import config


def get_templates(path=None):
    if path is None:
        path = config.TEMPLATE_DIR
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


def get_text(**kwargs):
    return get_text_from_file(config.template_dir('main.html'), **kwargs)


def get_text_from_file(path, **kwargs):
    return template.get_text_from_file(path, **kwargs)

import os

from sportorg import config
from sportorg.libs.template import template


def get_templates(path='', exclude_path=''):
    if not path:
        path = config.template_dir()
    if not exclude_path:
        exclude_path = config.template_dir()
    files = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_templates(full_path)
            for f in fs:
                f = f.replace(exclude_path, '')
                f = f.replace('\\', '/')
                files.append(f)
        else:
            full_path = full_path.replace(exclude_path, '')
            full_path = full_path.replace('\\', '/')
            files.append(full_path)

    return files


def get_text_from_file(path, **kwargs):
    kwargs['name'] = config.NAME
    kwargs['version'] = str(config.VERSION)
    if os.path.isfile(path):
        return template.get_text_from_path(path, **kwargs)
    else:
        return template.get_text_from_template(config.template_dir(), path, **kwargs)

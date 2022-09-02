import datetime
import locale

import dateutil.parser
from jinja2 import Environment, FileSystemLoader, Template


def to_hhmmss(value, fmt=None):
    """value = 1/1000 s"""
    if value is None:
        return ''
    if not fmt:
        fmt = '%H:%M:%S'
    dt = datetime.datetime(
        2000,
        1,
        1,
        value // 3600000 % 24,
        (value % 3600000) // 60000,
        (value % 60000) // 1000,
        (value % 1000) * 10,
    )
    return dt.strftime(fmt)


def date(value, fmt=None):
    if not value:
        return ''
    if not fmt:
        fmt = '%d.%m.%Y'
    return dateutil.parser.parse(value).strftime(fmt)


def finalize(thing):
    return thing if thing else ''


def get_text_from_path(path, **kwargs):
    custom_encoding = locale.getdefaultlocale()[1]
    # custom_encoding = 'cp1251'
    with open(path, errors='ignore') as f:
        html = f.read().encode(custom_encoding, 'ignore').decode(errors='ignore')

    template = Template(html, finalize=finalize)
    return template.render(**kwargs)


def get_text_from_template(searchpath, path, **kwargs):
    env = Environment(loader=FileSystemLoader(searchpath), finalize=finalize)
    env.filters['tohhmmss'] = to_hhmmss
    env.filters['date'] = date
    env.policies['json.dumps_kwargs']['ensure_ascii'] = False
    template = env.get_template(path)

    return template.render(**kwargs)

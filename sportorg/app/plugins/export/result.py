import config
from sportorg.lib.jinja2 import template


def get_text(**kwargs):
    return template.get_text_from_file(config.base_dir('templates', 'main.html'), **kwargs)

import locale

from jinja2 import Template


def get_text_from_file(path, **kwargs):
    custom_encoding = locale.getdefaultlocale()[1]
    # custom_encoding = 'cp1251'
    html = open(path).read().encode(custom_encoding, 'ignore').decode()

    template = Template(html)
    return template.render(**kwargs)

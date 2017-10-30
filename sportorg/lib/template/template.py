import locale

from jinja2 import Template


def get_text_from_file(path, **kwargs):
    custom_encoding = locale.getdefaultlocale()[1]
    # custom_encoding = 'cp1251'
    with open(path) as f:
        html = f.read().encode(custom_encoding, 'ignore').decode(errors='ignore')

    template = Template(html)
    return template.render(**kwargs)

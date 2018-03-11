import locale

from jinja2 import Template, Environment, FileSystemLoader


def finalize(thing):
    return thing if thing is not None else ''


def get_text_from_path(path, **kwargs):
    custom_encoding = locale.getdefaultlocale()[1]
    # custom_encoding = 'cp1251'
    with open(path, errors='ignore') as f:
        html = f.read().encode(custom_encoding, 'ignore').decode(errors='ignore')

    template = Template(html, finalize=finalize)
    return template.render(**kwargs)


def get_text_from_template(searchpath, path, **kwargs):
    env = Environment(
        loader=FileSystemLoader(searchpath),
        finalize=finalize
    )
    template = env.get_template(path)

    return template.render(**kwargs)

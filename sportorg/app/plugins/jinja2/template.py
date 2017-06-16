from jinja2 import Template


def get_text_from_file(path, **kwargs):
    html = open(path).read()
    template = Template(html)
    return template.render(**kwargs)

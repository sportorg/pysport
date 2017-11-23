from sportorg.app.models.memory import race
from sportorg.app.models.result.split_calculation import GroupSplits
from sportorg.app.modules.printing.printing import print_html
from sportorg.config import template_dir
from sportorg.lib.template.template import get_text_from_file


class NoResultToPrintException(Exception):
    pass


def split_printout(result):
    person = result.person

    if not person or not person.group:
        raise NoResultToPrintException('No results to print')

    template_path = template_dir('split_printout.html')
    spl = GroupSplits(person.group)
    template = get_text_from_file(template_path, **spl.get_json(person))

    obj = race()
    print_html(obj.get_setting('split_printer'), template)

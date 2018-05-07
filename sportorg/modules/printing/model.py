from sportorg.core.template import get_text_from_file
from sportorg.models.memory import race, Organization

from sportorg.modules.printing.printing import print_html
from sportorg.config import template_dir
from sportorg.models.result.split_calculation import GroupSplits


class NoResultToPrintException(Exception):
    pass


class NoPrinterSelectedException(Exception):
    pass


def split_printout(result):
    person = result.person

    if not person or not person.group:
        raise NoResultToPrintException('No results to print')

    obj = race()
    course = obj.find_course(person)

    if person.group and course:
        printer = obj.get_setting('split_printer')
        template_path = obj.get_setting('split_template', template_dir('split', 'split_printout.html'))

        organization = person.organization
        if not organization:
            organization = Organization()

        s = GroupSplits(obj, person.group).generate()
        template = get_text_from_file(
            template_path,
            race=obj.to_dict(),
            person=person.to_dict(),
            result=result.to_dict(),
            group=person.group.to_dict(),
            course=course.to_dict(),
            organization=organization.to_dict(),
            items=s.to_dict()
        )
        if not printer:
            raise NoPrinterSelectedException('No printer selected')
        print_html(
            printer,
            template,
            obj.get_setting('print_margin_left', 5.0),
            obj.get_setting('print_margin_top', 5.0),
            obj.get_setting('print_margin_right', 5.0),
            obj.get_setting('print_margin_bottom', 5.0),
        )

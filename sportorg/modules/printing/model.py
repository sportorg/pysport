import platform
from typing import List

from sportorg import settings
from sportorg.common.template import get_text_from_file
from sportorg.language import translate
from sportorg.models.memory import Course, Group, Organization, Result, race
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.printing.printing import print_html
from sportorg.modules.printing.printout_split import SportorgPrinter


class NoResultToPrintException(Exception):
    pass


class NoPrinterSelectedException(Exception):
    pass


def split_printout(results: List[Result]):
    obj = race()

    printer = settings.SETTINGS.printer_split
    if not printer:
        raise NoPrinterSelectedException("No printer selected")

    margins = {
        "left": obj.get_setting("print_margin_left", 5.0),
        "top": obj.get_setting("print_margin_top", 5.0),
        "right": obj.get_setting("print_margin_right", 5.0),
        "bottom": obj.get_setting("print_margin_bottom", 5.0),
    }
    template_path = obj.get_setting(
        "split_template", settings.template_dir("split", "1_split_printout.html")
    )

    # don't process results in one group several times while bulk printing, track processed groups
    processed_groups = set()

    isDirectMode = False
    if not str(template_path).endswith(".html") and platform.system() == "Windows":
        # Internal split printout, pure python. Works faster, than jinja2 template + pdf
        isDirectMode = True

        size = 60  # base scale factor is 60, used win32con.MM_TWIPS MapMode (unit = 1/20 of dot, 72dpi)

        array = str(template_path).split(translate("scale") + "=")
        if len(array) > 1:
            scale = array[1]
            if scale.isdecimal():
                size = int(scale) * size // 100

        pr = SportorgPrinter(
            printer,
            size,
            int(obj.get_setting("print_margin_left", 5.0)),
            int(obj.get_setting("print_margin_top", 5.0)),
        )

    for result in results:
        person = result.person

        if not person:
            continue

        group = person.group or Group()
        course = obj.find_course(result) or Course()
        organization = person.organization or Organization()

        if group not in processed_groups:
            group_splits = GroupSplits(obj, group).generate(True)
            processed_groups.add(group)

        result.check_who_can_win()

        if isDirectMode:
            pr.print_split(result)
        else:
            template = get_text_from_file(
                template_path,
                race=obj.to_dict(),
                person=person.to_dict(),
                result=result.to_dict(),
                group=group.to_dict(),
                course=course.to_dict(),
                organization=organization.to_dict(),
                items=group_splits.to_dict(),
            )
            print_html(printer, template, **margins)

    if isDirectMode:
        pr.end_doc()


def split_printout_close():
    print_html("NO_PRINTER", "CLOSE_SPLIT_PRN")

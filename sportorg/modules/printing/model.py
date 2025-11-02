import platform

from sportorg import settings
from sportorg.common.template import get_text_from_file
from sportorg.language import translate
from sportorg.models.memory import Organization, race
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.printing.printing import print_html
from sportorg.modules.printing.printout_split import SportorgPrinter


class NoResultToPrintException(Exception):
    pass


class NoPrinterSelectedException(Exception):
    pass


def split_printout(results):
    isDirectMode = False

    printer = settings.SETTINGS.printer_split
    obj = race()
    template_path = obj.get_setting(
        "split_template", settings.template_dir("split", "1_split_printout.html")
    )

    # don't process results in one group several times while bulk printing, track processed groups
    processed_groups = []

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

        course = obj.find_course(result)

        if person.group and course:
            if person.group not in processed_groups:
                s = GroupSplits(obj, person.group).generate(True)
                processed_groups.append(person.group)

            result.check_who_can_win()

            if isDirectMode:
                pr.print_split(result)

            else:
                organization = person.organization
                if not organization:
                    organization = Organization()

                template = get_text_from_file(
                    template_path,
                    race=obj.to_dict(),
                    person=person.to_dict(),
                    result=result.to_dict(),
                    group=person.group.to_dict(),
                    course=course.to_dict(),
                    organization=organization.to_dict(),
                    items=s.to_dict(),
                )
                if not printer:
                    raise NoPrinterSelectedException("No printer selected")
                print_html(
                    printer,
                    template,
                    obj.get_setting("print_margin_left", 5.0),
                    obj.get_setting("print_margin_top", 5.0),
                    obj.get_setting("print_margin_right", 5.0),
                    obj.get_setting("print_margin_bottom", 5.0),
                )
        else:
            # no group or course - just print all splits
            pr.print_split(result)

    if isDirectMode:
        pr.end_doc()


def split_printout_close():
    print_html("NO_PRINTER", "CLOSE_SPLIT_PRN")

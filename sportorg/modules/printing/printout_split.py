import platform

from sportorg.language import translate
from sportorg.models.memory import ResultStatus, race
from sportorg.models.result.result_calculation import ResultCalculation

if platform.system() == 'Windows':  # current realisation works on Windows only
    import win32con
    import win32print
    import win32ui


class SportorgPrinter(object):
    def __init__(self, printer_name, scale_factor=60, x_offset=5, y_offset=5):

        if not printer_name:
            printer_name = win32print.GetDefaultPrinter()

        self.dc = win32ui.CreateDC()
        self.dc.CreatePrinterDC(printer_name)
        self.dc.SetMapMode(
            win32con.MM_TWIPS
        )  # 1440 units per inch, 1/20 of dot with 72dpi
        self.y_offset = y_offset

        self.start_page()

        self.scale_factor = scale_factor
        self.x = x_offset * self.scale_factor
        self.y = -1 * y_offset * self.scale_factor

    def start_page(self):
        self.dc.StartDoc(translate('SportOrg printing'))
        self.dc.StartPage()

    def end_page(self):
        self.dc.EndPage()
        self.y = self.y_offset * self.scale_factor

    def end_doc(self):
        self.dc.EndDoc()

    def move_cursor(self, offset):
        self.y -= int(self.scale_factor * offset)

    def print_line(self, text, font_name, font_size, font_weight=400):
        font = win32ui.CreateFont(
            {
                'name': font_name,
                'height': int(self.scale_factor * font_size),
                'weight': font_weight,
            }
        )
        self.dc.SelectObject(font)
        self.dc.TextOut(self.x, self.y, str(text))
        self.move_cursor(font_size * 1.3)

    def print_split(self, result):
        obj = race()

        person = result.person
        if person is None or result.status in [
            ResultStatus.DID_NOT_START,
            ResultStatus.DID_NOT_FINISH,
        ]:
            return

        group = person.group
        if group is None:
            return

        course = obj.find_course(result)

        is_penalty_used = obj.get_setting('marked_route_mode', 'off') != 'off'
        is_relay = group.is_relay()

        fn = 'Lucida Console'
        fs_main = 3
        fs_large = 4

        # Information about start
        self.print_line(obj.data.title, fn, fs_main)
        self.print_line(
            str(obj.data.start_datetime)[:10] + ', ' + obj.data.location, fn, fs_main
        )

        # Athlete info, bib, card number, start time
        self.print_line(person.full_name, fn, fs_large, 700)
        self.print_line(translate('Group') + ': ' + group.name, fn, fs_main)
        if person.organization:
            self.print_line(
                translate('Team') + ': ' + person.organization.name, fn, fs_main
            )
        self.print_line(
            translate('Bib')
            + ': '
            + str(person.bib)
            + ' ' * 5
            + translate('Card')
            + ': '
            + str(person.card_number),
            fn,
            fs_main,
        )
        self.print_line(
            translate('Start') + ': ' + result.get_start_time().to_str(), fn, fs_main
        )

        # Splits
        for split in result.splits:
            if split.is_correct:
                line = (
                    ('  ' + str(split.course_index + 1))[-3:]
                    + ' '
                    + ('  ' + split.code)[-3:]
                    + ' '
                    + split.relative_time.to_str()[-7:]
                    + ' '
                    + split.leg_time.to_str()[-5:]
                    + ' '
                    + split.speed
                    + ' '
                )

                if not is_relay:
                    line += ('  ' + str(split.leg_place))[-3:]

                # Highlight correct controls of marked route ( '31' and '31(31,32,33)' => + )
                if is_penalty_used:
                    for course_cp in course.controls:
                        if str(course_cp).startswith(split.code):
                            line += ' +'
                            break

                self.print_line(line, fn, fs_main)
            else:
                line = (
                    ' ' * 4
                    + (' ' + split.code)[-3:]
                    + ' '
                    + split.relative_time.to_str()[-7:]
                )
                self.print_line(line, fn, fs_main)

        finish_split = ''
        if len(result.splits) > 0:
            finish_split = (result.get_finish_time() - result.splits[-1].time).to_str()

        # Finish
        self.print_line(
            translate('Finish')
            + ': '
            + result.get_finish_time().to_str()
            + ' ' * 4
            + finish_split,
            fn,
            fs_main,
        )

        # Result
        if is_penalty_used:
            self.print_line(
                translate('Penalty') + ': ' + result.get_penalty_time().to_str(),
                fn,
                fs_main,
            )

        if result.is_status_ok():
            self.print_line(
                translate('Result')
                + ': '
                + result.get_result()
                + ' ' * 4
                + result.speed,
                fn,
                fs_main,
            )
        else:
            self.print_line(
                translate('Result') + ': ' + result.get_result(), fn, fs_main
            )

        if is_relay and person.bib > 1000:
            self.print_line(
                translate('Team result') + ': ' + result.get_result_relay(), fn, fs_main
            )

        # Place
        if result.place > 0:
            place = translate('Place') + ': ' + str(result.place)
            if not is_relay:
                place += (
                    ' '
                    + translate('from')
                    + ' '
                    + str(group.count_finished)
                    + ' ('
                    + translate('total')
                    + ' '
                    + str(group.count_person)
                    + ')'
                )
            self.print_line(place, fn, fs_main)

        # Info about competitors, who can win current person
        if result.is_status_ok() and not is_relay:
            if obj.get_setting('system_start_source', 'protocol') == 'protocol':
                if hasattr(result, 'can_win_count'):
                    if result.can_win_count > 0:
                        self.print_line(
                            translate('Who can win you')
                            + ': '
                            + str(result.can_win_count),
                            fn,
                            fs_main,
                        )
                        self.print_line(
                            translate('Final result will be known')
                            + ': '
                            + result.final_result_time.to_str(),
                            fn,
                            fs_main,
                        )
                    else:
                        self.print_line(translate('Result is final'), fn, fs_main)

        # Punch checking info
        if result.is_status_ok():
            self.print_line(translate('Status: OK'), fn, fs_large, 700)
        else:
            self.print_line(translate('Status: DSQ'), fn, fs_large, 700)
            cp_list = ''
            line_limit = 35
            for cp in course.controls:
                if len(cp_list) > line_limit:
                    self.print_line(cp_list, fn, fs_main)
                    cp_list = ''
                cp_list += cp.code.split('(')[0] + ' '
            self.print_line(cp_list, fn, fs_main)

        # Short result list
        if is_relay:
            pass
        else:
            res = ResultCalculation(obj).get_group_finishes(group)
            self.print_line(translate('Draft results'), fn, fs_main)
            for cur_res in res[:10]:
                self.print_line(
                    ('  ' + str(cur_res.get_place()))[-2:]
                    + ' '
                    + (cur_res.person.full_name + ' ' * 22)[:22]
                    + ' '
                    + cur_res.get_result(),
                    fn,
                    fs_main,
                )

        self.print_line(obj.data.url, fn, fs_main)

        self.end_page()

import win32print
import win32ui
import win32con

from sportorg.models.memory import race, Race, Result, ResultStatus
from sportorg.models.result.result_calculation import ResultCalculation


class SportorgPrinter(object):
    def __init__(self, printer_name=win32print.GetDefaultPrinter(), scale_factor=60, x_offset=5, y_offset=5):
        self.dc = win32ui.CreateDC()
        self.dc.CreatePrinterDC(printer_name)
        self.dc.SetMapMode(win32con.MM_TWIPS)  # 1440 units per inch, 1/20 of dot with 72dpi
        self.y_offset = y_offset

        self.start_page()

        self.scale_factor = scale_factor
        self.x = x_offset * self.scale_factor
        self.y = -1 * y_offset * self.scale_factor

    def start_page(self):
        self.dc.StartDoc("SportOrg printing")
        self.dc.StartPage()

    def end_page(self):
        self.dc.EndPage()
        self.y = self.y_offset * self.scale_factor

    def end_doc(self):
        self.dc.EndDoc()

    def move_cursor(self, offset):
        self.y -= int(self.scale_factor * offset)

    def print_line(self, text, font_name, font_size, font_weight=400):
        font = win32ui.CreateFont({
            "name": font_name,
            "height": int(self.scale_factor * font_size),
            "weight": font_weight,
        })
        self.dc.SelectObject(font)
        self.dc.TextOut(self.x, self.y, str(text))
        self.move_cursor(font_size * 1.3)

    def print_split(self, result):
        assert isinstance(result, Result)
        obj = race()
        assert isinstance(obj, Race)

        person = result.person
        if person is None or result.status in [ResultStatus.DID_NOT_START, ResultStatus.DID_NOT_FINISH]:
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
        self.print_line(str(obj.data.start_datetime)[:10] + ', ' + obj.data.location,  fn, fs_main)

        # Athlete info, bib, card number, start time
        self.print_line(person.full_name,  fn, fs_large, 700)
        self.print_line('Группа' + ': ' + group.name, fn, fs_main)
        if person.organization:
            self.print_line('Команда' + ': ' + person.organization.name,  fn, fs_main)
        self.print_line('Номер' + ': ' + str(person.bib) + ' '*5 + 'ЧИП' + ': ' + str(person.card_number), fn, fs_main)
        self.print_line('Старт' + ': ' + result.get_start_time().to_str(), fn, fs_main)

        # Splits
        for split in result.splits:
            if split.is_correct:
                line = ('  ' + str(split.course_index + 1))[-3:] + ' ' +\
                       ('  ' + split.code)[-3:] + ' ' +\
                       split.relative_time.to_str()[-7:] + ' ' +\
                       split.leg_time.to_str()[-5:] + ' ' +\
                       split.speed + ' '

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
                line = ' '*4 + (' ' + split.code)[-3:] + ' ' + split.relative_time.to_str()[-7:]
                self.print_line(line, fn, fs_main)

        finish_split = ''
        if len(result.splits) > 0:
            finish_split = (result.get_finish_time() - result.splits[-1].time).to_str()

        # Finish
        self.print_line('Финиш' + ': ' + result.get_finish_time().to_str() + ' '*4 + finish_split, fn, fs_main)

        # Result
        if is_penalty_used:
            self.print_line('Штраф' + ': ' + result.get_penalty_time().to_str(), fn, fs_main)

        if result.is_status_ok():
            self.print_line('Результат' + ': ' + result.get_result() + ' '*4 + result.speed, fn, fs_main)
            try:
                self.print_line('Чистый Результат' + ': ' + result.get_result_start_in_comment(), fn, fs_main)
            except:
                pass
        else:
            self.print_line('Результат' + ': ' + result.get_result(), fn, fs_main)

        if is_relay and person.bib > 1000:
            self.print_line('Результат команды' + ': ' + result.get_result_relay(), fn, fs_main)

        # Place
        if result.place > 0:
            place = 'Место' + ': ' + str(result.place)
            if not is_relay:
                place += ' ' + 'из' + ' ' + str(group.count_finished) + \
                         ' (' + 'всего' + ' ' + str(group.count_person) + ')'
            self.print_line(place, fn, fs_main)

        # Info about competitors, who can win current person
        if result.is_status_ok() and not is_relay:
            if hasattr(result, 'can_win_count'):
                if result.can_win_count > 0:
                    self.print_line('Вас могут выиграть' + ': ' + str(result.can_win_count), fn, fs_main)
                    self.print_line('Результат определится в' + ': ' + result.final_result_time.to_str(), fn, fs_main)
                else:
                    self.print_line('Вас уже никто не обгонит!', fn, fs_main)

        # Punch checking info
        if result.is_status_ok():
            self.print_line('ОТМЕТКА - OK', fn, fs_large, 700)
        else:
            self.print_line('ПЛОХАЯ ОТМЕТКА', fn, fs_large, 700)
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
            relay_stub = 1
        else:
            res = ResultCalculation(obj).get_group_finishes(group)
            self.print_line('Предварительные результаты', fn, fs_main)
            for cur_res in res[:10]:
                assert isinstance(cur_res, Result)
                self.print_line(
                    ('  ' + str(cur_res.get_place()))[-2:] + ' ' + (cur_res.person.full_name + ' ' * 22)[:22] +
                    ' ' + cur_res.get_result(), fn, fs_main)

        self.print_line(obj.data.url, fn, fs_main)

        self.end_page()

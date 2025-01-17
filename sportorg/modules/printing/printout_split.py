import platform

from sportorg.language import translate
from sportorg.models.memory import Group, Result, ResultStatus, race
from sportorg.models.result.result_calculation import ResultCalculation

if platform.system() == "Windows":  # current realisation works on Windows only
    import win32con
    import win32print
    import win32ui


class SportorgPrinter:
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
        self.dc.StartDoc(translate("SportOrg printing"))
        self.dc.StartPage()

    def end_page(self):
        self.dc.EndPage()
        self.y = -1 * self.y_offset * self.scale_factor

    def end_doc(self):
        self.dc.EndDoc()
        self.dc.DeleteDC()

    def move_cursor(self, offset):
        self.y -= int(self.scale_factor * offset)

    def print_line(self, text, font_name, font_size, font_weight=400):
        font = win32ui.CreateFont(
            {
                "name": font_name,
                "height": int(self.scale_factor * font_size),
                "weight": font_weight,
            }
        )
        self.dc.SelectObject(font)
        self.dc.TextOut(self.x, self.y, str(text))
        self.move_cursor(font_size * 1.3)

    def print_split(self, result):
        if not (
            race().get_setting("marked_route_if_counting_lap", False)
            and race().get_setting("marked_route_mode", "laps") == "laps"
        ):
            # Normal split printout
            self.print_split_normal(result)
        else:
            # Printing of bib and penalty for Russian marked route with penalty laps
            self.print_penalty_laps(result)

    def print_penalty_laps(self, result: Result) -> None:
        person = result.person
        if person is None:
            return

        for _ in range(20):
            self.print_line(".", "Arial", 1)  # empty vertical space
        self.print_bib_line(result)
        for _ in range(7):
            self.print_line(".", "Arial", 1)  # empty vertical space
        self.print_penalty_line(result)

    def print_bib_line(self, result: Result) -> None:
        text = str(result.person.bib) if result.person else ""

        font_name = "Arial Black"
        font_size = 50
        font_weight = 400

        font = win32ui.CreateFont(
            {
                "name": font_name,
                "height": int(self.scale_factor * font_size),
                "weight": font_weight,
            }
        )
        self.dc.SelectObject(font)
        self.dc.TextOut(self.x, self.y, text)

        self.move_cursor(font_size * 1.3)

    def print_penalty_line(self, result: Result) -> None:
        laps = result.penalty_laps
        if not result.is_status_ok():
            laps = max(
                2, laps
            )  # print at least 2 laps for disqualified (to have possibility get lap time)
        text = str(laps).rjust(2)

        font_name = "Arial Black"
        font_size = 50
        font_weight = 400

        font = win32ui.CreateFont(
            {
                "name": font_name,
                "height": int(self.scale_factor * font_size),
                "weight": font_weight,
            }
        )
        self.dc.SelectObject(font)
        self.dc.TextOut(self.x, self.y, str(text))

        dx1, dy1 = self.dc.GetTextExtent(str(text))

        text_small = " " + translate("laps")
        font_name_small = "Arial"
        font_size_small = 15
        font_weight = 400

        font = win32ui.CreateFont(
            {
                "name": font_name_small,
                "height": int(self.scale_factor * font_size_small),
                "weight": font_weight,
            }
        )
        self.dc.SelectObject(font)
        _, dy2 = self.dc.GetTextExtent(str(text_small))
        dy = int(0.8 * (dy1 - dy2))  # calculate font baseline position
        self.dc.TextOut(self.x + dx1, self.y - dy, str(text_small))

        self.move_cursor(font_size * 1.3)
        self.end_page()

    def print_split_normal(self, result: Result):
        obj = race()

        person = result.person
        if person is None or result.status in [
            ResultStatus.DID_NOT_START,
            ResultStatus.DID_NOT_FINISH,
        ]:
            return

        group = person.group
        is_group_existed = True
        if group is None:
            group = Group()
            group.name = "-"
            is_group_existed = False

        course = obj.find_course(result)

        is_penalty_used = obj.get_setting("marked_route_mode", "off") != "off"
        is_relay = group.is_relay()
        is_credit_time_used = race().get_setting("credit_time_enabled", False)

        fn = "Lucida Console"
        fs_small = 2.5
        fs_main = 3
        fs_large = 4

        # Information about start
        self.print_line(obj.data.title, fn, fs_main)
        self.print_line(
            str(obj.data.start_datetime)[:10] + ", " + obj.data.location, fn, fs_main
        )

        # Athlete info, bib, card number, start time
        self.print_line(person.full_name, fn, fs_large, 700)
        self.print_line(translate("Group") + ": " + group.name, fn, fs_main)
        if person.organization:
            self.print_line(
                translate("Team") + ": " + person.organization.name, fn, fs_main
            )
        self.print_line(
            translate("Bib")
            + ": "
            + str(person.bib)
            + " " * 5
            + translate("Card")
            + ": "
            + str(person.card_number),
            fn,
            fs_main,
        )
        self.print_line(
            translate("Start") + ": " + result.get_start_time().to_str(), fn, fs_main
        )

        # Splits
        index = 1
        for split in result.splits:
            if not is_group_existed:
                line = (
                    ("  " + str(index))[-3:]
                    + " "
                    + ("  " + split.code)[-3:]
                    + " "
                    + split.time.to_str()[-7:]
                )
                index += 1
                self.print_line(line, fn, fs_main)
            elif not course:
                line = (
                    ("  " + str(index))[-3:]
                    + " "
                    + ("  " + split.code)[-3:]
                    + " "
                    + split.relative_time.to_str()[-7:]
                    + " "
                    + split.leg_time.to_str()[-5:]
                )
                index += 1
                self.print_line(line, fn, fs_main)
            elif split.is_correct:
                line = (
                    ("  " + str(split.course_index + 1))[-3:]
                    + " "
                    + ("  " + split.code)[-3:]
                    + " "
                    + split.relative_time.to_str()[-7:]
                    + " "
                    + split.leg_time.to_str()[-5:]
                    + " "
                    + split.speed
                    + " "
                )

                if not is_relay:
                    line += ("  " + str(split.leg_place))[-3:]

                # Highlight correct controls of marked route ( '31' and '31(31,32,33)' => + )
                if is_penalty_used and course:
                    for course_cp in course.controls:
                        if str(course_cp).startswith(split.code):
                            line += " +"
                            break

                self.print_line(line, fn, fs_main)
            else:
                line = (
                    " " * 4
                    + (" " + split.code)[-3:]
                    + " "
                    + split.relative_time.to_str()[-7:]
                )
                self.print_line(line, fn, fs_main)

        finish_split = ""
        if len(result.splits) > 0:
            finish_split = (result.get_finish_time() - result.splits[-1].time).to_str()

        # Finish
        self.print_line(
            translate("Finish")
            + ": "
            + result.get_finish_time().to_str()
            + " " * 4
            + finish_split,
            fn,
            fs_main,
        )

        # Result
        if is_penalty_used:
            if obj.get_setting("marked_route_mode") == "time":
                self.print_line(
                    translate("Penalty") + ": " + result.get_penalty_time().to_str(),
                    fn,
                    fs_main,
                )
            elif obj.get_setting("marked_route_mode") == "laps":
                self.print_line(
                    translate("Penalty") + ": " + str(result.penalty_laps),
                    fn,
                    fs_main,
                )

        if is_credit_time_used:
            self.print_line(
                translate("Credit") + ": " + result.get_credit_time().to_str(),
                fn,
                fs_main,
            )

        is_rogaine = race().get_setting("result_processing_mode", "time") == "scores"
        if is_rogaine and result.rogaine_penalty > 0:
            penalty = result.rogaine_penalty
            total_score = result.rogaine_score + penalty
            self.print_line(
                translate("Points gained") + ": " + str(total_score),
                fn,
                fs_main,
            )
            self.print_line(
                translate("Penalty for finishing late") + ": " + str(penalty),
                fn,
                fs_main,
            )

        if result.is_status_ok():
            self.print_line(
                translate("Result")
                + ": "
                + result.get_result()
                + " " * 4
                + result.speed,
                fn,
                fs_main,
            )
        else:
            self.print_line(
                translate("Result") + ": " + result.get_result(), fn, fs_main
            )

        if is_relay and person.bib > 1000:
            self.print_line(
                translate("Team result") + ": " + result.get_result_relay(), fn, fs_main
            )

        # Place
        if result.place > 0 and is_group_existed:
            place = translate("Place") + ": " + str(result.place)
            if not is_relay:
                place += (
                    " "
                    + translate("from")
                    + " "
                    + str(group.count_finished)
                    + " ("
                    + translate("total")
                    + " "
                    + str(group.count_person)
                    + ")"
                )
            self.print_line(place, fn, fs_main)
        elif result.person.is_out_of_competition:
            place = translate("Place") + ": " + translate("o/c").upper()
            self.print_line(place, fn, fs_main)

        # Info about competitors, who can win current person
        if (
            result.is_status_ok()
            and not is_relay
            and not is_rogaine
            and is_group_existed
        ):
            if obj.get_setting("system_start_source", "protocol") == "protocol":
                if hasattr(result, "can_win_count"):
                    if result.can_win_count > 0:
                        self.print_line(
                            translate("Who can win you")
                            + ": "
                            + str(result.can_win_count),
                            fn,
                            fs_main,
                        )
                        self.print_line(
                            translate("Final result will be known")
                            + ": "
                            + result.final_result_time.to_str(),
                            fn,
                            fs_main,
                        )
                    else:
                        self.print_line(translate("Result is final"), fn, fs_main)

        # Punch checking info
        if is_group_existed:
            if result.is_status_ok():
                self.print_line(translate("Status: OK"), fn, fs_large, 700)
            else:
                self.print_line(translate("Status: DSQ"), fn, fs_large, 700)
                cp_list = ""
                line_limit = 35
                if course and course.controls:
                    for cp in course.controls:
                        if len(cp_list) > line_limit:
                            self.print_line(cp_list, fn, fs_main)
                            cp_list = ""
                        cp_list += cp.code.split("(")[0] + " "
                    self.print_line(cp_list, fn, fs_main)

            # Short result list
            if is_relay:
                pass
            else:
                res = ResultCalculation(obj).get_group_finishes(group)
                self.print_line(translate("Draft results"), fn, fs_main)
                for cur_res in res[:10]:
                    self.print_line(
                        ("   " + str(cur_res.get_place()))[-3:]
                        + " "
                        + (cur_res.person.full_name + " " * 22)[:22]
                        + " "
                        + cur_res.get_result(),
                        fn,
                        fs_main if not is_rogaine else fs_small,
                    )

        self.print_line(obj.data.url, fn, fs_main)

        self.end_page()

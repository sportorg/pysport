"""
Parse backup SI log generated in C:\\Program Files (x86)\\SportOrg\\log

-- Format:

start
[SI_CARD]
[START] - 0:00:00 if not exist
[FINISH] - 0:00:00 if not exist
split_start
[CODE_1] [TIME_1]
...
[CODE_N] [TIME_N]
split_end
end

-- Example:

start
8013787
00:00:00
11:39:25
split_start
57 11:43:05
69 11:37:59
90 11:39:07
split_end
end

"""
from sportorg.common.otime import OTime
from sportorg.gui.dialogs.file_dialog import get_open_file_name
from sportorg.language import translate
from sportorg.models.memory import ResultSportident, Split, race
from sportorg.modules.sportident.fix_time_sicard_5 import fix_time
from sportorg.utils.time import hhmmss_to_time

race = race()


def recovery():
    zero_time_val = race.get_setting('system_zero_time', (8, 0, 0))
    zero_time = OTime(
        hour=zero_time_val[0], minute=zero_time_val[1], sec=zero_time_val[2]
    )

    file_name = get_open_file_name(
        translate('Open SportOrg SI log file'),
        translate('SportOrg SI log (*.log)'),
        False,
    )

    text_file = open(file_name, 'r')
    lines = text_file.readlines()

    cur_res = ResultSportident()
    read_num = False
    read_start = False
    read_spl = False
    read_finish = False

    for line in lines:
        print(line)
        line = line.strip()
        if read_num:
            cur_res.card_number = int(line)
            read_start = True
            read_num = False
        elif read_start:
            cur_res.start_time = hhmmss_to_time(line)
            read_start = False
            read_finish = True
        elif read_finish:
            cur_res.finish_time = hhmmss_to_time(line)
            read_finish = False
        elif line == 'end':
            fix_time(cur_res, zero_time)
            race.results.append(cur_res)
            cur_res = ResultSportident()
        elif line == 'start':
            read_num = True
        elif line == 'split_start':
            read_spl = True
        elif line == 'split_end':
            read_spl = False
        elif read_spl:
            spl = Split()
            spl.code = line.split(' ')[0]
            spl.time = hhmmss_to_time(line.split(' ')[1])
            cur_res.splits.append(spl)

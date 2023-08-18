from sportorg.gui.main import Application
from sportorg.models.memory import race, ResultSportident, Split
from sportorg.utils.time import str_to_date, hhmmss_to_time

app = Application()
mw = app.get_main_window()
mw.open_file("C:\\tmp\\1.json")
race = race()

text_file = open("C:\\tmp\\si.log", "r")
lines = text_file.readlines()

cur_res = ResultSportident()
cur_split = Split()
read_num = False
read_start = False
read_fin = False
read_spl = False
read_finish = False

for line in lines:
    print(line)
    line = line.strip()
    if read_num:
        cur_res.card_number = line
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
        spl.code = line.split(" ")[0]
        spl.time = hhmmss_to_time(line.split(" ")[1])
        cur_res.splits.append(spl)

mw.save_file_as()
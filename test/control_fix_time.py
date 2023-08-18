from sportorg.common.otime import OTime
from sportorg.gui.main import Application
from sportorg.models.memory import race, ResultSportident, Split
from sportorg.utils.time import str_to_date, hhmmss_to_time

app = Application()
mw = app.get_main_window()
mw.open_file("C:\\tmp\\1.json")
race = race()

for res in race.results:
    for split in res.splits:
        if split.code == '73':
            if split.time < OTime(hour=14):
                split.time = split.time + OTime(hour=14, minute=21, sec=00)
        if split.code == '31':
            if split.time < OTime(hour=14):
                split.time = split.time + OTime(hour=15, minute=24, sec=15)

            if split.time > OTime(hour=23):
                split.time = split.time + OTime(hour=15, minute=24, sec=15) - OTime(hour=24)

mw.save_file_as()
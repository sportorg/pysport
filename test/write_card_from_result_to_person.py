
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.main import Application
from sportorg.gui.main_window import MainWindow
from sportorg.models.memory import race, ResultSportident

file_name = 'C:\\tmp\\test.json'

GlobalAccess().set_app(Application())
main_win = GlobalAccess().get_main_window()
assert isinstance(main_win, MainWindow)
main_win.init_model()
main_win.open_file(file_name=file_name)

for res in race().results:
    if isinstance(res, ResultSportident):
        res.person.sportident_card = res.sportident_card

main_win.save_file()
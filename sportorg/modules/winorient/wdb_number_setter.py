# set numbers by name of athletes
import sys

from PyQt5.QtWidgets import QApplication

from sportorg.modules.winorient.wdb import WinOrientBinary
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.language import _
from sportorg.libs.winorient.wdb import WDB, write_wdb


def set_numbers(wdb_target, wdb_source):
    """
    :type wdb_target: WDB
    :type wdb_source: WDB
    """
    changed = False
    for i in wdb_target.man:
        name = i.name
        source = wdb_source.find_man_by_name(name)
        if source and source.qualification:
            i.qualification = source.qualification
            changed = True
    return changed


if __name__ == '__main__':

    app = QApplication(sys.argv)
    file1 = get_open_file_name(_('Open target WDB file'), _("WDB file (*.wdb)"))
    file2 = get_open_file_name(_('Open source WDB file'), _("WDB file (*.wdb)"))
    wb1 = WinOrientBinary(file1).wdb_object
    wb2 = WinOrientBinary(file2).wdb_object

    if set_numbers(wb1, wb2):
        file3 = get_save_file_name(_('Save WDB file'), _("WDB file (*.wdb)"))
        write_wdb(wb1, file3)

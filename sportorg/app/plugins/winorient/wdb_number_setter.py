# set numbers by name of athletes
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from sportorg.app.plugins.winorient.wdb import WinOrientBinary
from sportorg.lib.winorient.wdb import WDB, write_wdb

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
    file1 = QtWidgets.QFileDialog.getOpenFileName(None, ('Open target WDB file'), '/', ("WDB file (*.wdb)"))[0]
    file2 = QtWidgets.QFileDialog.getOpenFileName(None, ('Open source WDB file'), '/', ("WDB file (*.wdb)"))[0]
    wb1 = WinOrientBinary(file1).wdb_object
    wb2 = WinOrientBinary(file2).wdb_object

    if set_numbers(wb1, wb2):
        file3 = QtWidgets.QFileDialog.getSaveFileName(None, ('Save WDB file'), '/', ("WDB file (*.wdb)"))[0]
        write_wdb(wb1, file3)
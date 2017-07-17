from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QMainWindow



class GlobalAccess(object):
    __instance = None
    main_window = None

    def __new__(cls):
        if GlobalAccess.__instance is None:
            GlobalAccess.__instance = object.__new__(cls)
        return GlobalAccess.__instance

    def set_main_window(self, window):
        self.main_window = window

    def get_main_window(self):
        return self.main_window

    def get_current_tab_index(self):
        mw = self.main_window
        return mw.tabwidget.currentIndex()

    def get_table_by_name(self, name):
        return self.get_main_window().findChild(QtWidgets.QTableView, name)

    def get_person_table(self):
        return self.get_table_by_name('EntryTable')

    def get_result_table(self):
        return self.get_table_by_name('ResultTable')

    def get_group_table(self):
        return self.get_table_by_name('GroupTable')

    def get_course_table(self):
        return self.get_table_by_name('CourseTable')

    def get_organization_table(self):
        return self.get_table_by_name('TeamTable')

    def get_current_table(self):
        map_= ['EntryTable', 'ResultTable', 'GroupTable', 'CourseTable', 'TeamTable']
        idx = self.get_current_tab_index()
        if idx < len(map_):
            return self.get_table_by_name(map_[idx])

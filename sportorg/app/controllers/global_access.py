from PyQt5 import QtWidgets
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, QSortFilterProxyModel

from PyQt5.QtWidgets import QTableView, QMessageBox

from sportorg.app.models.memory import race
from sportorg.app.models.memory_model import PersonMemoryModel


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

    def get_selected_rows(self):
        table = self.get_current_table()
        assert isinstance(table, QTableView)
        sel_model = table.selectionModel()
        assert isinstance(sel_model, QItemSelectionModel)
        indexes = sel_model.selectedRows()
        model = table.model()
        assert (isinstance(model, QSortFilterProxyModel))
        ret = []
        for i in indexes:
            assert isinstance(i, QModelIndex)
            orig_index = model.mapToSource(i)
            assert isinstance(orig_index, QModelIndex)
            orig_index_int = orig_index.row()
            ret.append(orig_index_int)
        return ret

    def delete_object(self):
        confirm = QMessageBox.question(self.get_main_window(), 'Question', 'Please confirm', QMessageBox.Yes|QMessageBox.No)
        if confirm == QMessageBox.No:
            return
        tab = self.get_current_tab_index()
        indexes = self.get_selected_rows()
        if tab == 0:
            race().delete_persons(indexes, self.get_person_table())
            self.get_main_window().refresh()

        if tab == 1:
            race().delete_results(indexes)
        if tab == 2:
            race().delete_groups(indexes)
        if tab == 3:
            race().delete_courses(indexes)
        if tab == 4:
            race().delete_organizations(indexes)
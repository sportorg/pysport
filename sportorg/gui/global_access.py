import logging

from PyQt5 import QtWidgets
from PyQt5.QtCore import QItemSelectionModel, QModelIndex
from PyQt5.QtWidgets import QTableView, QMessageBox

from sportorg.core.singleton import Singleton
from sportorg.models.memory import race, NotEmptyException
from sportorg.models.result.result_checker import ResultChecker

from sportorg.language import _
from sportorg.models.result.result_calculation import ResultCalculation


class GlobalAccess(metaclass=Singleton):
    main_window = None

    def set_main_window(self, window):
        self.main_window = window

    def get_main_window(self):
        """

        :return: MainWindow
        """
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
        map_ = ['EntryTable', 'ResultTable', 'GroupTable', 'CourseTable', 'TeamTable']
        idx = self.get_current_tab_index()
        if idx < len(map_):
            return self.get_table_by_name(map_[idx])

    def get_selected_rows(self):
        table = self.get_current_table()
        assert isinstance(table, QTableView)
        sel_model = table.selectionModel()
        assert isinstance(sel_model, QItemSelectionModel)
        indexes = sel_model.selectedRows()

        ret = []
        for i in indexes:
            assert isinstance(i, QModelIndex)
            orig_index_int = i.row()
            ret.append(orig_index_int)
        return ret

    def delete_object(self):
        indexes = self.get_selected_rows()
        if not len(indexes):
            return

        confirm = QMessageBox.question(self.get_main_window(),
                                       _('Question'),
                                       _('Please confirm'),
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return
        tab = self.get_current_tab_index()

        if tab == 0:
            race().delete_persons(indexes)
            # recalculate places
            ResultCalculation().process_results()
            self.get_main_window().refresh()
        elif tab == 1:
            race().delete_results(indexes)
            # recalculate places
            ResultCalculation().process_results()
            self.get_main_window().refresh()
        elif tab == 2:
            try:
                race().delete_groups(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_group_table(),
                                     _('Error'),
                                     _('Cannot remove group'))
            self.get_main_window().refresh()
        elif tab == 3:
            try:
                race().delete_courses(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_course_table(),
                                     _('Error'),
                                     _('Cannot remove course'))
            self.get_main_window().refresh()
        elif tab == 4:
            try:
                race().delete_organizations(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_organization_table(),
                                     _('Error'),
                                     _('Cannot remove organization'))
            self.get_main_window().refresh()

    def add_object(self):
        try:
            tab = self.get_current_tab_index()
            if tab == 0:
                race().add_new_person()
                self.get_person_table().model().init_cache()
            elif tab == 1:
                self.get_main_window().manual_finish()
            elif tab == 2:
                race().add_new_group()
                self.get_person_table().model().init_cache()
            elif tab == 3:
                race().add_new_course()
                self.get_course_table().model().init_cache()
            elif tab == 4:
                race().add_new_organization()
                self.get_organization_table().model().init_cache()
            self.get_main_window().refresh()
        except Exception as e:
            logging.exception(str(e))

    def clear_filters(self, remove_condition=True):
        self.get_person_table().model().clear_filter(remove_condition)
        self.get_result_table().model().clear_filter(remove_condition)
        self.get_person_table().model().clear_filter(remove_condition)
        self.get_course_table().model().clear_filter(remove_condition)
        self.get_organization_table().model().clear_filter(remove_condition)

    def rechecking(self):
        try:
            logging.debug('Rechecking start')
            for result in race().results:
                if result.person is not None:
                    ResultChecker.checking(result)
            logging.debug('Rechecking finish')
            ResultCalculation().process_results()
            self.get_main_window().refresh()
        except Exception as e:
            logging.exception(str(e))

    def apply_filters(self):
        self.get_person_table().model().apply_filter()
        self.get_result_table().model().apply_filter()
        self.get_person_table().model().apply_filter()
        self.get_course_table().model().apply_filter()
        self.get_organization_table().model().apply_filter()

    def auto_save(self):
        main_window = self.get_main_window()
        if not main_window:
            return
        if not main_window.get_configuration().get('autosave'):
            return
        if main_window.file:
            main_window.save_file()
            logging.info(_('Auto save'))
        else:
            logging.warning(_('No file to auto save'))

    def refresh(self):
        self.get_main_window().refresh()

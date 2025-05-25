import logging
import time
import uuid
from os import remove
from typing import Any, Dict, Type

try:
    from PySide6 import QtCore
    from PySide6.QtWidgets import QApplication, QMessageBox
except ModuleNotFoundError:
    from PySide2 import QtCore
    from PySide2.QtWidgets import QApplication, QMessageBox

from sportorg import config
from sportorg.common.otime import OTime
from sportorg.gui.dialogs.about import AboutDialog
from sportorg.gui.dialogs.control_time_change_dialog import ControlTimeChangeDialog
from sportorg.gui.dialogs.cp_delete import CPDeleteDialog
from sportorg.gui.dialogs.entry_mass_edit import MassEditDialog
from sportorg.gui.dialogs.event_properties import EventPropertiesDialog
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.dialogs.filter_dialog import DialogFilter
from sportorg.gui.dialogs.group_mass_edit import GroupMassEditDialog
from sportorg.gui.dialogs.import_persons_table_dialog import ImportPersonsTableDialog
from sportorg.gui.dialogs.live_dialog import LiveDialog
from sportorg.gui.dialogs.marked_route_dialog import MarkedRouteDialog
from sportorg.gui.dialogs.merge_results import MergeResultsDialog
from sportorg.gui.dialogs.not_start_dialog import InputStartNumbersDialog
from sportorg.gui.dialogs.organization_mass_edit import OrganizationMassEditDialog
from sportorg.gui.dialogs.print_properties import PrintPropertiesDialog
from sportorg.gui.dialogs.relay_clone_dialog import RelayCloneDialog
from sportorg.gui.dialogs.relay_number_dialog import RelayNumberDialog
from sportorg.gui.dialogs.rent_cards_dialog import RentCardsDialog
from sportorg.gui.dialogs.report_dialog import ReportDialog
from sportorg.gui.dialogs.search_dialog import SearchDialog
from sportorg.gui.dialogs.settings import SettingsDialog
from sportorg.gui.dialogs.split_delete import SplitDeleteDialog
from sportorg.gui.dialogs.sportorg_import_dialog import SportOrgImportDialog
from sportorg.gui.dialogs.start_handicap_dialog import StartHandicapDialog
from sportorg.gui.dialogs.start_preparation import (
    StartPreparationDialog,
    guess_courses_for_groups,
)
from sportorg.gui.dialogs.start_time_change_dialog import StartTimeChangeDialog
from sportorg.gui.dialogs.teamwork_properties import TeamworkPropertiesDialog
from sportorg.gui.dialogs.telegram_dialog import TelegramDialog
from sportorg.gui.dialogs.text_io import TextExchangeDialog
from sportorg.gui.dialogs.timekeeping_properties import TimekeepingPropertiesDialog
from sportorg.gui.menu.action import Action
from sportorg.gui.utils.custom_controls import messageBoxQuestion
from sportorg.language import translate
from sportorg.libs.sfr import sfrximporter
from sportorg.libs.winorient.wdb import write_wdb
from sportorg.models.memory import ResultManual, ResultStatus, race
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.result_tools import recalculate_results
from sportorg.models.start.start_preparation import (
    copy_bib_to_card_number,
    copy_card_number_to_bib,
    guess_corridors_for_groups,
)
from sportorg.modules.backup.file import is_gzip_file
from sportorg.modules.backup.json import get_races_from_file
from sportorg.modules.configs.configs import Config
from sportorg.modules.iof import iof_xml
from sportorg.modules.live.live import live_client
from sportorg.modules.ocad import ocad
from sportorg.modules.ocad.ocad import OcadImportException
from sportorg.modules.recovery import (
    recovery_orgeo_finish_csv,
    recovery_si_master_csv,
    recovery_sportorg_html,
    recovery_sportorg_si_log,
)
from sportorg.modules.rfid_impinj.rfid_impinj import ImpinjClient
from sportorg.modules.sfr.sfrreader import SFRReaderClient
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.srpid.srpid import SrpidClient
from sportorg.modules.teamwork.teamwork import Teamwork
from sportorg.modules.telegram.telegram import telegram_client
from sportorg.modules.updater import checker
from sportorg.modules.winorient import winorient
from sportorg.modules.winorient.wdb import WDBImportError, WinOrientBinary


class ActionFactory(type):
    actions: Dict[str, Type[Action]] = {}

    def __new__(mcs, name, *args, **kwargs) -> Any:
        cls = super().__new__(mcs, name, *args, **kwargs)
        ActionFactory.actions[name] = cls
        return cls


class NewAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.create_file(is_new=True)


class SaveAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.save_file()


class OpenAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SportOrg file"), translate("SportOrg file (*.json)")
        )
        self.app.open_file(file_name)


class SaveAsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.save_file_as()


class OpenRecentAction(Action, metaclass=ActionFactory):
    def execute(self):
        pass


class CopyAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(5):
            return
        table = self.app.get_current_table()
        sel_model = table.selectionModel()
        data = "\t".join(sel_model.model().get_headers()) + "\n"
        indexes = sel_model.selectedRows()
        for index in indexes:
            row = [str(row) for row in sel_model.model().get_data(index.row())]
            data += "\t".join(row) + "\n"
        QApplication.instance().clipboard().setText(data)


class DuplicateAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(5):
            return
        table = self.app.get_current_table()
        sel_model = table.selectionModel()
        indexes = sel_model.selectedRows()
        if len(indexes):
            sel_model.model().duplicate(indexes[0].row())
            self.app.refresh()


class SettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        SettingsDialog().exec_()


class EventSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        EventPropertiesDialog().exec_()


class CSVWinorientImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open CSV Winorient file"), translate("CSV Winorient (*.csv)")
        )
        if file_name != "":
            try:
                winorient.import_csv(file_name)
            except Exception as e:
                logging.error(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Import error") + ": " + file_name,
                )
            self.app.init_model()


class SFRXImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SFRX file"), translate("SFRX (*.sfrx)")
        )
        if file_name:
            try:
                sfrximporter.import_sfrx(file_name)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Import error") + ": " + file_name,
                )
            self.app.init_model()


class WDBWinorientImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open WDB Winorient file"), translate("WDB Winorient (*.wdb)")
        )
        if file_name != "":
            try:
                winorient.import_wo_wdb(file_name)
            except WDBImportError as e:
                logging.error(str(e))
                logging.exception(e)
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Import error") + ": " + file_name,
                )
            self.app.init_model()


class OcadTXTv8ImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open Ocad txt v8 file"), translate("Ocad classes v8 (*.txt)")
        )
        if file_name != "":
            try:
                ocad.import_txt_v8(file_name)
            except OcadImportException as e:
                logging.error(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Import error") + ": " + file_name,
                )
            self.app.init_model()


class WDBWinorientExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As WDB file"),
            translate("WDB file (*.wdb)"),
            "{}_sportorg_export".format(
                race().data.get_start_datetime().strftime("%Y%m%d")
            ),
        )
        if file_name != "":
            try:
                wb = WinOrientBinary()

                self.app.clear_filters(False)
                wdb_object = wb.export()
                self.app.apply_filters()

                write_wdb(wdb_object, file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class IOFResultListExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As IOF xml"),
            translate("IOF xml (*.xml)"),
            "{}_resultList".format(race().data.get_start_datetime().strftime("%Y%m%d")),
        )
        if file_name != "":
            try:
                iof_xml.export_result_list(file_name, creator=config.get_creator_name())
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class IOFResultListAllSplitsExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As IOF xml"),
            translate("IOF xml (*.xml)"),
            "{}_resultList".format(race().data.get_start_datetime().strftime("%Y%m%d")),
        )
        if file_name != "":
            try:
                iof_xml.export_result_list(
                    file_name, creator=config.get_creator_name(), all_splits=True
                )
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class IOFEntryListExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As IOF xml"),
            translate("IOF xml (*.xml)"),
            "{}_entryList".format(race().data.get_start_datetime().strftime("%Y%m%d")),
        )
        if file_name != "":
            try:
                iof_xml.export_entry_list(file_name, creator=config.get_creator_name())
            except Exception as e:
                logging.error(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class IOFEntryListImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open IOF xml"), translate("IOF xml (*.xml)")
        )
        if file_name != "":
            try:
                iof_xml.import_from_iof(file_name)
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Import error") + ": " + file_name,
                )
            self.app.init_model()


class IOFStartListExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As IOF xml"),
            translate("IOF xml (*.xml)"),
            "{}_startList".format(race().data.get_start_datetime().strftime("%Y%m%d")),
        )
        if file_name != "":
            try:
                iof_xml.export_start_list(file_name, creator=config.get_creator_name())
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class IOFCompetitorListExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(
            translate("Save As IOF xml"),
            translate("IOF xml (*.xml)"),
            "{}_competitorList".format(
                race().data.get_start_datetime().strftime("%Y%m%d")
            ),
        )
        if file_name != "":
            try:
                iof_xml.export_competitor_list(
                    file_name, creator=config.get_creator_name()
                )
            except Exception as e:
                logging.exception(str(e))
                QMessageBox.warning(
                    self.app,
                    translate("Error"),
                    translate("Export error") + ": " + file_name,
                )


class RecoverySportorgHtmlAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SportOrg HTML file"),
            translate("SportOrg HTML report (*.html)"),
            False,
        )
        tmp_filename = recovery_sportorg_html.recovery(file_name)
        with open(tmp_filename) as f:
            attr = get_races_from_file(f)
        SportOrgImportDialog(*attr).exec_()
        remove(tmp_filename)
        self.app.refresh()


class RecoverySportorgSiLogAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SportOrg SI log file"),
            translate("SportOrg SI log (*.log)"),
            False,
        )
        recovery_sportorg_si_log.recovery(file_name, race())
        self.app.refresh()


class RecoverySportidentMasterCsvAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SPORTident master station backup file"),
            translate("CSV file (*.csv)"),
            False,
        )
        recovery_si_master_csv.recovery(file_name, race())
        self.app.refresh()


class RecoveryOrgeoFinishCsvAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open orgeo.ru finish CSV file"),
            translate("CSV file (*.csv)"),
            False,
        )
        recovery_orgeo_finish_csv.recovery(file_name, race())
        self.app.refresh()


class AddObjectAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.add_object()


class DeleteAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.delete_object()


class TextExchangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        TextExchangeDialog().exec_()
        race().rebuild_indexes()
        self.app.refresh()


class MassEditAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab == 0:
            MassEditDialog().exec_()
            race().rebuild_indexes()
            self.app.refresh()

        if self.app.current_tab == 2:
            GroupMassEditDialog().exec_()
            self.app.refresh()

        if self.app.current_tab == 4:
            OrganizationMassEditDialog().exec_()
            self.app.refresh()


class RefreshAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.refresh()


class FilterAction(Action, metaclass=ActionFactory):
    def execute(self):
        table = self.app.get_current_table()
        DialogFilter(table).exec_()
        self.app.refresh()


class FilterResetAction(Action, metaclass=ActionFactory):
    def execute(self):
        table = self.app.get_current_table()
        proxy_model = table.model()
        proxy_model.clear_filter()
        self.app.refresh()


class SearchAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(5):
            return
        table = self.app.get_current_table()
        SearchDialog(table).exec_()
        self.app.refresh()


class ToStartPreparationAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(0)


class ToRaceResultsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(1)


class ToGroupsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(2)


class ToCoursesAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(3)


class ToTeamsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(4)


class ToLogsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(5)


class StartPreparationAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartPreparationDialog().exec_()
        self.app.refresh()


class GuessCoursesAction(Action, metaclass=ActionFactory):
    def execute(self):
        guess_courses_for_groups()
        self.app.refresh()


class GuessCorridorsAction(Action, metaclass=ActionFactory):
    def execute(self):
        guess_corridors_for_groups()
        self.app.refresh()


class RelayNumberAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.relay_number_assign:
            self.app.relay_number_assign = False
            QApplication.restoreOverrideCursor()
        else:
            self.app.relay_number_assign = True
            QApplication.setOverrideCursor(QtCore.Qt.PointingHandCursor)
            RelayNumberDialog().exec_()
        self.app.refresh()


class StartTimeChangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartTimeChangeDialog().exec_()
        self.app.refresh()


class StartHandicapAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartHandicapDialog().exec_()
        self.app.refresh()


class RelayCloneAction(Action, metaclass=ActionFactory):
    def execute(self):
        RelayCloneDialog().exec_()
        self.app.refresh()


class CopyBibToCardNumber(Action, metaclass=ActionFactory):
    def execute(self):
        msg = translate("Use bib as card number") + "?"
        reply = messageBoxQuestion(
            self.app, translate("Question"), msg, QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            copy_bib_to_card_number()
            self.app.refresh()


class CopyCardNumberToBib(Action, metaclass=ActionFactory):
    def execute(self):
        msg = translate("Use card number as bib") + "?"
        reply = messageBoxQuestion(
            self.app, translate("Question"), msg, QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            copy_card_number_to_bib()
            self.app.refresh()


class ManualFinishAction(Action, metaclass=ActionFactory):
    def execute(self):
        result = race().new_result(ResultManual)
        Teamwork().send(result.to_dict())
        live_client.send(result)
        race().add_new_result(result)
        logging.info(translate("Manual finish"))
        self.app.refresh()


class SPORTidentReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SIReaderClient().toggle()
        time.sleep(0.5)
        self.app.interval()


class SportiduinoReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SportiduinoClient().toggle()
        time.sleep(0.5)
        self.app.interval()


class ImpinjReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        ImpinjClient().toggle()
        time.sleep(0.5)
        self.app.interval()


class SrpidReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SrpidClient().toggle()
        time.sleep(0.5)
        self.app.interval()


class SFRReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SFRReaderClient().toggle()
        time.sleep(0.5)
        self.app.interval()


class CreateReportAction(Action, metaclass=ActionFactory):
    def execute(self):
        ReportDialog().exec_()


class SplitPrintoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.split_printout_selected()


class RecheckingAction(Action, metaclass=ActionFactory):
    def execute(self):
        recalculate_results()
        race().rebuild_indexes()
        self.app.refresh()


class GroupFinderAction(Action, metaclass=ActionFactory):
    def execute(self):
        obj = race()
        indices = self.app.get_selected_rows()
        results = obj.results
        for index in indices:
            if index < 0:
                continue
            if index >= len(results):
                break
            result = results[index]
            if result.person and result.status in [ResultStatus.MISSING_PUNCH]:
                for group in obj.groups:
                    if result.check(group.course):
                        result.person.group = group
                        result.status = ResultStatus.OK
                        break
        self.app.refresh()


class PenaltyCalculationAction(Action, metaclass=ActionFactory):
    def execute(self):
        logging.debug("Penalty calculation start")
        for result in race().results:
            if result.person:
                ResultChecker.checking(result)
        logging.debug("Penalty calculation finish")
        recalculate_results(recheck_results=False)
        self.app.refresh()


class PenaltyRemovingAction(Action, metaclass=ActionFactory):
    def execute(self):
        logging.debug("Penalty removing start")
        for result in race().results:
            result.penalty_time = OTime(msec=0)
            result.penalty_laps = 0
        logging.debug("Penalty removing finish")
        recalculate_results(recheck_results=False)
        self.app.refresh()


class ChangeStatusAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab != 1:
            logging.warning(translate("No result selected"))
            return
        obj = race()

        status_dict = {
            ResultStatus.NONE: ResultStatus.OK,
            ResultStatus.OK: ResultStatus.DISQUALIFIED,
            ResultStatus.DISQUALIFIED: ResultStatus.DID_NOT_START,
            ResultStatus.DID_NOT_START: ResultStatus.DID_NOT_FINISH,
            ResultStatus.DID_NOT_FINISH: ResultStatus.RESTORED,
            ResultStatus.RESTORED: ResultStatus.OK,
        }

        table = self.app.get_result_table()
        index = table.currentIndex().row()
        if index < 0:
            index = 0
        if index >= len(obj.results):
            mes = QMessageBox()
            mes.setText(translate("No results to change status"))
            mes.exec_()
            return
        result = obj.results[index]
        if result.status in status_dict:
            result.status = status_dict[result.status]
        else:
            result.status = ResultStatus.OK
        Teamwork().send(result.to_dict())
        live_client.send(result)
        self.app.refresh()


class SetDNSNumbersAction(Action, metaclass=ActionFactory):
    def execute(self):
        InputStartNumbersDialog().exec_()
        self.app.refresh()


class ImportPersonsAction(Action, metaclass=ActionFactory):
    def execute(self):
        ImportPersonsTableDialog().exec_()
        self.app.refresh()


class ControlTimeChangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        ControlTimeChangeDialog().exec_()
        self.app.refresh()


class CPDeleteAction(Action, metaclass=ActionFactory):
    def execute(self):
        CPDeleteDialog().exec_()
        self.app.refresh()


class SplitDeleteAction(Action, metaclass=ActionFactory):
    def execute(self):
        SplitDeleteDialog().exec_()
        self.app.refresh()


class MergeResultsAction(Action, metaclass=ActionFactory):
    def execute(self):
        MergeResultsDialog().exec_()
        self.app.refresh()


class AddSPORTidentResultAction(Action, metaclass=ActionFactory):
    def execute(self):
        result = race().new_result()
        race().add_new_result(result)
        Teamwork().send(result.to_dict())
        logging.info("SPORTident result")
        self.app.get_result_table().model().init_cache()
        self.app.refresh()


class TimekeepingSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TimekeepingPropertiesDialog().exec_()
        self.app.refresh()


class TeamworkSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TeamworkPropertiesDialog().exec_()


class TeamworkEnableAction(Action, metaclass=ActionFactory):
    def execute(self):
        host = race().get_setting("teamwork_host", "localhost")
        port = race().get_setting("teamwork_port", 50010)
        token = race().get_setting("teamwork_token", str(uuid.uuid4())[:8])
        connection_type = race().get_setting("teamwork_type_connection", "client")
        if connection_type == "server":
            host = "0.0.0.0"
        Teamwork().set_options(host, port, token, connection_type)
        Teamwork().toggle()


class TeamworkSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            obj = race()
            data_list = [
                obj.persons,
                obj.results,
                obj.groups,
                obj.courses,
                obj.organizations,
            ]
            if not self.app.current_tab < len(data_list):
                return
            items = data_list[self.app.current_tab]
            indexes = self.app.get_selected_rows()
            items_dict = []
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(items):
                    break
                items_dict.append(items[index].to_dict())
            Teamwork().send(items_dict)
        except Exception as e:
            logging.exception(e)


class PrinterSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        PrintPropertiesDialog().exec_()


class LiveSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        LiveDialog().exec_()
        self.app.refresh()


class TelegramSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TelegramDialog().exec_()


class TelegramSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            if not self.app.current_tab == 1:
                logging.warning(translate("No result selected"))
                return
            items = race().results
            indexes = self.app.get_selected_rows()
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(items):
                    pass
                telegram_client.send_result(items[index])
        except Exception as e:
            logging.error(str(e))


class OnlineSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            items = []
            if self.app.current_tab == 0:
                items = race().persons
            if self.app.current_tab == 1:
                items = race().results
            if self.app.current_tab == 2:
                items = race().groups
            if self.app.current_tab == 3:
                items = race().courses
            if self.app.current_tab == 4:
                items = race().organizations
            indexes = self.app.get_selected_rows()
            if not indexes:
                return
            selected_items = []
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(items):
                    pass
                selected_items.append(items[index])
            if self.app.current_tab == 1:
                # Most recent results are sent last
                selected_items = selected_items[::-1]
            live_client.send(selected_items)
        except Exception as e:
            logging.exception(e)


class AboutAction(Action, metaclass=ActionFactory):
    def execute(self):
        AboutDialog().exec_()


class CheckUpdatesAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            if not checker.check_version(config.VERSION):
                message = translate("Update available") + " " + checker.get_version()
            else:
                message = translate("You are using the latest version")

            QMessageBox.information(self.app, translate("Info"), message)
        except Exception as e:
            logging.error(str(e))
            QMessageBox.warning(self.app, translate("Error"), str(e))


class AssignResultByBibAction(Action, metaclass=ActionFactory):
    def execute(self):
        for result in race().results:
            if result.person is None and result.bib:
                result.person = race().find_person_by_bib(result.bib)
        self.app.refresh()


class AssignResultByCardNumberAction(Action, metaclass=ActionFactory):
    def execute(self):
        for result in race().results:
            if result.person is None and result.card_number:
                result.person = race().find_person_by_card(result.card_number)
        self.app.refresh()


class ImportSportOrgAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(
            translate("Open SportOrg json"), translate("SportOrg (*.json)")
        )
        if file_name == "":
            return

        mode = "r"

        # if user set UTF-8 usage, first try to open file in UTF-8,
        # then in system locale (1251 for RU Windows)
        use_utf8 = Config().configuration.get("save_in_utf8", False)
        use_gzip = Config().configuration.get("save_in_gzip", False)

        if mode == "r":
            use_gzip = is_gzip_file(file_name)

        def_encoding = "utf-8" if use_utf8 and not use_gzip else None
        if use_gzip:
            mode = f"{mode}+b"

        try:
            with open(file_name, mode=mode, encoding=def_encoding) as f:
                attr = get_races_from_file(f, compress=use_gzip)
        except UnicodeDecodeError:
            f.close()

            alt_encoding = None if use_utf8 or use_gzip else "utf-8"

            with open(file_name, mode=mode, encoding=alt_encoding) as f:
                attr = get_races_from_file(f, compress=use_gzip)

        SportOrgImportDialog(*attr).exec_()
        self.app.refresh()


class RentCardsAction(Action, metaclass=ActionFactory):
    def execute(self):
        RentCardsDialog().exec_()
        self.app.refresh()


class MarkedRouteCourseGeneration(Action, metaclass=ActionFactory):
    def execute(self):
        MarkedRouteDialog().exec_()
        self.app.refresh()


class ExtractPersonMiddleName(Action, metaclass=ActionFactory):
    def execute(self):
        for person in race().persons:
            person.extract_middle_name()
        self.app.refresh()

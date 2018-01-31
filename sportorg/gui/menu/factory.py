from sportorg.gui.menu.actions import NewAction, SaveAction, OpenAction, SaveAsAction, OpenRecentAction, \
    SettingsAction, \
    EventSettingsAction, CSVWinorientImportAction, WDBWinorientImportAction, OcadTXTv8ImportAction, \
    WDBWinorientExportAction, IOFResultListExportAction, AddObjectAction, DeleteAction, TextExchangeAction, \
    RefreshAction, FilterAction, SearchAction, ToStartPreparationAction, ToRaceResultsAction, ToGroupsAction, \
    ToCoursesAction, ToTeamsAction, StartPreparationAction, GuessCoursesAction, GuessCorridorsAction,\
    RelayNumberAction, \
    NumberChangeAction, StartTimeChangeAction, StartListAction, TeamListAction, StartTimesAction, PrintBibAction, \
    ManualFinishAction, SPORTidentReadoutAction, CreateReportAction, CreateTeamResultsReportAction, \
    SplitPrintoutAction, \
    RecheckingAction, PenaltyCalculationAction, PenaltyRemovingAction, ChangeStatusAction, SetDNSNumbersAction, \
    AddSPORTidentResultAction, TimekeepingSettingsAction, PrinterSettingsAction, LiveSettingsAction, \
    LiveSendStartListAction, LiveSendResultsAction, LiveResendResultsAction, AboutAction, TestingAction


class Factory:
    def __init__(self, app):
        self.actions = [
            NewAction(),
            SaveAction(),
            OpenAction(),
            SaveAsAction(),
            OpenRecentAction(),
            SettingsAction(),
            EventSettingsAction(),
            CSVWinorientImportAction(),
            WDBWinorientImportAction(),
            OcadTXTv8ImportAction(),
            WDBWinorientExportAction(),
            IOFResultListExportAction(),
            AddObjectAction(),
            DeleteAction(),
            TextExchangeAction(),
            RefreshAction(),
            FilterAction(),
            SearchAction(),
            ToStartPreparationAction(),
            ToRaceResultsAction(),
            ToGroupsAction(),
            ToCoursesAction(),
            ToTeamsAction(),
            StartPreparationAction(),
            GuessCoursesAction(),
            GuessCorridorsAction(),
            RelayNumberAction(),
            NumberChangeAction(),
            StartTimeChangeAction(),
            StartListAction(),
            TeamListAction(),
            StartTimesAction(),
            PrintBibAction(),
            ManualFinishAction(),
            SPORTidentReadoutAction(),
            CreateReportAction(),
            CreateTeamResultsReportAction(),
            SplitPrintoutAction(),
            RecheckingAction(),
            PenaltyCalculationAction(),
            PenaltyRemovingAction(),
            ChangeStatusAction(),
            SetDNSNumbersAction(),
            AddSPORTidentResultAction(),
            TimekeepingSettingsAction(),
            PrinterSettingsAction(),
            LiveSettingsAction(),
            LiveSendStartListAction(),
            LiveSendResultsAction(),
            LiveResendResultsAction(),
            AboutAction(),
            TestingAction()
        ]
        self._map = {}
        for action in self.actions:
            action.app = app
            action_id = action.id
            if not action_id:
                action_id = action.__class__.__name__
            self._map[action_id] = action.callback

    def get_action(self, key):
        if key in self._map:
            return self._map[key]
        return lambda: print('...')

    def execute(self, key):
        self.get_action(key)()

from sportorg import config
from sportorg.language import translate


def menu_list():
    return [
        {
            "title": translate("File"),
            "actions": [
                {
                    "title": translate("New"),
                    "shortcut": "Ctrl+N",
                    "icon": config.icon_dir("file.svg"),
                    "action": "NewAction",
                },
                {
                    "title": translate("Save"),
                    "shortcut": "Ctrl+S",
                    "icon": config.icon_dir("save.svg"),
                    "action": "SaveAction",
                },
                {
                    "title": translate("Open"),
                    "shortcut": "Ctrl+O",
                    "icon": config.icon_dir("folder.svg"),
                    "action": "OpenAction",
                },
                {
                    "title": translate("Save As"),
                    "shortcut": "Ctrl+Shift+S",
                    "icon": config.icon_dir("save.svg"),
                    "action": "SaveAsAction",
                },
                {
                    "type": "separator",
                },
                {
                    "title": translate("Settings"),
                    "shortcut": "Ctrl+Alt+S",
                    "icon": config.icon_dir("settings.svg"),
                    "action": "SettingsAction",
                },
                {
                    "title": translate("Event Settings"),
                    "shortcut": "Ctrl+I",
                    "icon": config.icon_dir("form.svg"),
                    "action": "EventSettingsAction",
                },
                {
                    "type": "separator",
                },
                {
                    "title": translate("Import"),
                    "actions": [
                        {
                            "title": translate("Import from SportOrg file"),
                            "action": "ImportSportOrgAction",
                        },
                        {
                            "title": translate("CSV Winorient"),
                            "icon": config.icon_dir("csv.svg"),
                            "action": "CSVWinorientImportAction",
                        },
                        {
                            "title": translate("WDB Winorient"),
                            "action": "WDBWinorientImportAction",
                        },
                        {
                            "title": translate("file SFRX"),
                            "action": "SFRXImportAction",
                        },
                        {
                            "title": translate("Ocad txt v8"),
                            "action": "OcadTXTv8ImportAction",
                        },
                        {
                            "title": translate("IOF xml"),
                            "action": "IOFEntryListImportAction",
                        },
                        {
                            "title": translate("SPORTident master station CSV"),
                            "action": "RecoverySportidentMasterCsvAction",
                        },
                        {
                            "title": translate("SportOrg SI log"),
                            "action": "RecoverySportorgSiLogAction",
                        },
                        {
                            "title": translate("Orgeo.ru CSV"),
                            "action": "RecoveryOrgeoFinishCsvAction",
                        },
                        {
                            "title": translate("SportOrg HTML"),
                            "action": "RecoverySportorgHtmlAction",
                        },
                        {
                            "title": translate("Import persons from table (clipboard)"),
                            "action": "ImportPersonsAction",
                        },
                    ],
                },
                {
                    "title": translate("Export"),
                    "actions": [
                        {
                            "title": translate("WDB Winorient"),
                            "action": "WDBWinorientExportAction",
                        },
                        {
                            "title": translate("IOF xml"),
                            "actions": [
                                {
                                    "title": translate("ResultList"),
                                    "action": "IOFResultListExportAction",
                                },
                                {
                                    "title": translate("ResultListAllSplits"),
                                    "action": "IOFResultListAllSplitsExportAction",
                                },
                                {
                                    "title": translate("EntrytList"),
                                    "action": "IOFEntryListExportAction",
                                },
                                {
                                    "title": translate("CompetitorList"),
                                    "action": "IOFCompetitorListExportAction",
                                },
                                {
                                    "title": translate("StartList"),
                                    "action": "IOFStartListExportAction",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "title": translate("Edit"),
            "actions": [
                {
                    "title": translate("Add object"),
                    "tabs": list(range(5)),
                    "shortcut": ["insert", "i"],
                    "icon": config.icon_dir("add.svg"),
                    "action": "AddObjectAction",
                },
                {
                    "title": translate("Delete"),
                    "shortcut": "Del",
                    "tabs": list(range(5)),
                    "icon": config.icon_dir("delete.svg"),
                    "action": "DeleteAction",
                },
                {
                    "title": translate("Copy"),
                    "shortcut": "Ctrl+C",
                    "tabs": list(range(5)),
                    "action": "CopyAction",
                },
                {
                    "title": translate("Duplicate"),
                    "shortcut": "Ctrl+D",
                    "tabs": list(range(5)),
                    "action": "DuplicateAction",
                },
                {
                    "title": translate("Text exchange"),
                    "shortcut": "Ctrl+T",
                    "action": "TextExchangeAction",
                },
                {
                    "title": translate("Mass edit"),
                    "tabs": [0, 2, 4],
                    "shortcut": "Ctrl+E",
                    "action": "MassEditAction",
                },
            ],
        },
        {
            "title": translate("View"),
            "actions": [
                {
                    "title": translate("Refresh"),
                    "icon": config.icon_dir("refresh.svg"),
                    "shortcut": "F5",
                    "action": "RefreshAction",
                },
                {
                    "title": translate("Filter"),
                    "shortcut": "F2",
                    "tabs": list(range(5)),
                    "icon": config.icon_dir("filter.svg"),
                    "action": "FilterAction",
                },
                {
                    "title": translate("Filter reset"),
                    "shortcut": "Ctrl+F2",
                    "tabs": list(range(5)),
                    "icon": config.icon_dir("filter_reset.svg"),
                    "action": "FilterResetAction",
                },
                {
                    "title": translate("Search"),
                    "shortcut": "Ctrl+F",
                    "tabs": list(range(5)),
                    "icon": config.icon_dir("search.svg"),
                    "action": "SearchAction",
                },
                {
                    "type": "separator",
                },
                {
                    "title": translate("Start Preparation"),
                    "shortcut": "Ctrl+1",
                    "action": "ToStartPreparationAction",
                },
                {
                    "title": translate("Race Results"),
                    "shortcut": "Ctrl+2",
                    "action": "ToRaceResultsAction",
                },
                {
                    "title": translate("Groups"),
                    "shortcut": "Ctrl+3",
                    "action": "ToGroupsAction",
                },
                {
                    "title": translate("Courses"),
                    "shortcut": "Ctrl+4",
                    "action": "ToCoursesAction",
                },
                {
                    "title": translate("Teams"),
                    "shortcut": "Ctrl+5",
                    "action": "ToTeamsAction",
                },
                {
                    "title": translate("Logs"),
                    "shortcut": "Ctrl+6",
                    "action": "ToLogsAction",
                },
            ],
        },
        {
            "title": translate("Start Preparation"),
            "actions": [
                {
                    "title": translate("Start Preparation"),
                    "shortcut": "F6",
                    "action": "StartPreparationAction",
                },
                {"title": translate("Guess courses"), "action": "GuessCoursesAction"},
                {
                    "title": translate("Guess corridors"),
                    "action": "GuessCorridorsAction",
                },
                {
                    "title": translate("Relay number assign mode"),
                    "tabs": [0],
                    "action": "RelayNumberAction",
                },
                {
                    "title": translate("Start time change"),
                    "action": "StartTimeChangeAction",
                },
                {
                    "title": translate("Handicap start time"),
                    "action": "StartHandicapAction",
                },
                {"title": translate("Clone relay legs"), "action": "RelayCloneAction"},
                {
                    "title": translate("Use bib as card number"),
                    "action": "CopyBibToCardNumber",
                },
                {
                    "title": translate("Use card number as bib"),
                    "action": "CopyCardNumberToBib",
                },
                {
                    "title": translate("Marked route course generation"),
                    "action": "MarkedRouteCourseGeneration",
                },
                {
                    "title": translate("Extract person middle name"),
                    "action": "ExtractPersonMiddleName",
                },
            ],
        },
        {
            "title": translate("Race"),
            "actions": [
                {
                    "title": translate("Manual finish"),
                    "shortcut": "F3",
                    "icon": config.icon_dir("flag.svg"),
                    "action": "ManualFinishAction",
                },
                {
                    "title": translate("Add SPORTident result"),
                    "shortcut": "F7",
                    "action": "AddSPORTidentResultAction",
                },
            ],
        },
        {
            "title": translate("Results"),
            "actions": [
                {
                    "title": translate("Create report"),
                    "shortcut": "Ctrl+P",
                    "action": "CreateReportAction",
                },
                {
                    "title": translate("Split printout"),
                    "shortcut": "Ctrl+L",
                    "action": "SplitPrintoutAction",
                },
                {
                    "type": "separator",
                },
                {
                    "title": translate("Rechecking"),
                    "shortcut": "Ctrl+R",
                    "action": "RecheckingAction",
                },
                {
                    "title": translate("Find group by punches"),
                    "tabs": [1],
                    "shortcut": "Ctrl+G",
                    "action": "GroupFinderAction",
                },
                {
                    "title": translate("Penalty calculation"),
                    "action": "PenaltyCalculationAction",
                },
                {
                    "title": translate("Penalty removing"),
                    "action": "PenaltyRemovingAction",
                },
                {
                    "title": translate("Change status"),
                    "shortcut": "F4",
                    "tabs": [1],
                    "action": "ChangeStatusAction",
                },
                {
                    "title": translate("Set DNS numbers"),
                    "action": "SetDNSNumbersAction",
                },
                {
                    "title": translate("Control time change"),
                    "action": "ControlTimeChangeAction",
                },
                {"title": translate("Delete CP"), "action": "CPDeleteAction"},
                {"title": translate("Delete Split"), "action": "SplitDeleteAction"},
                {"title": translate("Merge results"), "action": "MergeResultsAction"},
                {
                    "title": translate("Assign result by bib"),
                    "action": "AssignResultByBibAction",
                },
                {
                    "title": translate("Assign result by card number"),
                    "action": "AssignResultByCardNumberAction",
                },
            ],
        },
        {
            "title": translate("Service"),
            "actions": [
                {
                    "title": translate("on/off SPORTident readout"),
                    "icon": config.icon_dir("sportident.png"),
                    "shortcut": "F8",
                    "action": "SPORTidentReadoutAction",
                },
                {
                    "title": translate("on/off Sportiduino readout"),
                    "icon": config.icon_dir("sportiduino.png"),
                    "action": "SportiduinoReadoutAction",
                },
                {
                    "title": translate("on/off SFR readout"),
                    "icon": config.icon_dir("sfr.png"),
                    "action": "SFRReadoutAction",
                },
                {
                    "title": translate("on/off RFID Impinj readout"),
                    "icon": config.icon_dir("rfid_impinj.png"),
                    "action": "ImpinjReadoutAction",
                },
                {
                    "title": translate("on/off SRPid readout"),
                    "icon": config.icon_dir("srpid.png"),
                    "action": "SrpidReadoutAction",
                },
                {
                    "title": translate("Teamwork"),
                    "icon": config.icon_dir("network.svg"),
                    "actions": [
                        {
                            "title": translate("Send selected"),
                            "shortcut": "Ctrl+Shift+K",
                            "tabs": list(range(5)),
                            "action": "TeamworkSendAction",
                        },
                        {
                            "type": "separator",
                        },
                        {
                            "title": translate("On/Off"),
                            "action": "TeamworkEnableAction",
                        },
                    ],
                },
                {
                    "title": translate("Telegram"),
                    "actions": [
                        {
                            "title": translate("Send results"),
                            "tabs": [1],
                            "action": "TelegramSendAction",
                        },
                    ],
                },
                {
                    "title": translate("Online"),
                    "actions": [
                        {
                            "title": translate("Send selected"),
                            "shortcut": "Ctrl+K",
                            "tabs": [0, 1, 2, 3, 4],
                            "action": "OnlineSendAction",
                        },
                    ],
                },
            ],
        },
        {
            "title": translate("Options"),
            "actions": [
                {
                    "title": translate("Timekeeping settings"),
                    "shortcut": "F9",
                    "icon": config.icon_dir("stopwatch.svg"),
                    "action": "TimekeepingSettingsAction",
                },
                {
                    "title": translate("Teamwork"),
                    "icon": config.icon_dir("network.svg"),
                    "action": "TeamworkSettingsAction",
                },
                {
                    "title": translate("Printer settings"),
                    "icon": config.icon_dir("printer.svg"),
                    "action": "PrinterSettingsAction",
                },
                {
                    "title": translate("Live"),
                    "icon": config.icon_dir("live.svg"),
                    "action": "LiveSettingsAction",
                },
                {
                    "title": translate("Telegram"),
                    "action": "TelegramSettingsAction",
                },
                {
                    "title": translate("Rent cards"),
                    "action": "RentCardsAction",
                },
            ],
        },
        {
            "title": translate("Help"),
            "actions": [
                {
                    "title": translate("About"),
                    "shortcut": "F1",
                    "action": "AboutAction",
                },
                {"title": translate("Check updates"), "action": "CheckUpdatesAction"},
            ],
        },
    ]

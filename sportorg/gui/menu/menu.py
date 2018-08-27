from sportorg import config
from sportorg.language import _


def menu_list():
    return [
        {
            'title': _('File'),
            'actions': [
                {
                    'title': _('New'),
                    'shortcut': 'Ctrl+N',
                    'icon': config.icon_dir('file.svg'),
                    'action': 'NewAction'
                },
                {
                    'title': _('Save'),
                    'shortcut': 'Ctrl+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAction'
                },
                {
                    'title': _('Open'),
                    'shortcut': 'Ctrl+O',
                    'icon': config.icon_dir('folder.svg'),
                    'action': 'OpenAction'
                },
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.svg'),
                    'action': 'SaveAsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'icon': config.icon_dir('settings.svg'),
                    'action': 'SettingsAction'
                },
                {
                    'title': _('Event Settings'),
                    'icon': config.icon_dir('form.svg'),
                    'action': 'EventSettingsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Import'),
                    'actions': [
                        {
                            'title': _('Import from SportOrg file'),
                            'action': 'ImportSportOrgAction'
                        },
                        {
                            'title': _('CSV Winorient'),
                            'icon': config.icon_dir('csv.svg'),
                            'action': 'CSVWinorientImportAction'
                        },
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientImportAction'
                        },
                        {
                            'title': _('Ocad txt v8'),
                            'action': 'OcadTXTv8ImportAction'
                        },
                        {
                            'title': _('IOF xml'),
                            'action': 'IOFEntryListImportAction'
                        },
                    ]
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientExportAction'
                        },
                        # {
                        #     'title': 'IOF xml',
                        #     'actions': [
                        #         {
                        #             'title': _('ResultList'),
                        #             'action': 'IOFResultListExportAction'
                        #         }
                        #     ]
                        # },
                    ]
                }
            ]
        },
        {
            'title': _('Edit'),
            'actions': [
                {
                    'title': _('Add object'),
                    'shortcut': 'insert',
                    'icon': config.icon_dir('add.svg'),
                    'action': 'AddObjectAction'
                },
                {
                    'title': _('Delete'),
                    'shortcut': 'Del',
                    'icon': config.icon_dir('delete.svg'),
                    'action': 'DeleteAction'
                },
                {
                    'title': _('Text exchange'),
                    'action': 'TextExchangeAction'
                }
            ]
        },
        {
            'title': _('View'),
            'actions': [
                {
                    'title': _('Refresh'),
                    'icon': config.icon_dir('refresh.svg'),
                    'shortcut': 'F5',
                    'action': 'RefreshAction'
                },
                {
                    'title': _('Filter'),
                    'shortcut': 'F2',
                    'icon': config.icon_dir('filter.svg'),
                    'action': 'FilterAction'
                },
                {
                    'title': _('Search'),
                    'shortcut': 'Ctrl+F',
                    'icon': config.icon_dir('search.svg'),
                    'action': 'SearchAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': 'ToStartPreparationAction'
                },
                {
                    'title': _('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': 'ToRaceResultsAction'
                },
                {
                    'title': _('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': 'ToGroupsAction'
                },
                {
                    'title': _('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': 'ToCoursesAction'
                },
                {
                    'title': _('Teams'),
                    'shortcut': 'Ctrl+5',
                    'action': 'ToTeamsAction'
                }
            ]
        },
        {
            'title': _('Start Preparation'),
            'actions': [
                {
                    'title': _('Start Preparation'),
                    'action': 'StartPreparationAction'
                },
                {
                    'title': _('Guess courses'),
                    'action': 'GuessCoursesAction'
                },
                {
                    'title': _('Guess corridors'),
                    'action': 'GuessCorridorsAction'
                },
                {
                    'title': _('Relay number assign mode'),
                    'action': 'RelayNumberAction'
                },
                {
                    'title': _('Start time change'),
                    'action': 'StartTimeChangeAction'
                },
                {
                    'title': _('Handicap start time'),
                    'action': 'StartHandicapAction'
                },
                {
                    'title': _('Use bib as card number'),
                    'action': 'CopyBibToCardNumber'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Start list'),
                    'shortcut': 'Ctrl+Shift+P',
                    'action': 'StartListAction'
                },
            ]
        },
        {
            'title': _('Race'),
            'actions': [
                {
                    'title': _('Manual finish'),
                    'shortcut': 'F3',
                    'icon': config.icon_dir('flag.svg'),
                    'action': 'ManualFinishAction'
                },
                {
                    'title': _('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction'
                },
            ]
        },
        {
            'title': _('Results'),
            'actions': [
                {
                    'title': _('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': 'CreateReportAction'
                },
                {
                    'title': _('Split printout'),
                    'shortcut': 'Ctrl+L',
                    'action': 'SplitPrintoutAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': 'RecheckingAction'
                },
                {
                    'title': _('Penalty calculation'),
                    'action': 'PenaltyCalculationAction'
                },
                {
                    'title': _('Penalty removing'),
                    'action': 'PenaltyRemovingAction'
                },
                {
                    'title': _('Change status'),
                    'shortcut': 'F4',
                    'action': 'ChangeStatusAction'
                },
                {
                    'title': _('Set DNS numbers'),
                    'action': 'SetDNSNumbersAction'
                },
                {
                    'title': _('Delete CP'),
                    'action': 'CPDeleteAction'
                },
                {
                    'title': _('Assign result by bib'),
                    'action': 'AssignResultByBibAction'
                },
                {
                    'title': _('Assign result by card number'),
                    'action': 'AssignResultByCardNumberAction'
                },
            ]
        },
        {
            'title': _('Service'),
            'actions': [
                {
                    'title': _('on/off SPORTident readout'),
                    'icon': config.icon_dir('sportident.png'),
                    'action': 'SPORTidentReadoutAction'
                },
                {
                    'title': _('on/off Sportiduino readout'),
                    'icon': config.icon_dir('sportiduino.png'),
                    'action': 'SportiduinoReadoutAction'
                },
                {
                    'title': _('on/off SFR readout'),
                    'icon': config.icon_dir('sfr.png'),
                    'action': 'SFRReadoutAction'
                },
                {
                    'title': _('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'actions': [
                        {
                            'title': _('Send selected'),
                            'shortcut': 'Ctrl+K',
                            'action': 'TeamworkSendAction'
                        },
                        {
                            'type': 'separator',
                        },
                        {
                            'title': _('On/Off'),
                            'action': 'TeamworkEnableAction'
                        }
                    ]
                },
                {
                    'title': _('Telegram'),
                    'actions': [
                        {
                            'title': _('Send results'),
                            'action': 'TelegramSendAction'
                        },
                    ]
                },
            ]
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('Timekeeping settings'),
                    'icon': config.icon_dir('stopwatch.svg'),
                    'action': 'TimekeepingSettingsAction'
                },
                {
                    'title': _('Teamwork'),
                    'icon': config.icon_dir('network.svg'),
                    'action': 'TeamworkSettingsAction'
                },
                {
                    'title': _('Printer settings'),
                    'icon': config.icon_dir('printer.svg'),
                    'action': 'PrinterSettingsAction'
                },
                {
                    'title': _('Live'),
                    'icon': config.icon_dir('live.svg'),
                    'action': 'LiveSettingsAction'
                },
                {
                    'title': _('Telegram'),
                    'action': 'TelegramSettingsAction'
                }
            ]
        },
        {
            'title': _('Help'),
            'actions': [
                {
                    'title': _('About'),
                    'shortcut': 'F1',
                    'action': 'AboutAction'
                },
                {
                    'title': _('Check updates'),
                    'action': 'CheckUpdatesAction'
                },
                {
                    'title': _('Testing'),
                    'show': config.DEBUG and not config.is_executable(),
                    'shortcut': 'F10',
                    'action': 'TestingAction',
                    'debug': True
                }
            ]
        },
    ]

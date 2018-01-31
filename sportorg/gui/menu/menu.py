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
                    'icon': config.icon_dir('file.png'),
                    'action': 'NewAction'
                },
                {
                    'title': _('Save'),
                    'shortcut': 'Ctrl+S',
                    'icon': config.icon_dir('save.png'),
                    'action': 'SaveAction'
                },
                {
                    'title': _('Open'),
                    'shortcut': 'Ctrl+O',
                    'icon': config.icon_dir('folder.png'),
                    'action': 'OpenAction'
                },
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.png'),
                    'action': 'SaveAsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'icon': config.icon_dir('settings.png'),
                    'action': 'SettingsAction'
                },
                {
                    'title': _('Event Settings'),
                    'action': 'EventSettingsAction'
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Import'),
                    'actions': [
                        {
                            'title': _('CSV Winorient'),
                            'icon': config.icon_dir('csv.png'),
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
                    'icon': config.icon_dir('plus.png'),
                    'action': 'AddObjectAction'
                },
                {
                    'title': _('Delete'),
                    'shortcut': 'Del',
                    'icon': config.icon_dir('delete.png'),
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
                    'icon': config.icon_dir('refresh.png'),
                    'shortcut': 'F5',
                    'action': 'RefreshAction'
                },
                {
                    'title': _('Filter'),
                    'shortcut': 'F2',
                    'icon': config.icon_dir('filter.png'),
                    'action': 'FilterAction'
                },
                {
                    'title': _('Search'),
                    'shortcut': 'Ctrl+F',
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
                    'type': 'separator',
                },
                {
                    'title': _('Start list'),
                    'action': 'StartListAction'
                },
                {
                    'title': _('Team list'),
                    'action': 'TeamListAction'
                },
                {
                    'title': _('Start times'),
                    'action': 'StartTimesAction'
                },
                {
                    'title': _('Print Bib'),
                    'action': 'PrintBibAction'
                }
            ]
        },
        {
            'title': _('Race'),
            'actions': [
                {
                    'title': _('Manual finish'),
                    'shortcut': 'F3',
                    'icon': config.icon_dir('flag.png'),
                    'action': 'ManualFinishAction'
                },
                {
                    'title': _('on/off SPORTident readout'),
                    'icon': config.icon_dir('sportident.png'),
                    'action': 'SPORTidentReadoutAction'
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
                    'title': _('Create team results report'),
                    'action': 'CreateTeamResultsReportAction'
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
                    'title': _('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction'
                }
            ]
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('Timekeeping settings'),
                    'action': 'TimekeepingSettingsAction'
                },
                {
                    'title': _('Printer settings'),
                    'icon': config.icon_dir('print.png'),
                    'action': 'PrinterSettingsAction'
                },
                {
                    'title': _('Live'),
                    'actions': [
                        {
                            'title': _('Settings'),
                            'action': 'LiveSettingsAction'
                        },
                        {
                            'title': _('Send start list'),
                            'action': 'LiveSendStartListAction'
                        },
                        {
                            'title': _('Send results'),
                            'action': 'LiveSendResultsAction'
                        },
                        {
                            'title': _('Resend results'),
                            'action': 'LiveResendResultsAction'
                        },
                    ]
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
                # {
                #     'title': _('Testing'),
                #     'show': config.DEBUG and not config.is_executable(),
                #     'shortcut': 'F10',
                #     'action': 'TestingAction'
                # }
            ]
        },
    ]

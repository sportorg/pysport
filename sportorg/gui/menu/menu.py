from sportorg.language import _


def menu_list():
    return [
        {
            'title': _('File'),
            'actions': [
                {'title': _('New'), 'shortcut': 'Ctrl+N', 'action': 'NewAction'},
                {'title': _('Save'), 'shortcut': 'Ctrl+S', 'action': 'SaveAction'},
                {'title': _('Open'), 'shortcut': 'Ctrl+O', 'action': 'OpenAction'},
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'action': 'SaveAsAction',
                },
                {'type': 'separator',},
                {
                    'title': _('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'action': 'SettingsAction',
                },
                {'title': _('Event Settings'), 'action': 'EventSettingsAction'},
                {'type': 'separator',},
                {
                    'title': _('Import'),
                    'actions': [
                        {
                            'title': _('Import from SportOrg file'),
                            'action': 'ImportSportOrgAction',
                        },
                        {
                            'title': _('CSV Winorient'),
                            'action': 'CSVWinorientImportAction',
                        },
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientImportAction',
                        },
                        {'title': _('Ocad txt v8'), 'action': 'OcadTXTv8ImportAction'},
                        {'title': _('IOF xml'), 'action': 'IOFEntryListImportAction'},
                    ],
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': _('WDB Winorient'),
                            'action': 'WDBWinorientExportAction',
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
                    ],
                },
            ],
        },
        {
            'title': _('Edit'),
            'actions': [
                {
                    'title': _('Add object'),
                    'tabs': list(range(5)),
                    'shortcut': ['insert', 'i'],
                    'action': 'AddObjectAction',
                },
                {
                    'title': _('Delete'),
                    'shortcut': 'Del',
                    'tabs': list(range(5)),
                    'action': 'DeleteAction',
                },
                {
                    'title': _('Copy'),
                    'shortcut': 'Ctrl+C',
                    'tabs': list(range(5)),
                    'action': 'CopyAction',
                },
                {
                    'title': _('Duplicate'),
                    'shortcut': 'Ctrl+D',
                    'tabs': list(range(5)),
                    'action': 'DuplicateAction',
                },
                {'title': _('Text exchange'), 'action': 'TextExchangeAction'},
                {'title': _('Mass edit'), 'tabs': [0], 'action': 'MassEditAction'},
            ],
        },
        {
            'title': _('View'),
            'actions': [
                {'title': _('Refresh'), 'shortcut': 'F5', 'action': 'RefreshAction'},
                {
                    'title': _('Filter'),
                    'shortcut': 'F2',
                    'tabs': [0, 1],
                    'action': 'FilterAction',
                },
                {
                    'title': _('Search'),
                    'shortcut': 'Ctrl+F',
                    'tabs': list(range(5)),
                    'action': 'SearchAction',
                },
                {'type': 'separator',},
                {
                    'title': _('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': 'ToStartPreparationAction',
                },
                {
                    'title': _('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': 'ToRaceResultsAction',
                },
                {
                    'title': _('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': 'ToGroupsAction',
                },
                {
                    'title': _('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': 'ToCoursesAction',
                },
                {'title': _('Teams'), 'shortcut': 'Ctrl+5', 'action': 'ToTeamsAction'},
            ],
        },
        {
            'title': _('Start Preparation'),
            'actions': [
                {'title': _('Start Preparation'), 'action': 'StartPreparationAction'},
                {'title': _('Guess courses'), 'action': 'GuessCoursesAction'},
                {'title': _('Guess corridors'), 'action': 'GuessCorridorsAction'},
                {
                    'title': _('Relay number assign mode'),
                    'tabs': [0],
                    'action': 'RelayNumberAction',
                },
                {'title': _('Start time change'), 'action': 'StartTimeChangeAction'},
                {'title': _('Handicap start time'), 'action': 'StartHandicapAction'},
                {'title': _('Clone relay legs'), 'action': 'RelayCloneAction'},
                {'title': _('Use bib as card number'), 'action': 'CopyBibToCardNumber'},
                {'title': _('Use card number as bib'), 'action': 'CopyCardNumberToBib'},
            ],
        },
        {
            'title': _('Race'),
            'actions': [
                {
                    'title': _('Manual finish'),
                    'shortcut': 'F3',
                    'action': 'ManualFinishAction',
                },
                {
                    'title': _('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction',
                },
            ],
        },
        {
            'title': _('Results'),
            'actions': [
                {
                    'title': _('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': 'CreateReportAction',
                },
                {
                    'title': _('Split printout'),
                    'shortcut': 'Ctrl+L',
                    'action': 'SplitPrintoutAction',
                },
                {'type': 'separator',},
                {
                    'title': _('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': 'RecheckingAction',
                },
                {
                    'title': _('Find group by punches'),
                    'tabs': [1],
                    'action': 'GroupFinderAction',
                },
                {
                    'title': _('Penalty calculation'),
                    'action': 'PenaltyCalculationAction',
                },
                {'title': _('Penalty removing'), 'action': 'PenaltyRemovingAction'},
                {
                    'title': _('Change status'),
                    'shortcut': 'F4',
                    'tabs': [1],
                    'action': 'ChangeStatusAction',
                },
                {'title': _('Set DNS numbers'), 'action': 'SetDNSNumbersAction'},
                {'title': _('Delete CP'), 'action': 'CPDeleteAction'},
                {
                    'title': _('Assign result by bib'),
                    'action': 'AssignResultByBibAction',
                },
                {
                    'title': _('Assign result by card number'),
                    'action': 'AssignResultByCardNumberAction',
                },
            ],
        },
        {
            'title': _('Service'),
            'actions': [
                {
                    'title': _('on/off SPORTident readout'),
                    'shortcut': 'F8',
                    'action': 'SPORTidentReadoutAction',
                },
                {
                    'title': _('on/off Sportiduino readout'),
                    'action': 'SportiduinoReadoutAction',
                },
                {'title': _('on/off SFR readout'), 'action': 'SFRReadoutAction'},
                {
                    'title': _('Teamwork'),
                    'actions': [
                        {
                            'title': _('Send selected'),
                            'shortcut': 'Ctrl+K',
                            'tabs': list(range(5)),
                            'action': 'TeamworkSendAction',
                        },
                        {'type': 'separator',},
                        {'title': _('On/Off'), 'action': 'TeamworkEnableAction'},
                    ],
                },
                {
                    'title': _('Telegram'),
                    'actions': [
                        {
                            'title': _('Send results'),
                            'tabs': [1],
                            'action': 'TelegramSendAction',
                        },
                    ],
                },
            ],
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('Timekeeping settings'),
                    'action': 'TimekeepingSettingsAction',
                },
                {'title': _('Teamwork'), 'action': 'TeamworkSettingsAction'},
                {'title': _('Printer settings'), 'action': 'PrinterSettingsAction'},
                {'title': _('Live'), 'action': 'LiveSettingsAction'},
                {'title': _('Telegram'), 'action': 'TelegramSettingsAction'},
                {'title': _('Rent cards'), 'action': 'RentCardsAction'},
            ],
        },
        {
            'title': _('Help'),
            'actions': [
                {'title': _('About'), 'shortcut': 'F1', 'action': 'AboutAction'},
                {'title': _('Check updates'), 'action': 'CheckUpdatesAction'},
            ],
        },
    ]

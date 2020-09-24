from sportorg.language import translate


def menu_list():
    return [
        {
            'title': translate('File'),
            'actions': [
                {
                    'title': translate('New'),
                    'shortcut': 'Ctrl+N',
                    'action': 'NewAction',
                },
                {
                    'title': translate('Save'),
                    'shortcut': 'Ctrl+S',
                    'action': 'SaveAction',
                },
                {
                    'title': translate('Open'),
                    'shortcut': 'Ctrl+O',
                    'action': 'OpenAction',
                },
                {
                    'title': translate('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'action': 'SaveAsAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'action': 'SettingsAction',
                },
                {'title': translate('Event Settings'), 'action': 'EventSettingsAction'},
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Import'),
                    'actions': [
                        {
                            'title': translate('Import from SportOrg file'),
                            'action': 'ImportSportOrgAction',
                        },
                        {
                            'title': translate('CSV Winorient'),
                            'action': 'CSVWinorientImportAction',
                        },
                        {
                            'title': translate('WDB Winorient'),
                            'action': 'WDBWinorientImportAction',
                        },
                        {
                            'title': translate('Ocad txt v8'),
                            'action': 'OcadTXTv8ImportAction',
                        },
                        {
                            'title': translate('IOF xml'),
                            'action': 'IOFEntryListImportAction',
                        },
                    ],
                },
                {
                    'title': translate('Export'),
                    'actions': [
                        {
                            'title': translate('WDB Winorient'),
                            'action': 'WDBWinorientExportAction',
                        },
                        # {
                        #     'title': 'IOF xml',
                        #     'actions': [
                        #         {
                        #             'title': translate('ResultList'),
                        #             'action': 'IOFResultListExportAction'
                        #         }
                        #     ]
                        # },
                    ],
                },
            ],
        },
        {
            'title': translate('Edit'),
            'actions': [
                {
                    'title': translate('Add object'),
                    'tabs': list(range(5)),
                    'shortcut': ['insert', 'i'],
                    'action': 'AddObjectAction',
                },
                {
                    'title': translate('Delete'),
                    'shortcut': 'Del',
                    'tabs': list(range(5)),
                    'action': 'DeleteAction',
                },
                {
                    'title': translate('Copy'),
                    'shortcut': 'Ctrl+C',
                    'tabs': list(range(5)),
                    'action': 'CopyAction',
                },
                {
                    'title': translate('Duplicate'),
                    'shortcut': 'Ctrl+D',
                    'tabs': list(range(5)),
                    'action': 'DuplicateAction',
                },
                {'title': translate('Text exchange'), 'action': 'TextExchangeAction'},
                {
                    'title': translate('Mass edit'),
                    'tabs': [0],
                    'action': 'MassEditAction',
                },
            ],
        },
        {
            'title': translate('View'),
            'actions': [
                {
                    'title': translate('Refresh'),
                    'shortcut': 'F5',
                    'action': 'RefreshAction',
                },
                {
                    'title': translate('Filter'),
                    'shortcut': 'F2',
                    'tabs': [0, 1],
                    'action': 'FilterAction',
                },
                {
                    'title': translate('Search'),
                    'shortcut': 'Ctrl+F',
                    'tabs': list(range(5)),
                    'action': 'SearchAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': 'ToStartPreparationAction',
                },
                {
                    'title': translate('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': 'ToRaceResultsAction',
                },
                {
                    'title': translate('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': 'ToGroupsAction',
                },
                {
                    'title': translate('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': 'ToCoursesAction',
                },
                {
                    'title': translate('Teams'),
                    'shortcut': 'Ctrl+5',
                    'action': 'ToTeamsAction',
                },
            ],
        },
        {
            'title': translate('Start Preparation'),
            'actions': [
                {
                    'title': translate('Start Preparation'),
                    'action': 'StartPreparationAction',
                },
                {'title': translate('Guess courses'), 'action': 'GuessCoursesAction'},
                {
                    'title': translate('Guess corridors'),
                    'action': 'GuessCorridorsAction',
                },
                {
                    'title': translate('Relay number assign mode'),
                    'tabs': [0],
                    'action': 'RelayNumberAction',
                },
                {
                    'title': translate('Start time change'),
                    'action': 'StartTimeChangeAction',
                },
                {
                    'title': translate('Handicap start time'),
                    'action': 'StartHandicapAction',
                },
                {'title': translate('Clone relay legs'), 'action': 'RelayCloneAction'},
                {
                    'title': translate('Use bib as card number'),
                    'action': 'CopyBibToCardNumber',
                },
                {
                    'title': translate('Use card number as bib'),
                    'action': 'CopyCardNumberToBib',
                },
            ],
        },
        {
            'title': translate('Race'),
            'actions': [
                {
                    'title': translate('Manual finish'),
                    'shortcut': 'F3',
                    'action': 'ManualFinishAction',
                },
                {
                    'title': translate('Add SPORTident result'),
                    'action': 'AddSPORTidentResultAction',
                },
            ],
        },
        {
            'title': translate('Results'),
            'actions': [
                {
                    'title': translate('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': 'CreateReportAction',
                },
                {
                    'title': translate('Split printout'),
                    'shortcut': 'Ctrl+L',
                    'action': 'SplitPrintoutAction',
                },
                {
                    'type': 'separator',
                },
                {
                    'title': translate('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': 'RecheckingAction',
                },
                {
                    'title': translate('Find group by punches'),
                    'tabs': [1],
                    'action': 'GroupFinderAction',
                },
                {
                    'title': translate('Penalty calculation'),
                    'action': 'PenaltyCalculationAction',
                },
                {
                    'title': translate('Penalty removing'),
                    'action': 'PenaltyRemovingAction',
                },
                {
                    'title': translate('Change status'),
                    'shortcut': 'F4',
                    'tabs': [1],
                    'action': 'ChangeStatusAction',
                },
                {
                    'title': translate('Set DNS numbers'),
                    'action': 'SetDNSNumbersAction',
                },
                {'title': translate('Delete CP'), 'action': 'CPDeleteAction'},
                {
                    'title': translate('Assign result by bib'),
                    'action': 'AssignResultByBibAction',
                },
                {
                    'title': translate('Assign result by card number'),
                    'action': 'AssignResultByCardNumberAction',
                },
            ],
        },
        {
            'title': translate('Service'),
            'actions': [
                {
                    'title': translate('on/off SPORTident readout'),
                    'shortcut': 'F8',
                    'action': 'SPORTidentReadoutAction',
                },
                {
                    'title': translate('on/off Sportiduino readout'),
                    'action': 'SportiduinoReadoutAction',
                },
                {
                    'title': translate('on/off SFR readout'),
                    'action': 'SFRReadoutAction',
                },
                {
                    'title': translate('Telegram'),
                    'actions': [
                        {
                            'title': translate('Send results'),
                            'tabs': [1],
                            'action': 'TelegramSendAction',
                        },
                    ],
                },
            ],
        },
        {
            'title': translate('Options'),
            'actions': [
                {
                    'title': translate('Timekeeping settings'),
                    'action': 'TimekeepingSettingsAction',
                },
                {
                    'title': translate('Printer settings'),
                    'action': 'PrinterSettingsAction',
                },
                {'title': translate('Live'), 'action': 'LiveSettingsAction'},
                {'title': translate('Telegram'), 'action': 'TelegramSettingsAction'},
                {'title': translate('Rent cards'), 'action': 'RentCardsAction'},
            ],
        },
        {
            'title': translate('Help'),
            'actions': [
                {
                    'title': translate('About'),
                    'shortcut': 'F1',
                    'action': 'AboutAction',
                },
                {'title': translate('Check updates'), 'action': 'CheckUpdatesAction'},
            ],
        },
    ]

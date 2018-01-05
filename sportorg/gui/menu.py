import os

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
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
                    'action': GlobalAccess().get_main_window().create_file
                },
                {
                    'title': _('Save'),
                    'shortcut': 'Ctrl+S',
                    'icon': config.icon_dir('save.png'),
                    'action': GlobalAccess().get_main_window().save_file
                },
                {
                    'title': _('Open'),
                    'shortcut': 'Ctrl+O',
                    'icon': config.icon_dir('folder.png'),
                    'action': GlobalAccess().get_main_window().open_file_dialog
                },
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.png'),
                    'action': GlobalAccess().get_main_window().save_file_as
                },
                {
                    'title': _('Open Recent'),
                    'actions': menu_recent_files()
                },
                {
                    'type': 'separator',
                },
                # {
                #     'title': _('New Race'),
                #     'action': lambda: print('...')
                # },
                {
                    'title': _('Settings'),
                    'shortcut': 'Ctrl+Alt+S',
                    'icon': config.icon_dir('settings.png'),
                    'action': GlobalAccess().get_main_window().settings_dialog
                },
                {
                    'title': _('Event Settings'),
                    'action': GlobalAccess().get_main_window().event_settings_dialog
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
                            'action': GlobalAccess().get_main_window().import_wo_csv
                        },
                        {
                            'title': _('WDB Winorient'),
                            'action': GlobalAccess().get_main_window().import_wo_wdb
                        },
                        {
                            'title': _('Ocad txt v8'),
                            'action': GlobalAccess().get_main_window().import_txt_v8
                        },
                    ]
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': _('WDB Winorient'),
                            'action': GlobalAccess().get_main_window().export_wo_wdb
                        },
                        {
                            'title': 'IOF xml',
                            'actions': [
                                {
                                    'title': _('ResultList'),
                                    'action': GlobalAccess().get_main_window().export_iof_result_list
                                }
                            ]
                        },
                    ]
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Exit'),
                    'action': lambda: exit(0)
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
                    'action': GlobalAccess().get_main_window().create_object
                },
                {
                    'title': _('Delete'),
                    'shortcut': 'Del',
                    'icon': config.icon_dir('delete.png'),
                    'action': GlobalAccess().get_main_window().delete_object
                },
                {
                    'title': _('Text exchange'),
                    'action': GlobalAccess().get_main_window().text_exchange
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
                    'action': GlobalAccess().get_main_window().refresh
                },
                {
                    'title': _('Filter'),
                    'shortcut': 'F2',
                    'icon': config.icon_dir('filter.png'),
                    'action': GlobalAccess().get_main_window().filter_dialog
                },
                {
                    'title': _('Search'),
                    'shortcut': 'Ctrl+F',
                    'action': GlobalAccess().get_main_window().search_dialog
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('Start Preparation'),
                    'shortcut': 'Ctrl+1',
                    'action': lambda: GlobalAccess().get_main_window().select_tab(0)
                },
                {
                    'title': _('Race Results'),
                    'shortcut': 'Ctrl+2',
                    'action': lambda: GlobalAccess().get_main_window().select_tab(1)
                },
                {
                    'title': _('Groups'),
                    'shortcut': 'Ctrl+3',
                    'action': lambda: GlobalAccess().get_main_window().select_tab(2)
                },
                {
                    'title': _('Courses'),
                    'shortcut': 'Ctrl+4',
                    'action': lambda: GlobalAccess().get_main_window().select_tab(3)
                },
                {
                    'title': _('Teams'),
                    'shortcut': 'Ctrl+5',
                    'action': lambda: GlobalAccess().get_main_window().select_tab(4)
                }
            ]
        },
        {
            'title': _('Start Preparation'),
            'actions': [
                {
                    'title': _('Start Preparation'),
                    'action': GlobalAccess().get_main_window().start_preparation_dialog
                },
                # {
                #     'title': _('Number Change'),
                #     'action': GlobalAccess().get_main_window().number_change_dialog
                # },
                {
                    'title': _('Guess courses'),
                    'action': GlobalAccess().get_main_window().guess_courses
                },
                {
                    'title': _('Guess corridors'),
                    'action': GlobalAccess().get_main_window().guess_corridors
                },
                {
                    'title': _('Relay number assign mode'),
                    'action': GlobalAccess().get_main_window().relay_number_assign
                },
                {
                    'title': _('Start time change'),
                    'action': GlobalAccess().get_main_window().start_time_change
                },
                {
                    'title': _('Start list'),
                    'action': GlobalAccess().get_main_window().create_start_protocol_dialog
                },
                {
                    'title': _('Team list'),
                    'action': GlobalAccess().get_main_window().create_team_protocol_dialog
                },
                {
                    'title': _('Start times'),
                    'action': GlobalAccess().get_main_window().create_chess_dialog
                },
                {
                    'title': _('Print Bib'),
                    'action': GlobalAccess().get_main_window().bib_report_dialog
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
                    'action': GlobalAccess().get_main_window().manual_finish
                },
                {
                    'title': _('on/off SPORTident readout'),
                    'icon': config.icon_dir('sportident.png'),
                    'action': GlobalAccess().get_main_window().sportident_connect
                },
            ]
        },
        {
            'title': _('Results'),
            'actions': [
                {
                    'title': _('Create report'),
                    'shortcut': 'Ctrl+P',
                    'action': GlobalAccess().get_main_window().report_dialog
                },
                {
                    'title': _('Split printout'),
                    'action': GlobalAccess().get_main_window().split_printout_selected
                },
                {
                    'title': _('Rechecking'),
                    'shortcut': 'Ctrl+R',
                    'action': GlobalAccess().rechecking
                },
                {
                    'title': _('Add SPORTident result'),
                    'action': GlobalAccess().get_main_window().sportident_result
                }
            ]
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('SPORTident settings'),
                    'icon': config.icon_dir('sportident.png'),
                    'action': GlobalAccess().get_main_window().sportident_settings_dialog
                },
                {
                    'title': _('Printer settings'),
                    'icon': config.icon_dir('print.png'),
                    'action': GlobalAccess().get_main_window().print_settings_dialog
                }
            ]
        },
        {
            'title': _('Help'),
            'actions': [
                # {
                #     'title': _('Help'),
                #     'action': lambda: print('...')
                # },
                {
                    'title': _('About'),
                    'shortcut': 'F1',
                    'action': GlobalAccess().get_main_window().about_dialog
                },
                {
                    'title': _('Testing'),
                    'show': config.DEBUG and not config.is_executable(),
                    'shortcut': 'F10',
                    'action': GlobalAccess().get_main_window().testing
                }
            ]
        },
    ]


def menu_recent_files():
    def open_file(f):
        return lambda: GlobalAccess().get_main_window().open_file(f)
    result = []
    for file in GlobalAccess().get_main_window().recent_files:
        result.append({
            'title': os.path.basename(file),
            'status_tip': '{} {}'.format(_('Open'), file),
            'action': open_file(file)
        })
    return result

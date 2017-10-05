from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.language import _
from sportorg import config

from sportorg.app.modules.winorient import winorient
from sportorg.app.modules.sportident import sportident
from sportorg.app.modules.ocad import ocad


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
                    'action': GlobalAccess().get_main_window().open_file
                },
                {
                    'title': _('Save As'),
                    'shortcut': 'Ctrl+Shift+S',
                    'icon': config.icon_dir('save.png'),
                    'action': GlobalAccess().get_main_window().save_file_as
                },
                {
                    'title': _('Open Recent'),
                    'action': lambda: print('...')
                },
                {
                    'type': 'separator',
                },
                {
                    'title': _('New Race'),
                    'action': lambda: print('...')
                },
                {
                    'title': _('Settings'),
                    'action': lambda: print('...')
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
                            'action': winorient.import_wo_csv
                        },
                        {
                            'title': _('WDB Winorient'),
                            'action': winorient.import_wo_wdb
                        },
                        {
                            'title': _('Ocad txt v8'),
                            'action': ocad.import_txt_v8_action
                        },
                    ]
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': _('WDB Winorient'),
                            'action': winorient.export_wo_wdb
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
                    'action': GlobalAccess().get_main_window().create_object
                },
                {
                    'title': _('Delete'),
                    'action': GlobalAccess().get_main_window().delete_object
                }
            ]
        },
        {
            'title': _('Start Preparation'),
            'actions': [
                {
                    'title': _('Filter'),
                    'action': GlobalAccess().get_main_window().filter_dialog
                },
                {
                    'title': _('Start Preparation'),
                    'action': GlobalAccess().get_main_window().start_preparation
                },
                {
                    'title': _('Number Change'),
                    'action': GlobalAccess().get_main_window().number_change
                },
                {
                    'title': _('Guess courses'),
                    'action': GlobalAccess().get_main_window().guess_courses
                },
                {
                    'title': _('Guess corridors'),
                    'action': GlobalAccess().get_main_window().guess_corridors
                },
                {
                    'title': _('Create start'),
                    'action': GlobalAccess().get_main_window().create_start_protocol
                },
                {
                    'title': _('Create chess'),
                    'action': GlobalAccess().get_main_window().create_chess
                }
            ]
        },
        {
            'title': _('Race'),
            'actions': [
                {
                    'title': _('Manual finish'),
                    'shortcut': 'F3',
                    'action': GlobalAccess().get_main_window().manual_finish
                }
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
                    'action': GlobalAccess().get_main_window().split_printout
                }
            ]
        },
        {
            'title': _('Tools'),
            'actions': [
            ]
        },
        {
            'title': _('Service'),
            'actions': [
            ]
        },
        {
            'title': _('Options'),
            'actions': [
                {
                    'title': _('SPORTident settings'),
                    'action': sportident.sportident_settings
                },
                {
                    'title': _('Printer settings'),
                    'action': GlobalAccess().get_main_window().print_settings
                }
            ]
        },
        {
            'title': _('Help'),
            'actions': [
                {
                    'title': _('Help'),
                    'action': lambda: print('...')
                },
                {
                    'title': _('About'),
                    'action': lambda: print('...')
                }
            ]
        },
    ]

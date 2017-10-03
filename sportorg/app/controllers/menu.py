from sportorg.app.controllers.global_access import GlobalAccess
from sportorg.language import _
from sportorg import config


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
                    'icon': config.icon_dir('save.png'),
                    'action': GlobalAccess().get_main_window().open_file
                },
                {
                    'title': _('New Race'),
                    'action': lambda: print('...')
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
                    'title': _('Settings'),
                    'action': lambda: print('...')
                },
                {
                    'title': _('Event Settings'),
                    'action': GlobalAccess().get_main_window().event_settings_dialog
                },
                {
                    'title': _('Import'),
                    'actions': [
                        {
                            'title': 'Wdb',
                            'action': lambda: print('...')
                        },
                    ]
                },
                {
                    'title': _('Export'),
                    'actions': [
                        {
                            'title': 'Wdb',
                            'action': lambda: print('...')
                        },
                    ]
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
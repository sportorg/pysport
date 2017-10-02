def menu_list():
    return [
        {
            'title': 'File',
            'actions': [
                {
                    'title': 'Open',
                    'action': lambda: print('open')
                },
                {
                    'title': 'Save',
                    'action': lambda: print('save')
                },
                {
                    'title': 'Import',
                    'actions': [
                        {
                            'title': 'Wdb',
                            'action': lambda: print('wdb')
                        },
                        {
                            'title': 'Wdb1',
                            'action': lambda: print('wdb1')
                        },
                    ]
                }
            ],
        },
        {
            'title': 'Edit',
            'actions': [
                {
                    'title': 'Open',
                    'action': lambda: print('open')
                },
                {
                    'title': 'Save',
                    'action': lambda: print('save')
                }
            ],
        },
    ]

from sportorg.gui.menu.actions import ActionFactory


class Factory(object):
    def __init__(self, app):
        self._actions = {}
        for key, cls in ActionFactory.actions.items():
            self._actions[key] = cls(app)

    def get_action(self, key):
        if key in self._actions:
            return self._actions[key]
        return lambda: print('...')

    def execute(self, key):
        self.get_action(key)()

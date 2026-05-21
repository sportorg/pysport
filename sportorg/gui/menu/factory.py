from sportorg.gui.menu.actions import ActionFactory
from sportorg.modules.plugins.manager import (
    PLUGIN_MENU_ACTION_PREFIX,
    plugin_client,
)


class Factory:
    def __init__(self, app):
        self._app = app
        self._actions = {}
        for key, cls in ActionFactory.actions.items():
            self._actions[key] = cls(app)

    def get_action(self, key):
        if isinstance(key, str) and key.startswith(PLUGIN_MENU_ACTION_PREFIX):
            return lambda: plugin_client.execute_menu_action(key, self._app)
        if key in self._actions:
            return self._actions[key]
        return lambda: ...

    def execute(self, key):
        self.get_action(key)()

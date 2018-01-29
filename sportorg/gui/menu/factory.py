

class Factory:
    def __init__(self, app):
        self.actions = [

        ]
        self._map = {}
        for action in self.actions:
            action.app = app
            self._map[action.__class__.__name__] = action.execute

    def get_action(self, key):
        if key in self._map:
            return self._map[key]

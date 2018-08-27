import logging


class Script:
    def __init__(self, config=None, actions=None, content=None):
        self.config = config or {}
        self.actions = actions
        self.content = content
        self.logger = logging.root

    def is_type(self, value):
        if 'type' in self.config:
            return str(self.config['type']) == value
        return False

    def is_enabled(self):
        if 'enabled' in self.config:
            return bool(self.config['enabled'])
        return True

    def call(self, action, *args, **kwargs):
        try:
            if action in self.actions:
                return self.actions[action](*args, **kwargs)
        except Exception as e:
            self.logger.error(str(e))


SCRIPTS = []

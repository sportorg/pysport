

class Factory:
    def __init__(self):
        self.actions = [

        ]
        self.map = {}
        for action in self.actions:
            self.map[action.__class__.name] = action.execute

    def get_actions(self):
        pass

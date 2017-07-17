class GlobalAccess(object):
    __instance = None
    main_window = None

    def __new__(cls):
        if GlobalAccess.__instance is None:
            GlobalAccess.__instance = object.__new__(cls)
        return GlobalAccess.__instance

    def set_main_window(self, window):
        self.main_window = window

    def get_main_window(self):
        return self.main_window


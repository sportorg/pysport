import traceback

from .event import event


class App:

    def __init__(self, options=None):
        self.options = options
        self.file = None

    def create_file(self, file_name):
        if file_name is not '':
            self.file = file_name
            event('create_file', file_name)

    def open_file(self, file_name):
        if file_name is not '':
            self.file = file_name
            event('open_file', file_name)
            self.backup('load')

    def save_file(self):
        if self.file is not None:
            event('save_file', self.file)
            self.backup('dump')

    def get_settings(self):
        pass

    def save_settings(self):
        pass

    def backup(self, e, func=None):
        """
        
        :param func: tuple or function
        :param e: event: 'load' or 'dump'
        :return: 
        """
        if func is not None:
            if not isinstance(func, tuple):
                return func(self.file)
            else:
                cls = func[0]
                method_name = func[1]
                try:
                    method = getattr(cls, method_name)
                    return method(self.file)
                except AttributeError:
                    print("Class `{}` does not implement `{}`".format(cls.__class__.__name__, method_name))
                    return

        if self.file is None:
            return

        """
        :event: load or dump
        """
        event(e, self.file)

from abc import ABCMeta, abstractmethod
from importlib import import_module
import os

from sportorg import config


class Plugin:
    __metaclass__ = ABCMeta

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def version(self):
        pass

    @abstractmethod
    def configs(self):
        pass

    @abstractmethod
    def handlers(self):
        pass


def run_plugins():
    modules = ['sportorg', 'app', 'plugins']
    path = config.base_dir(*modules)
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        file_path = os.path.join(full_path, p + '.py')

        if os.path.isdir(full_path) and os.path.isfile(file_path):
            import_module('.'.join(modules) + '.' + p + '.' + p)

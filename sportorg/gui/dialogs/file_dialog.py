import os

from PyQt5.QtWidgets import QFileDialog

from sportorg.modules.configs.configs import ConfigFile, Config


def get_open_file_name(caption='', filter_text=''):
    result = QFileDialog.getOpenFileName(None, caption, get_default_dir(), filter_text)[0]
    if result:
        set_default_dir(os.path.dirname(os.path.abspath(result)))
    return result


def get_save_file_name(caption='', filter_text='', file_name=''):
    result = QFileDialog.getSaveFileName(None, caption, os.path.join(get_default_dir(), file_name), filter_text)[0]
    if result:
        set_default_dir(os.path.dirname(os.path.abspath(result)))
    return result


def get_default_dir():
    if get_conf().has_section(ConfigFile.DIRECTORY):
        return get_conf().get(ConfigFile.DIRECTORY, 'dialog_default_dir', fallback='')
    return ''


def set_default_dir(directory):
    # FIXME
    get_conf()[ConfigFile.DIRECTORY] = {
        'dialog_default_dir': directory
    }


def get_conf():
    return Config().parser

import os
import platform
import re

try:
    from PySide6.QtWidgets import QFileDialog
except ModuleNotFoundError:
    from PySide2.QtWidgets import QFileDialog

from sportorg import settings


def get_existing_directory(caption="", dir=""):
    result = QFileDialog.getExistingDirectory(None, caption, dir)
    return result


def get_open_file_name(caption="", filter_text="", set_dir=True):
    result = QFileDialog.getOpenFileName(None, caption, get_default_dir(), filter_text)[
        0
    ]
    if result and set_dir:
        set_default_dir(os.path.dirname(os.path.abspath(result)))
    return result


def get_save_file_name(caption="", filter_text="", file_name=""):
    if platform.system() == "Linux":
        match = re.search(r"\*(\.\w+)", filter_text)
        if match:
            suffix = match.group(1)
            if not file_name.endswith(suffix):
                file_name += suffix
    result = QFileDialog.getSaveFileName(
        None, caption, os.path.join(get_default_dir(), file_name), filter_text
    )[0]
    if result:
        set_default_dir(os.path.dirname(os.path.abspath(result)))
    return result


def get_default_dir():
    return settings.SETTINGS.window_dialog_path


def set_default_dir(directory):
    settings.SETTINGS.window_dialog_path = directory

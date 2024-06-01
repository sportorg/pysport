import sys

from cx_Freeze import Executable, setup

from sportorg import config

base = None
if sys.platform == "win32":
    base = "Win32GUI"

include_files = [
    config.LOCALE_DIR,
    config.TEMPLATE_DIR,
    config.IMG_DIR,
    config.SOUND_DIR,
    config.base_dir("LICENSE"),
    config.base_dir("changelog.md"),
    config.base_dir("changelog_ru.md"),
    config.base_dir("configs"),
    config.STYLE_DIR,
]
includes = ["atexit", "codecs", "playsound", "pyImpinj"]
excludes = ["Tkinter", "unittest", "test", "pydoc"]

options = {
    "build_exe": {
        "includes": includes,
        "excludes": excludes,
        "packages": ["idna", "requests", "encodings", "asyncio", "pywinusb"],
        "include_files": include_files,
        "zip_include_packages": ["PySide6"],
        "optimize": 2,
        'include_msvcr': True,
    }
}

executables = [
    Executable(
        "SportOrg.pyw",
        base=base,
        icon=config.icon_dir("sportorg.ico"),
        shortcut_dir=config.NAME.lower(),
        copyright="GNU GENERAL PUBLIC LICENSE {}".format(config.NAME),
    )
]

setup(
    name=config.NAME,
    version=config.VERSION.file,
    description=config.NAME,
    options=options,
    executables=executables,
    packages=[],
)

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
    config.COMMIT_VERSION_FILE,
]
includes = ["atexit", "codecs", "playsound3", "pyImpinj"]
excludes = ["Tkinter", "unittest", "test", "pydoc"]

build_exe_options = {
    "includes": includes,
    "excludes": excludes,
    "packages": ["idna", "requests", "encodings", "asyncio", "pywinusb"],
    "include_files": include_files,
    "zip_include_packages": ["PySide6"],
    "optimize": 2,
    "include_msvcr": True,
    "silent": 1,
}

bdist_msi_options = {
    "all_users": False,
    "data": {
        "Shortcut": [
            (
                "DesktopShortcut",  # Shortcut
                "DesktopFolder",  # Directory
                config.NAME,  # Name
                "TARGETDIR",  # Component
                "[TARGETDIR]SportOrg.exe",  # Target
                None,  # Arguments
                None,  # Description
                None,  # Hotkey
                None,  # Icon
                None,  # IconIndex
                None,  # ShowCmd
                "TARGETDIR",  # WkDir
            ),
        ]
    },
}

options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options}

executables = [
    Executable(
        "SportOrg.pyw",
        base=base,
        icon=config.icon_dir("sportorg.ico"),
        copyright="GNU GENERAL PUBLIC LICENSE {}".format(config.NAME),
    )
]

setup(
    name=config.NAME,
    version=config.VERSION,
    description=config.NAME,
    options=options,
    executables=executables,
)

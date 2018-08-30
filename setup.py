import sys
from cx_Freeze import setup, Executable
from sportorg import config

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

include_files = [config.LOCALE_DIR, config.TEMPLATE_DIR, config.IMG_DIR, config.SOUND_DIR, config.base_dir('LICENSE'),
                 config.base_dir('changelog.md'), config.base_dir('changelog_ru.md'),
                 config.base_dir('status_comments.txt'), config.base_dir('regions.txt'), config.base_dir('names.txt'),
                 config.base_dir('ranking.txt')]
includes = ['atexit', 'codecs']
excludes = ['Tkinter']

options = {
    'build_exe': {
        'includes': includes,
        'excludes': excludes,
        "packages": ['idna', 'requests', 'encodings', 'asyncio', 'pywinusb/hid'],
        'include_files': include_files
    }
}

executables = [
    Executable(
        'SportOrg.pyw',
        base=base,
        icon=config.ICON,
        shortcutDir=config.NAME.lower(),
        copyright='MIT Licence {}'.format(config.NAME)
    )
]

setup(
    name=config.NAME,
    version=config.VERSION.file,
    description=config.NAME,
    options=options,
    executables=executables
)

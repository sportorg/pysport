from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = dict(packages=["os"], excludes=["tkinter"])

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = {
    Executable(
        'SportOrg.pyw',
        base=base,
        icon="img/icon/sportorg.ico",
        targetName="SportOrg.exe"
    )
}

setup(
    name='SportOrg',
    version='0.1',
    description='',
    options=dict(build_exe=build_options),
    executables=executables, requires=['PyQt5']
)

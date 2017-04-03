# SportOrg

### Build
`pyinstaller.exe --onefile -windowed --icon=img/icon/sportorg.ico SportOrg.pyw`

For build, you need `pyinstaller`

### Packages

- [sireader](https://pypi.python.org/pypi/sireader/1.0.1)
- [peewee](http://docs.peewee-orm.com/en/latest/peewee/quickstart.html)

Install packages
```
pip install package-name

pip install sireader
```

### Struct

```
<sportorg>/
    data/
    docs/
    img/
        icon/
    languages/
        <lang>/
            LC_MESSAGES/
                sportorg.mo
                sportorg.po
```

! For work need all folders

### Project

```
SportOrg.pyw - point of entry;
app.py - main class;
appframe.py - tabs.
```

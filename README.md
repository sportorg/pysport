# SportOrg

### Build
`pyinstaller.exe --onefile -windowed --icon=img/icon/sportorg.ico SportOrg.pyw`

Для билда нужно установить пакет `pyinstaller`

### Packages

- [sireader](https://pypi.python.org/pypi/sireader/1.0.1)
- [peewee](http://docs.peewee-orm.com/en/latest/peewee/quickstart.html)

Установка
```
pip install package-name

pip install sireader
```

### Структура

```
data/
docs/
img/icon/
languages/<lang>/LC_MESSAGES/sportorg.po
```

! Для работы требуются все папки

### Проект

```
SportOrg.pyw - точка входа в программу
app.py - основной класс
appframe.py - окна вкладок в программе
```
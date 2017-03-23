# SportOrg

### Build
`pyinstaller.exe --onefile -windowed --icon=img/icon/sportorg.ico SportOrg.pyw`

Для билда нужно установить пакет `pyinstaller`

### Packages

- sireader
- peewee

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

! Для работы требуется все папки

### Проект

```
SportOrg.pyw - точка входа в программу
app.py - основной класс
appframe.py - окна вкладок в программе
```
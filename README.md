#SportOrg

build
`pyinstaller.exe --onefile -windowed --icon=img/icon/stopwatch.ico SportOrg.pyw`

Для билда нужно установить пакет `pyinstaller`

###Packages

- sireader
- peewee

Установка
```
pip install package-name

pip install sireader
```


### Проект

```
SportOrg.pyw - точка входа в программу
app.py - основной класс
appframe.py - окна вкладок в программе
```
[![Build Status](https://api.travis-ci.org/sportorg/pysport.svg?branch=dev)](https://api.travis-ci.org/sportorg/pysport)

# SportOrg

### Packages

- PyQt5
- [sireader](https://pypi.python.org/pypi/sireader/1.0.1)
- jinja2
- [polib](http://polib.readthedocs.io/en/latest/quickstart.html)
- xmlschema
- cx_Freeze
- requests

Install packages
```commandline
pip install package-name

pip install sireader
```

or

```commandline
pip install -r requirements.txt
```

Run

```commandline
python SportOrg.pyw
```

### Struct

```
<sportorg>/
    data/
    docs/
    log/
    templates/
    test/
    img/
        icon/
    languages/
        <lang>/
            LC_MESSAGES/
                sportorg.po
    sportorg/
        core/
        gui/
        models/
        modules/
        libs/
        utils/
```

![Mainwindow sportorg](img/mainwindow.png)

![Dialogedit sportorg](img/dialogedit.png)
![Result sportorg](img/result.png)
![Bibprintout sportorg](img/bibprintout.png)


### build

#### cx_Freeze

`python setup.py build`

"""
Parse SportOrg HTML report (containing full json)

"""
import os.path
import string
from io import open
from random import choices
from tempfile import gettempdir
from sportorg.gui.dialogs.file_dialog import get_open_file_name
from sportorg.gui.dialogs.sportorg_import_dialog import SportOrgImportDialog
from sportorg.language import translate
from sportorg.modules.backup.json import get_races_from_file


def recovery():

    file_name = get_open_file_name(
        translate('Open SportOrg HTML file'), translate('SportOrg HTML report (*.html)'), False
    )

    text_file = open(file_name, "r", encoding="utf-8")
    lines = text_file.readlines()

    for line in lines:
        if line.find("var race = {\"courses\":") > -1:
            json = line.strip()[11:-1]

            # save json to tmp file and op[en with standard import action
            tmp_filename = os.path.join(gettempdir(),
                                        "sportorg_" + ''.join(choices(string.ascii_letters, k=10)) + ".json")
            temp_file = open(tmp_filename, "w")
            temp_file.write(json)
            temp_file.close()

            with open(tmp_filename) as f:
                attr = get_races_from_file(f)
            SportOrgImportDialog(*attr).exec_()

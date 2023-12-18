"""
Parse SportOrg HTML report (containing full json)

"""
import os.path
import string
from io import open
from random import choices
from tempfile import gettempdir


def recovery(file_name):

    with open(file_name, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if line.find("var race = {\"courses\":") > -1:
                json = line.strip()[11:-1]

                # save json to tmp file and op[en with standard import action
                tmp_filename = os.path.join(
                    gettempdir(),
                    'sportorg_'
                    + ''.join(choices(string.ascii_letters, k=10))
                    + '.json',
                )
                temp_file = open(tmp_filename, 'w')
                temp_file.write(json)
                temp_file.close()
                return tmp_filename
    return None

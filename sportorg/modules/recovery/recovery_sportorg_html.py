"""
Parse SportOrg HTML report (containing full json)

"""

import logging
import os.path
import string
from io import open
from random import choices
from tempfile import gettempdir
from sportorg.utils.text import detect_encoding


def recovery(file_name: str) -> str:
    encoding = detect_encoding(file_name)
    with open(file_name, "r", encoding=encoding) as f:
        for line in f.readlines():
            if line.find('var race = {"courses":') > -1:
                json = line.strip()[11:-1]

                # save json to tmp file and op[en with standard import action
                tmp_filename = os.path.join(
                    gettempdir(),
                    f"sportorg_{''.join(choices(string.ascii_letters, k=10))}.json",
                )
                with open(tmp_filename, "w", encoding="utf-8") as temp_file:
                    temp_file.write(json)

                return tmp_filename
    logging.info("SportOrg HTML objects not found in file")
    return ""

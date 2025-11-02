"""
Parse SportOrg HTML report (containing full json)

"""

import base64
import gzip
import io
import logging
import os.path
import string
from random import choices
from tempfile import gettempdir

from sportorg.utils.text import detect_encoding


def recovery(file_name: str) -> str:
    encoding = detect_encoding(file_name)
    with open(file_name, "r", encoding=encoding) as f:
        for line in f.readlines():
            if line.find('var race = "') > -1:
                data = line.strip()[12:-2]

                compressed_data = base64.b64decode(data)
                with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                    json = gz.read().decode("utf-8")

                return save_to_tmp_file(json)

            if line.find('var race = {"courses":') > -1:
                json = line.strip()[11:-1]

                return save_to_tmp_file(json)
    logging.info("SportOrg HTML objects not found in file")
    return ""


def save_to_tmp_file(json: str) -> str:
    tmp_filename = os.path.join(
        gettempdir(),
        f"sportorg_{''.join(choices(string.ascii_letters, k=10))}.json",
    )
    with open(tmp_filename, "w", encoding="utf-8") as temp_file:
        temp_file.write(json)
    return tmp_filename

# sfrexporter.py
import logging
from datetime import datetime

from sportorg.language import translate
from sportorg.models import memory
from sportorg.models.memory import ResultStatus

def export_sfr_data(destination: str, export_type='file'):
    race = memory.race()
    if not race:
        logging.error(translate("No race data found"))
        return False
    if export_type == 'file':
        from sportorg.modules.sfr.sfrxexporter import export_sfrx
        return export_sfrx(destination)
    return False
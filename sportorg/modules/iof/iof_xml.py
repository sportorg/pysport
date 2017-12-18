from datetime import datetime

from sportorg import config
from sportorg.libs.iof.iof import ResultList
from sportorg.models.memory import race


def export_result_list(file):
    obj = race()
    result_list = ResultList()
    result_list.iof.creator = config.NAME
    result_list.iof.create_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    result_list.event.name.value = obj.data.name
    if obj.data.start_time is not None:
        result_list.event.start_time.date.value = obj.data.start_time.strftime("%Y-%m-%d")
        result_list.event.start_time.time.value = obj.data.start_time.strftime("%H:%M:%S")
    # TODO
    result_list.write(open(file, 'wb'), xml_declaration=True, encoding='UTF-8')

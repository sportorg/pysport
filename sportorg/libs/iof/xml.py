import xml.etree.ElementTree as ET
from .utils import indent


def write(elem, file, **kwargs):
    """
        write(elem, file, encoding='utf-8', xml_declaration=True)
    
    """
    indent(elem)
    return ET.ElementTree(elem).write(file, **kwargs)

import os
from pathlib import Path


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MrMap.settings_docker")

import django
django.setup()
from resourceNew.xmlmapper.ogc.capabilities.factory import WebService

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = Path(current_dir + '/../test_data/wms/dwd_wms_1.3.0.xml')

    xml_service = WebService(path)  # deserialized xml to XmlObject


    xml_service.convert_to_model()
    i=0

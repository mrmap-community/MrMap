import os
from pathlib import Path


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MrMap.settings_docker")

import django
django.setup()
from eulxml import xmlmap
from resourceNew.xmlmapper.ogc.capabilities.service_wms import Wms130Service, Wms111Service

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = current_dir + '/../test_data/wms/dwd_wms_1.1.1.xml'
    service = xmlmap.load_xmlobject_from_file(filename=path, xmlclass=Wms111Service)
    i=0

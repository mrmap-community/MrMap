import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MrMap.settings_docker")

import django
django.setup()

if __name__ == '__main__':
    from requests import Request
    from resourceNew.services.register_service import RegisterOgcServiceService

    request = Request(method="GET",
                      url="https://maps.dwd.de/geoserver/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities")
    db_service = RegisterOgcServiceService.register_service_from_remote(request=request)

    i=0

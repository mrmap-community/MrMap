from requests import Session, Request

from MrMap.settings import PROXIES
from resourceNew.builder.db_wms_service import WmsDbBuilder, WmsDbDirector
from resourceNew.ows_client.request_builder import WebService


def register_service_from_remote(request: Request):
    session = Session()
    session.proxies = PROXIES
    response = session.send(request.prepare())

    parsed_service = WebService(xml=response.content)

    builder = WmsDbBuilder(proto_service=parsed_service)
    director = WmsDbDirector()
    director.builder = builder

    director.build_service()

    db_service = builder.service
    
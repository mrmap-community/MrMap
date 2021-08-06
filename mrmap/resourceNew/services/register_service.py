import time
from abc import ABC, abstractmethod

from resourceNew.builder.db_wms_service import WmsDbBuilder, WmsDbDirector
from resourceNew.xmlmapper.ogc.capabilities.factory import OgcServiceXml
from requests import Session, Request
from django.conf import settings


class RegisterOgcService(ABC):

    @classmethod
    def register_service_from_remote(cls, request: Request, session: Session = None):
        if not session:
            _session = Session()
            _session.proxies = settings.PROXIES

        time_start = time.time()
        response = _session.send(request.prepare())

        settings.ROOT_LOGGER.debug(f"request took {time.time() - time_start}ms")

        time_start = time.time()
        proto_service = OgcServiceXml(xml=response.content)
        settings.ROOT_LOGGER.debug(f"parsing xml took {time.time() - time_start}ms")

        return cls._build(proto_service=proto_service)

    @classmethod
    def register_service_from_local(cls, db_service):
        time_start = time.time()
        proto_service = OgcServiceXml(xml=db_service.xml_backup_string)
        settings.ROOT_LOGGER.debug(f"parsing xml took {time.time() - time_start}ms")

        return cls._build(proto_service=proto_service, db_service=db_service)

    @classmethod
    @abstractmethod
    def _build(cls, proto_service, db_service=None):
        raise NotImplementedError


class RegisterOgcWmsService(RegisterOgcService):

    @classmethod
    def _build(cls, proto_service, db_service=None):
        builder = WmsDbBuilder(proto_service=proto_service, db_service=db_service)
        director = WmsDbDirector()
        director.builder = builder

        time_start = time.time()
        director.build_service()
        settings.ROOT_LOGGER.debug(f"build service took {time.time()-time_start}ms")

        time_start = time.time()
        db_service = builder.service
        settings.ROOT_LOGGER.debug(f"fetching service took {time.time()-time_start}ms")
        return db_service

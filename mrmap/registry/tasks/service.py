from urllib import parse

from celery import shared_task, states
from celery.canvas import group
from django.conf import settings
from django.db import transaction
from notify.tasks import BackgroundProcessBased
from ows_lib.xml_mapper.utils import get_parsed_service
from registry.exceptions.metadata import UnknownMetadataKind
from registry.models import CatalogueService, WebFeatureService, WebMapService
from registry.models.metadata import (DatasetMetadata,
                                      WebFeatureServiceRemoteMetadata,
                                      WebMapServiceRemoteMetadata)
from registry.models.security import (WebFeatureServiceAuthentication,
                                      WebMapServiceAuthentication)
from requests import Request, Session
from rest_framework.reverse import reverse
from urllib3.exceptions import MaxRetryError


@shared_task(
    bind=True,
    queue="default",
    base=BackgroundProcessBased,
    priority=10,
)
def build_ogc_service(self, get_capabilities_url: str, collect_metadata_records: bool, service_auth_pk: None, **kwargs):
    try:

        self.update_state(state=states.STARTED, meta={
            'done': 0, 'total': 3, 'phase': 'download capabilities document...'})
        self.update_background_process()

        auth = None
        if service_auth_pk:
            match parse.parse_qs(parse.urlsplit(get_capabilities_url).query)['SERVICE'][0].lower():
                case 'wms':
                    auth = WebMapServiceAuthentication.objects.get(
                        id=service_auth_pk)
                case 'wfs':
                    auth = WebFeatureServiceAuthentication.objects.get(
                        id=service_auth_pk)
                case _:
                    auth = None

        session = Session()
        session.proxies = settings.PROXIES
        request = Request(method="GET",
                          url=get_capabilities_url,
                          auth=auth.get_auth_for_request() if auth else None)
        response = session.send(request.prepare())

        self.update_state(state=states.STARTED, meta={
            'done': 1, 'total': 3, 'phase': 'parse capabilities document...'})
        self.update_background_process('parse capabilities document...')

        parsed_service = get_parsed_service(capabilities_xml=response.content)

        self.update_state(state=states.STARTED, meta={
            'done': 2, 'total': 3, 'phase': 'persisting service...'})
        self.update_background_process('persisting service...')

        with transaction.atomic():
            # create all needed database objects and rollback if any error occours to avoid from database inconsistence
            if parsed_service.service_type.name == "wms":
                db_service = WebMapService.capabilities.create(
                    parsed_service=parsed_service)
                resource_name = "WebMapService"
                self_url = reverse(
                    viewname='registry:wms-detail', args=[db_service.pk])
            elif parsed_service.service_type.name == "wfs":
                db_service = WebFeatureService.capabilities.create(
                    parsed_service=parsed_service)
                resource_name = "WebFeatureService"
                self_url = reverse(
                    viewname='registry:wfs-detail', args=[db_service.pk])
            elif parsed_service.service_type.name == "csw":
                db_service = CatalogueService.capabilities.create(
                    parsed_service=parsed_service)
                resource_name = "CatalogueService"
                self_url = reverse(
                    viewname='registry:csw-detail', args=[db_service.pk])
            else:
                self.update_background_process(
                    'Unknown XML mapper detected. Only WMS, WFS and CSW services are allowed.')
                raise NotImplementedError(
                    "Unknown XML mapper detected. Only WMS, WFS and CSW services are allowed.")

            if auth:
                auth.service = db_service
                auth.save()

        self.update_state(state=states.SUCCESS, meta={'done': 3, 'total': 3})

        # TODO: use correct Serializer and render the json:api as result
        return_dict = {
            "data": {
                "type": resource_name,
                "id": str(db_service.pk),
                "links": {
                    "self": self_url
                }
            }
        }
    except Exception as e:
        self.update_state(state=states.FAILURE)
        self.update_background_process(str(e))
        settings.ROOT_LOGGER.exception(e, stack_info=True, exc_info=True)
        raise

    if collect_metadata_records:
        remote_metadata_list = None
        if isinstance(db_service, WebMapService):
            remote_metadata_list = WebMapServiceRemoteMetadata.objects.filter(
                service__pk=db_service.pk)
        elif isinstance(db_service, WebFeatureService):
            remote_metadata_list = WebFeatureServiceRemoteMetadata.objects.filter(
                service__pk=db_service.pk)
        if remote_metadata_list:
            # TODO: create Task Result objects for all child threads, so we can append them directly to the Background Process to avoid
            #  progress bar melting after increasement
            job = group([fetch_remote_metadata_xml.s(remote_metadata.pk, db_service.__class__.__name__, **kwargs)
                        for remote_metadata in remote_metadata_list])
            group_result = job.apply_async()
            group_result.save()

            data = return_dict["data"]
            data.update({
                "meta": {
                    "collect_metadata_records_job_id": str(group_result.id)
                }
            })
            self.update_background_process(
                'collecting metadata records...', db_service)
        else:
            self.update_background_process('successed', db_service)

    else:
        self.update_background_process('successed', db_service)

    return return_dict


@shared_task(bind=True,
             queue="download",
             base=BackgroundProcessBased,
             priority=10,
             autoretry_for=(MaxRetryError,),
             # retry after 30 minutes
             retry_kwargs={'max_retries': 2, 'countdown': 1800}
             )
def fetch_remote_metadata_xml(self, remote_metadata_id, class_name, **kwargs):
    self.update_state(state=states.STARTED, meta={
                      'done': 0, 'total': 1, 'phase': 'fetching remote document...'})
    self.update_background_process()

    remote_metadata = None
    if class_name == 'WebMapService':
        remote_metadata = WebMapServiceRemoteMetadata.objects.get(
            pk=remote_metadata_id)
    elif class_name == 'WebFeatureService':
        remote_metadata = WebFeatureServiceRemoteMetadata.objects.get(
            pk=remote_metadata_id)
    if not remote_metadata:
        return None
    try:
        remote_metadata.fetch_remote_content()
        self.update_state(state=states.STARTED, meta={'done': 1, 'total': 2})

        metadata_record = remote_metadata.create_metadata_instance()
        self.update_state(state=states.STARTED, meta={'done': 2, 'total': 2})
        return {
            "data": {
                "type": "DatasetMetadata" if isinstance(metadata_record, DatasetMetadata) else "ServiceMetadata",
                "id": f"{metadata_record.pk}",
                "links": {
                    "self": f"{reverse(viewname='registry:datasetmetadata-detail', args=[metadata_record.pk])}"
                }
            }
        }
    except MaxRetryError:
        # fetch_remote_content went wrong
        pass
    except UnknownMetadataKind:
        try:
            kind = remote_metadata.parsed_metadata._hierarchy_level
        except Exception:
            kind = 'unknown'
        settings.ROOT_LOGGER.warning(
            f"Can't handle RemoteMetadata with id: {remote_metadata.pk}, cause the kind '{kind}' is not supported.")

    except Exception as e:
        settings.ROOT_LOGGER.exception(
            f"RemoteMetadata id: {remote_metadata.pk}", e, stack_info=True, exc_info=True)
        raise

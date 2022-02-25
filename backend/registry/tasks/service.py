from urllib import parse

from celery import shared_task, states
from celery.canvas import group
from django.conf import settings
from django.db import transaction
from django_celery_results.models import TaskResult
from notify.models import BackgroundProcess, ProcessNameEnum
from registry.models import CatalougeService, WebFeatureService, WebMapService
from registry.models.metadata import (DatasetMetadata,
                                      WebFeatureServiceRemoteMetadata,
                                      WebMapServiceRemoteMetadata)
from registry.models.security import (WebFeatureServiceAuthentication,
                                      WebMapServiceAuthentication)
from registry.xmlmapper.ogc.capabilities import CswService as CswXmlMapper
from registry.xmlmapper.ogc.capabilities import Wfs200Service as WfsXmlMapper
from registry.xmlmapper.ogc.capabilities import WmsService as WmsXmlMapper
from registry.xmlmapper.ogc.capabilities import get_parsed_service
from requests import Request, Session
from rest_framework.reverse import reverse


@shared_task(
    bind=True,
    queue="default"
)
def build_ogc_service(self, get_capabilities_url: str, collect_metadata_records: bool, service_auth_pk: None, **kwargs):
    background_process: BackgroundProcess = BackgroundProcess.objects.create(
        process_type=ProcessNameEnum.REGISTERING.value,
        description=f'Register a new service with url {get_capabilities_url}',
        phase="download capabilities document...")
    self.update_state(state=states.STARTED, meta={
                      'done': 0, 'total': 3, 'phase': 'download capabilities document...'})
    if self.request and self.request.id:
        background_process.threads.add(
            *TaskResult.objects.filter(task_id=self.request.id))
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
    background_process.phase = 'parse capabilities document...'
    background_process.save()

    parsed_service = get_parsed_service(xml=response.content)

    self.update_state(state=states.STARTED, meta={
                      'done': 2, 'total': 3, 'phase': 'persisting service...'})
    background_process.phase = 'persisting service...'
    background_process.save()

    with transaction.atomic():
        # create all needed database objects and rollback if any error occours to avoid from database inconsistence
        # FIXME: pass the current user
        if isinstance(parsed_service, WmsXmlMapper):
            db_service = WebMapService.capabilities.create_from_parsed_service(
                parsed_service=parsed_service)
            resource_name = "WebMapService"
            self_url = reverse(
                viewname='registry:wms-detail', args=[db_service.pk])
        elif isinstance(parsed_service, WfsXmlMapper):
            db_service = WebFeatureService.capabilities.create_from_parsed_service(
                parsed_service=parsed_service)
            resource_name = "WebFeatureService"
            self_url = reverse(
                viewname='registry:wfs-detail', args=[db_service.pk])
        elif isinstance(parsed_service, CswXmlMapper):
            db_service = CatalougeService.capabilities.create_from_parsed_service(
                parsed_service=parsed_service)
            resource_name = "CatalougeService"
            self_url = reverse(
                viewname='registry:csw-detail', args=[db_service.pk])
        else:
            background_process.phase = 'Unknown XML mapper detected. Only WMS, WFS and CSW services are allowed.'
            background_process.save()
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
            job = group([fetch_remote_metadata_xml.s(remote_metadata.pk, db_service.__class__.__name__, background_process.pk, **kwargs)
                        for remote_metadata in remote_metadata_list])
            group_result = job.apply_async()
            group_result.save()

            data = return_dict["data"]
            data.update({
                "meta": {
                    "collect_metadata_records_job_id": str(group_result.id)
                }
            })
        background_process.phase = 'collecting metadata records...'
        background_process.save()
    else:
        background_process.phase = 'completed.'
        background_process.save()

    return return_dict


@shared_task(bind=True,
             queue="download")
def fetch_remote_metadata_xml(self, remote_metadata_id, class_name, background_process_id, **kwargs):
    self.update_state(state=states.STARTED, meta={
                      'done': 0, 'total': 1, 'phase': 'fetching remote document...'})
    if self.request and self.request.id and background_process_id:
        # TODO: see todo above... if we add the threads first we can dropt this code part...
        background_process: BackgroundProcess = BackgroundProcess.objects.get(
            pk=background_process_id)
        background_process.threads.add(
            *TaskResult.objects.filter(task_id=self.request.id))
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
    except Exception as e:
        settings.ROOT_LOGGER.exception(e, stack_info=True, exc_info=True)
        return None

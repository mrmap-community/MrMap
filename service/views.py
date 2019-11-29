import json

from django.contrib import messages
from django.contrib.gis.geos import Polygon, Point, GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from MapSkinner import utils
from MapSkinner.decorator import check_session, check_permission
from MapSkinner.messages import FORM_INPUT_INVALID, SERVICE_UPDATE_WRONG_TYPE, \
    SERVICE_REMOVED, SERVICE_UPDATED, MULTIPLE_SERVICE_METADATA_FOUND, \
    SECURITY_PROXY_ERROR_MULTIPLE_SECURED_OPERATIONS, SECURITY_PROXY_NOT_ALLOWED, SECURITY_PROXY_ERROR_BROKEN_URI, \
    SERVICE_NOT_FOUND, SECURITY_PROXY_ERROR_MISSING_REQUEST_TYPE, SERVICE_DISABLED, SERVICE_LAYER_NOT_FOUND, \
    SECURITY_PROXY_ERROR_PARAMETER
from MapSkinner.responses import BackendAjaxResponse, DefaultContext
from MapSkinner.settings import ROOT_URL
from service import tasks
from service.forms import ServiceURIForm
from service.helper import service_helper, update_helper
from service.helper.common_connector import CommonConnector
from service.helper.enums import ServiceEnum, MetadataEnum
from service.helper.iso.metadata_generator import MetadataGenerator
from service.helper.service_comparator import ServiceComparator
from service.models import Metadata, Layer, Service, FeatureType, Document, MetadataRelation, SecuredOperation, MimeType
from service.settings import MD_TYPE_SERVICE
from service.tasks import async_remove_service_task
from structure.models import User, Permission, PendingTask, Group
from users.helper import user_helper


@check_session
def index(request: HttpRequest, user: User, service_type=None):
    """ Renders an overview of all wms and wfs

    Args:
        request (HttpRequest): The incoming request
        user (User): The session user
        service_type: Indicates if only a special service type shall be displayed
    Returns:
         A view
    """
    template = "service_index.html"
    GET_params = request.GET

    # possible results per page values
    rpp_select = [5, 10, 15, 20, 50, 100, 200, 500, 1000]
    try:
        wms_page = int(GET_params.get("wmsp", 1))
        wfs_page = int(GET_params.get("wfsp", 1))
        results_per_page = int(GET_params.get("rpp", 5))
        if wms_page < 1 or wfs_page < 1 or results_per_page < 1:
            raise ValueError
        if results_per_page not in rpp_select:
            results_per_page = 5
    except ValueError as e:
        # since parameters could be changed directly in the uri, we need to make sure to avoid problems
        return redirect("service:index")

    # whether whole services or single layers should be displayed
    display_service_type = GET_params.get("q", None)  # s=services, l=layers
    is_root = True
    if display_service_type is not None:
        is_root = display_service_type != "l"

    # get services
    paginator_wms = None
    paginator_wfs = None
    if service_type is None or service_type == ServiceEnum.WMS.value:
        md_list_wms = Metadata.objects.filter(
            service__servicetype__name="wms",
            service__is_root=is_root,
            created_by__in=user.groups.all(),
            service__is_deleted=False,
        ).order_by("title")
        paginator_wms = Paginator(md_list_wms, results_per_page).get_page(wms_page)
    if service_type is None or service_type == ServiceEnum.WFS.value:
        md_list_wfs = Metadata.objects.filter(
            service__servicetype__name="wfs",
            created_by__in=user.groups.all(),
            service__is_deleted=False,
        ).order_by("title")
        paginator_wfs = Paginator(md_list_wfs, results_per_page).get_page(wfs_page)

    # get pending tasks
    pending_tasks = PendingTask.objects.filter(created_by__in=user.groups.all())
    for task in pending_tasks:
        task.description = json.loads(task.description)
    params = {
        "metadata_list_wms": paginator_wms,
        "metadata_list_wfs": paginator_wfs,
        "select_default": display_service_type,
        "only_type": service_type,
        "user": user,
        "rpp_select_options": rpp_select,
        "rpp": results_per_page,
        "pending_tasks": pending_tasks,
    }
    context = DefaultContext(request, params, user)
    return render(request=request, template_name=template, context=context.get_context())


@check_session
@check_permission(Permission(can_remove_service=True))
def remove(request: HttpRequest, user: User):
    """ Renders the remove form for a service

    Args:
        request(HttpRequest): The used request
        user (User): The performing user
    Returns:
        A rendered view
    """
    template = "overlay/remove_service_confirmation.html"
    service_id = request.GET.dict().get("id")
    confirmed = request.GET.dict().get("confirmed")
    service = get_object_or_404(Service, id=service_id)
    service_type = service.servicetype
    sub_elements = None
    if service_type.name == ServiceEnum.WMS.value:
        sub_elements = Layer.objects.filter(parent_service=service)
    elif service_type.name == ServiceEnum.WFS.value:
        sub_elements = service.featuretypes.all()
    metadata = get_object_or_404(Metadata, service=service)
    if confirmed == 'false':
        params = {
            "service": service,
            "metadata": metadata,
            "sub_elements": sub_elements,
        }
        html = render_to_string(template_name=template, context=params, request=request)
        return BackendAjaxResponse(html=html).get_response()
    else:
        # remove service and all of the related content
        user_helper.create_group_activity(metadata.created_by, user, SERVICE_REMOVED, metadata.title)

        # set service as deleted, so it won't be listed anymore in the index view until completely removed
        service.is_deleted = True
        service.save()

        # call removing as async task
        async_remove_service_task.delay(service_id)

        return BackendAjaxResponse(html="", redirect=ROOT_URL + "/service").get_response()

@check_session
@check_permission(Permission(can_activate_service=True))
def activate(request: HttpRequest, id: int, user:User):
    """ (De-)Activates a service and all of its layers

    Args:
        request:
    Returns:
         An Ajax response
    """
    # run activation async!
    pending_task = tasks.async_activate_service.delay(id, user.id)

    return redirect("service:index")


def get_service_metadata(request: HttpRequest, id: int):
    """ Returns the service metadata xml file for a given metadata id

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
    Returns:
         A HttpResponse containing the xml file
    """
    docs = []
    doc = None
    metadata = Metadata.objects.get(id=id)

    # check if the metadata record already has a service metadata document linked
    md_relations = MetadataRelation.objects.filter(
        metadata_from=metadata,
        metadata__is_active=True,
        metadata_to__metadata_type__type=MD_TYPE_SERVICE
    )
    for rel in md_relations:
        md_to = rel.metadata_to
        tmp_docs = Document.objects.filter(
            related_metadata=md_to,
        ).exclude(
            service_metadata_document=None
        )
        docs.extend(tmp_docs)

    if len(docs) > 1:
        # Something is odd, there are multiple service metadata documents for this metadata record
        messages.error(request, MULTIPLE_SERVICE_METADATA_FOUND)
        return redirect("service:detail", id)
    elif len(docs) == 1:
        # Everything is fine, we get the service metadata document
        doc = docs.pop().service_metadata_document
    else:
        if not metadata.is_active:
            return HttpResponse(content=SERVICE_DISABLED, status=423)
        # There is no service metadata document in the database, we need to create it during runtime
        generator = MetadataGenerator(id, MetadataEnum.SERVICE)
        doc = generator.generate_service_metadata()

    return HttpResponse(doc, content_type='application/xml')


def get_dataset_metadata(request: HttpRequest, id: int):
    """ Returns the dataset metadata xml file for a given metadata id

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
    Returns:
         A HttpResponse containing the xml file
    """
    md = Metadata.objects.get(id=id)
    if not md.is_active:
        return HttpResponse(content=SERVICE_DISABLED, status=423)
    if md.metadata_type != 'dataset':
        try:
            # the user gave the metadata id of the service metadata, we must resolve this to the related dataset metadata
            md = MetadataRelation.objects.get(
                metadata_from=md,
            ).metadata_to
            document = Document.objects.get(related_metadata=md)
            document = document.dataset_metadata_document
            if document is None:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            return HttpResponse(content=_("No dataset metadata found"), status=404)
    return HttpResponse(document, content_type='application/xml')


def get_dataset_metadata_button(request: HttpRequest, id: int):
    """ Checks whether an element (layer or featuretype) has a dataset metadata record.

    This function is used for ajax calls from the client, to check dynamically on an opened subelement if there
    are dataset metadata to get.

    Args:
        request (HttpRequest): The incoming request
        id (int): The element id
    Returns:
         A BackendAjaxResponse, containing a boolean, whether the requested element has a dataset metadata record or not
    """
    elementType = request.GET.get("serviceType")
    if elementType == ServiceEnum.WMS.value:
        element = Layer.objects.get(id=id)
    elif elementType == ServiceEnum.WFS.value:
        element = FeatureType.objects.get(id=id)
    md = element.metadata
    try:
        # the user gave the metadata id of the service metadata, we must resolve this to the related dataset metadata
        md_2 = MetadataRelation.objects.get(
            metadata_from=md,
        ).metadata_to
        doc = Document.objects.get(
            related_metadata=md_2
        )
        has_dataset_doc = doc.dataset_metadata_document is not None
    except ObjectDoesNotExist:
        has_dataset_doc = False

    return BackendAjaxResponse(html="", has_dataset_doc=has_dataset_doc).get_response()


def get_capabilities(request: HttpRequest, id: int):
    """ Returns the current capabilities xml file

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
    Returns:
         A HttpResponse containing the xml file
    """
    md = Metadata.objects.get(id=id)
    if not md.is_active:
        return HttpResponse(content=SERVICE_DISABLED, status=423)
    cap_doc = Document.objects.get(related_metadata=md)
    doc = cap_doc.current_capability_document
    return HttpResponse(doc, content_type='application/xml')


def get_capabilities_original(request: HttpRequest, id: int):
    """ Returns the current capabilities xml file

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
    Returns:
         A HttpResponse containing the xml file
    """
    md = Metadata.objects.get(id=id)
    if not md.is_active:
        return HttpResponse(content=SERVICE_DISABLED, status=423)
    cap_doc = Document.objects.get(related_metadata=md)
    doc = cap_doc.original_capability_document
    return HttpResponse(doc, content_type='application/xml')


@check_session
def set_session(request: HttpRequest, user:User):
    """ Can set a value to the django session

    Args:
        request:
    Returns:
    """
    param_GET = request.GET.dict()
    _session = param_GET.get("session", None)
    if _session is None:
        return BackendAjaxResponse(html="").get_response()
    _session = json.loads(_session)
    for _session_key, _session_val in _session.items():
        request.session[_session_key] = _session_val
    return BackendAjaxResponse(html="").get_response()

@check_session
def wms(request:HttpRequest, user:User):
    """ Renders an overview of all wms

    Args:
        request (HttpRequest): The incoming request
    Returns:
         A view
    """
    return redirect("service:index", ServiceEnum.WMS.value)


@check_session
@check_permission(Permission(can_register_service=True))
def register_form(request: HttpRequest, user: User):
    """ Returns the form for providing a capabilities URI

    Args:
        request:
    Returns:
        BackendAjaxResponse
    """
    template = "overlay/service_url_form.html"
    POST_params = request.POST.dict()
    if POST_params.get("uri", None) is not None:

        error = False
        cap_url = POST_params.get("uri", "")
        url_dict = service_helper.split_service_uri(cap_url)

        if url_dict["request"].lower() != "getcapabilities":
            # not allowed!
            error = True

        try:
            # create group->publishable organizations dict
            group_orgs = {}
            for group in user.groups.all():
                group_orgs[group.id] = list(group.publish_for_organizations.all().values_list("id", flat=True))
            params = {
                "error": error,
                "uri": url_dict["base_uri"],
                "version": url_dict["version"].value,
                "service_type": url_dict["service"].value,
                "request_action": url_dict["request"],
                "full_uri": cap_url,
                "user": user,
                "group_publishable_orgs": json.dumps(group_orgs),
                "page_indicator_list": [False, True, False],
            }
        except AttributeError as e:
            params = {
                "error": e,
            }

        template = "overlay/register_new_service.html"
    else:
        uri_form = ServiceURIForm()
        params = {
            "form": uri_form,
            "action_url": ROOT_URL + "/service/new/register-form",
            "button_text": "Next",
            "page_indicator_list": [True, False, False],
        }
    html = render_to_string(request=request, template_name=template, context=params)
    return BackendAjaxResponse(html).get_response()


@check_session
@check_permission(Permission(can_register_service=True))
def new_service(request: HttpRequest, user: User):
    """ Register a new service

    Args:
        request:
    Returns:

    """
    POST_params = request.POST.dict()

    cap_url = POST_params.get("uri", "")
    cap_url = cap_url.replace("&amp;", "&")
    register_group = POST_params.get("registerGroup")
    register_for_organization = POST_params.get("registerForOrg")

    url_dict = service_helper.split_service_uri(cap_url)
    url_dict["service"] = url_dict["service"].value
    url_dict["version"] = url_dict["version"].value

    # run creation async!
    try:
        pending_task = tasks.async_new_service.delay(url_dict, user.id, register_group, register_for_organization)
        #pending_task = tasks.async_new_service(url_dict, user.id, register_group, register_for_organization)
    except Exception as e:
        template = "overlay/error.html"
        params = {
            "error_code": e.args[0],
            "page_indicator_list": [False, False, True],
        }
        html = render_to_string(template_name=template, request=request, context=params)
        return BackendAjaxResponse(html).get_response()

    # create db object, so we know which pending task is still ongoing
    pending_task_db = PendingTask()
    pending_task_db.created_by = Group.objects.get(id=register_group)
    pending_task_db.task_id = pending_task.task_id
    pending_task_db.description = json.dumps({
        "service": cap_url,
        "phase": "Parsing",
    })

    pending_task_db.save()

    params = {
        "pending_task": pending_task,
        "url_dict": url_dict,
        "page_indicator_list": [False, False, True],
    }

    template = "overlay/new_service_progress.html"
    html = render_to_string(template_name=template, request=request, context=params)
    return BackendAjaxResponse(html=html).get_response()


@check_session
@check_permission(Permission(can_update_service=True))
@transaction.atomic
def update_service(request: HttpRequest, user: User, id: int):
    """ Compare old service with new service and collect differences

    Args:
        request: The incoming request
        user: The active user
        id: The service id
    Returns:
        A rendered view
    """
    template = "service_differences.html"
    update_params = request.session["update"]
    url_dict = service_helper.split_service_uri(update_params["full_uri"])
    new_service_type = url_dict.get("service")
    old_service = Service.objects.get(id=id)

    # check if metadata should be kept
    keep_custom_metadata = request.POST.get("keep-metadata", None)
    if keep_custom_metadata is None:
        keep_custom_metadata = request.session.get("keep-metadata", "")
    request.session["keep-metadata"] = keep_custom_metadata
    keep_custom_metadata = keep_custom_metadata == "on"


    # get info which layers/featuretypes are linked (old->new)
    links = json.loads(request.POST.get("storage", '{}'))
    update_confirmed = utils.resolve_boolean_attribute_val(request.POST.get("confirmed", 'false'))

    # parse new capabilities into db model
    registrating_group = old_service.created_by
    new_service = service_helper.get_service_model_instance(service_type=url_dict.get("service"), version=url_dict.get("version"), base_uri=url_dict.get("base_uri"), user=user, register_group=registrating_group)
    xml = new_service["raw_data"].service_capabilities_xml
    new_service = new_service["service"]

    # Collect differences
    comparator = ServiceComparator(service_1=new_service, service_2=old_service)
    diff = comparator.compare_services()

    if update_confirmed:
        # check cross service update attempt
        if old_service.servicetype.name != new_service_type.value:
            # cross update attempt -> forbidden!
            messages.add_message(request, messages.ERROR, SERVICE_UPDATE_WRONG_TYPE)
            return BackendAjaxResponse(html="", redirect="{}/service/detail/{}".format(ROOT_URL, str(old_service.metadata.id))).get_response()
        # check if new capabilities is even different from existing
        # if not we do not need to spend time and money on performing it!
        # if not service_helper.capabilities_are_different(update_params["full_uri"], old_service.metadata.capabilities_original_uri):
        #     messages.add_message(request, messages.INFO, SERVICE_UPDATE_ABORTED_NO_DIFF)
        #     return BackendAjaxResponse(html="", redirect="{}/service/detail/{}".format(ROOT_URL, str(old_service.metadata.id))).get_response()

        if not keep_custom_metadata:
            # the update is confirmed, we can continue changing the service!
            # first update the metadata of the whole service
            md = update_helper.update_metadata(old_service.metadata, new_service.metadata)
            old_service.metadata = md
            # don't forget the timestamp when we updated the last time
            old_service.metadata.last_modified = timezone.now()
            # save the metadata changes
            old_service.metadata.save()
        # secondly update the service itself, overwrite the metadata with the previously updated metadata
        old_service = update_helper.update_service(old_service, new_service)
        old_service.last_modified = timezone.now()

        if new_service.servicetype.name == ServiceEnum.WFS.value:
            old_service = update_helper.update_wfs(old_service, new_service, diff, links, keep_custom_metadata)

        elif new_service.servicetype.name == ServiceEnum.WMS.value:
            old_service = update_helper.update_wms(old_service, new_service, diff, links, keep_custom_metadata)

        cap_document = Document.objects.get(related_metadata=old_service.metadata)
        cap_document.current_capability_document = xml
        cap_document.save()

        old_service.save()
        del request.session["keep-metadata"]
        del request.session["update"]
        user_helper.create_group_activity(old_service.metadata.created_by, user, SERVICE_UPDATED, old_service.metadata.title)
        return BackendAjaxResponse(html="", redirect="{}/service/detail/{}".format(ROOT_URL,str(old_service.metadata.id))).get_response()
    else:
        # otherwise
        params = {
            "diff": diff,
            "old_service": old_service,
            "new_service": new_service,
            "page_indicator_list": [False, True],
        }
        #request.session["update_confirmed"] = True
    context = DefaultContext(request, params, user)
    return render(request, template, context.get_context())


@check_session
def discard_update(request: HttpRequest, user: User):
    """ If the user does not want to proceed with the update,
    we need to go back and drop the session stored data about the update

    Args:
        request (HttpRequest):
        user (User):
    Returns:
         redirects
    """
    del request.session["update"]
    return redirect("service:index")


@check_session
@check_permission(Permission(can_update_service=True))
def update_service_form(request: HttpRequest, user:User, id: int):
    """ Creates the form for updating a service

    Args:
        request: The incoming request
        user: The current user
        id: The service id
    Returns:
         A BackendAjaxResponse
    """
    template = "overlay/service_url_form.html"
    uri_form = ServiceURIForm(request.POST or None)
    params = {}
    if request.method == 'POST':
        template = "overlay/update_service.html"
        if uri_form.is_valid():
            error = False
            cap_url = uri_form.data.get("uri", "")
            url_dict = service_helper.split_service_uri(cap_url)

            if url_dict["request"] != "GetCapabilities":
                # not allowed!
                error = True

            try:
                # get current service to compare with
                service = Service.objects.get(id=id)
                params = {
                    "action_url": ROOT_URL + "/service/update/" + str(id),
                    "service": service,
                    "error": error,
                    "uri": url_dict["base_uri"],
                    "version": url_dict["version"].value,
                    "service_type": url_dict["service"].value,
                    "request_action": url_dict["request"],
                    "full_uri": cap_url,
                    "page_indicator_list": [False, True],
                }
                request.session["update"] = {
                    "full_uri": cap_url,
                }
            except AttributeError:
                params = {
                    "error": error,
                    "page_indicator_list": [False, True],
                }

        else:
            params = {
                "error": FORM_INPUT_INVALID,
                "page_indicator_list": [False, True],
            }

    else:
        params = {
            "form": uri_form,
            "article": _("Enter the new capabilities URL of your service."),
            "action_url": ROOT_URL + "/service/register-form/" + str(id),
            "button_text": "Update",
            "page_indicator_list": [True, False],
        }
    params["service_id"] = id
    html = render_to_string(template_name=template, request=request, context=params)
    return BackendAjaxResponse(html=html).get_response()


@check_session
def wfs(request:HttpRequest, user:User):
    """ Renders an overview of all wfs

    Args:
        request (HttpRequest): The incoming request
    Returns:
         A view
    """
    params = {
        "only": ServiceEnum.WFS
    }
    return redirect("service:index", ServiceEnum.WFS.value)


@check_session
def detail(request: HttpRequest, id, user:User):
    """ Renders a detail view of the selected service

    Args:
        request: The incoming request
        id: The id of the selected metadata
    Returns:
    """
    template = "detail/service_detail.html"
    service_md = get_object_or_404(Metadata, id=id)

    if service_md.service.is_root:
        service = service_md.service
    else:
        service = Layer.objects.get(
            metadata=service_md
        )
    layers = Layer.objects.filter(parent_service=service_md.service)
    layers_md_list = layers.filter(parent_layer=None)

    try:
        related_md = MetadataRelation.objects.get(
            metadata_from=service_md,
            metadata_to__metadata_type__type='dataset',
        )
        document = Document.objects.get(
            related_metadata=related_md.metadata_to
        )
        has_dataset_metadata = document.dataset_metadata_document is not None
    except ObjectDoesNotExist:
        has_dataset_metadata = False

    params = {
        "has_dataset_metadata": has_dataset_metadata,
        "root_metadata": service_md,
        "root_service": service,
        "layers": layers_md_list,
    }
    context = DefaultContext(request, params, user)
    return render(request=request, template_name=template, context=context.get_context())


@check_session
def detail_child(request: HttpRequest, id, user: User):
    """ Returns a rendered html overview of the element with the given id

    Args:
        request (HttpRequest): The incoming request
        id (int): The element id
        user (User): The performing user
    Returns:
         A rendered view for ajax insertion
    """
    elementType = request.GET.get("serviceType")
    if elementType == "wms":
        template = "detail/service_detail_child_wms.html"
        element = Layer.objects.get(id=id)
    elif elementType == "wfs":
        template = "detail/service_detail_child_wfs.html"
        element = FeatureType.objects.get(id=id)
    else:
        template = ""
        element = None

    params = {
        "element": element,
        "user_permissions": user.get_permissions(),
    }
    html = render_to_string(template_name=template, context=params)
    return BackendAjaxResponse(html=html).get_response()


def metadata_proxy(request: HttpRequest, id: int):
    """ Returns the xml document which is resolved by the metadata id.

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
    Returns:
         HttpResponse
    """
    dataset_metadata = Metadata.objects.get(id=id)
    con = CommonConnector(url=dataset_metadata.metadata_url)
    con.load()
    xml_raw = con.content
    return HttpResponse(xml_raw, content_type='application/xml')


@check_session
def metadata_proxy_operation(request: HttpRequest, id: int, user: User):
    """ Checks whether the requested metadata is secured and resolves the operations uri for an allowed user - or not.

    Decides which operation will be handled by resolving a given 'request=' query parameter.

    Args:
        request (HttpRequest): The incoming request
        id (int): The metadata id
        user (User): The performing user
    Returns:
         A redirect to the GetMap uri
    """
    # get request type and requested layer
    get_query_string = request.environ.get("QUERY_STRING", "")

    GET_params = {
        "request": None,  # refers to param 'REQUEST'
        "layer": None,  # refers to param 'LAYERS'
        "x_y": [None, None],  # refers to param 'X/Y' (WMS 1.0.0), 'X, Y' (WMS 1.1.1), 'I,J' (WMS 1.3.0)
        "bbox": None,  # refers to param 'BBOX'
        "srs": None,  # refers to param 'SRS' (WMS 1.0.0 - 1.1.1) and 'CRS' (WMS 1.3.0)
        "version": None,  # refers to param 'VERSION'
    }

    for key, val in request.GET.items():
        key = key.upper()
        if key == "REQUEST":
            GET_params["request"] = val
        if key == "LAYER":
            GET_params["layer"] = val
        if key == "BBOX":
            GET_params["bbox"] = val
        if key == "X" or key == "I":
            GET_params["x_y"][0] = val
        if key == "Y" or key == "J":
            GET_params["x_y"][1] = val
        if key == "VERSION":
            GET_params["version"] = val
        if key == "SRS" or key == "CRS":
            GET_params["srs"] = val
        if key == "WIDTH":
            GET_params["width"] = val
        if key == "HEIGHT":
            GET_params["height"] = val

    if GET_params["request"] is None:
        return HttpResponse(status=500, content=SECURITY_PROXY_ERROR_MISSING_REQUEST_TYPE)

    try:
        # redirects request to parent service, if the given id is not the root of the service
        metadata = Metadata.objects.get(id=id)
        if not metadata.is_root():
            redirect_uri = "/service/metadata/proxy/operation/{}?{}".format(
                metadata.service.parent_service.metadata.id,
                get_query_string
            )
            return redirect(redirect_uri)

        if not metadata.is_active:
            return HttpResponse(status=423, content=SERVICE_DISABLED)

        # if the 'layer' parameter indicates the request for a subelement of this service, we need to fetch this metadata
        # to continue with!
        if GET_params["layer"] is not None:
            try:
                metadata = Metadata.objects.get(identifier=GET_params["layer"])
            except ObjectDoesNotExist:
                return HttpResponse(status=404, content=SERVICE_LAYER_NOT_FOUND)

        tmp_st = metadata.service.servicetype
        service_type = "{}_{}".format(tmp_st.name, GET_params["version"])

    except ObjectDoesNotExist:
        return HttpResponse(status=404, content=SERVICE_NOT_FOUND)

    GET_params["bbox"] = service_helper.process_bbox_param(GET_params["bbox"], GET_params["srs"], service_type)

    GET_params["x_y"] = service_helper.process_x_y_param(GET_params["x_y"], GET_params["srs"])

    # identify requested operation and resolve the uri
    if metadata.service.servicetype.name == ServiceEnum.WFS.value:
        operations = {
            "GETFEATURE": metadata.service.get_feature_info_uri,  # get_feature_info_uri is used in WFS for get_feature_uri
            "TRANSACTION": metadata.service.transaction_uri,
        }
    else:
        operations = {
            "GETMAP": metadata.service.get_map_uri,
            "GETFEATUREINFO": metadata.service.get_feature_info_uri,
        }
    uri = operations.get(GET_params["request"].upper(), None)

    if uri is None:
        return HttpResponse(status=500, content=SECURITY_PROXY_ERROR_BROKEN_URI)
    uri += get_query_string

    if metadata.is_secured:
        return service_helper.get_secured_operation_result(
            metadata,
            GET_params,
            user,
            uri
        )
    else:
        # if the metadata is not secured, there is no reason this route would have been called in the first place!
        # We simply redirect to the original route!
        return redirect(uri)

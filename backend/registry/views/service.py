from typing import OrderedDict

from django.db.models.query import Prefetch
from django_celery_results.models import TaskResult
from extras.permissions import DjangoObjectPermissionsOrAnonReadOnly
from extras.viewsets import (HistoryInformationViewSetMixin,
                             ObjectPermissionCheckerViewSetMixin)
from notify.serializers import TaskResultSerializer
from registry.filters.service import (FeatureTypeFilterSet, LayerFilterSet,
                                      WebFeatureServiceFilterSet,
                                      WebMapServiceFilterSet)
from registry.models import (FeatureType, Layer, WebFeatureService,
                             WebMapService)
from registry.models.metadata import (Keyword, MetadataContact,
                                      ReferenceSystem, Style)
from registry.serializers.service import (FeatureTypeSerializer,
                                          LayerSerializer,
                                          WebFeatureServiceCreateSerializer,
                                          WebFeatureServiceSerializer,
                                          WebMapServiceCreateSerializer,
                                          WebMapServiceSerializer)
from registry.tasks.service import build_ogc_service
from rest_framework import status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_json_api.schemas.openapi import AutoSchema
from rest_framework_json_api.views import ModelViewSet, RelationshipView


class OgcServiceCreateMixin:

    def get_serializer_class(self):
        return self.serializer_classes.get(
            self.action, self.serializer_classes["default"]
        )

    def create(self, request, *args, **kwargs):
        # followed the jsonapi recommendation for async processing
        # https://jsonapi.org/recommendations/#asynchronous-processing
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = build_ogc_service.delay(get_capabilities_url=serializer.validated_data['get_capabilities_url'],
                                       collect_metadata_records=serializer.validated_data[
                                           'collect_metadata_records'],
                                       service_auth_pk=serializer.service_auth.id if hasattr(
                                           serializer, 'service_auth') else None,
                                       **{'request': {'path': request.path, 'method': request.method, 'content_type': request.content_type, 'data': request.GET, 'user_pk': request.user.pk}})
        task_result, created = TaskResult.objects.get_or_create(
            task_id=task.id,
            task_name='registry.tasks.service.build_ogc_service')

        # TODO: add auth information and other headers we need here
        dummy_request = APIRequestFactory().get(
            path=request.build_absolute_uri(
                reverse("notify:taskresult-detail", args=[task_result.pk])
            ),
            data={},
        )

        dummy_request.query_params = OrderedDict()
        # FIXME: wrong response data type is used. We need to set the resource_name to TaskResult here.
        serialized_task_result = TaskResultSerializer(
            task_result, **{"context": {"request": dummy_request}}
        )
        serialized_task_result_data = serialized_task_result.data
        # meta object is None... we need to set it to an empty dict to prevend uncaught runtime exceptions
        if not serialized_task_result_data.get("meta", None):
            serialized_task_result_data.update({"meta": {}})

        headers = self.get_success_headers(serialized_task_result_data)

        return Response(
            serialized_task_result_data,
            status=status.HTTP_202_ACCEPTED,
            headers=headers,
        )

    def get_success_headers(self, data):
        try:
            return {"Content-Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class WebMapServiceRelationshipView(RelationshipView):
    schema = AutoSchema(
        tags=["WebMapService"],
    )
    queryset = WebMapService.objects
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]


class WebMapServiceViewSet(ObjectPermissionCheckerViewSetMixin, HistoryInformationViewSetMixin, NestedViewSetMixin, OgcServiceCreateMixin, ModelViewSet):
    schema = AutoSchema(
        tags=["WebMapService"],
    )
    queryset = WebMapService.objects.all()
    serializer_classes = {
        "default": WebMapServiceSerializer,
        "create": WebMapServiceCreateSerializer
    }
    select_for_includes = {
        "service_contact": ["service_contact"],
        "metadata_contact": ["metadata_contact"],
    }
    prefetch_for_includes = {
        "layers": ["layers"],
        "keywords": ["keywords"]
    }
    filterset_class = WebMapServiceFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]

    def dispatch(self, request, *args, **kwargs):
        if 'layer_pk' in self.kwargs:
            self.lookup_field = 'layer'
            self.lookup_url_kwarg = 'layer_pk'
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get('include', None)
        if not include or 'layers' not in include:
            qs = qs.prefetch_related(Prefetch('layers', queryset=Layer.objects.only(
                'id', 'service_id', 'tree_id', 'lft', )))
        if not include or 'keywords' not in include:
            qs = qs.prefetch_related(
                Prefetch('keywords', queryset=Keyword.objects.only('id')))
        return qs


class LayerRelationshipView(RelationshipView):
    schema = AutoSchema(
        tags=["WebMapService"],
    )
    queryset = Layer.objects
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]


class LayerViewSet(NestedViewSetMixin, ObjectPermissionCheckerViewSetMixin, HistoryInformationViewSetMixin, ModelViewSet):
    schema = AutoSchema(
        tags=["WebMapService"],
    )
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    filterset_class = LayerFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    prefetch_for_includes = {
        "styles": ["styles"],
        "keywords": ["keywords"],
        "reference_systems": ["reference_systems"],
    }
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get('include', None)
        if not include or 'service' not in include:
            defer = [f'service__{field.name}' for field in WebMapService._meta.get_fields(
            ) if field.name not in ['id', 'pk']]
            qs = qs.select_related('service').defer(*defer)
        if not include or 'styles' not in include:
            qs = qs.prefetch_related(
                Prefetch('styles', queryset=Style.objects.only('id')))
        if not include or 'keywords' not in include:
            qs = qs.prefetch_related(
                Prefetch('keywords', queryset=Keyword.objects.only('id')))
        if not include or 'reference_systems' not in include:
            qs = qs.prefetch_related(
                Prefetch('reference_systems', queryset=ReferenceSystem.objects.only('id')))

        return qs


class WebFeatureServiceRelationshipView(RelationshipView):
    schema = AutoSchema(
        tags=["WebFeatureService"],
    )
    queryset = WebFeatureService.objects
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]


class WebFeatureServiceViewSet(ObjectPermissionCheckerViewSetMixin, NestedViewSetMixin, OgcServiceCreateMixin, ModelViewSet):
    schema = AutoSchema(
        tags=["WebFeatureService"],
    )
    queryset = WebFeatureService.objects.all()
    serializer_classes = {
        "default": WebFeatureServiceSerializer,
        "create": WebFeatureServiceCreateSerializer,
    }
    prefetch_for_includes = {"__all__": [], "featuretypes": ["featuretypes"]}
    filterset_class = WebFeatureServiceFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]


class FeatureTypeRelationshipView(RelationshipView):
    schema = AutoSchema(
        tags=["WebFeatureService"],
    )
    queryset = FeatureType.objects
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]


class FeatureTypeViewSet(NestedViewSetMixin, ModelViewSet):
    schema = AutoSchema(
        tags=["WebFeatureService"],
    )
    queryset = FeatureType.objects.all()
    serializer_class = FeatureTypeSerializer
    filterset_class = FeatureTypeFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")

    prefetch_for_includes = {"__all__": [], "keywords": ["keywords"]}
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]

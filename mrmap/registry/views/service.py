from django.contrib.auth import get_user_model
from django.db.models.query import Prefetch
from extras.permissions import DjangoObjectPermissionsOrAnonReadOnly
from extras.viewsets import (AsyncCreateMixin, HistoryInformationViewSetMixin,
                             NestedModelViewSet,
                             ObjectPermissionCheckerViewSetMixin,
                             SerializerClassesMixin)
from notify.models import BackgroundProcess, ProcessNameEnum
from registry.filters.service import (FeatureTypeFilterSet, LayerFilterSet,
                                      WebFeatureServiceFilterSet,
                                      WebMapServiceFilterSet)
from registry.models import (FeatureType, Layer, WebFeatureService,
                             WebMapService)
from registry.models.metadata import (DatasetMetadataRecord, Keyword,
                                      MetadataContact, MimeType,
                                      ReferenceSystem, Style)
from registry.models.security import AllowedWebMapServiceOperation
from registry.models.service import (CatalogueService,
                                     CatalogueServiceOperationUrl,
                                     WebFeatureServiceOperationUrl,
                                     WebMapServiceOperationUrl)
from registry.serializers.service import (CatalogueServiceCreateSerializer,
                                          CatalogueServiceSerializer,
                                          FeatureTypeSerializer,
                                          LayerSerializer,
                                          WebFeatureServiceCreateSerializer,
                                          WebFeatureServiceSerializer,
                                          WebMapServiceCreateSerializer,
                                          WebMapServiceHistorySerializer,
                                          WebMapServiceListSerializer,
                                          WebMapServiceSerializer)
from registry.tasks.service import build_ogc_service
from rest_framework_json_api.views import ModelViewSet


class WebMapServiceHistoricalViewSet(
    SerializerClassesMixin,
    ModelViewSet
):
    # removes create and delete endpoints, cause this two actions are made by the mrmap system it self in registrion or update processing of the service.
    # delete is only provided on the service endpoint it self, which implicit removes all related objects
    http_method_names = ["get", "patch", "head", "options"]

    queryset = WebMapService.change_log.all()
    serializer_classes = {
        "default": WebMapServiceHistorySerializer,
    }

    select_for_includes = {
        "history_user": ["history_user"],
        "history_relation": ["history_relation"]
    }

    filterset_fields = {
        'history_relation': ['exact'],
    }

    def get_queryset(self):
        defer_metadata_contact = [
            f"metadata_contact__{field.name}"
            for field in MetadataContact._meta.get_fields()
            if field.name not in ["id", "pk"]
        ]
        defer_service_contact = [
            f"metadata_contact__{field.name}"
            for field in MetadataContact._meta.get_fields()
            if field.name not in ["id", "pk"]
        ]

        qs = super().get_queryset().select_related("metadata_contact",
                                                   "service_contact").defer(*defer_metadata_contact, *defer_service_contact)

        include = self.request.GET.get("include", None)

        if not include or "historyUser" not in include:
            defer = [
                f"history_user__{field.name}"
                for field in get_user_model()._meta.get_fields()
                if field.name not in ["id", "pk"]
            ]
            qs = qs.select_related("history_user").defer(*defer)
        elif include and "historyUser" in include:
            # TODO: select_for_includes setup does not work for history records...
            qs = qs.select_related("history_user")

        if not include or "history_relation__layers" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "history_relation__layers",
                    queryset=Layer.objects.only(
                        "id",
                        "service_id",
                        "mptt_tree_id",
                        "mptt_lft",
                    ),
                )
            )
        if not include or "history_relation__metadata_contact" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "history_relation__metadata_contact",
                    queryset=MetadataContact.objects.only(
                        "id",
                    ),
                )
            )
        if not include or "history_relation__keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("history_relation__keywords",
                         queryset=Keyword.objects.only("id"))
            )
        if not include or "history_relation__allowedOperations" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "history_relation__allowed_operations",
                    queryset=AllowedWebMapServiceOperation.objects.only(
                        "id", "secured_service__id")
                )
            )
        if not include or "history_relation__operationUrls" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "history_relation__operation_urls",
                    queryset=WebMapServiceOperationUrl.objects.only(
                        "id", "service_id"),
                )
            )
        return qs


class WebMapServiceViewSet(
    SerializerClassesMixin,
    AsyncCreateMixin,
    ObjectPermissionCheckerViewSetMixin,
    HistoryInformationViewSetMixin,
    ModelViewSet,
):
    """ Endpoints for resource `WebMapService`

        create:
            Endpoint to register new `WebMapServices` object
        list:
            Retrieves all registered `WebMapServices` objects
        retrieve:
            Retrieve one specific `WebMapServices` by the given id
        partial_update:
            Endpoint to update some fields of a registered `WebMapServices`
        destroy:
            Endpoint to remove a registered `WebMapServices` from the system
    """
    queryset = WebMapService.objects.all()
    serializer_classes = {
        "default": WebMapServiceSerializer,
        "list": WebMapServiceListSerializer,
        "create": WebMapServiceCreateSerializer,
    }
    select_for_includes = {
        "service_contact": ["service_contact"],
        "metadata_contact": ["metadata_contact"],
    }
    prefetch_for_includes = {
        "layers": [
            Prefetch(
                "layers",
                queryset=Layer.objects.with_inherited_attributes().select_related("mptt_parent").prefetch_related(
                    Prefetch(
                        "keywords",
                        queryset=Keyword.objects.only("id")
                    ),
                    Prefetch(
                        "registry_datasetmetadatarecord_metadata_records",
                        queryset=DatasetMetadataRecord.objects.only("id")
                    )
                )
            )
        ],
        "keywords": ["keywords"],
        "operation_urls": [
            Prefetch(
                "operation_urls",
                queryset=WebMapServiceOperationUrl.objects.select_related(
                    "service"
                ).prefetch_related("mime_types"),
            )
        ],
    }
    filterset_class = WebMapServiceFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    ordering_fields = ["id", "title", "abstract", "hits", "date_stamp"]
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]
    task_function = build_ogc_service

    def get_task_kwargs(self, request, serializer):
        background_process = BackgroundProcess.objects.create(
            phase="Background process created",
            process_type=ProcessNameEnum.REGISTERING.value,
            description=f'Register new service with url {serializer.validated_data["get_capabilities_url"]}'
        )

        return {
            "get_capabilities_url": serializer.validated_data["get_capabilities_url"],
            "collect_metadata_records": serializer.validated_data["collect_metadata_records"],
            "service_auth_pk": serializer.service_auth.id if hasattr(serializer, "service_auth") else None,
            "http_request": {
                "path": request.path,
                "method": request.method,
                "content_type": request.content_type,
                "data": request.GET,
                "user_pk": request.user.pk,
            },
            "background_process_pk": background_process.pk
        }

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get("include", None)
        if not include or "layers" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "layers",
                    queryset=Layer.objects.only(
                        "id",
                        "service_id",
                        "mptt_tree_id",
                        "mptt_lft",
                    ),
                )
            )

        if not include or "keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("keywords", queryset=Keyword.objects.only("id"))
            )
        if not include or "allowedOperations" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "allowed_operations",
                    queryset=AllowedWebMapServiceOperation.objects.only(
                        "id", "secured_service__id")
                )
            )
        if not include or "operationUrls" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "operation_urls",
                    queryset=WebMapServiceOperationUrl.objects.only(
                        "id", "service_id"),
                )
            )
        return qs


class LayerViewSetMixin(
    HistoryInformationViewSetMixin,
):
    queryset = Layer.objects.with_inherited_attributes()
    serializer_class = LayerSerializer
    filterset_class = LayerFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    select_for_includes = {
        "service": ["service"],
        "service.operation_urls": ["service"]
    }
    prefetch_for_includes = {
        "service": ["service__keywords", "service__layers"],
        "service.operation_urls": [
            Prefetch(
                "service__operation_urls",
                queryset=WebMapServiceOperationUrl.objects.prefetch_related(
                    "mime_types"
                ),
            ),
            "service__keywords",
            "service__layers"
        ],
        "styles": ["styles"],
        "keywords": ["keywords"],
        "reference_systems": ["reference_systems"],
        "dataset_metadata": ["registry_datasetmetadatarecord_metadata_records"]
    }
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]
    ordering_fields = ["id", "title", "abstract",
                       "hits", "scale_max", "scale_min", "date_stamp", "mptt_lft", "mptt_rgt", "mptt_depth"]

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get("include", None)
        if not include or "service" not in include:
            defer = [
                f"service__{field.name}"
                for field in WebMapService._meta.get_fields()
                if field.name not in ["id", "pk"]
            ]
            qs = qs.select_related("service").defer(*defer)

        if not include or "mpttParent" not in include:
            # TODO optimize queryset with defer
            qs = qs.select_related("mptt_parent")
        if not include or "styles" not in include:
            qs = qs.prefetch_related(
                Prefetch("styles", queryset=Style.objects.only("id", "layer_id"))
            )
        if not include or "keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("keywords", queryset=Keyword.objects.only("id"))
            )
        if not include or "referenceSystems" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "reference_systems", queryset=ReferenceSystem.objects.only("id")
                )
            )
        if not include or "datasetMetadata" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "registry_datasetmetadatarecord_metadata_records", queryset=DatasetMetadataRecord.objects.only("id")
                )
            )

        return qs


class LayerViewSet(
        LayerViewSetMixin,
        ModelViewSet):
    """ Endpoints for resource `Layer`

        list:
            Retrieves all registered `Layer` objects
        retrieve:
            Retrieve one specific `Layer` by the given id
        partial_update:
            Endpoint to update some fields of a registered `Layer`

    """
    # removes create and delete endpoints, cause this two actions are made by the mrmap system it self in registrion or update processing of the service.
    # delete is only provided on the service endpoint it self, which implicit removes all related objects
    http_method_names = ["get", "patch", "head", "options"]


class NestedLayerViewSet(
        LayerViewSetMixin,
        NestedModelViewSet):
    """ Nested list endpoint for resource `Layer`

        list:
            Retrieves all registered `Layer` objects

    """


class WebFeatureServiceViewSet(
    SerializerClassesMixin,
    AsyncCreateMixin,
    ObjectPermissionCheckerViewSetMixin,
    HistoryInformationViewSetMixin,
    ModelViewSet,
):
    """ Endpoints for resource `WebFeatureService`

        create:
            Endpoint to register new `WebFeatureService` object
        list:
            Retrieves all registered `WebFeatureService` objects
        retrieve:
            Retrieve one specific `WebFeatureService` by the given id
        partial_update:
            Endpoint to update some fields of a registered `WebFeatureService`
        destroy:
            Endpoint to remove a registered `WebFeatureService` from the system
    """
    queryset = WebFeatureService.objects.all()
    serializer_classes = {
        "default": WebFeatureServiceSerializer,
        "create": WebFeatureServiceCreateSerializer,
    }
    select_for_includes = {
        "service_contact": ["service_contact"],
        "metadata_contact": ["metadata_contact"],
    }
    prefetch_for_includes = {
        "featuretypes": [
            Prefetch(
                "featuretypes",
                queryset=FeatureType.objects.prefetch_related(
                    "keywords",
                    "reference_systems",
                    "output_formats",
                ),
            ),
        ],
        "keywords": ["keywords"],
        "operation_urls": [
            Prefetch(
                "operation_urls",
                queryset=WebFeatureServiceOperationUrl.objects.select_related(
                    "service"
                ).prefetch_related("mime_types"),
            )
        ],
    }
    filterset_class = WebFeatureServiceFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    ordering_fields = ["id", "title", "abstract", "hits", "date_stamp"]
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]
    task_function = build_ogc_service

    def get_task_kwargs(self, request, serializer):
        return {
            "get_capabilities_url": serializer.validated_data["get_capabilities_url"],
            "collect_metadata_records": serializer.validated_data["collect_metadata_records"],
            "service_auth_pk": serializer.service_auth.id if hasattr(serializer, "service_auth") else None,
            "http_request": {
                "path": request.path,
                "method": request.method,
                "content_type": request.content_type,
                "data": request.GET,
                "user_pk": request.user.pk,
            }
        }

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get("include", None)
        if not include or "featuretypes" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "featuretypes",
                    queryset=FeatureType.objects.only(
                        "id",
                        "service_id",
                    )
                ),
            )
        if not include or "keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("keywords", queryset=Keyword.objects.only("id"))
            )
        if not include or "operationUrls" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "operation_urls",
                    queryset=WebFeatureServiceOperationUrl.objects.only(
                        "id", "service_id"),
                )
            )
        return qs


class FeatureTypeViewSetMixin(
    HistoryInformationViewSetMixin,
):
    queryset = FeatureType.objects.all()
    serializer_class = FeatureTypeSerializer
    filterset_class = FeatureTypeFilterSet
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    ordering_fields = ["id", "title", "abstract", "hits", "date_stamp"]

    select_for_includes = {
        "service": ["service"],
        "service.operation_urls": ["service"]
    }
    prefetch_for_includes = {
        "service": ["service__keywords", "service__featuretypes"],
        "service.operation_urls": [
            Prefetch(
                "service__operation_urls",
                queryset=WebFeatureServiceOperationUrl.objects.prefetch_related(
                    "mime_types"
                ),
            ),
            "service__keywords",
            "service__featuretypes"
        ],
        "output_formats": ["output_formats"],
        "keywords": ["keywords"],
        "reference_systems": ["reference_systems"],
    }
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get("include", None)
        if not include or "service" not in include:
            defer = [
                f"service__{field.name}"
                for field in WebFeatureService._meta.get_fields()
                if field.name not in ["id", "pk"]
            ]
            qs = qs.select_related("service").defer(*defer)
        if not include or "keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("keywords", queryset=Keyword.objects.only("id"))
            )
        if not include or "referenceSystems" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "reference_systems", queryset=ReferenceSystem.objects.only("id")
                )
            )

        if not include or "output_formats" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "output_formats", queryset=MimeType.objects.only("id")
                )
            )

        return qs


class FeatureTypeViewSet(
    FeatureTypeViewSetMixin,
    ModelViewSet
):
    """ Endpoints for resource `FeatureType`

        list:
            Retrieves all registered `FeatureType` objects
        retrieve:
            Retrieve one specific `FeatureType` by the given id
        partial_update:
            Endpoint to update some fields of a registered `FeatureType`

    """
    # removes create and delete endpoints, cause this two actions are made by the mrmap system it self in registrion or update processing of the service.
    # delete is only provided on the service endpoint it self, which implicit removes all related objects
    http_method_names = ["get", "patch", "head", "options"]


class NestedFeatureTypeViewSet(
    FeatureTypeViewSetMixin,
    NestedModelViewSet
):
    """ Nested list endpoint for resource `FeatureType`

        list:
            Retrieves all registered `FeatureType` objects

    """


class CatalogueServiceViewSetMixin(
    SerializerClassesMixin,
    AsyncCreateMixin,
    ObjectPermissionCheckerViewSetMixin,
    HistoryInformationViewSetMixin,
):
    """ Endpoints for resource `CatalogueService`

        create:
            Endpoint to register new `CatalogueService` object
        list:
            Retrieves all registered `CatalogueService` objects
        retrieve:
            Retrieve one specific `CatalogueService` by the given id
        partial_update:
            Endpoint to update some fields of a registered `CatalogueService`
        destroy:
            Endpoint to remove a registered `CatalogueService` from the system
    """
    queryset = CatalogueService.objects.all()
    serializer_classes = {
        "default": CatalogueServiceSerializer,
        "create": CatalogueServiceCreateSerializer,
    }
    search_fields = ("id", "title", "abstract", "keywords__keyword")
    filterset_fields = {
        'title': ['exact', 'icontains', 'contains'],
        'abstract': ['exact', 'icontains', 'contains']
    }
    ordering_fields = ["id", "title", "abstract", "hits", "date_stamp"]
    permission_classes = [DjangoObjectPermissionsOrAnonReadOnly]
    task_function = build_ogc_service

    def get_task_kwargs(self, request, serializer):
        return {
            "get_capabilities_url": serializer.validated_data["get_capabilities_url"],
            "collect_metadata_records": False,  # CSW has no remote metadata records
            "service_auth_pk": serializer.service_auth.id if hasattr(serializer, "service_auth") else None,
            "http_request": {
                "path": request.path,
                "method": request.method,
                "content_type": request.content_type,
                "data": request.GET,
                "user_pk": request.user.pk,
            }
        }

    def get_queryset(self):
        qs = super().get_queryset()
        include = self.request.GET.get("include", None)
        # TODO:
        # if not include or "datasetMetadata" not in include:
        #     qs = qs.prefetch_related(
        #         Prefetch(
        #             "dataset_metadata",
        #             queryset=DatasetMetadataRecord.objects.only(
        #                 "id",
        #                 "service_id",
        #             )
        #         ),
        #     )
        if not include or "keywords" not in include:
            qs = qs.prefetch_related(
                Prefetch("keywords", queryset=Keyword.objects.only("id"))
            )
        if not include or "operationUrls" not in include:
            qs = qs.prefetch_related(
                Prefetch(
                    "operation_urls",
                    queryset=CatalogueServiceOperationUrl.objects.only(
                        "id", "service_id"),
                )
            )
        return qs


class CatalogueServiceViewSet(
    CatalogueServiceViewSetMixin,
    ModelViewSet
):
    pass


class NestedCatalogueServiceViewSet(
    CatalogueServiceViewSetMixin,
    NestedModelViewSet
):
    pass

from django.db import models
from django.db.models import Count
from django.utils import timezone
from mptt.managers import TreeManager
from main.models import get_current_owner
from resourceNew.enums.service import OGCServiceEnum
from crum import get_current_user

class WfsManager(models.Manager):

    def for_table_view(self):
        return self.get_queryset().select_related("metadata",
                                                  "metadata__service_contact",
                                                  "metadata__metadata_contact",
                                                  "created_by_user",
                                                  "owned_by_org",
                                                  "external_authentication",
                                                  "proxy_setting") \
                       .prefetch_related("allowed_operations",
                                         "operation_urls")\
                       .order_by("-metadata__title")\
                       .annotate(is_secured=Count("allowed_operation"),
                                 feature_types_count=Count("featuretype", distinct=True))

    def for_tree_view(self):
        return self.get_queryset().select_related("metadata")\
                                  .prefetch_related("featuretypes",
                                                    "featuretypes__metadata",
                                                    "featuretypes__elements")\
                                  .annotate(feature_types_count=Count("featuretype", distinct=True))


class WmsManager(models.Manager):
    """Provide the creation/resolving of a full service."""

    def get_full_service(self, *args, **kwargs):
        return self.get_queryset().select_related("metadata",
                                                  "metadata__metadata_contact",
                                                  "metadata__service_contact",
                                                  "external_authentication",
                                                  "proxy_setting",)\
                                   .prefetch_related("metadata__keywords",
                                                     "layers",
                                                     "layers__metadata",
                                                     "layers__metadata__keywords",
                                                     "layers__reference_systems",)\
                                   .get(*args, **kwargs)

    def from_proto_service(self, proto_service, *args, **kwargs):
        """Build a service object
        """
        from resourceNew.builder.db_wms_service import WmsDbBuilder, WmsDbDirector  # to avoid circular imports
        builder = WmsDbBuilder(proto_service=proto_service)
        director = WmsDbDirector()
        director.builder = builder

        director.build_service()
        return builder.service

    def for_table_view(self):
        return self.get_queryset().select_related("metadata",
                                                  "metadata__service_contact",
                                                  "metadata__metadata_contact",
                                                  "created_by_user",
                                                  "owned_by_org",
                                                  "external_authentication",
                                                  "proxy_setting") \
                       .prefetch_related("allowed_operations",
                                         "operation_urls")\
                       .order_by("-metadata__title")\
                       .annotate(is_secured=Count("allowed_operation"),
                                 layers_count=Count("layer"))

    def for_tree_view(self):
        return self.get_queryset().select_related("metadata")


class FeatureTypeElementXmlManager(models.Manager):
    common_info = {}

    def _reset_local_variables(self):
        # bulk_create will not call the default save() of CommonInfo model. So we need to set the attributes manual. We
        # collect them once.
        now = timezone.now()
        current_user = get_current_user()
        self.common_info = {"created_at": now,
                            "last_modified_at": now,
                            "last_modified_by": current_user,
                            "created_by_user": current_user,
                            "owned_by_org": get_current_owner(),
                            }

    def create_from_parsed_xml(self, parsed_xml, related_object):
        self._reset_local_variables()

        db_element_list = []
        for element in parsed_xml.elements:
            db_element_list.append(self.model(feature_type=related_object,
                                              **self.common_info,
                                              **element.get_field_dict()))
        return self.model.objects.bulk_create(objs=db_element_list)


class LayerManager(TreeManager):

    def get_queryset(self):
        return super().get_queryset().select_related("metadata")

    def for_table_view(self):
        return self.get_queryset()\
            .annotate(children_count=Count("child", distinct=True))\
            .annotate(dataset_metadata_count=Count("dataset_metadata_relation", distinct=True))\
            .select_related("service",
                            "service__metadata",
                            "parent",
                            "parent__metadata",
                            "created_by_user",
                            "owned_by_org")


class FeatureTypeManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related("metadata")

    def for_table_view(self):
        return self.get_queryset()\
            .annotate(elements_count=Count("element", distinct=True))\
            .annotate(dataset_metadata_count=Count("dataset_metadata_relation", distinct=True))\
            .select_related("service",
                            "service__metadata",
                            "service__service_type",
                            "created_by_user",
                            "owned_by_org")


class FeatureTypeElementManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related("feature_type")

    def for_table_view(self):
        return self.get_queryset().select_related("feature_type__metadata",
                                                  "feature_type__service",
                                                  "feature_type__service__service_type",
                                                  "feature_type__service__metadata",
                                                  "created_by_user",
                                                  "owned_by_org")

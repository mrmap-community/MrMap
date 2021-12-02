from django.contrib.auth.models import Group
from rest_framework_json_api.schemas.openapi import AutoSchema
from rest_framework_json_api.views import ModelViewSet

from users.api.filters.groups import OrganizationFilterSet
from users.api.serializers.groups import (GroupSerializer,
                                          OrganizationSerializer)
from users.models.groups import Organization


class GroupViewSet(ModelViewSet):
    schema = AutoSchema(
        tags=['Users'],
    )
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_queryset(self):
        queryset = super(GroupViewSet, self).get_queryset()
        if "parent_lookup_user" in self.kwargs:
            queryset = queryset.filter(
                user__id=self.kwargs["parent_lookup_user"])
        return queryset


class OrganizationViewSet(ModelViewSet):
    schema = AutoSchema(
        tags=['Users'],
    )
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filterset_class = OrganizationFilterSet
    search_fields = ('id', 'name')

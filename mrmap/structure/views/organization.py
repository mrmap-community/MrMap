from django.contrib.auth import get_user_model
from django.db.models import Case, When
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin
from django_bootstrap_swt.components import Badge
from django_bootstrap_swt.enums import BadgeColorEnum
from django_filters.views import FilterView
from MrMap.messages import ORGANIZATION_SUCCESSFULLY_EDITED
from guardian_roles.models.acl import AccessControlList
from main.buttons import DefaultActionButtons
from main.views import SecuredDependingListMixin, SecuredListMixin, SecuredDetailView, SecuredUpdateView
from structure.forms import OrganizationChangeForm
from structure.models import Organization, PublishRequest
from structure.tables.tables import OrganizationTable, OrganizationDetailTable, OrganizationPublishersTable, \
    OrganizationAccessControlListTable


class OrganizationDetailContextMixin(ContextMixin):
    object = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab_nav = [{'url': self.object.get_absolute_url,
                    'title': _('Details')},
                   {'url': self.object.publishers_uri,
                    'title': _('Publishers ').__str__() +
                             Badge(content=str(self.object.get_publishers().count()),
                                   color=BadgeColorEnum.SECONDARY)},

                   ]
        context.update({"object": self.object,
                        'actions': [DefaultActionButtons(instance=self.object, request=self.request).render()],
                        'tab_nav': tab_nav,
                        'publisher_requests_count': PublishRequest.objects.filter(from_organization=self.object).count()})
        return context


class OrganizationTableView(SecuredListMixin, FilterView):
    model = Organization
    table_class = OrganizationTable
    filterset_fields = {'organization_name': ['icontains'],
                        'description': ['icontains']}


class OrganizationDetailView(OrganizationDetailContextMixin, SecuredDetailView):
    class Meta:
        verbose_name = _('Details')

    model = Organization
    template_name = 'MrMap/detail_views/table_tab.html'
    title = _('Details')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        details_table = OrganizationDetailTable(data=[self.object, ], request=self.request)
        context.update({'table': details_table})
        return context


class OrganizationUpdateView(SecuredUpdateView):
    model = Organization
    template_name = "MrMap/detail_views/generic_form.html"
    form_class = OrganizationChangeForm
    success_message = ORGANIZATION_SUCCESSFULLY_EDITED
    title = _('Edit organization')


class OrganizationPublishersTableView(SecuredDependingListMixin, OrganizationDetailContextMixin, FilterView):
    model = Organization
    depending_model = Organization
    depending_field_name = 'can_publish_for'
    table_class = OrganizationPublishersTable
    filterset_fields = {'organization_name': ['icontains']}
    template_name = 'MrMap/detail_views/table_tab.html'


class OrganizationAccessControlListTableView(SecuredDependingListMixin, OrganizationDetailContextMixin, FilterView):
    model = AccessControlList
    depending_model = Organization
    depending_field_name = 'owned_by_org'
    table_class = OrganizationAccessControlListTable
    #filterset_fields = {'organization_name': ['icontains']}
    template_name = 'MrMap/detail_views/table_tab.html'

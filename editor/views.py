from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.views.generic import DeleteView
from MrMap.decorators import permission_required, ownership_required
from MrMap.messages import METADATA_RESTORING_SUCCESS, SERVICE_MD_RESTORED
from MrMap.views import GenericUpdateView, ConfirmView
from editor.forms import MetadataEditorForm
from service.helper.enums import MetadataEnum, ResourceOriginEnum
from service.models import Metadata
from structure.permissionEnums import PermissionEnum
from users.helper import user_helper


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required(PermissionEnum.CAN_REMOVE_DATASET_METADATA.value), name='dispatch')
@method_decorator(ownership_required(klass=Metadata, id_name='pk'), name='dispatch')
class DatasetDelete(DeleteView):
    model = Metadata
    success_url = reverse_lazy('resource:index')
    template_name = 'generic_views/generic_confirm.html'
    # todo: filter isn't working as expected. See issue #519
    #  what's about dataset metadatas without any relations?
    queryset = Metadata.objects.filter(metadata_type=MetadataEnum.DATASET.value, related_metadata__origin=ResourceOriginEnum.EDITOR.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update({
            "action_url": self.object.remove_view_uri,
            "action": _("Delete"),
            "msg": _("Are you sure you want to delete " + self.object.__str__()) + "?"
        })
        return context

    def delete(self, request, *args, **kwargs):
        """
            Creates an async task job which will do the deletion on the fetched object and then redirect to the
            success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete(force=True)
        messages.success(self.request, message=_("Dataset successfully deleted."))
        return HttpResponseRedirect(success_url)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required(PermissionEnum.CAN_EDIT_METADATA.value), name='dispatch')
@method_decorator(ownership_required(klass=Metadata, id_name='pk'), name='dispatch')
class EditMetadata(GenericUpdateView):
    model = Metadata
    form_class = MetadataEditorForm
    queryset = Metadata.objects.all().exclude(metadata_type=MetadataEnum.CATALOGUE.value)

    def get_object(self, queryset=None):
        instance = super().get_object(queryset=queryset)
        self.action_url = instance.edit_view_uri
        self.action = _("Edit " + instance.__str__())
        return instance


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required(PermissionEnum.CAN_EDIT_METADATA.value), name='dispatch')
@method_decorator(ownership_required(klass=Metadata, id_name='pk'), name='dispatch')
class RestoreMetadata(ConfirmView):
    model = Metadata
    no_cataloge_type = ~Q(metadata_type=MetadataEnum.CATALOGUE.value)
    is_custom = Q(is_custom=True)
    queryset = Metadata.objects.filter(is_custom | no_cataloge_type)
    action = _("Restore")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"is_confirmed_label": _("Do you really want to restore Metadata?")})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "action_url": self.object.restore_view_uri,
        })
        return context

    def form_valid(self, form):
        self.object = self.get_object()

        ext_auth = self.object.get_external_authentication_object()

        self.object.restore(self.object.identifier, external_auth=ext_auth)

        # Todo: add last_changed_by_user field to Metadata and move this piece of code to Metadata.restore()
        if self.object.is_metadata_type(MetadataEnum.DATASET):
            user_helper.create_group_activity(self.object.created_by, self.request.user, SERVICE_MD_RESTORED,
                                              "{}".format(self.object.title, ))
        else:
            user_helper.create_group_activity(self.object.created_by, self.request.user, SERVICE_MD_RESTORED,
                                              "{}: {}".format(self.object.get_root_metadata().title,
                                                              self.object.title))

        success_url = self.get_success_url()
        messages.add_message(self.request, messages.SUCCESS, METADATA_RESTORING_SUCCESS)
        return HttpResponseRedirect(success_url)

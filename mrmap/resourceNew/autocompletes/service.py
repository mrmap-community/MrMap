from dal import autocomplete
from guardian.mixins import LoginRequiredMixin

from main.autocompletes import SecuredAutocompleteMixin
from resourceNew.models import OgcServiceClient


class ServiceAutocomplete(SecuredAutocompleteMixin, LoginRequiredMixin, autocomplete.Select2QuerySetView):
    model = OgcServiceClient
    search_fields = ['title', 'id']

    def get_queryset(self):
        return super().get_queryset().select_related("metadata")

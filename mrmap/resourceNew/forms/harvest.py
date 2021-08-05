from django import forms

from main.forms import Form
from resourceNew.models import CswService


class StartHarvest(Form):
    service = forms.ModelChoiceField(queryset=CswService.objects.all())

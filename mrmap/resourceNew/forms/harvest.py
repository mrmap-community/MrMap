from django import forms

from main.forms import Form
from resourceNew.models import OgcCsw


class StartHarvest(Form):
    service = forms.ModelChoiceField(queryset=OgcCsw.objects.all())

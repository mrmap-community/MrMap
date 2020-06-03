"""
Author: Michel Peltriaux
Organization: Spatial data infrastructure Rhineland-Palatinate, Germany
Contact: michel.peltriaux@vermkv.rlp.de
Created on: 09.07.19

"""
from django.conf.urls import url
from django.urls import path

from editor.autocompletes import KeywordAutocomplete, CategoryAutocomplete, DatasetMetadataAutocomplete, \
    MetadataLanguageAutocomplete
from editor.views import *
from editor.wizards import DATASET_WIZARD_FORMS, DatasetWizard

app_name = 'editor'
urlpatterns = [
    path('', index, name='index'),
    path('keyword-autocomplete/', KeywordAutocomplete.as_view(create_field="keyword"), name="keyword-autocomplete"),
    path('category-autocomplete/', CategoryAutocomplete.as_view(), name="category-autocomplete"),
    path('metadata-autocomplete/', DatasetMetadataAutocomplete.as_view(), name="metadata-autocomplete"),
    path('language-autocomplete/', MetadataLanguageAutocomplete.as_view(), name="language-autocomplete"),
    path('wms/', index_wms, name='wms-index'),
    path('wfs/', index_wfs, name='wfs-index'),
    path('datasets/', index_datasets, name='datasets-index'),
    path('metadata/<metadata_id>', edit, name='edit'),

    path('dataset/wizard/<current_view>', add_new_dataset_wizard, name="dataset-metadata-wizard-new"),
    path('dataset/wizard/<current_view>/<instance_id>', edit_dataset_wizard, name="dataset-metadata-wizard-instance"),

    path('dataset/remove/<metadata_id>', remove_dataset, name='remove-dataset-metadata'),
    path('access/<id>', edit_access, name='edit_access'),
    path('access/<id>/geometry-form/', access_geometry_form, name='access_geometry_form'),
    path('restore/<metadata_id>', restore, name='restore'),
    path('restore-dataset-metadata/<metadata_id>', restore_dataset_metadata, name='restore-dataset-metadata'),
]

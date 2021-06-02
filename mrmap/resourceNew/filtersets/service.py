import django_filters
from resourceNew.models.service import Layer


class LayerFilterSet(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='metadata__title', lookup_expr='iexact')

    class Meta:
        model = Layer
        fields = {
            "id": ["in", ]
        }

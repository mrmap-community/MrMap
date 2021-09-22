from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from main.models import GenericModelMixin, CommonInfo
from resourceNew.models import DatasetMetadata, LayerMetadata, FeatureTypeMetadata


class MapContext(GenericModelMixin, CommonInfo):
    title = models.CharField(max_length=1000,
                             verbose_name=_("title"),
                             help_text=_("a short descriptive title for this map context"))
    abstract = models.TextField(null=True,
                                verbose_name=_("abstract"),
                                help_text=_("brief summary of the topic of this map context"))

    # Additional possible parameters:
    # specReference
    # language
    # author
    # publisher
    # creator
    # rights
    # areaOfInterest
    # timeIntervalOfInterest
    # keyword
    # resource
    # contextMetadata
    # extension

    def __str__(self):
        return self.title


class MapContextLayer(MPTTModel):
    parent = TreeForeignKey("MapContextLayer", on_delete=models.CASCADE, null=True, blank=True,
                            related_name="child_layers")
    map_context = models.ForeignKey(MapContext, on_delete=models.CASCADE)
    name = models.CharField(max_length=1000,
                            null=False,
                            blank=False,
                            verbose_name=_("name"),
                            help_text=_("an identifying name for this map context layer"))
    title = models.CharField(max_length=1000,
                             null=True,
                             blank=True,
                             verbose_name=_("title"),
                             help_text=_("a short descriptive title for this map context layer"))
    dataset_metadata = models.ForeignKey(DatasetMetadata,
                                         on_delete=models.CASCADE,
                                         null=True,
                                         blank=True)
    # TODO
    # layer_metadata = models.ForeignKey(LayerMetadata,
    #                                   on_delete=models.CASCADE,
    #                                   null=True,
    #                                   blank=True)
    # TODO
    #feature_type_metadata = models.ForeignKey(FeatureTypeMetadata,
    #                                          on_delete=models.CASCADE,
    #                                          null=True,
    #                                          blank=True)
    preview_image = models.ImageField(null=True, blank=True)
    # zukünftig: kml, gml, ...

    def __str__(self):
        return f"{self.name}"

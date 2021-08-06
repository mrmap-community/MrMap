from eulxml import xmlmap

from resourceNew.xmlmapper.ogc.capabilities.metadata import KeywordConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.metadata import WmsServiceMetadata, WmsLayerMetadata


class Wms100ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.NodeListField(xpath="Keywords", node_class=KeywordConverter)


class Wms100LayerMetadata(WmsLayerMetadata):
    """xml mapper class for wms layer metadata information for service version == 1.0.0."""
    title = xmlmap.StringField(xpath="Title")
    abstract = xmlmap.StringField(xpath="Abstract")
    keywords = xmlmap.NodeListField(xpath="Keywords", node_class=KeywordConverter)

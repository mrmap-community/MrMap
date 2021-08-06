from eulxml import xmlmap

from resourceNew.xmlmapper.ogc.capabilities.metadata import KeywordConverter, MetadataUrlConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.metadata import WmsServiceMetadata, WmsLayerMetadata


class Wms110ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.NodeListField(xpath="KeywordList/Keyword", node_class=KeywordConverter)


class Wms110LayerMetadata(WmsLayerMetadata):
    """xml mapper class for wms layer metadata information for service version >= 1.1.0 and < 1.3.0"""
    title = xmlmap.StringField(xpath="Title")
    abstract = xmlmap.StringField(xpath="Abstract")
    keywords = xmlmap.NodeListField(xpath="KeywordList/Keyword", node_class=KeywordConverter)
    remote_metadata = xmlmap.NodeListField(xpath="MetadataUrl", node_class=MetadataUrlConverter)

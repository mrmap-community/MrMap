from eulxml import xmlmap
from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.ogc.capabilities.metadata import ServiceMetadataContact, ServiceMetadata


class WmsServiceMetadataContact(ServiceMetadataContact):
    ROOT_NAME = "ContactInformation"


class WmsServiceMetadata(ServiceMetadata):
    ROOT_NAME = "Service"


class WmsLayerMetadata(DBModelConverterMixin, xmlmap.XmlObject):
    """Abstract xml mapper class with basic xmlmap attributes for wms layers."""
    model = 'resourceNew.LayerMetadata'
    ROOT_NAME = "Layer"

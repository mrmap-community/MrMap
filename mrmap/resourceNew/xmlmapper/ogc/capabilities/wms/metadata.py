from resourceNew.xmlmapper.mixins import DBModelConverter
from resourceNew.xmlmapper.ogc.capabilities.metadata import ServiceMetadataContact, OgcServiceMetadataConverter


class WmsServiceMetadataContact(ServiceMetadataContact):
    ROOT_NAME = "ContactInformation"

    def convert_to_model(self, **kwargs):
        return self.get_model_class()(**self.get_field_dict())


class WmsServiceMetadata(OgcServiceMetadataConverter):
    ROOT_NAME = "Service"


class WmsLayerMetadata(DBModelConverter):
    """Abstract xml mapper class with basic xmlmap attributes for wms layers."""
    model = 'resourceNew.LayerMetadata'
    ROOT_NAME = "Layer"

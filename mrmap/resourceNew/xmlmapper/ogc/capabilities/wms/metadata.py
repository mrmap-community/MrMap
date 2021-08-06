from eulxml import xmlmap

from resourceNew.xmlmapper.mixins import DBModelConverter
from resourceNew.xmlmapper.ogc.capabilities.metadata import ServiceMetadataContact, OgcServiceMetadataConverter


class WmsServiceMetadataContact(ServiceMetadataContact):
    ROOT_NAME = "ContactInformation"

    name = xmlmap.StringField(xpath="ContactPersonPrimary/ContactOrganization")
    person_name = xmlmap.StringField(xpath="ContactPersonPrimary/ContactPerson")
    phone = xmlmap.StringField(xpath="ContactVoiceTelephone")
    facsimile = xmlmap.StringField(xpath="ContactFacsimileTelephone")
    email = xmlmap.StringField(xpath="ContactElectronicMailAddress")
    country = xmlmap.StringField(xpath="ContactAddress/Country")
    postal_code = xmlmap.StringField(xpath="ContactAddress/PostCode")
    city = xmlmap.StringField(xpath="ContactAddress/City")
    state_or_province = xmlmap.StringField(xpath="ContactAddress/StateOrProvince")
    address = xmlmap.StringField(xpath="ContactAddress/Address")

    def convert_to_model(self, **kwargs):
        return self.get_model_class()(**self.get_field_dict())


class WmsServiceMetadata(OgcServiceMetadataConverter):
    ROOT_NAME = "Service"
    service_contact = xmlmap.NodeField(xpath="ContactInformation",
                                       node_class=WmsServiceMetadataContact)


class WmsLayerMetadata(DBModelConverter):
    """Abstract xml mapper class with basic xmlmap attributes for wms layers."""
    model = 'resourceNew.LayerMetadata'
    ROOT_NAME = "Layer"

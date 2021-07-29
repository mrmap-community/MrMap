from eulxml import xmlmap
from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.ogc.capabilities.metadata import ServiceMetadataContact, ServiceMetadata, Keyword, \
    MetadataUrl


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


class WmsServiceMetadata(ServiceMetadata):
    ROOT_NAME = "Service"
    service_contact = xmlmap.NodeField(xpath="ContactInformation",
                                       node_class=WmsServiceMetadataContact)


class Wms100ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.StringListField(xpath="Keywords")


class Wms110ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.NodeListField(xpath="KeywordList//Keyword", node_class=Keyword)


class LayerMetadata(DBModelConverterMixin, xmlmap.XmlObject):
    """Abstract xml mapper class with basic xmlmap attributes for wms layers."""
    model = 'resourceNew.LayerMetadata'
    title = xmlmap.StringField(xpath="Title")
    abstract = xmlmap.StringField(xpath="Abstract")


class LayerMetadata100(LayerMetadata):
    """xml mapper class for wms layer metadata information for service version == 1.0.0."""
    keywords = xmlmap.StringListField(xpath="Keywords")


class LayerMetadata110(LayerMetadata):
    """xml mapper class for wms layer metadata information for service version >= 1.1.0."""
    keywords = xmlmap.NodeListField(xpath="KeywordList//Keyword", node_class=Keyword)
    remote_metadata = xmlmap.NodeListField(xpath="MetadataUrl[@type='TC211']", node_class=MetadataUrl)

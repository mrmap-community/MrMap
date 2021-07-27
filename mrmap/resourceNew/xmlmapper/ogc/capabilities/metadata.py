from eulxml import xmlmap

from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.namespaces import WFS_2_0_0_NAMESPACE, OWS_1_1_0_NAMESPACE, WFS_1_1_2_NAMESPACE, \
    OWS_1_0_0_NAMESPACE


class Keyword(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.Keyword'
    ROOT_NAME = "Keyword"

    keyword = xmlmap.StringField(xpath=".")

    def __str__(self):
        return str(self.keyword)


class ServiceMetadataContact(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.MetadataContact'


class WmsServiceMetadataContact(ServiceMetadataContact):
    ROOT_NAME = "Service"

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


class WfsServiceMetadataContact(ServiceMetadataContact):
    ROOT_NAME = "wfs:WFS_Capabilities/ows:ServiceProvider"

    name = xmlmap.StringField(xpath="ows:ProviderName")
    person_name = xmlmap.StringField(xpath="ows:ServiceContact/ows:IndividualName")
    phone = xmlmap.StringField(xpath="ows:ContactInfo/ows:Phone/ows:Voice")
    facsimile = xmlmap.StringField(xpath="ows:ContactInfo/ows:Phone/ows:Facsimile")
    email = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:ElectronicMailAddress")
    country = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:Country")
    postal_code = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:PostalCode")
    city = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:City")
    state_or_province = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:AdministrativeArea")
    address = xmlmap.StringField(xpath="ows:ContactInfo/ows:Address/ows:DeliveryPoint")


class Wfs110ServiceMetadataContact(WfsServiceMetadataContact):
    ROOT_NAMESPACES = dict([("wfs", WFS_1_1_2_NAMESPACE),
                            ("ows", OWS_1_0_0_NAMESPACE)])


class Wfs200ServiceMetadataContact(WfsServiceMetadataContact):
    ROOT_NAMESPACES = dict([("wfs", WFS_2_0_0_NAMESPACE),
                            ("ows", OWS_1_1_0_NAMESPACE)])


class ServiceMetadata(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.ServiceMetadata'
    ROOT_NAME = "Service"

    title = xmlmap.StringField(xpath="Title")
    abstract = xmlmap.StringField(xpath="Abstract")
    fees = xmlmap.StringField(xpath="Fees")
    access_constraints = xmlmap.StringField(xpath="AccessConstraints")


class WmsServiceMetadata(ServiceMetadata):
    service_contact = xmlmap.NodeField(xpath="ContactInformation",
                                       node_class=WmsServiceMetadataContact)


class Wms100ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.StringListField(xpath="Keywords")


class Wms110ServiceMetadata(WmsServiceMetadata):
    keywords = xmlmap.StringListField(xpath="KeywordList/Keyword")

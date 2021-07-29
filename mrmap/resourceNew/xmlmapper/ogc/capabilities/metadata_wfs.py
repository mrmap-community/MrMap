from eulxml import xmlmap

from resourceNew.xmlmapper.namespaces import WFS_2_0_0_NAMESPACE, OWS_1_1_0_NAMESPACE, WFS_1_1_2_NAMESPACE, \
    OWS_1_0_0_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata import ServiceMetadataContact


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
from eulxml import xmlmap
from resourceNew.xmlmapper.namespaces import WMS_1_3_0_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata import Keyword, MetadataUrl
from resourceNew.xmlmapper.ogc.capabilities.wms.metadata import WmsServiceMetadataContact, WmsServiceMetadata, \
    WmsLayerMetadata


class Wms130Keyword(Keyword):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130MetadataUrl(MetadataUrl):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    type = xmlmap.StringField(xpath="@type")
    format = xmlmap.StringField(xpath="default:Format")
    link = xmlmap.StringField(xpath="default:OnlineResource[@xlink:type='simple']/@xlink:href")


class Wms130ServiceMetadataContact(WmsServiceMetadataContact):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    name = xmlmap.StringField(xpath="default:ContactPersonPrimary/default:ContactOrganization")
    person_name = xmlmap.StringField(xpath="default:ContactPersonPrimary/default:ContactPerson")
    phone = xmlmap.StringField(xpath="default:ContactVoiceTelephone")
    facsimile = xmlmap.StringField(xpath="default:ContactFacsimileTelephone")
    email = xmlmap.StringField(xpath="default:ContactElectronicMailAddress")
    country = xmlmap.StringField(xpath="default:ContactAddress/default:Country")
    postal_code = xmlmap.StringField(xpath="default:ContactAddress/default:PostCode")
    city = xmlmap.StringField(xpath="default:ContactAddress/default:City")
    state_or_province = xmlmap.StringField(xpath="default:ContactAddress/default:StateOrProvince")
    address = xmlmap.StringField(xpath="default:ContactAddress/default:Address")


class Wms130ServiceMetadata(WmsServiceMetadata):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])
    service_contact = xmlmap.NodeField(xpath="default:ContactInformation",
                                       node_class=Wms130ServiceMetadataContact)
    keywords = xmlmap.NodeListField(xpath="default:KeywordList/default:Keyword", node_class=Keyword)


class Wms130LayerMetadata(WmsLayerMetadata):
    """xml mapper class for wms layer metadata information for service version >= 1.3.0."""
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])
    title = xmlmap.StringField(xpath="default:Title")
    abstract = xmlmap.StringField(xpath="default:Abstract")
    keywords = xmlmap.NodeListField(xpath="default:KeywordList//default:Keyword", node_class=Wms130Keyword)
    remote_metadata = xmlmap.NodeListField(xpath="default:MetadataUrl[@type='TC211']", node_class=Wms130MetadataUrl)




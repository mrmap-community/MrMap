from eulxml import xmlmap

from resourceNew.models import Keyword
from resourceNew.xmlmapper.mixins import DBModelConverter
from resourceNew.xmlmapper.namespaces import INSPIRE_VS_NAMESPACE, INSPIRE_COMMON_NAMESPACE, XLINK_NAMESPACE


class RemoteMetadata(DBModelConverter):
    model = 'resourceNew.RemoteMetadata'
    ROOT_NAME = "MetadataUrl"


class KeywordConverter(DBModelConverter):
    model = Keyword
    ROOT_NAME = "Keyword"

    keyword = xmlmap.StringField(xpath=".")

    def __str__(self):
        return self.keyword.__str__()


class InspireMetadataUrl(DBModelConverter):
    ROOT_NAME = "ExtendedCapabilities"
    ROOT_NS = "inspire_vs"
    ROOT_NAMESPACES = dict([("inspire_vs", INSPIRE_VS_NAMESPACE),
                            ("inspire_common", INSPIRE_COMMON_NAMESPACE)])

    link = xmlmap.StringField(xpath="inspire_common:MetadataUrl/inspire_common:URL")
    media_type = xmlmap.StringField(xpath="inspire_common:MetadataUrl/inspire_common:MediaType")
    default_language = xmlmap.StringField(xpath="inspire_common:SupportedLanguages/inspire_common:DefaultLanguage/inspire_common:Language")
    response_language = xmlmap.StringField(xpath="inspire_common:ResponseLanguage/inspire_common:Language")


class ServiceMetadataContact(DBModelConverter):
    model = 'resourceNew.MetadataContact'


class OgcServiceMetadataConverter(DBModelConverter):
    model = 'resourceNew.ServiceMetadata'
    ROOT_NAME = "Service"

    title = xmlmap.StringField(xpath="Title")
    abstract = xmlmap.StringField(xpath="Abstract")
    fees = xmlmap.StringField(xpath="Fees")
    access_constraints = xmlmap.StringField(xpath="AccessConstraints")


class MetadataUrl(DBModelConverter):
    model = 'resourceNew.RemoteMetadata'
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "MetadataUrl"

    type = xmlmap.StringField(xpath="@type")
    format = xmlmap.StringField(xpath="Format")
    link = xmlmap.StringField(xpath="OnlineResource[@xlink:type='simple']/@xlink:href")

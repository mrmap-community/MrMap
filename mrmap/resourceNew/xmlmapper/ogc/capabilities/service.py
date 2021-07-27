from eulxml import xmlmap

from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.namespaces import INSPIRE_VS_NAMESPACE, INSPIRE_COMMON_NAMESPACE, XLINK_NAMESPACE


class InspireMetadataUrl(DBModelConverterMixin, xmlmap.XmlObject):
    ROOT_NAME = "ExtendedCapabilities"
    ROOT_NS = "inspire_vs"
    ROOT_NAMESPACES = dict([("inspire_vs", INSPIRE_VS_NAMESPACE),
                            ("inspire_common", INSPIRE_COMMON_NAMESPACE)])

    link = xmlmap.StringField(xpath="inspire_common:MetadataUrl/inspire_common:URL")
    media_type = xmlmap.StringField(xpath="inspire_common:MetadataUrl/inspire_common:MediaType")
    default_language = xmlmap.StringField(xpath="inspire_common:SupportedLanguages/inspire_common:DefaultLanguage/inspire_common:Language")
    response_language = xmlmap.StringField(xpath="inspire_common:ResponseLanguage/inspire_common:Language")


class OperationUrl(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.OperationUrl'
    ROOT_NAME = "OnlineResource"
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    url = xmlmap.StringField(xpath="@xlink:href")

    def get_field_dict(self):
        dic = super().get_field_dict()
        method = dic.get("method", None)
        if method and ":" in method:
            dic.update({"method": method.rsplit(":", 1)[-1]})
        url = dic.get("url", None)
        if url:
            dic.update({"url": url.split("?", 1)[0]})
        return dic


class Service(DBModelConverterMixin, xmlmap.XmlObject):
    """Abstract service xml mapper class"""
    model = 'resourceNew.Service'
    ROOT_NAMESPACES = dict([("inspire_vs", INSPIRE_VS_NAMESPACE),
                            ("xlink", XLINK_NAMESPACE)])

    remote_metadata = xmlmap.NodeField(xpath="inspire_vs:ExtendedCapabilities",
                                       node_class=InspireMetadataUrl)
    url = xmlmap.StringField(xpath="Service/OnlineResource[@xlink:type='simple']/@xlink:href")



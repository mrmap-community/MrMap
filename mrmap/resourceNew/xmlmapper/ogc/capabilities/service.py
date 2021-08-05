from eulxml import xmlmap
from resourceNew.xmlmapper.exceptions import SemanticError
from resourceNew.xmlmapper.mixins import DBModelConverter
from resourceNew.xmlmapper.namespaces import INSPIRE_VS_NAMESPACE, XLINK_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata import InspireMetadataUrl
from resourceNew.models.service import Service


class ReferenceSystem(DBModelConverter):
    model = "resourceNew.ReferenceSystem"

    ref_system = xmlmap.StringField(xpath=".")

    def get_field_dict(self):
        dic = super().get_field_dict()

        ref_system = dic.get("ref_system", None)
        if "::" in ref_system:
            # example: ref_system = urn:ogc:def:crs:EPSG::4326
            code = ref_system.rsplit(":")[-1]
            prefix = ref_system.rsplit(":")[-3]
        elif ":" in ref_system:
            # example: ref_system = EPSG:4326
            code = ref_system.rsplit(":")[-1]
            prefix = ref_system.rsplit(":")[-2]
        else:
            raise SemanticError("reference system unknown")
        dic.update({"code": code,
                    "prefix": prefix.upper()})
        del dic["ref_system"]
        return dic

    def convert_to_model(self, **kwargs):
        return self.get_model_class()(**self.get_field_dict())


class OnlineResource(DBModelConverter):
    ROOT_NAME = "OnlineResource"
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    url = xmlmap.StringField(xpath="@xlink:href")
    type = xmlmap.StringField(xpath="@xlink:type")

    def get_field_dict(self):
        dic = super().get_field_dict()
        method = dic.get("method", None)
        if method and ":" in method:
            dic.update({"method": method.rsplit(":", 1)[-1]})
        url = dic.get("url", None)
        if url:
            dic.update({"url": url.split("?", 1)[0]})
        return dic


class OperationUrl(DBModelConverter):
    model = "resourceNew.OperationUrl"

    def convert_to_model(self, **kwargs):
        instance = super().convert_to_model()
        instance.method = self.method
        instance.operation = self.operation
        instance.url = self.url
        return instance


class OgcServiceCapabilitiesConverter(DBModelConverter):
    """Converter service xml mapper class"""
    model = Service
    ROOT_NAMESPACES = dict([("inspire_vs", INSPIRE_VS_NAMESPACE),
                            ("xlink", XLINK_NAMESPACE)])
    remote_metadata = xmlmap.NodeField(xpath="inspire_vs:ExtendedCapabilities",
                                       node_class=InspireMetadataUrl)
    url = xmlmap.StringField(xpath="Service/OnlineResource[@xlink:type='simple']/@xlink:href")
    version = xmlmap.StringField(xpath="@version")

from pathlib import Path
from eulxml import xmlmap
from resourceNew.enums.service import OGCServiceEnum, OGCServiceVersionEnum
from resourceNew.xmlmapper.namespaces import NS_WC
from resourceNew.xmlmapper.ogc.capabilities.wms.a.service import Wms100CapabilitiesConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.b.service import Wms110CapabilitiesConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.c.service import Wms130CapabilitiesConverter


class ServiceType(xmlmap.XmlObject):
    _wms_name = xmlmap.StringField(xpath=f"{NS_WC}Service']/{NS_WC}Name']")
    _wfs_csw_name = xmlmap.StringField(xpath=f"{NS_WC}ServiceIdentification']/{NS_WC}ServiceType']")
    version = xmlmap.StringField(xpath=f"@{NS_WC}version']")

    @property
    def service_type(self):
        name = ""
        if self._wms_name:
            name = self._wms_name.__str__()
        elif self._wfs_csw_name:
            name = self._wfs_csw_name.__str__()
        if ":" in name:
            name = name.split(":")[1]
        return name

    def is_service_type(self, service_type: OGCServiceEnum):
        if self.service_type.lower() == service_type.value.lower():
            return True
        return False

    def is_version(self, version: OGCServiceVersionEnum):
        if self.version and self.version == version.value:
            return True
        return False


def OgcServiceXml(xml):
    """Factory function to deserialize given xml documents with the right xmlmapper and return it as xmlmap.XmlObject.

    :param xml: the xml as string | bytes | Path
    :return web_service: the parsed webservice from given xml
    :rtype: xmlmap.XmlObject
    """
    if isinstance(xml, str) or isinstance(xml, bytes):
        load_func = xmlmap.load_xmlobject_from_string
    elif isinstance(xml, Path):
        xml = xml.resolve().__str__()
        load_func = xmlmap.load_xmlobject_from_file
    else:
        raise ValueError("xml must be ether a str or Path")

    xml_class = None
    service_type = load_func(xml, xmlclass=ServiceType)
    if service_type.is_service_type(OGCServiceEnum.WMS):
        if service_type.is_version(OGCServiceVersionEnum.V_1_0_0):
            xml_class = Wms100CapabilitiesConverter
        elif service_type.is_version(OGCServiceVersionEnum.V_1_1_0) or \
                service_type.is_version(OGCServiceVersionEnum.V_1_1_1):
            xml_class = Wms110CapabilitiesConverter
        elif service_type.is_version(OGCServiceVersionEnum.V_1_3_0):
            xml_class = Wms130CapabilitiesConverter
    elif service_type.is_service_type(OGCServiceEnum.WFS):
        pass
    elif service_type.is_service_type(OGCServiceEnum.CSW):
        pass

    if not xml_class:
        raise NotImplementedError(f"unsupported service type `{service_type.service_type}` with version "
                                  f"`{service_type.version}` detected.")

    return load_func(xml, xmlclass=xml_class)

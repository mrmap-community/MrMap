from eulxml import xmlmap
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE, INSPIRE_VS_NAMESPACE, WMS_1_3_0_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata import RemoteMetadata
from resourceNew.xmlmapper.ogc.capabilities.service import ReferenceSystem, OgcServiceCapabilitiesConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.service import LegendUrlConverter, StyleConverter, LayerConverter, WmsGetCapabilitiesUrls, \
    WmsGetMapUrls, WmsGetFeatureInfoUrls, WmsDescribeLayerUrls, WmsGetLegendGraphicUrls, WmsGetStylesUrls, \
    WmsOperationUrlsMixin
from resourceNew.xmlmapper.ogc.capabilities.wms.c.metadata import Wms130ServiceMetadata, Wms130LayerMetadata, \
    Wms130Keyword


class Wms130RemoteMetadata(RemoteMetadata):
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE),
                            ("default", WMS_1_3_0_NAMESPACE)])
    ROOT_NS = "default"
    ignore_fields = ["mime_type", "type"]

    type = xmlmap.StringField(xpath="@type")
    mime_type = xmlmap.StringField(xpath="default:Format")
    link = xmlmap.StringField(xpath="default:OnlineResource/@xlink:href")


class Wms130ReferenceSystem(ReferenceSystem):
    ROOT_NAME = "CRS"
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130LegendUrl(LegendUrlConverter):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    legend_url = xmlmap.StringField(xpath="default:OnlineResource[@xlink:type='simple']/@xlink:href")
    height = xmlmap.IntegerField(xpath="@height")
    width = xmlmap.IntegerField(xpath="@width")
    mime_type = xmlmap.StringField(xpath="default:Format")


class Wms130Style(StyleConverter):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    name = xmlmap.StringField(xpath="default:Name")
    title = xmlmap.StringField(xpath="default:Title")
    legend_url = xmlmap.NodeField(xpath="default:LegendURL", node_class=Wms130LegendUrl)


class Wms130LayerConverter(LayerConverter):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    scale_min = xmlmap.FloatField(xpath="default:MinScaleDenominator")
    scale_max = xmlmap.FloatField(xpath="default:MaxScaleDenominator")
    bbox_min_x = xmlmap.FloatField(xpath="default:EX_GeographicBoundingBox/default:westBoundLongitude")
    bbox_max_x = xmlmap.FloatField(xpath="default:EX_GeographicBoundingBox/default:eastBoundLongitude")
    bbox_min_y = xmlmap.FloatField(xpath="default:EX_GeographicBoundingBox/default:southBoundLatitude")
    bbox_max_y = xmlmap.FloatField(xpath="default:EX_GeographicBoundingBox/default:northBoundLatitude")
    identifier = xmlmap.StringField(xpath="default:Name")
    styles = xmlmap.NodeListField(xpath="default:Style", node_class=Wms130Style)
    is_queryable = xmlmap.SimpleBooleanField(xpath="@queryable", true=1, false=0)
    is_opaque = xmlmap.SimpleBooleanField(xpath="@opaque", true=1, false=0)
    is_cascaded = xmlmap.SimpleBooleanField(xpath="@cascaded", true=1, false=0)
    remote_metadata = xmlmap.NodeListField(xpath="default:MetadataURL", node_class=Wms130RemoteMetadata)

    # dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension130)
    reference_systems = xmlmap.NodeListField(xpath="default:CRS", node_class=Wms130ReferenceSystem)
    children = xmlmap.NodeListField(xpath="default:Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=Wms130LayerMetadata)
    keywords = xmlmap.NodeListField(xpath="default:KeywordList/default:Keyword", node_class=Wms130Keyword)


class Wms130GetCapabilitiesUrls(WmsGetCapabilitiesUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130GetMapUrls(WmsGetMapUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130GetFeatureInfoUrls(WmsGetFeatureInfoUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130DescribeLayerUrls(WmsDescribeLayerUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130GetLegendGraphicUrls(WmsGetLegendGraphicUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130GetStylesUrls(WmsGetStylesUrls):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])


class Wms130OperationUrlsMixin(WmsOperationUrlsMixin):
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])

    get_capabilities_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:GetCapabilities",
                                             node_class=Wms130GetCapabilitiesUrls)
    get_map_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:GetMap",
                                    node_class=Wms130GetMapUrls)
    get_feature_info_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:GetFeatureInfo",
                                             node_class=Wms130GetFeatureInfoUrls)
    get_describe_layer_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:DescribeLayer",
                                               node_class=Wms130DescribeLayerUrls)
    get_legend_graphic_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:GetLegendGraphic",
                                               node_class=Wms130GetLegendGraphicUrls)
    get_styles_urls = xmlmap.NodeField(xpath="default:Capability/default:Request/default:GetStyles",
                                       node_class=Wms130GetStylesUrls)


class Wms130CapabilitiesConverter(Wms130OperationUrlsMixin, OgcServiceCapabilitiesConverter):
    """Converter service xml mapper class"""
    ROOT_NS = "default"
    ROOT_NAME = "WMS_Capabilities"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE),
                            ("inspire_vs", INSPIRE_VS_NAMESPACE),
                            ("xlink", XLINK_NAMESPACE)])
    XSD_SCHEMA = "http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd"

    url = xmlmap.StringField(xpath="default:Service/default:OnlineResource[@xlink:type='simple']/@xlink:href")
    service_metadata = xmlmap.NodeField(xpath="default:Service", node_class=Wms130ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="default:Capability/default:Layer", node_class=Wms130LayerConverter)

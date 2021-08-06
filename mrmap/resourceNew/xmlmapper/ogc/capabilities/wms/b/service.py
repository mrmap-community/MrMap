from eulxml import xmlmap
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE, INSPIRE_VS_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata import RemoteMetadata, KeywordConverter
from resourceNew.xmlmapper.ogc.capabilities.service import ReferenceSystem, OgcServiceCapabilitiesConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.service import LegendUrlConverter, StyleConverter, LayerConverter, WmsOperationUrlsMixin, \
    WmsGetCapabilitiesUrls, WmsGetMapUrls, WmsGetFeatureInfoUrls, WmsDescribeLayerUrls, WmsGetLegendGraphicUrls, \
    WmsGetStylesUrls
from resourceNew.xmlmapper.ogc.capabilities.wms.b.metadata import Wms110ServiceMetadata, Wms110LayerMetadata


class Wms110RemoteMetadata(RemoteMetadata):
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ignore_fields = ["mime_type", "type"]

    type = xmlmap.StringField(xpath="@type")
    mime_type = xmlmap.StringField(xpath="default:Format")
    link = xmlmap.StringField(xpath="OnlineResource/@xlink:href")


class Wms110ReferenceSystem(ReferenceSystem):
    ROOT_NAME = "SRS"


class Wms110LegendUrl(LegendUrlConverter):
    legend_url = xmlmap.StringField(xpath="OnlineResource[@xlink:type='simple']/@xlink:href")
    height = xmlmap.IntegerField(xpath="@height")
    width = xmlmap.IntegerField(xpath="@width")
    mime_type = xmlmap.StringField(xpath="Format")


class Wms110Style(StyleConverter):
    name = xmlmap.StringField(xpath="Name")
    title = xmlmap.StringField(xpath="Title")
    legend_url = xmlmap.NodeField(xpath="LegendURL", node_class=Wms110LegendUrl)


class Wms110Layer(LayerConverter):
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")
    identifier = xmlmap.StringField(xpath="Name")
    styles = xmlmap.NodeListField(xpath="Style", node_class=Wms110Style)
    is_queryable = xmlmap.SimpleBooleanField(xpath="@queryable", true=1, false=0)
    is_opaque = xmlmap.SimpleBooleanField(xpath="@opaque", true=1, false=0)
    is_cascaded = xmlmap.SimpleBooleanField(xpath="@cascaded", true=1, false=0)
    remote_metadata = xmlmap.NodeListField(xpath="MetadataURL", node_class=Wms110RemoteMetadata)

    # dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)

    reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=Wms110ReferenceSystem)
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=Wms110LayerMetadata)
    keywords = xmlmap.NodeListField(xpath="default:KeywordList/default:Keyword", node_class=KeywordConverter)


class Wms110GetCapabilitiesUrls(WmsGetCapabilitiesUrls):
    pass


class Wms110GetMapUrls(WmsGetMapUrls):
    pass


class Wms110GetFeatureInfoUrls(WmsGetFeatureInfoUrls):
    pass


class Wms110DescribeLayerUrls(WmsDescribeLayerUrls):
    pass


class Wms110GetLegendGraphicUrls(WmsGetLegendGraphicUrls):
    pass


class Wms110GetStylesUrls(WmsGetStylesUrls):
    pass


class Wms110OperationUrlsMixin(WmsOperationUrlsMixin):
    get_capabilities_urls = xmlmap.NodeField(xpath="Capability/Request/GetCapabilities",
                                             node_class=Wms110GetCapabilitiesUrls)
    get_map_urls = xmlmap.NodeField(xpath="Capability/Request/GetMap",
                                    node_class=Wms110GetMapUrls)
    get_feature_info_urls = xmlmap.NodeField(xpath="Capability/Request/GetFeatureInfo",
                                             node_class=Wms110GetFeatureInfoUrls)
    get_describe_layer_urls = xmlmap.NodeField(xpath="Capability/Request/DescribeLayer",
                                               node_class=Wms110DescribeLayerUrls)
    get_legend_graphic_urls = xmlmap.NodeField(xpath="Capability/Request/GetLegendGraphic",
                                               node_class=Wms110GetLegendGraphicUrls)
    get_styles_urls = xmlmap.NodeField(xpath="Capability/Request/GetStyles",
                                       node_class=Wms110GetStylesUrls)


class Wms110CapabilitiesConverter(Wms110OperationUrlsMixin, OgcServiceCapabilitiesConverter):
    """Abstract service xml mapper class"""
    ROOT_NAMESPACES = dict([("inspire_vs", INSPIRE_VS_NAMESPACE),
                           ("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "WMT_MS_Capabilities"
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=Wms110ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="Capability/Layer", node_class=Wms110Layer)

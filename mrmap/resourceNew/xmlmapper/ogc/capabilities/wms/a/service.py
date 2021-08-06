from eulxml import xmlmap
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.service import ReferenceSystem, OgcServiceCapabilitiesConverter
from resourceNew.xmlmapper.ogc.capabilities.wms.service import LegendUrlConverter, StyleConverter, LayerConverter, \
    WmsOperationUrlsMixin, WmsGetCapabilitiesUrls, WmsGetMapUrls, WmsGetFeatureInfoUrls, WmsDescribeLayerUrls, \
    WmsGetLegendGraphicUrls, WmsGetStylesUrls
from resourceNew.xmlmapper.ogc.capabilities.wms.a.metadata import Wms100ServiceMetadata, Wms100LayerMetadata


class Wms100ReferenceSystem(ReferenceSystem):
    ROOT_NAME = "SRS"


class Wms100LegendUrl(LegendUrlConverter):
    legend_url = xmlmap.StringField(xpath="OnlineResource[@xlink:type='simple']/@xlink:href")
    height = xmlmap.IntegerField(xpath="@height")
    width = xmlmap.IntegerField(xpath="@width")
    mime_type = xmlmap.StringField(xpath="Format")


class Wms100Style(StyleConverter):
    name = xmlmap.StringField(xpath="Name")
    title = xmlmap.StringField(xpath="Title")
    legend_url = xmlmap.NodeField(xpath="LegendURL", node_class=Wms100LegendUrl)


class Wms100Layer(LayerConverter):
    """xml mapper class for wms layer information for service version >= 1.0.0 and < 1.1.1"""
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")
    identifier = xmlmap.StringField(xpath="Name")
    styles = xmlmap.NodeListField(xpath="Style", node_class=Wms100Style)
    is_queryable = xmlmap.SimpleBooleanField(xpath="@queryable", true=1, false=0)
    is_opaque = xmlmap.SimpleBooleanField(xpath="@opaque", true=1, false=0)
    is_cascaded = xmlmap.SimpleBooleanField(xpath="@cascaded", true=1, false=0)
    # todo: has wms 1.0.0 linked metadata?
    remote_metadata = []

    #dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)
    _reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=Wms100ReferenceSystem)
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=Wms100LayerMetadata)

    @property
    def reference_systems(self):
        # wms 1.0.0 supports whitelist spacing of srs. There is no default split function way in xpath 1.0
        _reference_systems = []
        for reference_system in self._reference_systems:
            if " " in reference_system:
                for _ref_system in reference_system.split(" "):
                    _concrete_reference_system = ReferenceSystem()
                    _concrete_reference_system.ref_system = _ref_system
                    _reference_systems.append(_concrete_reference_system)
            else:
                _reference_systems.append(reference_system)
        return _reference_systems

    @reference_systems.setter
    def reference_systems(self, reference_systems):
        # Todo: implement this setter
        raise NotImplementedError


class Wms100GetCapabilitiesUrls(WmsGetCapabilitiesUrls):
    pass


class Wms100GetMapUrls(WmsGetMapUrls):
    pass


class Wms100GetFeatureInfoUrls(WmsGetFeatureInfoUrls):
    pass


class Wms100DescribeLayerUrls(WmsDescribeLayerUrls):
    pass


class Wms100GetLegendGraphicUrls(WmsGetLegendGraphicUrls):
    pass


class Wms100GetStylesUrls(WmsGetStylesUrls):
    pass


class Wms100OperationUrlsMixin(WmsOperationUrlsMixin):
    get_capabilities_urls = xmlmap.NodeField(xpath="Capability/Request/GetCapabilities",
                                             node_class=Wms100GetCapabilitiesUrls)
    get_map_urls = xmlmap.NodeField(xpath="Capability/Request/GetMap",
                                    node_class=Wms100GetMapUrls)
    get_feature_info_urls = xmlmap.NodeField(xpath="Capability/Request/GetFeatureInfo",
                                             node_class=Wms100GetFeatureInfoUrls)
    get_describe_layer_urls = xmlmap.NodeField(xpath="Capability/Request/DescribeLayer",
                                               node_class=Wms100DescribeLayerUrls)
    get_legend_graphic_urls = xmlmap.NodeField(xpath="Capability/Request/GetLegendGraphic",
                                               node_class=Wms100GetLegendGraphicUrls)
    get_styles_urls = xmlmap.NodeField(xpath="Capability/Request/GetStyles",
                                       node_class=Wms100GetStylesUrls)


class Wms100CapabilitiesConverter(Wms100OperationUrlsMixin, OgcServiceCapabilitiesConverter):
    """Abstract service xml mapper class"""
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "WMT_MS_Capabilities"
    url = xmlmap.StringField(xpath="Service/OnlineResource[@xlink:type='simple']/@xlink:href")
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=Wms100ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="Capability/Layer", node_class=Wms100Layer)

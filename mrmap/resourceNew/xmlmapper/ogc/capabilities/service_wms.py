from django.contrib.gis.geos import Polygon
from eulxml import xmlmap

from main.utils import camel_to_snake
from resourceNew.models import RemoteMetadata
from resourceNew.xmlmapper.mixins import DBModelConverterMixin, DynamicRootNameMixin
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE, WMS_1_3_0_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.metadata_wms import Wms110ServiceMetadata, Wms100ServiceMetadata, \
    LayerMetadata100, LayerMetadata110
from resourceNew.xmlmapper.ogc.capabilities.service import Service, OnlineResource, ReferenceSystem, OperationUrl

EDGE_COUNTER = 0


class Reference110System(ReferenceSystem):
    ROOT_NAME = "SRS"


class Reference130System(ReferenceSystem):
    ROOT_NAME = "CRS"


class LegendUrl(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.LegendUrl'
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "LegendURL"

    legend_url = xmlmap.StringField(xpath="OnlineResource[@xlink:type='simple']/@xlink:href")
    height = xmlmap.IntegerField(xpath="@height")
    width = xmlmap.IntegerField(xpath="@width")
    mime_type = xmlmap.StringField(xpath="Format")


class Style(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.Style'
    ROOT_NAME = "Style"

    name = xmlmap.StringField(xpath="Name")
    title = xmlmap.StringField(xpath="Title")
    legend_url = xmlmap.NodeField(xpath="LegendURL", node_class=LegendUrl)


class Layer(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.Layer'
    ROOT_NAME = "Layer"
    is_leaf_node = False
    level = 0
    left = 0
    right = 0

    identifier = xmlmap.StringField(xpath="Name")
    styles = xmlmap.NodeListField(xpath="Style", node_class=Style)
    is_queryable = xmlmap.SimpleBooleanField(xpath="@queryable", true=1, false=0)
    is_opaque = xmlmap.SimpleBooleanField(xpath="@opaque", true=1, false=0)
    is_cascaded = xmlmap.SimpleBooleanField(xpath="@cascaded", true=1, false=0)
    remote_metadata = xmlmap.NodeListField(xpath="MetadataURL", node_class=RemoteMetadata)

    def get_descendants(self, include_self=True, level=0):
        global EDGE_COUNTER
        EDGE_COUNTER += 1
        self.left = EDGE_COUNTER

        self.level = level

        descendants = []

        if self.children:
            level += 1
            for layer in self.children:
                descendants.extend(layer.get_descendants(level=level))
        else:
            self.is_leaf_node = True

        EDGE_COUNTER += 1
        self.right = EDGE_COUNTER

        if include_self:
            descendants.insert(0, self)

        return descendants

    def get_field_dict(self):
        dic = super().get_field_dict()
        # there is no default xmlmap field which parses to a geos polygon. So we convert it here.
        min_x = dic.get('bbox_min_x')
        max_x = dic.get('bbox_max_x')
        min_y = dic.get('bbox_min_y')
        max_y = dic.get('bbox_max_y')
        del dic['bbox_min_x'], dic['bbox_max_x'], dic['bbox_min_y'], dic['bbox_max_y']
        if min_x and max_x and min_y and max_y:
            bbox_lat_lon = Polygon(((min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y)))
            dic.update({"bbox_lat_lon": bbox_lat_lon})
        return dic


class Layer100(Layer):
    """xml mapper class for wms layer information for service version >= 1.0.0 and < 1.1.1"""
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")

    #dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)
    # wms 1.1.0 supports whitelist spacing of srs. There is no default split function way in xpath 1.0
    # FIXME: try to use f"{NS_WC}SRS/tokenize(.," ")']"
    reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=Reference110System)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=LayerMetadata100)


class Layer111(Layer):
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")

   # dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)

    reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=Reference110System)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=LayerMetadata110)


class Layer130(Layer):
    scale_min = xmlmap.FloatField(xpath="MinScaleDenominator")
    scale_max = xmlmap.FloatField(xpath="MaxScaleDenominator")
    bbox_min_x = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/westBoundLongitude")
    bbox_max_x = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/eastBoundLongitude")
    bbox_min_y = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/southBoundLatitude")
    bbox_max_y = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/northBoundLatitude")

   # dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension130)
    reference_systems = xmlmap.NodeListField(xpath="CRS", node_class=Reference130System)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")
    layer_metadata = xmlmap.NodeField(xpath=".", node_class=LayerMetadata110)


class WmsOperationUrls(OperationUrl):
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    mime_types = xmlmap.StringListField(xpath="Format")
    get_url = xmlmap.StringField(xpath="DCPType/HTTP/Get/OnlineResource/@xlink:href")
    post_url = xmlmap.StringField(xpath="DCPType/HTTP/Post/OnlineResource/@xlink:href")


class WmsGetCapabilitiesUrls(WmsOperationUrls):
    ROOT_NAME = "GetCapabilities"


class WmsGetMapUrls(WmsOperationUrls):
    ROOT_NAME = "GetMap"


class WmsGetFeatureInfoUrls(WmsOperationUrls):
    ROOT_NAME = "GetFeatureInfo"


class WmsDescribeLayerUrls(WmsOperationUrls):
    ROOT_NAME = "DescribeLayer"


class WmsGetLegendGraphicUrls(WmsOperationUrls):
    ROOT_NAME = "GetLegendGraphic"


class WmsGetStylesUrls(WmsOperationUrls):
    ROOT_NAME = "GetStyles"


class WmsOperationUrlsMixin:
    @property
    def operation_urls(self):
        _operation_urls = []
        for key in self._fields.keys():
            if isinstance(self._fields.get(key), xmlmap.NodeField) and "_urls" in key:
                operation_url = getattr(self, key)
                if operation_url and operation_url.get_url:
                    _operation_urls.append({"method": "Get",
                                            "operation": operation_url.ROOT_NAME,
                                            "url": operation_url.get_url,
                                            "mime_types": list(operation_url.mime_types)})
                if operation_url and operation_url.post_url:
                    _operation_urls.append({"method": "Post",
                                            "operation": operation_url.ROOT_NAME,
                                            "url": operation_url.post_url,
                                            "mime_types": list(operation_url.mime_types)})
        return _operation_urls

    @operation_urls.setter
    def operation_urls(self, operation_urls):
        """

        :param operation_urls: the operation url objects
        """
        for operation_url in operation_urls:
            key = camel_to_snake(operation_url["operation"]) + "_urls"
            node_field = self._fields.get(key)

            if not getattr(self, key):
                setattr(self, key, node_field.mapper.node_class())
            _operation_url = getattr(self, key)
            if operation_url["method"] == "Get":
                _operation_url.get_url = operation_url["url"]
            elif operation_url["method"] == "Post":
                _operation_url.post_url = operation_url["url"]

            _operation_url.mime_types.extend(operation_url.get("mime_types", []))


class Wms110OperationUrlsMixin(WmsOperationUrlsMixin):
    get_capabilities_urls = xmlmap.NodeField(xpath="Capability/Request/GetCapabilities",
                                             node_class=WmsGetCapabilitiesUrls)
    get_map_urls = xmlmap.NodeField(xpath="Capability/Request/GetMap",
                                    node_class=WmsGetMapUrls)
    get_feature_info_urls = xmlmap.NodeField(xpath="Capability/Request/GetFeatureInfo",
                                             node_class=WmsGetFeatureInfoUrls)
    get_describe_layer_urls = xmlmap.NodeField(xpath="Capability/Request/DescribeLayer",
                                               node_class=WmsDescribeLayerUrls)
    get_legend_graphic_urls = xmlmap.NodeField(xpath="Capability/Request/GetLegendGraphic",
                                               node_class=WmsGetLegendGraphicUrls)
    get_styles_urls = xmlmap.NodeField(xpath="Capability/Request/GetStyles",
                                       node_class=WmsGetStylesUrls)


class WmsService(Service):
    """Abstract wms service xml mapper class.

    :attr all_layers: cache to store the layer list, which is computed by the :meth:`~.get_all_layers`
    """
    all_layers = None

    def get_all_layers(self):
        """Return all layers of the wms in pre order.

        .. note::
           the returned layer list is cached in :attr all_layers:

        :return all_layers: all layers
        :rtype: list
        """
        if not self.all_layers:
            self.all_layers = self.root_layer.get_descendants()
        return self.all_layers


class Wms100Service(WmsService):
    ROOT_NAME = "WMT_MS_Capabilities"
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=Wms100ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="Capability/Layer", node_class=Layer100)
    # todo operation urls

class Wms110Service(Wms110OperationUrlsMixin, WmsService):
    ROOT_NAME = "WMT_MS_Capabilities"
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=Wms110ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="Capability/Layer", node_class=Layer100)


class Wms111Service(Wms110OperationUrlsMixin, WmsService):
    ROOT_NAME = "WMT_MS_Capabilities"
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=Wms110ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="Capability/Layer", node_class=Layer111)


class Wms130Service(WmsService):
    ROOT_NAME = "WMS_Capabilities"
    ROOT_NS = "default"
    ROOT_NAMESPACES = dict([("default", WMS_1_3_0_NAMESPACE)])
    XSD_SCHEMA = "http://schemas.opengis.net/wms/1.3.0/capabilities_1_3_0.xsd"
    service_metadata = xmlmap.NodeField(xpath="default:Service", node_class=Wms110ServiceMetadata)
    root_layer = xmlmap.NodeField(xpath="default:Capability/default:Layer", node_class=Layer130)

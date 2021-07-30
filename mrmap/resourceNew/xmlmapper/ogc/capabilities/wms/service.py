from django.contrib.gis.geos import Polygon
from eulxml import xmlmap

from main.utils import camel_to_snake
from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.service import OperationUrl, Service

EDGE_COUNTER = 0


class LegendUrl(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.LegendUrl'
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "LegendURL"


class Style(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.Style'
    ROOT_NAME = "Style"


class Layer(DBModelConverterMixin, xmlmap.XmlObject):
    model = 'resourceNew.Layer'
    ROOT_NAME = "Layer"
    is_leaf_node = False
    level = 0
    left = 0
    right = 0

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

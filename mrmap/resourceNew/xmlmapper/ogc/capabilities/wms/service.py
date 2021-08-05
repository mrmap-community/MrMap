from collections import OrderedDict

from django.contrib.gis.geos import Polygon
from eulxml import xmlmap

from main.utils import camel_to_snake
from resourceNew.xmlmapper.mixins import DBModelConverter
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.service import OperationUrl, OgcServiceCapabilitiesConverter
from resourceNew.models.service import Layer

EDGE_COUNTER = 0


class LegendUrlConverter(DBModelConverter):
    model = 'resourceNew.LegendUrl'
    ROOT_NAMESPACES = dict([("xlink", XLINK_NAMESPACE)])
    ROOT_NAME = "LegendURL"


class StyleConverter(DBModelConverter):
    model = 'resourceNew.Style'
    ROOT_NAME = "Style"


class LayerConverter(DBModelConverter):
    model = Layer
    ROOT_NAME = "Layer"
    ignore_fields = ["bbox_min_x", "bbox_max_x", "bbox_min_y", "bbox_max_y"]

    def convert_to_model(self, **kwargs):
        """Converter function to convert the current xml mapper instance to a db model instance.

        :return layer: the constructed layer
        :rtype layer: :class:`resourceNew.Layer`
        """
        layer = super().convert_to_model(**kwargs)
        if self.bbox_min_x and self.bbox_max_x and self.bbox_min_y and self.bbox_max_y:
            layer.bbox_lat_lon = Polygon(((self.bbox_min_x, self.bbox_min_y),
                                         (self.bbox_min_x, self.bbox_max_y),
                                         (self.bbox_max_x, self.bbox_min_y),
                                         (self.bbox_max_x, self.bbox_min_y),
                                         (self.bbox_min_x, self.bbox_min_y)))
        return layer


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
                    operation_url = OperationUrl()
                    operation_url.method = "Get"
                    operation_url.operation = operation_url.ROOT_NAME
                    operation_url.url = operation_url.get_url
                    operation_url.mime_types = list(operation_url.mime_types)
                    _operation_urls.append(operation_url)
                if operation_url and operation_url.post_url:
                    operation_url = OperationUrl()
                    operation_url.method = "Post"
                    operation_url.operation = operation_url.ROOT_NAME
                    operation_url.url = operation_url.post_url
                    operation_url.mime_types = list(operation_url.mime_types)
                    _operation_urls.append(operation_url)
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

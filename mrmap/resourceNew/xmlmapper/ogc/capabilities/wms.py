from django.contrib.gis.geos import Polygon
from eulxml import xmlmap

from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.namespaces import XLINK_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.service import Service, OperationUrl, ServiceMetadata


class WmsOperationUrl(OperationUrl):
    method = xmlmap.StringField(xpath="name(..)")
    operation = xmlmap.StringField(xpath="name(../../../..)")
    # todo:
    mime_types = xmlmap.NodeListField(xpath="../../../../Format", node_class=MimeType)


class WmsService(Service):
    """Abstract wms service xml mapper class.

    :attr all_layers: cache to store the layer list, which is computed by the :meth:`~.get_all_layers`
    """
    ROOT_NAME = "WMS_Capabilities"

    all_layers = None
    service_type = xmlmap.NodeField(xpath=".", node_class=ServiceType)
    service_metadata = xmlmap.NodeField(xpath="Service", node_class=WmsServiceMetadata)
    operation_urls = xmlmap.NodeListField(
        xpath="Capability/Request//DCPType/HTTP//OnlineResource",
        node_class=WmsOperationUrl)

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


EDGE_COUNTER = 0


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
    metadata = xmlmap.NodeField(xpath=".", node_class=LayerMetadata)
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


class Layer110(Layer):
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")

    dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)
    # wms 1.1.0 supports whitelist spacing of srs. There is no default split function way in xpath 1.0
    # FIXME: try to use f"{NS_WC}SRS/tokenize(.," ")']"
    reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=ReferenceSystem)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")


class Layer111(Layer):
    scale_min = xmlmap.FloatField(xpath="ScaleHint/@min")
    scale_max = xmlmap.FloatField(xpath="ScaleHint/@max")
    bbox_min_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@minx")
    bbox_max_x = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxx")
    bbox_min_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@miny")
    bbox_max_y = xmlmap.FloatField(xpath="LatLonBoundingBox/@maxy")

    dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension111)

    reference_systems = xmlmap.NodeListField(xpath="SRS", node_class=ReferenceSystem)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")


class Layer130(Layer):
    scale_min = xmlmap.FloatField(xpath="MinScaleDenominator")
    scale_max = xmlmap.FloatField(xpath="MaxScaleDenominator")
    bbox_min_x = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/westBoundLongitude")
    bbox_max_x = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/eastBoundLongitude")
    bbox_min_y = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/southBoundLatitude")
    bbox_max_y = xmlmap.FloatField(xpath="EX_GeographicBoundingBox/northBoundLatitude")

    dimensions = xmlmap.NodeListField(xpath="Dimension", node_class=Dimension130)
    reference_systems = xmlmap.NodeListField(xpath="CRS", node_class=ReferenceSystem)
    parent = xmlmap.NodeField(xpath="../../Layer", node_class="self")
    children = xmlmap.NodeListField(xpath="Layer", node_class="self")

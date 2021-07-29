from abc import ABC

from django.contrib.gis.geos import Polygon
from eulxml import xmlmap

from resourceNew.xmlmapper.mixins import DBModelConverterMixin
from resourceNew.xmlmapper.namespaces import WFS_2_0_0_NAMESPACE, WFS_1_1_2_NAMESPACE, OWS_1_1_0_NAMESPACE, \
    OWS_1_0_0_NAMESPACE
from resourceNew.xmlmapper.ogc.capabilities.service import Service


class FeatureType(DBModelConverterMixin, xmlmap.XmlObject, ABC):
    model = "resourceNew.FeatureType"
    ROOT_NAME = "FeatureType"


class FeatureType100(FeatureType):
    ROOT_NAMESPACES = dict([("ows", OWS_1_0_0_NAMESPACE)])


class FeatureType200(FeatureType):
    ROOT_NAMESPACES = dict([("ows", OWS_1_1_0_NAMESPACE)])

    identifier = xmlmap.StringField(xpath="Name")
    metadata = xmlmap.NodeField(xpath=".", node_class=FeatureTypeMetadata)
    remote_metadata = xmlmap.NodeListField(xpath="MetadataURL", node_class=RemoteMetadata)
    bbox_lower_corner = xmlmap.StringField(xpath="ows:WGS84BoundingBox/ows:LowerCorner")
    bbox_upper_corner = xmlmap.StringField(xpath="ows:WGS84BoundingBox/ows:UpperCorner")
    output_formats = xmlmap.NodeListField(xpath="OutputFormats/Format", node_class=MimeType)
    reference_systems = xmlmap.NodeListField(xpath="DefaultCRS|OtherCRS", node_class=ReferenceSystem)
    # todo: add dimensions

    def get_field_dict(self):
        dic = super().get_field_dict()
        # there is no default xmlmap field which parses to a geos polygon. So we convert it here.
        bbox_lower_corner = dic.get('bbox_lower_corner', None)
        bbox_upper_corner = dic.get('bbox_upper_corner', None)

        if bbox_lower_corner and bbox_upper_corner:
            min_x = float(bbox_lower_corner.split(" ")[0])
            min_y = float(bbox_lower_corner.split(" ")[1])
            max_x = float(bbox_upper_corner.split(" ")[0])
            max_y = float(bbox_upper_corner.split(" ")[1])

            bbox_lat_lon = Polygon(((min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y)))
            dic.update({"bbox_lat_lon": bbox_lat_lon})

        del dic['bbox_lower_corner'], dic['bbox_upper_corner']

        return dic


class WfsService(Service, ABC):
    """Abstract wms service xml mapper class.

    :attr all_layers: cache to store the layer list, which is computed by the :meth:`~.get_all_layers`
    """

    all_layers = None
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


class Wfs110Service(WfsService):
    ROOT_NAMESPACES = dict([("wfs", WFS_1_1_2_NAMESPACE),
                            ("ows", OWS_1_0_0_NAMESPACE)])
    XSD_SCHEMA = "http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"

    version = xmlmap.StringField(xpath="@version/concat(./text(), '1.1.0')")


class Wfs113Service(WfsService):
    ROOT_NAMESPACES = dict([("wfs", WFS_1_1_2_NAMESPACE),
                            ("ows", OWS_1_0_0_NAMESPACE)])
    XSD_SCHEMA = "http://schemas.opengis.net/wfs/1.1/wfs.xsd"

    version = xmlmap.StringField(xpath="@version/concat(./text(), '1.1.3')")


class Wfs200Service(WfsService):
    ROOT_NAMESPACES = dict([("wfs", WFS_2_0_0_NAMESPACE),
                            ("ows", OWS_1_1_0_NAMESPACE)])
    ROOT_NAME = "WFS_Capabilities"
    XSD_SCHEMA = "http://schemas.opengis.net/wfs/2.0/wfs.xsd"

    version = xmlmap.StringField(xpath="@version/concat(./text(), '2.0.0')")
    service_metadata = xmlmap.NodeField(xpath="ServiceIdentification", node_class=ServiceMetadata)
    operation_urls = xmlmap.NodeListField(xpath="OperationsMetadata/Operation//DCP/HTTP/*",
                                          node_class=WfsCswOperationUrl)
    feature_types = xmlmap.NodeListField(xpath="FeatureTypeList//FeatureType",
                                         node_class=FeatureType)

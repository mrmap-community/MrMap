# common classes for handling of WMS (OGC WebMapServices)
# http://www.opengeospatial.org/standards/wms
"""Common classes to handle WMS (OGC WebMapServices).

.. moduleauthor:: Armin Retterath <armin.retterath@gmail.com>

"""
from service.helper.enums import VersionTypes
from service.helper.ogc.ows import OGCWebService
from service.helper.ogc.layer import OGCLayer

from service.helper import service_helper


class OGCWebMapServiceFactory:
    """ Creates the correct OGCWebMapService objects

    """
    def get_ogc_wms(self, version: VersionTypes, service_connect_url: str):
        """ Returns the correct implementation of an OGCWebMapService according to the given version

        Args:
            version: The version number of the service
            service_connect_url: The capabilities request uri
        Returns:
            An OGCWebMapService
        """
        if version is VersionTypes.V_1_0_0:
            return OGCWebMapService_1_0_0(service_connect_url=service_connect_url)
        if version is VersionTypes.V_1_1_0:
            return OGCWebMapService_1_1_0(service_connect_url=service_connect_url)
        if version is VersionTypes.V_1_1_1:
            return OGCWebMapService_1_1_1(service_connect_url=service_connect_url)
        if version is VersionTypes.V_1_3_0:
            return OGCWebMapService_1_3_0(service_connect_url=service_connect_url)


class OGCWebMapService(OGCWebService):
    """Base class for OGC WebMapServices."""


    # define layers as array of OGCWebMapServiceLayer objects
    # Using None here to avoid mutable appending of infinite layers (python specific)
    # For further details read: http://effbot.org/zone/default-values.htm
    layers = None

    class Meta:
        abstract = True

    ### IDENTIFIER ###
    def __parse_identifier(self, layer, layer_obj):
        layer_obj.identifier = service_helper.try_get_text_from_xml_element("./Name", layer)

    ### KEYWORDS ###
    def __parse_keywords(self, layer, layer_obj):
        keywords = service_helper.try_get_element_from_xml("./KeywordList/Keyword", layer)
        for keyword in keywords:
            layer_obj.capability_keywords.append(keyword.text)

    ### ABSTRACT ###
    def __parse_abstract(self, layer, layer_obj):
        layer_obj.abstract = service_helper.try_get_text_from_xml_element("./Abstract", layer)

    ### TITLE ###
    def __parse_title(self, layer, layer_obj):
        layer_obj.title = service_helper.try_get_text_from_xml_element("./Title", layer)

    ### SRS/CRS     PROJECTION SYSTEM ###
    def __parse_projection_system_1_1_1(self, layer, layer_obj):
        srs = service_helper.try_get_element_from_xml("./SRS", layer)
        for elem in srs:
            layer_obj.capability_projection_system.append(elem.text)

    def __parse_projection_system_1_3_0(self, layer, layer_obj):
        crs = service_helper.try_get_element_from_xml("./CRS", layer)
        for elem in crs:
            layer_obj.capability_projection_system.append(elem.text)

    def __parse_projection_system(self, layer, layer_obj):
        if self.service_version is VersionTypes.V_1_0_0:
            self.__parse_projection_system_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_0:
            self.__parse_projection_system_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_1:
            self.__parse_projection_system_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_3_0:
            self.__parse_projection_system_1_3_0(layer=layer, layer_obj=layer_obj)

    ### BOUNDING BOX    LAT LON ###
    def __parse_lat_lon_bounding_box_1_1_1(self, layer, layer_obj):
        try:
            bbox = service_helper.try_get_element_from_xml("./LatLonBoundingBox", layer)[0]
            attrs = ["minx", "miny", "maxx", "maxy"]
            for attr in attrs:
                layer_obj.capability_bbox_lat_lon[attr] = bbox.get(attr)
        except IndexError:
            pass

    def __parse_lat_lon_bounding_box_1_3_0(self, layer, layer_obj):
        try:
            bbox = service_helper.try_get_element_from_xml("./EX_GeographicBoundingBox", layer)[0]
            attrs = {
                "westBoundLongitude": "minx",
                "eastBoundLongitude": "maxx",
                "southBoundLatitude": "miny",
                "northBoundLatitude": "maxy",
            }
            for key, val in attrs.items():
                layer_obj.capability_bbox_lat_lon[val] = bbox.get(key)
        except IndexError:
            pass

    def __parse_lat_lon_bounding_box(self, layer, layer_obj):
        if self.service_version is VersionTypes.V_1_0_0:
            self.__parse_lat_lon_bounding_box_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_0:
            self.__parse_lat_lon_bounding_box_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_1:
            self.__parse_lat_lon_bounding_box_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_3_0:
            self.__parse_lat_lon_bounding_box_1_3_0(layer=layer, layer_obj=layer_obj)

    ### BOUNDING BOX ###
    def __parse_bounding_box_generic(self, layer, layer_obj, elem_name):
        try:
            bboxs = layer.xpath("./BoundingBox")
            for bbox in bboxs:
                srs = bbox.get(elem_name)
                srs_dict = {
                    "minx": "",
                    "miny": "",
                    "maxx": "",
                    "maxy": "",
                }
                attrs = ["minx", "miny", "maxx", "maxy"]
                for attr in attrs:
                    srs_dict[attr] = bbox.get(attr)
                layer_obj.capability_bbox_srs[srs] = srs_dict
        except (AttributeError, IndexError) as error:
            pass

    def __parse_bounding_box(self, layer, layer_obj):
        # switch depending on service version
        elem_name = "SRS"
        if self.service_version is VersionTypes.V_1_0_0:
            pass
        if self.service_version is VersionTypes.V_1_1_0:
            pass
        if self.service_version is VersionTypes.V_1_1_1:
            pass
        if self.service_version is VersionTypes.V_1_3_0:
            elem_name = "CRS"
        self.__parse_bounding_box_generic(layer=layer, layer_obj=layer_obj, elem_name=elem_name)

    ### SCALE HINT ###
    def __parse_scale_hint(self, layer, layer_obj):
        try:
            scales = service_helper.try_get_element_from_xml("./ScaleHint", layer)[0]
            attrs = ["min", "max"]
            for attr in attrs:
                layer_obj.capability_scale_hint[attr] = scales.get(attr)
        except IndexError:
            pass

    ### IS QUERYABLE ###
    def __parse_queryable(self, layer, layer_obj):
            try:
                is_queryable = layer.get("queryable")
                if is_queryable is None:
                    is_queryable = False
                else:
                    is_queryable = service_helper.resolve_boolean_attribute_val(is_queryable)
                layer_obj.is_queryable = is_queryable
            except AttributeError:
                pass

    ### IS OPAQUE ###
    def __parse_opaque(self, layer, layer_obj):
            try:
                is_opaque = layer.get("opaque")
                if is_opaque is None:
                    is_opaque = False
                else:
                    is_opaque = service_helper.resolve_boolean_attribute_val(is_opaque)
                layer_obj.is_opaque = is_opaque
            except AttributeError:
                pass

    ### IS CASCADED ###
    def __parse_cascaded(self, layer, layer_obj):
            try:
                is_opaque = layer.get("cascaded")
                if is_opaque is None:
                    is_opaque = False
                else:
                    is_opaque = service_helper.resolve_boolean_attribute_val(is_opaque)
                layer_obj.is_cascaded = is_opaque
            except AttributeError:
                pass

    ### REQUEST URIS ###
    def __parse_request_uris(self, layer, layer_obj):
        attributes = {
            "cap": "//GetCapabilities/DCPType/HTTP/Get/OnlineResource",
            "map": "//GetMap/DCPType/HTTP/Get/OnlineResource",
            "feat": "//GetFeatureInfo/DCPType/HTTP/Get/OnlineResource",
            "desc": "//DescribeLayer/DCPType/HTTP/Get/OnlineResource",
            "leg": "//GetLegendGraphic/DCPType/HTTP/Get/OnlineResource",
            "style": "//GetStyles/DCPType/HTTP/Get/OnlineResource",
        }
        for key, val in attributes.items():
            try:
                tmp = layer.xpath(val)[0].get("{http://www.w3.org/1999/xlink}href")
                attributes[key] = tmp
            except (AttributeError, IndexError) as error:
                attributes[key] = None

        layer_obj.get_capabilities_uri = attributes.get("cap")
        layer_obj.get_map_uri = attributes.get("map")
        layer_obj.get_feature_info_uri = attributes.get("feat")
        layer_obj.describe_layer_uri = attributes.get("desc")
        layer_obj.get_legend_graphic_uri = attributes.get("leg")
        layer_obj.get_styles_uri = attributes.get("style")

    ### FORMATS ###
    def __parse_formats_1_1_1(self, layer, layer_obj):
        actions = ["GetMap", "GetCapabilities", "GetFeatureInfo", "DescribeLayer", "GetLegendGraphic", "GetStyles"]
        results = {}
        for action in actions:
            try:
                results[action] = []
                format_list = layer.xpath("//" + action + "/Format")
                for format in format_list:
                    results[action].append(format.text)
            except AttributeError:
                pass
        layer_obj.format_list = results

    def __parse_formats_1_0_0(self, layer, layer_obj):
        # ToDo: Find wms 1.0.0 for testing!!!!
        actions = ["Map", "Capabilities", "FeatureInfo"]
        results = {}
        for action in actions:
            try:
                results[action] = []
                format_list = layer.xpath("//Request/" + action + "/Format").getchildren()
                for format in format_list:
                    results[action].append(format.text)
            except AttributeError:
                pass
        layer_obj.format_list = results

    def __parse_formats(self, layer, layer_obj):
        # switch between versions
        if self.service_version is VersionTypes.V_1_0_0:
            # do 1.0.0 stuff
            self.__parse_formats_1_0_0(layer_obj=layer_obj, layer=layer)
        if self.service_version is VersionTypes.V_1_1_0:
            # do 1.1.0 stuff
            # no difference to 1.1.1
            self.__parse_formats_1_1_1(layer_obj=layer_obj, layer=layer)
        if self.service_version is VersionTypes.V_1_1_1:
            # do 1.1.1 stuff
            self.__parse_formats_1_1_1(layer_obj=layer_obj, layer=layer)
        if self.service_version is VersionTypes.V_1_3_0:
            # do 1.3.0 stuff
            # no difference to 1.1.1
            self.__parse_formats_1_1_1(layer_obj=layer_obj, layer=layer)

    ### DIMENSIONS ###
    def __parse_dimension_1_1_1(self, layer, layer_obj):
        dims_list = []
        try:
            dim = layer.xpath("./Dimension")[0]
            ext = layer.xpath("./Extent")[0]
            dim_dict = {
                "name": dim.get("name"),
                "units": dim.get("units"),
                "default": ext.get("default"),
                "extent": ext.text,
            }
            dims_list.append(dim_dict)
        except (IndexError, AttributeError) as error:
            pass
        layer_obj.dimension = dims_list

    def __parse_dimension_1_3_0(self, layer, layer_obj):
        dims_list = []
        try:
            dims = layer.xpath("./Dimension")
            for dim in dims:
                dim_dict = {
                    "name": dim.get("name"),
                    "units": dim.get("units"),
                    "default": dim.get("default"),
                    "extent": dim.text,
                    "nearestValue": dim.get("nearestValue"),
                }
                dims_list.append(dim_dict)
        except (IndexError, AttributeError) as error:
            pass
        layer_obj.dimension = dims_list

    def __parse_dimension(self, layer, layer_obj):
        if self.service_version is VersionTypes.V_1_0_0:
            self.__parse_dimension_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_0:
            self.__parse_dimension_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_1_1:
            self.__parse_dimension_1_1_1(layer=layer, layer_obj=layer_obj)
        if self.service_version is VersionTypes.V_1_3_0:
            self.__parse_dimension_1_3_0(layer=layer, layer_obj=layer_obj)


    ### STYLES ###
    def __parse_style(self, layer, layer_obj):
        style = service_helper.try_get_element_from_xml("./Style", layer)
        elements = {
            "name": "./Name",
            "title": "./Title",
            "width": "./LegendURL",
            "height": "./LegendURL",
            "uri": "./LegendURL/OnlineResource"
        }
        for key, val in elements.items():
            tmp = service_helper.try_get_element_from_xml(val, style)
            try:
                elements[key] = tmp[0]
            except (IndexError, TypeError) as error:
                elements[key] = None
        elements["name"] = elements["name"].text if elements["name"] is not None else None
        elements["title"] = elements["title"].text if elements["title"] is not None else None
        elements["width"] = elements["width"].get("width") if elements["width"] is not None else None
        elements["height"] = elements["height"].get("height") if elements["height"] is not None else None
        elements["uri"] = elements["uri"].get("xlink:href") if elements["uri"] is not None else None
        layer_obj.style = elements

    def __get_layers_recursive(self, layers, parent=None, position=0):
        """ Recursive Iteration over all children and subchildren.

        Creates OGCWebMapLayer objects for each xml layer and fills it with the layer content.

        Args:
            layers: An array of layers (In fact the children of the parent layer)
            parent: The parent layer. If no parent exist it means we are in the root layer
            position: The position inside the layer tree, which is more like an order number
        :return:
        """
        for layer in layers:
            # iterate over all top level layer and find their children
            layer_obj = OGCWebMapServiceLayer()
            layer_obj.parent = parent
            layer_obj.position = position
            # iterate over single parsing functions -> improves maintainability
            parse_functions = [
                self.__parse_identifier,
                self.__parse_keywords,
                self.__parse_abstract,
                self.__parse_title,
                self.__parse_projection_system,
                self.__parse_lat_lon_bounding_box,
                self.__parse_bounding_box,
                self.__parse_scale_hint,
                self.__parse_queryable,
                self.__parse_opaque,
                self.__parse_cascaded,
                self.__parse_request_uris,
                self.__parse_formats,
                self.__parse_dimension,
                self.__parse_style,
            ]
            for func in parse_functions:
                func(layer=layer, layer_obj=layer_obj)

            if self.layers is None:
                self.layers = []
            self.layers.append(layer_obj)
            sublayers = layer.xpath("./Layer")
            position += 1
            self.__get_layers_recursive(layers=sublayers, parent=layer_obj, position=position)

    def get_layers(self, xml_obj):
        """ Parses all layers of a service and creates objects for it.

        Uses recursion on the inside to get all children.

        Args:
            xml_obj: The iterable xml tree
        Returns:
             nothing
        """
        # get most upper parent layer, which normally lives directly in <Capability>
        layers = xml_obj.xpath("//Capability/Layer")
        self.__get_layers_recursive(layers)

    def create_from_capabilities(self):
        """ Fills the object with data from the capabilities document

        Returns:
             nothing
        """
        # get xml as iterable object
        xml_obj = service_helper.parse_xml(xml=self.service_capabilities_xml)
        if self.service_version is VersionTypes.V_1_0_0:
            self.get_service_metadata_v100(xml_obj=xml_obj, service_type=self.service_type)
        if self.service_version is VersionTypes.V_1_1_0:
            self.get_service_metadata_v110(xml_obj=xml_obj, service_type=self.service_type)
        if self.service_version is VersionTypes.V_1_1_1:
            self.get_service_metadata_v111(xml_obj=xml_obj, service_type=self.service_type)
        if self.service_version is VersionTypes.V_1_3_0:
            self.get_service_metadata_v130(xml_obj=xml_obj, service_type=self.service_type)
        self.get_layers(xml_obj=xml_obj)


class OGCWebMapServiceLayer(OGCLayer):
    """ The OGCWebMapServiceLayer class

    """


class OGCWebMapService_1_0_0(OGCWebMapService):
    """ The WMS class for standard version 1.0.0

    """
    def __init__(self, service_connect_url):
        super().__init__(service_connect_url=service_connect_url)
        self.service_version = VersionTypes.V_1_0_0


class OGCWebMapService_1_1_0(OGCWebMapService):
    """ The WMS class for standard version 1.1.0

    """
    def __init__(self, service_connect_url):
        super().__init__(service_connect_url=service_connect_url)
        self.service_version = VersionTypes.V_1_1_0


class OGCWebMapService_1_1_1(OGCWebMapService):
    """ The WMS class for standard version 1.1.1

    """
    def __init__(self, service_connect_url):
        super().__init__(service_connect_url=service_connect_url)
        self.service_version = VersionTypes.V_1_1_1


class OGCWebMapService_1_3_0(OGCWebMapService):
    """ The WMS class for standard version 1.3.0

    """

    def __init__(self, service_connect_url):
        super().__init__(service_connect_url=service_connect_url)
        self.service_version = VersionTypes.V_1_3_0
            
    # https://stackoverflow.com/questions/34009992/python-elementtree-default-namespace
    # def create_from_capabilities(self):
    #     # Remove the default namespace definition (xmlns="http://some/namespace")
    #     xmlstring = re.sub(r'\sxmlns="[^"]+"', '', self.service_capabilities_xml, count=1)
    #     root = etree.XML(str.encode(xmlstring))
    #     tree = etree.ElementTree(root)
    #     # service metadata
    #     r = tree.xpath('/WMS_Capabilities/Service/Title')
    #     self.service_identification_title = r[0].text
    #     r = tree.xpath('/WMS_Capabilities/Service/Abstract')
    #     self.service_identification_abstract = r[0].text
    #     r = tree.xpath('/WMS_Capabilities/Service/KeywordList/Keyword')
    #     for keyword in r:
    #         self.service_identification_keywords.append(keyword.text)
    #         # print(keyword.text)
    #     r = tree.xpath('/WMS_Capabilities/Service/Fees')
    #     self.service_identification_fees = r[0].text
    #     r = tree.xpath('/WMS_Capabilities/Service/AccessConstraints')
    #     self.service_identification_accessconstraints = r[0].text
    #
    #     #p arse layer objects recursive
    #     layers = tree.xpath('/WMS_Capabilities/Capability/Layer')
    #     for layer in layers:
    #         self.parse_layers_recursive(etree.tostring(layer), 0)
    #     # transform to mptt
    #
    #     # debug output
    #     for layer in self.layers:
    #         print(layer.position, layer.parent, layer.title)

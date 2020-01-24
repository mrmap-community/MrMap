"""
Author: Michel Peltriaux
Organization: Spatial data infrastructure Rhineland-Palatinate, Germany
Contact: michel.peltriaux@vermkv.rlp.de
Created on: 05.12.19

"""
import urllib
import io
from collections import OrderedDict

from PIL import Image, ImageFont, ImageDraw
from cryptography.fernet import InvalidToken
from django.core.exceptions import ObjectDoesNotExist
from lxml import etree

from django.contrib.gis.geos import Polygon, GEOSGeometry, Point, GeometryCollection, MultiLineString
from django.http import HttpRequest, HttpResponse, QueryDict
from lxml.etree import QName

from MapSkinner import utils
from MapSkinner.messages import PARAMETER_ERROR, TD_POINT_HAS_NOT_ENOUGH_VALUES, \
    SECURITY_PROXY_ERROR_MISSING_EXT_AUTH_KEY, SECURITY_PROXY_ERROR_WRONG_EXT_AUTH_KEY, \
    OPERATION_HANDLER_MULTIPLE_QUERIES_NOT_ALLOWED
from MapSkinner.settings import GENERIC_NAMESPACE_TEMPLATE, XML_NAMESPACES
from editor.settings import WMS_SECURED_OPERATIONS, WFS_SECURED_OPERATIONS
from service.helper import xml_helper
from service.helper.common_connector import CommonConnector
from service.helper.crypto_handler import CryptoHandler
from service.helper.enums import OGCOperationEnum, OGCServiceEnum, OGCServiceVersionEnum
from service.helper.ogc.request_builder import OGCRequestPOSTBuilder
from service.models import Metadata, FeatureType, Layer
from service.settings import ALLLOWED_FEATURE_TYPE_ELEMENT_GEOMETRY_IDENTIFIERS, DEFAULT_SRS, DEFAULT_SRS_STRING, \
    MAPSERVER_SECURITY_MASK_FILE_PATH, MAPSERVER_SECURITY_MASK_TABLE, MAPSERVER_SECURITY_MASK_KEY_COLUMN, \
    MAPSERVER_SECURITY_MASK_GEOMETRY_COLUMN, MAPSERVER_LOCAL_PATH, DEFAULT_SRS_FAMILY, MIN_FONT_SIZE, FONT_IMG_RATIO, \
    RENDER_TEXT_ON_IMG, MAX_FONT_SIZE
from users.helper import user_helper


class OGCOperationRequestHandler:
    """ Provides methods for handling an operation request for OGC services

    """

    def __init__(self, request: HttpRequest, metadata: Metadata, uri: str = None):
        """ Constructor for OGCOperationRequestHandler

        Args:
            request (HttpRequest): An incoming request
            metadata (Metadata): The metadata object related to the operation call
            uri (str): The uri of the requested operation (optional)
        """
        self.get_uri = uri
        self.original_operation_base_uri = None
        self.post_uri = None

        self.external_auth = None
        try:
            self.external_auth = metadata.external_authentication
            crypto_handler = CryptoHandler()
            key = crypto_handler.get_key_from_file(metadata.id)
            self.external_auth.decrypt(key)
        except ObjectDoesNotExist:
            # this is normal for services which do not need an external authentication
            pass
        except FileNotFoundError:
            raise Exception(SECURITY_PROXY_ERROR_MISSING_EXT_AUTH_KEY)
        except InvalidToken:
            raise Exception(SECURITY_PROXY_ERROR_WRONG_EXT_AUTH_KEY)

        # check what type of request we are facing
        self.request_is_GET = request.method == "GET"
        self.original_params_dict = OrderedDict()  # contains the original, unedited parameters
        self.new_params_dict = OrderedDict()  # contains the parameters, which could be still original or might have changed during method processing

        self.service_type_param = None  # refers to param 'SERVICE'
        self.request_param = None  # refers to param 'REQUEST'
        self.layers_param = None  # refers to param 'LAYERS'
        self.x_y_param = [None, None]  # refers to param 'X/Y' (WMS 1.0.0), 'X, Y' (WMS 1.1.1), 'I,J' (WMS 1.3.0)
        self.bbox_param = None  # refers to param 'BBOX'
        self.srs_param = None  # refers to param 'SRS'|'SRSNAME' (WMS 1.0.0 - 1.1.1) and 'CRS' (WMS 1.3.0)
        self.srs_code = None  # only the srsid as int
        self.format_param = None  # refers to param 'FORMAT'
        self.count_param = None  # refers to param 'COUNT' (WFS 2.x) and 'MAXFEATURES' (WFS 1.x)
        self.version_param = None  # refers to param 'VERSION'
        self.filter_param = None  # refers to param 'FILTER' (WFS)
        self.width_param = None  # refers to param 'WIDTH' (WMS)
        self.height_param = None  # refers to param 'HEIGHT' (WMS)
        self.type_name_param = None  # refers to param 'TYPENAME' (WFS) or 'TYPENAMES' (> WFS 2.0.0)
        self.geom_property_name = None  # will be set, if type_name_param is not None
        self.POST_raw_body = None  # refers to the body content of a Transaction operation
        self.transaction_geometries = None  # contains all geometries that shall be INSERTed or UPDATEd by a  Transaction operation

        self.intersected_allowed_geometry = None
        self.user = user_helper.get_user(request)
        self.access_denied_img = None  # if subelements are not accessible for the user, this PIL.Image object represents an overlay with information about the resources, which can not be accessed

        if self.request_is_GET:
            self.original_params_dict = request.GET.dict()
        else:
            self.original_params_dict = request.POST.dict()

        if len(self.original_params_dict) == 0:
            # Possible, if no GET query parameter or no x-www-form-urlencoded POST values have been given
            # In this case, all the information can be found inside a xml document in the POST body, that has to be parsed now.
            self._parse_POST_xml_body(request.body)

        # fill new_params_dict with upper case keys from original_params_dict
        for key, val in self.original_params_dict.items():
            self.new_params_dict[key.upper()] = val

        self._parse_GET_params()
        self._check_for_srs_in_bbox_param()
        self._resolve_original_operation_uri(request, metadata)
        self._process_bbox_param()
        self._process_x_y_param()
        self._process_transaction_geometries()
        self._preprocess_get_feature_params(metadata)
        self._fill_new_params_dict()

        # We expect the srs_code to be set until now. There are cases where this might fail - so we make a last check in here.
        # Check if the srs_param is set, but the srs_code isn't yet. If so -> find the code inside the param.
        # srs_param could be a link, but also something like "EPSG:4326"...
        if self.srs_param is not None and self.srs_code is None:
            self.srs_code = int(self.srs_param.split(":")[-1])

        # Only work on the requested param objects, if the metadata is secured.
        # Otherwise we can pass this, since it's too expensive for a basic, non secured request
        if metadata.is_secured:
            self._filter_not_allowed_subelements(metadata)

    def _parse_GET_params(self):
        """ Parses the GET parameters into all member variables, which can be found in new_params_dict.

        Returns:

        """
        # extract parameter attributes from params dict
        for key, val in self.new_params_dict.items():
            if key == "SERVICE":
                self.service_type_param = val
            if key == "REQUEST":
                self.request_param = val
            elif key == "LAYERS":
                self.layers_param = val
            elif key == "BBOX":
                self.bbox_param = val
            elif key == "X" or key == "I":
                self.x_y_param[0] = val
            elif key == "Y" or key == "J":
                self.x_y_param[1] = val
            elif key == "VERSION":
                self.version_param = val
            elif key == "FORMAT":
                self.format_param = val
            elif key == "SRS" or key == "CRS" or key == "SRSNAME":
                self.srs_param = val
                self.srs_code = int(self.srs_param.split(":")[-1])  # get the last element of the ':' splitted string
                self.srs_param = DEFAULT_SRS_FAMILY + ":" + str(self.srs_code)
            elif key == "WIDTH":
                self.width_param = val
            elif key == "HEIGHT":
                self.height_param = val
            elif key == "COUNT" or key == "MAXFEATURES":
                self.count_param = val
            elif key == "FILTER":
                self.filter_param = val
            elif key == "TYPENAME" or key == "TYPENAMES":
                self.type_name_param = val

    def _bbox_to_filter(self):
        """ Transforms the BBOX parameter into a valid Filter. Removes the BBOX parameter from the query, since
        Filter and BBOX parameter can not coexist in one request.

        THIS FUNCTION IS ONLY USED FOR GetFeature OPERATION!

        Args:

        Returns:

        """
        if self.bbox_param is None:
            return

        # remove srs from the last position of the bbox (if it is there - might be, or not)
        _filter = self._create_filter_xml_from_geometries([self.bbox_param.get("geom")])

        # Remove the bbox param
        uri_parsed = urllib.parse.urlparse(self.get_uri)
        query = dict(urllib.parse.parse_qsl(uri_parsed.query))

        # remove bbox parameter (also from uri)
        self.bbox_param = None
        try:
            bbox_param_name = None
            for key, val in query.items():
                if key.upper() == "BBOX":
                    bbox_param_name = key
                    break
            if bbox_param_name is not None:
                del query[bbox_param_name]
        except KeyError:
            # it was not there in the first place
            pass
        try:
            del self.new_params_dict["BBOX"]
        except KeyError:
            # it was not there in the first place
            pass

        query["filter"] = _filter
        self.filter_param = _filter
        self.new_params_dict["FILTER"] = _filter

        query = urllib.parse.urlencode(query, safe=", :")
        uri_parsed = uri_parsed._replace(query=query)
        self.get_uri = urllib.parse.urlunparse(uri_parsed)

    def _preprocess_get_feature_params(self, metadata: Metadata):
        """ Preprocessor for GetFeature operation requests

        Fetches a fallback srs code, if none was given in the request.
        Resolves the identifier for the geometry holding featuretypeelement (self.geom_property_name)

        Args:
            metadata (Metadata): The service metadata
        Returns:

        """
        if self.request_param.upper() == OGCOperationEnum.GET_FEATURE.value.upper() and self.type_name_param is not None:
            # for WFS we need to check a few things in here!
            # first get the featuretype object, that is requested
            featuretype = FeatureType.objects.get(
                metadata__identifier=self.type_name_param,
                parent_service__metadata=metadata
            )

            if self.srs_param is None:
                # if the srs_param could not be identified by a GET parameter, we need to check if the default srs of the
                # featuretype object is set. Otherwise we take our DEFAULT_STRING constant (EPSG:4326)
                if featuretype.default_srs is None:
                    self.srs_param = DEFAULT_SRS_STRING
                    self.srs_code = DEFAULT_SRS
                else:
                    self.srs_param = "EPSG:{}".format(featuretype.default_srs.code)
                    self.srs_code = int(featuretype.default_srs.code)

            try:
                tmp = []
                # Since the OGC standard does not specify a single identifier for the geometry part in a featuretype,
                # we need to check if our featuretype holds ANYTHING that matches the possible geometry identifiers...
                for allowed_geom_id in ALLLOWED_FEATURE_TYPE_ELEMENT_GEOMETRY_IDENTIFIERS:
                    elements = featuretype.elements.filter(
                        type__contains=allowed_geom_id
                    )
                    tmp += list(elements)
                if len(tmp) > 0:
                    self.geom_property_name = tmp[0].name
            except ObjectDoesNotExist:
                pass

    def _check_for_srs_in_bbox_param(self):
        """ Checks if the 'bbox' param might hold a srs param as well

        Returns:

        """
        # The bbox parameter contains n extent points and might(!) contain a crs/srs identifier at the end
        # we need to check if this is the case and react correctly!
        if self.bbox_param is not None:
            last_elem = self.bbox_param.split(",")[-1]
            try:
                float(last_elem)
            except ValueError:
                # this is the case if the last element isn't a coordinate - we assume it must be the srs/crs
                self.srs_param = last_elem

    def _filter_not_allowed_subelements(self, md: Metadata):
        """ Remove identifier names from parameter if the user has no access to them!

        Args:
            md (Metadata): The requested service metadata
        Returns:
            nothing
        """
        if md.get_service_type().lower() == OGCServiceEnum.WMS.value:
            self._resolve_layer_param_to_leaf_layers(md)

        if self.layers_param is not None and self.type_name_param is None:
            # in case of WMS
            layer_identifiers = self.layers_param.split(",")

            if self.user is not None:
                user_groups = self.user.groups.all()
            else:
                user_groups = []
            allowed_layers = Metadata.objects.filter(
                service__parent_service__metadata=md,
                identifier__in=layer_identifiers,
                secured_operations__allowed_group__in=user_groups,
                secured_operations__operation__operation_name__iexact=self.request_param,
            )
            allowed_layers_identifier_list = [l.identifier for l in allowed_layers]

            restricted_layers = []
            allowed_layers = []
            for l_i in layer_identifiers:
                if l_i in allowed_layers_identifier_list:
                    allowed_layers.append(l_i)
                else:
                    restricted_layers.append(l_i)
            self.new_params_dict["LAYERS"] = ",".join(allowed_layers)

            # create text for image of restricted layers
            if RENDER_TEXT_ON_IMG:
                height = int(self.height_param)
                text_img = Image.new("RGBA", (int(self.width_param), int(height)), (255, 255, 255, 0))
                draw = ImageDraw.Draw(text_img)
                font_size = int(height * FONT_IMG_RATIO)

                num_res_layers = len(restricted_layers)
                if font_size * num_res_layers > height:
                    # if area of text would be larger than requested height, we simply create a new font_size, that fits!
                    # increase the num_res_layers by 1 to create some space at the bottom for a better feeling
                    font_size = int(height / (num_res_layers + 1))

                if font_size < MIN_FONT_SIZE:
                    font_size = MIN_FONT_SIZE
                elif font_size > MAX_FONT_SIZE:
                    font_size = MAX_FONT_SIZE

                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", font_size)
                y = 0

                for restricted_layer in restricted_layers:
                    # render text listed one under another
                    draw.text((0, y), "Access denied for '{}'".format(restricted_layer), (0, 0, 0), font=font)
                    y += font_size
                self.access_denied_img = text_img

    def _fill_new_params_dict(self):
        """ Fills all processed parameters into an internal dict

        Returns:

        """
        # fill new_params_dict
        self.new_params_dict["REQUEST"] = self.request_param
        self.new_params_dict["SERVICE"] = self.service_type_param
        self.new_params_dict["VERSION"] = self.version_param
        self.new_params_dict["FORMAT"] = self.format_param
        self.new_params_dict["WIDTH"] = self.width_param
        self.new_params_dict["HEIGHT"] = self.height_param

        # We can not put all parameters directly in the new_params_dict. For the POST xml building - if the regular
        # post fails - we must prevent some elements from existing, if they are None
        if self.filter_param is not None:
            self.new_params_dict["FILTER"] = self.filter_param

        if self.layers_param is not None:
            self.new_params_dict["LAYERS"] = self.layers_param

        if self.count_param is not None:
            param_tag = "MAXFEATURES"
            if self.version_param == OGCServiceVersionEnum.V_2_0_0.value or self.version_param == OGCServiceVersionEnum.V_2_0_2.value:
                param_tag = "COUNT"
            self.new_params_dict[param_tag] = self.count_param

        if self.type_name_param is not None:
            typename_param_key = "TYPENAME"

            # The specification for WFS states, that for version 1.x this parameter is called "TYPENAME".
            # For version 2.x it was renamed to "TYPENAMES".
            # However, if you are requesting a DescribeFeatureType instead of GetFeature, it is still called "TYPENAME"
            # just like in the 1.x specification... great!
            # So just change this parameter name if we have the case of WFS 2.x AND a non DescribeFeatureType request
            if self.request_param != OGCOperationEnum.DESCRIBE_FEATURE_TYPE.value:
                if self.version_param == OGCServiceVersionEnum.V_2_0_0.value or self.version_param == OGCServiceVersionEnum.V_2_0_2.value:
                    typename_param_key = "TYPENAMES"
            self.new_params_dict[typename_param_key] = self.type_name_param

        x_id = None
        y_id = None
        if self.version_param == OGCServiceVersionEnum.V_1_0_0.value or self.version_param == OGCServiceVersionEnum.V_1_1_1.value:
            # WMS 1.0.0 | 1.1.1
            self.new_params_dict["SRS"] = "{}:{}".format(DEFAULT_SRS_FAMILY, self.srs_code)
            x_id = "X"
            y_id = "Y"
        elif self.version_param == OGCServiceVersionEnum.V_1_1_0.value:
            # WFS 1.1.0
            if self.new_params_dict.get("SRSNAME", None) is None:
                self.new_params_dict["SRSNAME"] = self.srs_param
        elif self.version_param == OGCServiceVersionEnum.V_1_3_0.value:
            # WMS 1.3.0
            self.new_params_dict["CRS"] = "{}:{}".format(DEFAULT_SRS_FAMILY, self.srs_code)
            x_id = "I"
            y_id = "J"

        if self.x_y_param is not None and x_id is not None:
            self.new_params_dict[x_id] = self.x_y_param[0]
        if self.x_y_param is not None and y_id is not None:
            self.new_params_dict[y_id] = self.x_y_param[1]

    def _resolve_original_operation_uri(self, request: HttpRequest, metadata: Metadata):
        """ Creates the intended operation uri, which is masked by the proxy.

        This is important, so we can perform this request internally.
        Result is written into self.full_operation_uri.

        Args:
            request (HttpRequest): The incoming user request
            metadata (Metadata): The metadata, which holds the operation specification
        Returns:
             nothing
        """

        # identify requested operation and resolve the uri
        if metadata.service.servicetype.name == OGCServiceEnum.WFS.value:
            secured_operation_uris = {
                "GETFEATURE": {
                    "get": metadata.service.get_feature_info_uri_GET,
                    "post": metadata.service.get_feature_info_uri_POST,
                },  # get_feature_info_uri_GET is reused in WFS for get_feature_uri
                "TRANSACTION": {
                    "get": metadata.service.transaction_uri_GET,
                    "post": metadata.service.transaction_uri_POST,
                },
            }
        else:
            secured_operation_uris = {
                "GETMAP": {
                    "get": metadata.service.get_map_uri_GET,
                    "post": metadata.service.get_map_uri_POST,
                },
                "GETFEATUREINFO": {
                    "get": metadata.service.get_feature_info_uri_GET,
                    "post": metadata.service.get_feature_info_uri_POST,
                },
            }

        secured_uri_GET = secured_operation_uris.get(self.request_param.upper(), {}).get("get", None)
        secured_uri_POST = secured_operation_uris.get(self.request_param.upper(), {}).get("post", None)

        if secured_uri_GET is not None:
            # use the secured uri
            uri_GET = secured_uri_GET
        else:
            # use the original uri
            uri_GET = metadata.online_resource

        if secured_uri_POST is not None:
            # use the secured uri
            uri_POST = secured_uri_POST
        else:
            # use the original uri
            uri_POST = metadata.online_resource

        # add the request query parameter to the ones, which already exist in the persisted uri
        uri_GET = list(urllib.parse.urlparse(uri_GET))
        get_query_params = request.GET.dict()
        uri_params = dict(urllib.parse.parse_qsl(uri_GET[4]))
        uri_params.update(get_query_params)
        get_query_string = urllib.parse.urlencode(uri_params)
        uri_GET[4] = get_query_string
        self.get_uri = urllib.parse.urlunparse(uri_GET)
        self.post_uri = uri_POST

    def _parse_POST_xml_body(self, body: bytes):
        """ Reads all relevant request data from the POST body xml document

        Furthermore for the WFS operation implementation the following Oracle documentation was used:
        https://docs.oracle.com/database/121/SPATL/wfs-operations-requests-and-responses-xml-examples.htm#SPATL926

        Args:
            body (bytes): The POST body as bytes
        Returns:

        """
        body = body.decode("UTF-8")
        xml = xml_helper.parse_xml(body)
        self.POST_raw_body = body

        root = xml.getroot()
        self.request_param = QName(root).localname

        if self.request_param == OGCOperationEnum.GET_MAP.value:
            self._parse_POST_get_map_xml_body(xml)
        elif self.request_param == OGCOperationEnum.GET_FEATURE.value:
            self._parse_POST_get_feature_xml_body(xml)
        elif self.request_param == OGCOperationEnum.TRANSACTION.value:
            # TODO!
            pass
        else:
            # No need to parse anything other for further handling - we can allow it and just pass through!
            pass

    def _parse_POST_get_map_xml_body(self, xml):
        """ Reads all relevant request data from the GetMap POST body xml document

        The WMS specification does not provide information about WMS POST XML structure. However, the WMS 1.3.0
        allows POST XML messages. Examples are not provided, they can be found here and there on the web - which is pretty
        bad for a clean implementation!

        For development the following (only available) example of a WMS GetMap request as xml document was used:
        https://docs.geoserver.org/stable/en/user/services/wms/reference.html

        Args:
            xml: The parsed xml object
        Returns:
             nothing
        """

        root = xml.getroot()
        self.version_param = xml_helper.try_get_attribute_from_xml_element(root, "version")

        self.layers_param = xml_helper.try_get_text_from_xml_element(xml, "//" + GENERIC_NAMESPACE_TEMPLATE.format("NamedLayer") + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Name"))

        bbox_elem = xml_helper.try_get_single_element_from_xml(elem="//" + GENERIC_NAMESPACE_TEMPLATE.format("BoundingBox"), xml_elem=xml)

        # Old client implementations might not send the expected 'EPSG:xyz' style. Instead they send a link, which ends on e.g. '...#4326'
        self.srs_param = xml_helper.try_get_text_from_xml_element(root, "//" + GENERIC_NAMESPACE_TEMPLATE.format("CRS"))
        if self.srs_param is None:
            self.srs_param = xml_helper.try_get_attribute_from_xml_element(bbox_elem, "srsName")
        if self.srs_param is not None:
            possible_separators = [":", "#"]
            for sep in possible_separators:
                try:
                    self.srs_code = int(self.srs_param.split(sep)[-1])
                    break
                except ValueError:
                    continue

        bbox_extent = []
        # bbox extent could exist by using gml:coord or ogc:lowerCorner/ogc:upperCorner
        bbox_coords = xml_helper.try_get_element_from_xml(elem=".//" + GENERIC_NAMESPACE_TEMPLATE.format("coord"), xml_elem=bbox_elem)
        if len(bbox_coords) > 0:
            tmp = ["X", "Y"]
            for coord in bbox_coords:
                for t in tmp:
                    bbox_extent.append(xml_helper.try_get_text_from_xml_element(elem="./" + GENERIC_NAMESPACE_TEMPLATE.format(t), xml_elem=coord))
        else:
            del bbox_coords
            bbox_lower_corner_txt = xml_helper.try_get_text_from_xml_element(bbox_elem, ".//" + GENERIC_NAMESPACE_TEMPLATE.format("lowerCorner"))
            bbox_upper_corner_txt = xml_helper.try_get_text_from_xml_element(bbox_elem, ".//" + GENERIC_NAMESPACE_TEMPLATE.format("upperCorner"))
            bbox_extent += bbox_lower_corner_txt.split(" ")
            bbox_extent += bbox_upper_corner_txt.split(" ")

        self.bbox_param = ",".join(bbox_extent)

        output_elem = xml_helper.try_get_single_element_from_xml(elem="//" + GENERIC_NAMESPACE_TEMPLATE.format("Output"), xml_elem=xml)
        self.format_param = xml_helper.try_get_text_from_xml_element(output_elem, "./" + GENERIC_NAMESPACE_TEMPLATE.format("Format"))

        size_elem = xml_helper.try_get_single_element_from_xml(elem="./" + GENERIC_NAMESPACE_TEMPLATE.format("Size"), xml_elem=output_elem)
        self.height_param = int(xml_helper.try_get_text_from_xml_element(size_elem, "./" + GENERIC_NAMESPACE_TEMPLATE.format("Height")))
        self.width_param = int(xml_helper.try_get_text_from_xml_element(size_elem, "./" + GENERIC_NAMESPACE_TEMPLATE.format("Width")))

        # type_name differs in WFS versions
        if self.version_param == OGCServiceVersionEnum.V_2_0_2.value or self.version_param == OGCServiceVersionEnum.V_2_0_0.value:
            type_name = "typeNames"
        else:
            type_name = "typeName"

        self.type_name_param = xml_helper.try_get_attribute_from_xml_element(xml, type_name, "//" + GENERIC_NAMESPACE_TEMPLATE.format("Query"))
        self.filter_param = xml_helper.xml_to_string(xml_helper.try_get_single_element_from_xml(elem="//" + GENERIC_NAMESPACE_TEMPLATE.format("Filter"), xml_elem=xml))

    def _parse_POST_get_feature_xml_body(self, xml):
        """ Tries to parse the most important data from the POST xml body

        Args:
            xml: The xml document
        Returns:

        """
        root = xml.getroot()
        self.version_param = xml_helper.try_get_attribute_from_xml_element(root, "version")
        self.service_type_param = xml_helper.try_get_attribute_from_xml_element(root, "service")
        self.format_param = xml_helper.try_get_attribute_from_xml_element(root, "outputFormat")
        self.count_param = xml_helper.try_get_attribute_from_xml_element(root, "count") or xml_helper.try_get_attribute_from_xml_element(root, "maxFeatures")

        # multiple <Query> objects are possible according to the specification
        # Due to our security restrictions we cannot allow a GetFeature POST xml request, since multiple different <Filter>
        # elements could be provided
        queries = xml_helper.try_get_element_from_xml("//" + GENERIC_NAMESPACE_TEMPLATE.format("Query"), root)
        if len(queries) > 1:
            raise Exception(OPERATION_HANDLER_MULTIPLE_QUERIES_NOT_ALLOWED)

        for query in queries:
            self.type_name_param = xml_helper.try_get_attribute_from_xml_element(query, "typeName")
            filter_elem = xml_helper.try_get_single_element_from_xml(".//" + GENERIC_NAMESPACE_TEMPLATE.format("Filter"), query)
            self.filter_param = xml_helper.xml_to_string(filter_elem)

    def _create_filter_xml_from_geometries(self, geom_list: list):
        """ Creates a xml string for the filter parameter of a WFS operation

        Returns:
             _filter (str): The xml parameter as string
        """
        _filter = ""
        if len(geom_list) == 0:
            return _filter

        _filter_prefix = ""
        nsmap = {
            "gml": XML_NAMESPACES["gml"],
            "xsd": XML_NAMESPACES["xsd"],
        }

        if self.version_param == "1.0.0" or self.version_param == "1.1.0":
            # default implementation, nothing to do here
            pass

        elif self.version_param == "2.0.0" or self.version_param == "2.0.2":
            nsmap["fes"] = XML_NAMESPACES["fes"]
            nsmap["gml"] = "http://www.opengis.net/gml/3.2"
            _filter_prefix = "{" + nsmap.get("fes") + "}"
        gml = "{" + nsmap.get("gml") + "}"

        # create xml filter string
        root_attributes = {
            "version": self.version_param,
        }
        root = etree.Element("{}Filter".format(_filter_prefix), nsmap=nsmap, attrib=root_attributes)

        geom_list_len = len(geom_list)

        if geom_list_len > 1:
            upper_elem = xml_helper.create_subelement(root, "{}Or".format(_filter_prefix))
        else:
            upper_elem = root

        for geom in geom_list:
            within_elem = xml_helper.create_subelement(upper_elem, "{}Within".format(_filter_prefix))

            prop_tag = "PropertyName"
            outer_bound_tag = "outerBoundaryIs"

            if self.version_param == OGCServiceVersionEnum.V_2_0_0.value or self.version_param == OGCServiceVersionEnum.V_2_0_2.value:
                prop_tag = "ValueReference"
                outer_bound_tag = "exterior"

            property_elem = xml_helper.create_subelement(within_elem, "{}{}".format(_filter_prefix, prop_tag))
            property_elem.text = self.geom_property_name
            polygon_elem = xml_helper.create_subelement(within_elem, "{}Polygon".format(gml),
                                                        attrib={"srsName": self.srs_param})
            outer_bound_elem = xml_helper.create_subelement(polygon_elem, "{}{}".format(gml, outer_bound_tag))
            linear_ring_elem = xml_helper.create_subelement(outer_bound_elem, "{}LinearRing".format(gml))
            pos_list_elem = xml_helper.create_subelement(linear_ring_elem, "{}posList".format(gml))
            tmp = []

            for vertex in geom.coords[0]:
                tmp.append(str(vertex[0]))
                tmp.append(str(vertex[1]))
            pos_list_elem.text = " ".join(tmp)

        _filter = xml_helper.xml_to_string(root)

        return _filter

    def _process_bbox_param(self):
        """ Creates a polygon from the given string bounding box

        Args:

        Returns:
            Nothing, performs method directly on object
        """
        ret_dict = {
            "geom": None,
            "bbox_param": None
        }
        if self.bbox_param is None:
            return ret_dict
        # epsg_api = EpsgApi()

        # create Polygon object from raw BBOX parameter
        tmp_bbox = self.bbox_param.split(",")

        if len(tmp_bbox) == 5:
            # this might happen, if the 5th element is a SRS identifier instead of a BBOX coordinate - could happen...
            del tmp_bbox[-1]

        bbox_param_geom = GEOSGeometry(Polygon.from_bbox(tmp_bbox), srid=self.srs_code)

        # check whether the axis of the bbox extent vertices have to be switched
        # switch_axis = epsg_api.switch_axis_order(service_type, srs_param)

        # if switch_axis:
        #    for i in range(0, len(tmp_bbox)-1, 2):
        #        tmp = tmp_bbox[i]
        #        tmp_bbox[i] = tmp_bbox[i+1]
        #        tmp_bbox[i+1] = tmp

        ret_dict["geom"] = bbox_param_geom
        ret_dict["bbox_param"] = ",".join(tmp_bbox)

        self.new_params_dict["BBOX"] = ret_dict["bbox_param"]
        self.bbox_param = ret_dict

    def _process_x_y_param(self):
        """ Creates a point from the given x_y_param dict

        Args:

        Returns:
            Nothing, performs method directly on object

        """
        # create Point object from raw X/Y parameters
        if self.x_y_param[0] is None and self.x_y_param[1] is not None:
            # make sure both values are set or none
            return HttpResponse(status=500, content=PARAMETER_ERROR.format("X"))
        elif self.x_y_param[0] is not None and self.x_y_param[1] is None:
            # make sure both values are set or none
            return HttpResponse(status=500, content=PARAMETER_ERROR.format("Y"))
        elif self.x_y_param[0] is not None and self.x_y_param[1] is not None:
            # we can create a Point object from this!
            self.x_y_param = Point(int(self.x_y_param[0]), int(self.x_y_param[1]))
        else:
            self.x_y_param = None

        if self.x_y_param is not None:
            self.x_y_coord = self._convert_image_point_to_spatial_coordinates(
                self.x_y_param,
                int(self.width_param),
                int(self.height_param),
                self.bbox_param.get("geom")[0],
            )

    def _create_polygons_from_xml_elements(self, polygon_elements: list):
        """ Creates a list of Polygon objects from xml elements, which contain <gml:Polygon> elements

        Args:
            polygon_elements (list): List of <gml:Polygon> xml elements
        Returns:
             ret_list (list): List of Polygon objects
        """
        ret_list = []

        for poly in polygon_elements:
            pos_list = xml_helper.try_get_text_from_xml_element(poly,
                                                                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("posList"))

            if pos_list is None or len(pos_list) == 0:
                continue

            pos_list = pos_list.split(" ")
            vertices_pairs = []

            for i in range(0, len(pos_list), 2):
                vertices_pairs.append((float(pos_list[i]), float(pos_list[i + 1])))

            polygon_obj = GEOSGeometry(
                Polygon(
                    vertices_pairs
                ),
                srid=self.srs_code or DEFAULT_SRS
            )
            ret_list.append(polygon_obj)

        return ret_list

    def _create_multi_line_strings_from_xml_elements(self, multi_line_string_elements: list):
        """ Creates a list of MultiLineString objects from xml elements, which contain <gml:MultiLineString> elements

        Args:
            multi_line_string_elements (list): List of <gml:MultiLineString> xml elements
        Returns:
             ret_list (list): List of MultiLineString objects
        """
        ret_list = []

        for elem in multi_line_string_elements:
            coord_list = xml_helper.try_get_element_from_xml(elem, ".//" + GENERIC_NAMESPACE_TEMPLATE.format("coordinates"))

            for coord in coord_list:
                separator = xml_helper.try_get_attribute_from_xml_element(coord, "cs")
                decimal_symbol = xml_helper.try_get_attribute_from_xml_element(coord, "decimal")

                coords = xml_helper.try_get_text_from_xml_element(coord)
                coords = coords.split(separator)

                # make sure the decimal representation uses '.'
                if decimal_symbol != ".":
                    coords = [c.replace(decimal_symbol, ".") for c in coords]

                vertices_pairs = []

                for i in range(0, len(coords), 2):
                    vertices_pairs.append((float(coords[i]), float(coords[i + 1])))

                obj = GEOSGeometry(
                    MultiLineString(
                        vertices_pairs
                    ),
                    srid=self.srs_code or DEFAULT_SRS
                )
                ret_list.append(obj)

        return ret_list

    def _create_points_from_xml_elements(self, point_elements: list):
        """ Creates a list of Point objects from xml elements, which contain <gml:Point> elements

        Args:
            point_elements (list): List of <gml:Point> xml elements
        Returns:
             ret_list (list): List of Point objects
        """
        ret_list = []

        for elem in point_elements:
            pos = xml_helper.try_get_element_from_xml(elem, ".//" + GENERIC_NAMESPACE_TEMPLATE.format("pos"))
            pos = pos.split(" ")

            if len(pos) != 2:
                raise ValueError(TD_POINT_HAS_NOT_ENOUGH_VALUES)

            obj = GEOSGeometry(
                Point(pos[0], pos[1]),
                srid=self.srs_code or DEFAULT_SRS
            )

            ret_list.append(obj)

        return ret_list

    def _process_transaction_geometries(self):
        """ Creates geometries from <gml:Polygon>|<gml:MultiLineString>|<gml:Point> elements inside the transaction xml body

        Returns:
             nothing
        """
        # skip this if we have no transaction body
        if self.POST_raw_body is None:
            return

        xml_body = xml_helper.parse_xml(self.POST_raw_body)

        actions = ["INSERT", "UPDATE"]
        geom_collection = GeometryCollection()

        # Find INSERT and UPDATE geometries
        for action in actions:
            xml_elements = xml_helper.try_get_element_from_xml("//" + GENERIC_NAMESPACE_TEMPLATE.format(action), xml_body)

            for xml_element in xml_elements:
                # vertices can be found in <gml:posList> elements, as well as in <gml:coordinates>
                polygon_elements = xml_helper.try_get_element_from_xml(
                    ".//" + GENERIC_NAMESPACE_TEMPLATE.format("Polygon"), xml_element
                )
                multi_line_string_elements = xml_helper.try_get_element_from_xml(
                    ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MultiLineString"), xml_element
                )
                point_elements = xml_helper.try_get_element_from_xml(
                    ".//" + GENERIC_NAMESPACE_TEMPLATE.format("Point"), xml_element
                )

                # process found Polygons
                polygons = self._create_polygons_from_xml_elements(polygon_elements)
                geom_collection.extend(polygons)

                # process found MultiLineStrings
                multi_line_strings = self._create_multi_line_strings_from_xml_elements(multi_line_string_elements)
                geom_collection.extend(multi_line_strings)

                # process found Points
                points = self._create_points_from_xml_elements(point_elements)
                geom_collection.extend(points)

        geom_collection = geom_collection.unary_union
        self.transaction_geometries = geom_collection

    def _convert_image_point_to_spatial_coordinates(self, point: Point, width: int, height: int, bbox_coords: list):
        """ Converts the x|y coordinates of an image point to spatial EPSG:4326 coordinates, derived from a bounding box

        Args:
            point (Point): The Point object, which holds the image x|y position
            width (int); The width of the image
            height (int); The height of the image
            bbox_coords (list); The bounding box vertices as tuples in a list
        Returns:
             point (Point): The Point object, holding converted spatial coordinates
        """

        # the coordinate systems origin is 0|0 in the upper left corner of the image
        # get the vertices of the bbox which represent these image points: 0|0, max|0, 0|max
        bbox_upper_left = bbox_coords[1]
        bbox_upper_right = bbox_coords[2]
        bbox_lower_left = bbox_coords[0]

        # calculate the movement vector (only the non-zero part)
        # divide the movement vector using the width/height to get a vector step size
        step_left_right = (bbox_upper_right[0] - bbox_upper_left[0]) / width
        step_up_down = (bbox_lower_left[1] - bbox_upper_left[1]) / height

        # x represents the upper left "corner", increased by the product of the image X coordinate and the step size for this direction
        # equivalent for y
        point.x = bbox_upper_left[0] + point.x * step_left_right
        point.y = bbox_upper_left[1] + point.y * step_up_down
        point.srid = self.srs_code
        return point

    def _create_POST_data(self):
        """ Getter for the data which is used in a POST request

        Returns:
             post_data (dict)
        """
        post_data = {}
        for key, val in self.new_params_dict.items():
            if val is not None:
                post_data[key] = val
        return post_data

    def _create_GET_uri(self):
        """ Returns the processed operation uri.

        Inserts parameter changes before returning.

        Returns:
             uri (str): The operation uri
        """
        if self.request_is_GET:
            for key, val in self.new_params_dict.items():
                if val is not None:
                    self.get_uri = utils.set_uri_GET_param(self.get_uri, key, val)
        return self.get_uri

    def _check_get_feature_info_operation_access(self, sec_ops: QueryDict):
        """ Checks whether the user given x/y Point parameter object is inside the geometry, which defines the allowed
        access for the GetFeatureInfo operation

        Args:
            sec_ops (QueryDict): A QueryDict containing SecuredOperation objects
        Returns:
             Whether the Point is inside the geometry or not
        """

        # User is at least in one group that has access to this operation on this metadata.
        # Now check the spatial restriction!
        constraints = {}
        if self.x_y_coord is not None:
            constraints["x_y"] = False

        for sec_op in sec_ops:
            if sec_op.bounding_geometry.empty:
                # there is no specific area, so this group is allowed to request everywhere
                constraints["x_y"] = True
                break
            total_bounding_geometry = sec_op.bounding_geometry.unary_union
            if self.x_y_coord is not None:
                if total_bounding_geometry.covers(self.x_y_coord):
                    constraints["x_y"] = True

        return False not in constraints.values()

    def _create_secured_service_mask(self, metadata: Metadata, sec_ops: QueryDict):
        """ Creates call to local mapserver and returns the response

        Gets a mask image, which can be used to remove restricted areas from another image

        Args:
            metadata (Metadata): The metadata object
            sec_ops (QueryDict): SecuredOperation objects in a query dict
        Returns:
             bytes
        """
        response = ""
        for op in sec_ops:
            if op.bounding_geometry.empty:
                return None
            request_dict = {
                "map": MAPSERVER_SECURITY_MASK_FILE_PATH,
                "version": "1.1.1",
                "request": "GetMap",
                "service": "WMS",
                "format": "image/png",
                "layers": "mask",
                "srs": self.srs_param,
                "bbox": self.bbox_param.get("bbox_param"),
                "width": self.width_param,
                "height": self.height_param,
                "keys": op.id,
                "table": MAPSERVER_SECURITY_MASK_TABLE,
                "key_column": MAPSERVER_SECURITY_MASK_KEY_COLUMN,
                "geom_column": MAPSERVER_SECURITY_MASK_GEOMETRY_COLUMN,
            }
            uri = "{}?{}".format(
                MAPSERVER_LOCAL_PATH,
                urllib.parse.urlencode(request_dict)
            )

            c = CommonConnector(url=uri)
            c.load()
            response = c.content

        return response

    def _create_masked_image(self, img: bytes, mask: bytes, as_bytes: bool = False):
        """ Creates a masked image from two image byte object

        Args:
            img (byte): The bytes of the image
            mask (byte): The bytes of the mask
        Returns:
             img (Image): The masked image
        """
        try:
            img = Image.open(io.BytesIO(img))
        except OSError:
            raise Exception("Could not create image! Content was:\n {}".format(img))
        try:
            alpha_layer = Image.new("RGBA", img.size, (255, 0, 0, 0))
            if mask is None:
                # no bounding geometry for masking exist, just create a mask that does nothing
                mask = Image.new("RGB", img.size, (0, 0, 0))
            else:
                mask = Image.open(io.BytesIO(mask))

        except OSError:
            raise Exception("Could not create image! Content was:\n {}".format(mask))

        mask = mask.convert("L").resize(img.size)

        # save image format for restoring a few steps later
        img_format = img.format
        img = Image.composite(alpha_layer, img, mask)
        img.format = img_format
        del img_format

        # add access_denied_img image
        if self.access_denied_img is not None:
            old_format = img.format
            img = Image.alpha_composite(img, self.access_denied_img)
            img.format = old_format

        if as_bytes:
            outBytesStream = io.BytesIO()
            try:
                img.save(outBytesStream, img.format, optimize=True, quality=80)
                img = outBytesStream.getvalue()
            except IOError:
                # happens if a non-alpha channel format is requested, such as jpeg
                # replace alpha channel with white background
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                bg.save(outBytesStream, img.format, optimize=True, quality=80)
                img = outBytesStream.getvalue()
        return img

    def _check_transaction_operation_access(self, sec_ops: QueryDict):
        """ Checks whether the Transaction request can be allowed or not.

        Checks the SecuredOperations against geometries from the request

        Args:
            sec_ops (QueryDict): The SecuredOperations in a QueryDict object
        Returns:
             True|False
        """
        ret_val = True

        for sec_op in sec_ops:

            if sec_op.bounding_geometry.empty:
                # there is no allowed area defined, so this group is allowed to request everywhere
                return ret_val

            bounding_geom = sec_op.bounding_geometry.unary_union

            if not bounding_geom.covers(self.transaction_geometries):
                # If the geometries, that can be found in the transaction operation are not fully covered by the allowed
                # geometry, we do not allowe the access!
                return False

        return ret_val

    def _resolve_layer_param_to_leaf_layers(self, metadata: Metadata):
        """ Replaces the original requested layer param with all (leaf) child layers identifier as param.

        This way we can make sure no layer is returned, that would not be allowed on a direct call.

        Args:
            metadata (Metadata): The metadata of the requested service
        Returns:
             nothing
        """
        leaf_layers = []
        if self.layers_param is None:
            return

        for layer_param in self.layers_param.split(","):
            layer_obj = Layer.objects.get(
                parent_service__metadata=metadata,
                identifier=layer_param
            )
            leaf_layers += layer_obj.get_leaf_layers()

        if len(leaf_layers) > 0:
            self.layers_param = ",".join(leaf_layers)
        self.new_params_dict["LAYERS"] = self.layers_param

    def _extend_filter_by_spatial_restriction(self, sec_ops: QueryDict):
        """ Appends the spatial restriction filter element to an already existing filter

        Args:
            sec_ops (QueryDict: The secured operations, which hold the bounding geometries
        Returns:

        """
        bounding_geoms_filter_xml = []
        prefix = ""
        if self.version_param == OGCServiceVersionEnum.V_2_0_0 or OGCServiceVersionEnum.V_2_0_2:
            prefix = "{" + XML_NAMESPACES["fes"] + "}"

        # First get all single polygons from the GeometryCollection
        for sec_op in sec_ops:
            bounding_geom_collection = sec_op.bounding_geometry
            for bounding_geom in bounding_geom_collection.coords:
                coords = bounding_geom[0]
                geom = GEOSGeometry(Polygon(coords), bounding_geom_collection.srid)
                geom.transform(self.srs_code)
                bounding_geoms_filter_xml.append(geom)

        # Then transform them into spatial restricting filter xml elements
        _filter = self._create_filter_xml_from_geometries(bounding_geoms_filter_xml)

        # check if there is already a filter, that came with the initial request. If so, we need to combine this
        # with our newly created one
        if self.filter_param is not None and len(_filter) > 0:
            request_filter_elem = xml_helper.parse_xml(self.filter_param).getroot()
            request_filter_elem_children = request_filter_elem.getchildren()
            backend_filter_elem = xml_helper.parse_xml(_filter).getroot()
            backend_filter_elem_children = backend_filter_elem.getchildren()

            if len(backend_filter_elem_children) > 0 and len(request_filter_elem_children) > 0:
                add_elem = etree.Element("{}And".format(prefix))
                for child in request_filter_elem_children:
                    xml_helper.add_subelement(add_elem, child)
                for child in backend_filter_elem_children:
                    xml_helper.add_subelement(add_elem, child)

                xml_helper.add_subelement(request_filter_elem, add_elem)
            _filter = xml_helper.xml_to_string(request_filter_elem)

            self.filter_param = _filter
            self.new_params_dict["FILTER"] = self.filter_param

    def get_secured_operation_response(self, request: HttpRequest, metadata: Metadata):
        """ Calls the operation of a service if it is secured.

        Args:
            request (HttpRequest):
            metadata (Metadata):
        Returns:

        """
        response = None

        # if user could not be found in request -> not logged in -> no permission!
        if self.user is None:
            return response

        check_sec_ops = False
        if self.request_param in WMS_SECURED_OPERATIONS or self.request_param in WFS_SECURED_OPERATIONS:
            check_sec_ops = True

        # check if the metadata allows operation performing for certain groups
        sec_ops = metadata.secured_operations.filter(
            operation__operation_name__iexact=self.request_param,
            allowed_group__in=self.user.groups.all(),
        )

        if check_sec_ops and sec_ops.count() == 0:
            # this means the service is secured and the group has no access!
            return response

        # WMS - Features
        if self.request_param.upper() == OGCOperationEnum.GET_FEATURE_INFO.value.upper():
            allowed = self._check_get_feature_info_operation_access(sec_ops)
            if allowed:
                response = self.get_operation_response()

        # WMS - 'Map image'
        elif self.request_param.upper() == OGCOperationEnum.GET_MAP.value.upper():
            # no need to check if the access is allowed, since we mask the output anyway
            # but we need to make sure, that no top level layer is called, which contains a secured child!
            # therefore we need to check if there is at least one secured child, somewhere, and then replace the top
            # level layer with all direct, allowed children!
            img = self.get_operation_response()
            mask = self._create_secured_service_mask(metadata, sec_ops)
            response = self._create_masked_image(img, mask, as_bytes=True)

        # WMS - 'Legend image'
        elif self.request_param.upper() == OGCOperationEnum.GET_LEGEND_GRAPHIC.value.upper():
            uri = self.get_uri
            con = CommonConnector(uri)
            con.load()
            response = con.content

        # WFS - 'GetFeature'
        elif self.request_param.upper() == OGCOperationEnum.GET_FEATURE.value.upper():
            self._bbox_to_filter()
            self._extend_filter_by_spatial_restriction(sec_ops)
            response = self.get_operation_response()

        # WFS - 'DescribeFeatureType'
        elif self.request_param.upper() == OGCOperationEnum.DESCRIBE_FEATURE_TYPE.value.upper():
            response = self.get_operation_response()

        # WFS
        elif self.request_param.upper() == OGCOperationEnum.TRANSACTION.value.upper():
            allowed = self._check_transaction_operation_access(sec_ops)
            if allowed:
                response = self.get_operation_response(self.POST_raw_body)

        return response

    def get_operation_response(self, uri: str = None, post_data: dict = None):
        """ Performs the request.

        This may be called after the security checks have passed or otherwise if no security checks had to be done.

        Args:
            uri (str): The operation uri
            post_data (dict): A key-value dict of the POST data
        Returns:
             The xml response
        """
        if uri is None:
            uri = self._create_GET_uri()

        force_POST = False
        if len(uri) > 2048:
            force_POST = True

        if self.request_is_GET and not force_POST:
            c = CommonConnector(url=uri, external_auth=self.external_auth)
            c.load()

        else:
            c = CommonConnector(url=self.post_uri, external_auth=self.external_auth)
            if post_data is None:
                post_data = self._create_POST_data()  # get default POST as dict content

            # there are two ways to post data to a server:
            # 1)    Using x-www-form-urlencoded (mostly used)
            # 2)    Using a raw post body, which contains a xml (old style, used by some GIS servers
            # So if 1) fails, due to missing support, we need to build a parameter xml and try another post with raw body
            c.post(post_data)
            try_again_code_list = [500, 501, 502, 504, 510]
            if c.status_code is not None and c.status_code in try_again_code_list:
                # create xml from parameters according to specification
                request_builder = OGCRequestPOSTBuilder(post_data, self.POST_raw_body)
                post_xml = request_builder.build_POST_xml()
                c.post(post_xml)

        if c.status_code is not None and c.status_code != 200:
            raise Exception(c.status_code)

        return c.content

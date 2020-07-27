"""
Author: Michel Peltriaux
Organization: Spatial data infrastructure Rhineland-Palatinate, Germany
Contact: michel.peltriaux@vermkv.rlp.de
Created on: 15.07.20

"""
import json
from time import time
import datetime

import requests
from billiard.context import Process
from dateutil.parser import parse
from django.contrib.gis.geos import Polygon, GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, connections, IntegrityError, DataError
from django.db.models import Q
from django.utils.timezone import utc
from django.utils.translation import gettext_lazy as _
from lxml.etree import Element
from multiprocessing import cpu_count

from MrMap.settings import GENERIC_NAMESPACE_TEMPLATE
from MrMap.utils import execute_threads
from csw.settings import csw_logger, CSW_ERROR_LOG_TEMPLATE, CSW_EXTENT_WARNING_LOG_TEMPLATE, HARVEST_METADATA_TYPES
from service.helper import xml_helper
from service.helper.enums import OGCOperationEnum, ResourceOriginEnum, MetadataRelationEnum
from service.models import Metadata, Dataset, Keyword, Category, MetadataRelation, MimeType, Service
from service.settings import DEFAULT_SRS, DEFAULT_SERVICE_BOUNDING_BOX_EMPTY
from structure.models import PendingTask, MrMapGroup, Organization


class Harvester:
    def __init__(self, metadata: Metadata, group: MrMapGroup, max_records_per_request: int = 200):
        self.metadata = metadata
        self.harvesting_group = group
        self.harvest_url = metadata.service.operation_urls.filter(
            operation=OGCOperationEnum.GET_RECORDS.value,
        ).exclude(
            url=None
        ).first()

        self.version = self.metadata.get_service_version().value
        self.max_records_per_request = max_records_per_request
        self.start_position = 1

        self.method = self.harvest_url.method

        self.harvest_url = getattr(self.harvest_url, "url", None)
        if self.harvest_url is None:
            raise ValueError(_("No get records URL available"))
        self.output_format = getattr(
            self.metadata.formats.filter(
                mime_type__icontains="xml"
            ).first(),
            "mime_type",
            None
        )

        if self.output_format is None:
            raise ValueError(_("No XML output format available"))

        self.pending_task = None  # will be initialized in harvest()
        self.deleted_metadata = {}
        self.parent_child_map = {}

    def harvest(self, task_id: str = None):
        """ Starts harvesting procedure

        Returns:

        """
        # Create a pending task record for the database first!
        task_exists = PendingTask.objects.filter(
            description__icontains=self.metadata.title
        ).exists()
        if task_exists:
            raise ProcessLookupError(_("Harvesting is currently performed"))
        else:
            async_task_id = task_id or self.metadata.id
            self.pending_task = PendingTask.objects.create(
                task_id=async_task_id,
                description=json.dumps({
                    "service": self.metadata.title,
                    "phase": "Loading Harvest...",
                }),
                progress=0,
                remaining_time=None,
                created_by=self.harvesting_group
            )

        # Fill the deleted_metadata with all persisted metadata, so we can eliminate each entry if it is still provided by
        # the catalogue. In the end we will have a list, which contains metadata IDs that are not found in the catalogue anymore.
        all_harvested_metadata = Metadata.objects.filter(
            related_metadata__origin=ResourceOriginEnum.CATALOGUE.value,
            related_metadata__relation_type=MetadataRelationEnum.HARVESTED_THROUGH.value,
            related_metadata__metadata_to=self.metadata
        ).distinct()
        # Use a dict instead of list to increase lookup afterwards
        self.deleted_metadata = {str(md.identifier): None for md in all_harvested_metadata}

        # Perform the initial "hits" request to get an overview of how many data will be fetched
        hits_response = self._get_harvest_response(result_type="hits")
        if hits_response.status_code != 200:
            raise ConnectionError(_("Harvest failed: Code {}\n{}").format(hits_response.status_code, hits_response.content))
        xml_response = xml_helper.parse_xml(hits_response.content)
        if xml_response is None:
            raise ConnectionError(_("Response is no proper xml: \n{}".format(hits_response.content)))

        total_number_to_harvest = int(xml_helper.try_get_attribute_from_xml_element(
            xml_response,
            "numberOfRecordsMatched",
            "//" + GENERIC_NAMESPACE_TEMPLATE.format("SearchResults"),
            ))

        progress_step_per_request = float(self.max_records_per_request / total_number_to_harvest) * 100

        t_start = time()
        number_rest_to_harvest = total_number_to_harvest
        number_of_harvested = 0
        # Run as long as we can fetch data!
        while self.start_position != 0:
            # Get response
            next_response = self._get_harvest_response(result_type="results", only_content=True)

            self._process_harvest_response(next_response)

            # Calculate time since loop started
            duration = time() - t_start
            number_rest_to_harvest -= self.max_records_per_request
            number_of_harvested += self.max_records_per_request
            if self.start_position == 0:
                # We are done!
                estimated_time_for_all = datetime.timedelta(seconds=0)
            else:
                seconds_for_rest = (number_rest_to_harvest * (duration / number_of_harvested))
                estimated_time_for_all = datetime.timedelta(seconds=seconds_for_rest)
            self._update_pending_task(self.start_position, total_number_to_harvest, progress_step_per_request, estimated_time_for_all)

        # Delete Metadata records which could not be found in the catalogue anymore
        deleted_metadata_ids = [k for k, v in self.deleted_metadata.items()]
        deleted_metadatas = Metadata.objects.filter(
            identifier__in=deleted_metadata_ids
        )
        deleted_metadatas.delete()

        self.pending_task.delete()

    def _generate_request_POST_body(self, start_position: int, result_type: str = "results"):
        """ Creates a CSW POST body xml document for GetRecords

        Args:
            start_position (int): The start position for the request
        Returns:
             xml (str): The GetRecords xml document
        """
        namespaces = {
            "csw": "http://www.opengis.net/cat/csw/2.0.2",
            "apiso": "http://www.opengis.net/cat/csw/apiso/1.0",
            "ogc": "http://www.opengis.net/ogc",
            "gmd": "http://www.isotc211.org/2005/gmd",
            "ows": "http://www.opengis.net/ows",
            "xsd": "http://www.w3.org/2001/XMLSchema",
            "xsi": "http://www.w3.org/2001/XMLSchema",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dct": "http://purl.org/dc/terms/",
            "schemaLocation": "http://www.opengis.net/cat/csw/{}".format(self.version),
            None: "http://www.opengis.net/cat/csw/{}".format(self.version),
        }
        csw_ns = "{" + namespaces["csw"] + "}"

        root_elem = Element(
            "{}{}".format(csw_ns, OGCOperationEnum.GET_RECORDS.value),
            attrib={
                "version": self.version,
                "service": "CSW",
                "resultType": result_type,
                "outputFormat": self.output_format,
                "startPosition": str(start_position),
                "maxRecords": str(self.max_records_per_request),
                #"{}schemaLocation".format(xsi_ns): "http://www.opengis.net/cat/csw/2.0.2",
            },
            nsmap=namespaces
        )
        xml_helper.create_subelement(
            root_elem,
            "{}Query".format(csw_ns),
            None,
            {
                "typeNames": "gmd:MD_Metadata"
            }
        )

        return xml_helper.xml_to_string(root_elem)

    def _update_pending_task(self, next_record: int, total_records: int, progress_step: float, remaining_time):
        """ Updates the PendingTask object

        Args:
            next_record (int): The nextRecord value
            total_records (int): The totalRecord value
            progress_step (int): The increment for the next step
            remaining_time: The timedelta for the remaining time
        Returns:

        """
        descr = json.loads(self.pending_task.description)
        descr["phase"] = _("Harvesting {} of {}").format(next_record, total_records)
        self.pending_task.description = json.dumps(descr)
        self.pending_task.remaining_time = remaining_time
        self.pending_task.progress += progress_step
        self.pending_task.save()

    def _get_harvest_response(self, result_type: str = "results", only_content: bool = False):
        """ Fetch a response for the harvesting (GetRecords)

        Args:
            result_type (str): Which resultType should be used (hits|results)
        Returns:
             harvest_response (bytes): The response content
        """
        if self.method.upper() == "GET":
            params = {
                "service": "CSW",
                "typeNames": "gmd:MD_Metadata",
                "resultType": result_type,
                "startPosition": self.start_position,
                "outputFormat": self.output_format,
                "maxRecords": self.max_records_per_request,
                "version": self.version,
                "request": OGCOperationEnum.GET_RECORDS.value,
            }
            harvest_response = requests.get(
                url=self.harvest_url,
                params=params
            )
        elif self.method.upper() == "POST":
            post_body = self._generate_request_POST_body(self.start_position, result_type=result_type)
            harvest_response = requests.post(self.harvest_url, data=post_body)
        else:
            raise NotImplementedError()

        response = harvest_response if not only_content else harvest_response.content
        return response

    def _process_harvest_response(self, next_response: bytes):
        """ Processes the harvest response content

        While the last response is being processed, the next one is already loaded to decrease run time

        Args:
            response (bytes): The response as bytes
        Returns:
             next_record (int): The nextRecord value (used for next startPosition)
        """
        xml_response = xml_helper.parse_xml(next_response)
        if xml_response is None:
            csw_logger.error(
                "Response is no valid xml. catalogue: {}, startPosition: {}, maxRecords: {}".format(
                    self.metadata.title,
                    self.start_position,
                    self.max_records_per_request
                )
            )
            # Abort!
            self.start_position = 0
            return

        md_metadata_entries = xml_helper.try_get_element_from_xml(
            "//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_Metadata"),
            xml_response
        ) or []
        next_record_position = int(xml_helper.try_get_attribute_from_xml_element(
            xml_response,
            "nextRecord",
            "//" + GENERIC_NAMESPACE_TEMPLATE.format("SearchResults"),
        ))
        self.start_position = next_record_position

        # Delete response to free memory
        del xml_response

        # Process response via multiple processes
        t_start = time()
        num_processes = int(cpu_count()/2)
        num_processes = num_processes if num_processes >= 1 else 1
        index_step = int(len(md_metadata_entries)/num_processes)
        start_index = 0
        end_index = 0
        self.resource_list = md_metadata_entries
        process_list = []
        for i in range(0, num_processes):
            if index_step < 1:
                end_index = -1
            else:
                end_index += index_step
            p = Process(target=self._create_metadata_from_md_metadata, args=(start_index, end_index))
            start_index += index_step
            process_list.append(p)
        # Close all connections to force each process to create a new one for itself
        connections.close_all()
        execute_threads(process_list)

        csw_logger.debug(
            "Harvesting '{}': runtime for {} metadata parsing: {}s ####".format(
                self.metadata.title,
                self.max_records_per_request,
                time() - t_start
            )
        )

    def _create_metadata_from_md_metadata(self, start_index, end_index):
        """ Creates Metadata records from raw xml md_metadata data.

        Runs multiprocessed. Therefore only a start_index and end_index is given, since each process reads from the
        same parent process resource_list.

        Args:
            start_index (int): The start index
            end_index (int): The end index
        Returns:
        """
        if end_index < 0:
            md_metadata_entries = self.resource_list
        else:
            md_metadata_entries = self.resource_list[start_index:end_index]
        md_data = self._md_metadata_parse_to_dict(md_metadata_entries)

        for md_data_entry in md_data:
            self._persist_metadata(md_data_entry)

        self._persist_metadata_parent_relation()

    def _persist_metadata(self, md_data_entry: dict):
        """ Creates real Metadata model records from the parsed data

        Args:
            md_data_entry (dict):
        Returns:
             metadata (Metadata): The persisted metadata object
        """
        _id = md_data_entry["id"]
        # Check if id can be found in dict of metadata to be deleted. If so, it can be removed
        if self.deleted_metadata.get(_id, None) is not None:
            del self.deleted_metadata[_id]

        try:
            md = Metadata.objects.get(
                identifier=_id,
            )
            is_new = False
            if md.last_remote_change == md_data_entry["date_stamp"]:
                # Nothing to do here!
                return
        except ObjectDoesNotExist:
            md = Metadata(
                identifier=_id
            )
            is_new = True
        md.access_constraints = md_data_entry.get("access_constraints", None)
        md.created_by = self.harvesting_group
        md.origin = ResourceOriginEnum.CATALOGUE.value
        md.last_remote_change = md_data_entry.get("date_stamp", None)
        md.title = md_data_entry.get("title", None)
        md.public_id = md.generate_public_id()
        md.contact = md_data_entry.get("contact", None)
        md.language_code = md_data_entry.get("language_code", None)
        md.metadata_type = md_data_entry.get("metadata_type", None)
        md.abstract = md_data_entry.get("abstract", None)
        md.bounding_geometry = md_data_entry.get("bounding_geometry", None)
        md.online_resource = md_data_entry.get("link", None)
        formats = md_data_entry.get("formats", [])
        md.is_active = True

        try:
            # Improve speed for keyword get-create by fetching (filter) all existing ones and only perform
            # get_or_create on the ones that do not exist yet. Speed up by ~50% for large amount of data
            existing_kws = Keyword.objects.filter(keyword__in=md_data_entry["keywords"])
            existing_kws = [kw.keyword for kw in existing_kws]
            new_kws = [kw for kw in md_data_entry["keywords"] if kw not in existing_kws]
            [Keyword.objects.get_or_create(keyword=kw)[0] for kw in new_kws]
            kws = Keyword.objects.filter(keyword__in=md_data_entry["keywords"])

            # Same for MimeTypes
            existing_formats = MimeType.objects.filter(mime_type__in=md_data_entry["formats"])
            existing_formats = [_format.mime_type for _format in existing_formats]
            new_formats = [_format for _format in md_data_entry["formats"] if _format not in existing_formats]
            [MimeType.objects.get_or_create(mime_type=_format)[0] for _format in new_formats]
            formats = MimeType.objects.filter(mime_type__in=md_data_entry["formats"])

            with transaction.atomic():
                q = Q()
                for cat in md_data_entry["categories"]:
                    q |= Q(title_EN__iexact=cat)
                categories = Category.objects.filter(q)

                md.save(add_monitoring=False)
                md.keywords.add(*kws)
                md.categories.add(*categories)
                md.formats.add(*formats)

                # To reduce runtime, we only create a new MetadataRelation if we are sure there hasn't already been one.
                # Using get_or_create increases runtime on existing metadata too much!
                if is_new:
                    md.related_metadata.add(
                        MetadataRelation.objects.create(
                            metadata_from=md,
                            relation_type=MetadataRelationEnum.HARVESTED_THROUGH.value,
                            metadata_to=self.metadata,
                            origin=ResourceOriginEnum.CATALOGUE.value
                        )
                    )

            parent_id = md_data_entry["parent_id"]
            # Add the found parent_id to the parent_child map!
            if parent_id is not None:
                if self.parent_child_map.get(parent_id, None) is None:
                    self.parent_child_map[parent_id] = [md]
                else:
                    self.parent_child_map[parent_id].append(md)

        except (IntegrityError, DataError) as e:
            csw_logger.error(
                CSW_ERROR_LOG_TEMPLATE.format(
                    md.identifier,
                    self.metadata.title,
                    e
                )
            )

    @transaction.atomic
    def _persist_metadata_parent_relation(self):
        """ Creates MetadataRelation records if there is information about a parent-child relation

        Args:
            md_data_entry (dict):
        Returns:
             metadata (Metadata): The persisted metadata object
        """
        # Make sure there is some kind of parent-subelement relation. We can not use the regular Service.parent_service
        # model since there is not enough data from the CSW to use Service properly and we can not 100% determine which
        # types of Servives we are dealing with (WFS/WMS). Therefore for harvesting, we need to use this workaround using
        # MetadataRelation

        for parent_id, children in self.parent_child_map.items():
            try:
                parent_md = Metadata.objects.get(
                    identifier=parent_id
                )
            except ObjectDoesNotExist:
                # it seems that this metadata has not been harvested yet - we keep it in the map for later!
                continue
            for child in children:
                # Check if relation already exists - again a faster alternative to get_or_create
                rel_exists = child.related_metadata.filter(
                    metadata_to=parent_md,
                    relation_type=MetadataRelationEnum.HARVESTED_PARENT.value,
                    origin=ResourceOriginEnum.CATALOGUE.value,
                ).exists()
                if not rel_exists:
                    md_relation = MetadataRelation.objects.create(
                        metadata_from=child,
                        relation_type=MetadataRelationEnum.HARVESTED_PARENT.value,
                        metadata_to=parent_md,
                        origin=ResourceOriginEnum.CATALOGUE.value
                    )
                    parent_md.related_metadata.add(md_relation)
                    child.related_metadata.add(md_relation)

            # clear children list of parent afterwards so we don't work on them again
            self.parent_child_map[parent_id] = []

    def _md_metadata_parse_to_dict(self, md_metadata_entries: list) -> list:
        """ Read most important data from MD_Metadata xml element

        Args:
            md_metadata_entries (list): The xml MD_Metadata elements
        Returns:
             ret_list (list): The list containing dicts
        """
        ret_list = []
        for md_metadata in md_metadata_entries:
            md_data_entry = {}

            # Check before anything else, whether this metadata type can be skipped!
            hierarchy_level = xml_helper.try_get_attribute_from_xml_element(
                md_metadata,
                "codeListValue",
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("hierarchyLevel")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("MD_ScopeCode")
            )
            metadata_type = hierarchy_level
            md_data_entry["metadata_type"] = metadata_type
            if not HARVEST_METADATA_TYPES.get(metadata_type, False):
                continue

            _id = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("fileIdentifier")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            md_data_entry["id"] = _id

            parent_id = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("parentIdentifier")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            md_data_entry["parent_id"] = parent_id

            # A workaround, so we do not need to check whether SV_ServiceIdentification or MD_DataIdentification is present
            # in this metadata: Simply take the direct parent and perform a deeper nested search on the inside of this element.
            # Yes, we could simply decide based on the hierarchyLevel attribute whether to search for SV_xxx or MD_yyy.
            # No, there are metadata entries which do not follow these guidelines and have "service" with MD_yyy
            # Yes, they are important since they can be found in the INSPIRE catalogue (07/2020)
            identification_elem = xml_helper.try_get_single_element_from_xml(
                xml_elem=md_metadata,
                elem=".//" + GENERIC_NAMESPACE_TEMPLATE.format("identificationInfo")
            )
            title = xml_helper.try_get_text_from_xml_element(
                identification_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("citation")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CI_Citation")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("title")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            md_data_entry["title"] = title

            language_code = xml_helper.try_get_attribute_from_xml_element(
                md_metadata,
                "codeListValue",
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("language")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("LanguageCode")
            )
            md_data_entry["language_code"] = language_code

            date_stamp = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                "./" + GENERIC_NAMESPACE_TEMPLATE.format("dateStamp")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Date")
            ) or xml_helper.try_get_text_from_xml_element(
                md_metadata,
                "./" + GENERIC_NAMESPACE_TEMPLATE.format("dateStamp")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("DateTime")
            )
            try:
                md_data_entry["date_stamp"] = parse(date_stamp).replace(tzinfo=utc)
            except TypeError:
                md_data_entry["date_stamp"] = None

            abstract = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("abstract")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            md_data_entry["abstract"] = abstract

            resource_link = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_DigitalTransferOptions")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("onLine")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CI_OnlineResource")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("linkage")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("URL"),
            )
            md_data_entry["link"] = resource_link

            keywords = xml_helper.try_get_element_from_xml(
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("keyword")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString"),
                md_metadata,
            ) or []
            keywords = [
                xml_helper.try_get_text_from_xml_element(
                    kw
                )
                for kw in keywords
            ]
            md_data_entry["keywords"] = keywords

            access_constraints = xml_helper.try_get_text_from_xml_element(
                md_metadata,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("otherConstraints")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            md_data_entry["access_constraints"] = access_constraints

            categories = xml_helper.try_get_element_from_xml(
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_TopicCategoryCode"),
                md_metadata,
            ) or []
            categories = [
                xml_helper.try_get_text_from_xml_element(
                    cat
                )
                for cat in categories
            ]
            md_data_entry["categories"] = categories

            bbox_elem = xml_helper.try_get_single_element_from_xml(
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("EX_GeographicBoundingBox"),
                md_metadata
            )
            if bbox_elem is not None:
                extent = [
                    xml_helper.try_get_text_from_xml_element(
                        bbox_elem,
                        ".//" + GENERIC_NAMESPACE_TEMPLATE.format("westBoundLongitude")
                        + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Decimal")
                    ) or "0.0",
                    xml_helper.try_get_text_from_xml_element(
                        bbox_elem,
                        ".//" + GENERIC_NAMESPACE_TEMPLATE.format("southBoundLatitude")
                        + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Decimal")
                    ) or "0.0",
                    xml_helper.try_get_text_from_xml_element(
                        bbox_elem,
                        ".//" + GENERIC_NAMESPACE_TEMPLATE.format("eastBoundLongitude")
                        + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Decimal")
                    ) or "0.0",
                    xml_helper.try_get_text_from_xml_element(
                        bbox_elem,
                        ".//" + GENERIC_NAMESPACE_TEMPLATE.format("northBoundLatitude")
                        + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Decimal")
                    ) or "0.0",
                ]
                # There are metadata with wrong vertex notations like 50,3 instead of 50.3
                # We should just drop them, since they are not compatible with the specifications but in here, we make an
                # exception and replace , since it's quite easy
                extent = [vertex.replace(",", ".") for vertex in extent]
                try:
                    bounding_geometry = GEOSGeometry(Polygon.from_bbox(bbox=extent), srid=DEFAULT_SRS)
                except Exception:
                    # Log malicious extent!
                    csw_logger.warning(
                        CSW_EXTENT_WARNING_LOG_TEMPLATE.format(
                            _id,
                            self.metadata.title,
                            extent
                        )
                    )
                    bounding_geometry = DEFAULT_SERVICE_BOUNDING_BOX_EMPTY
            else:
                bounding_geometry = DEFAULT_SERVICE_BOUNDING_BOX_EMPTY

            md_data_entry["bounding_geometry"] = bounding_geometry
            md_data_entry["contact"] = self._create_contact_from_md_metadata(md_metadata)
            md_data_entry["formats"] = self._create_formats_from_md_metadata(md_metadata)

            # Load non-metadata data
            # ToDo: Should harvesting persist non-metadata data?!
            #described_resource = None
            #metadata = None
            #if hierarchy_level == MetadataEnum.DATASET.value:
            #    described_resource = self._create_dataset_from_md_metadata(md_metadata, metadata)
            #    described_resource.metadata = metadata
            #    described_resource.is_active = True
            #    described_resource.save()

            ret_list.append(md_data_entry)
        return ret_list

    def _create_dataset_from_md_metadata(self, md_metadata: Element, metadata: Metadata) -> Dataset:
        """ Creates a Dataset record from xml data
        Args:
            md_metadata (Element): The xml element which holds the data
            metadata (Metadata): The related metadata element
        Returns:
            dataset (Dataset): The dataset record
        """
        dataset = Dataset()
        dataset.language_code = metadata.language_code
        dataset.language_code_list_url = xml_helper.try_get_attribute_from_xml_element(
            md_metadata,
            "codeList",
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("language")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("LanguageCode")
        )
        dataset.character_set_code = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("characterSet")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("MD_CharacterSetCode")
        )
        dataset.character_set_code_list_url = xml_helper.try_get_attribute_from_xml_element(
            md_metadata,
            "codeList",
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("characterSet")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("MD_CharacterSetCode")
        )
        dataset.date_stamp = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("dateStamp")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("Date")
        )
        dataset.metadata_standard_name = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("metadataStandardName")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        dataset.metadata_standard_version = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("metadataStandardVersion")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        dataset.update_frequency_code = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_MaintenanceFrequencyCode")
        )
        dataset.update_frequency_code_list_url = xml_helper.try_get_attribute_from_xml_element(
            md_metadata,
            "codeList",
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_MaintenanceFrequencyCode")
        )
        dataset.use_limitation = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("useLimitation")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        dataset.lineage_statement = xml_helper.try_get_text_from_xml_element(
            md_metadata,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("statement")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        return dataset

    def _create_formats_from_md_metadata(self, md_metadata: Element) -> list:
        """ Creates a list of MimeType objects from MD_Metadata element

        Args:
            md_metadata (Element): The xml element
        Returns:
             formats (list)
        """
        formats = []
        distribution_elem = xml_helper.try_get_single_element_from_xml(
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("distributionFormat"),
            md_metadata
        )
        if distribution_elem is None:
            return formats
        md_format_elems = xml_helper.try_get_element_from_xml(
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("MD_Format"),
            md_metadata
        )
        for md_format_elem in md_format_elems:
            name = xml_helper.try_get_text_from_xml_element(
                md_format_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("name")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            if name is not None:
                formats.append(name)
        return formats

    def _create_contact_from_md_metadata(self, md_metadata: Element) -> Organization:
        """ Creates an Organization (Contact) instance from MD_Metadata.

        Holds the basic information

        Args:
            md_metadata (Element): The xml element
        Returns:
             org (Organization): The organization element
        """
        resp_party_elem = xml_helper.try_get_single_element_from_xml(
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("CI_ResponsibleParty"),
            md_metadata
        )
        if resp_party_elem is None:
            return None

        organization_name = xml_helper.try_get_text_from_xml_element(
            resp_party_elem,
            "./" + GENERIC_NAMESPACE_TEMPLATE.format("organisationName")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        person_name = xml_helper.try_get_text_from_xml_element(
            resp_party_elem,
            "./" + GENERIC_NAMESPACE_TEMPLATE.format("individualName")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        phone = xml_helper.try_get_text_from_xml_element(
            resp_party_elem,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("CI_Telephone")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("voice")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        facsimile = xml_helper.try_get_text_from_xml_element(
            resp_party_elem,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("CI_Telephone")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("facsimile")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
        )
        # Parse address information, create fallback values
        address = None
        city = None
        postal_code = None
        country = None
        email = None
        state = None
        address_elem = xml_helper.try_get_single_element_from_xml(
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("CI_Address"),
            md_metadata
        )
        if address_elem is not None:
            address = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("deliveryPoint")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            city = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("city")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            postal_code = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("postalCode")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            country = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("country")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            email = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("electronicMailAddress")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
            state = xml_helper.try_get_text_from_xml_element(
                address_elem,
                ".//" + GENERIC_NAMESPACE_TEMPLATE.format("administrativeArea")
                + "/" + GENERIC_NAMESPACE_TEMPLATE.format("CharacterString")
            )
        is_auto_generated = True
        description = xml_helper.try_get_text_from_xml_element(
            resp_party_elem,
            ".//" + GENERIC_NAMESPACE_TEMPLATE.format("CI_OnlineResource")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("linkage")
            + "/" + GENERIC_NAMESPACE_TEMPLATE.format("URL")
        )
        org = Organization.objects.get_or_create(
            person_name=person_name,
            organization_name=organization_name,
            phone=phone,
            facsimile=facsimile,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            email=email,
            state_or_province=state,
            is_auto_generated=is_auto_generated,
            description=description,
        )[0]
        return org
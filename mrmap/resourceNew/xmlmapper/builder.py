from abc import ABC, abstractmethod
from collections import OrderedDict

from resourceNew.models import Service, Keyword, ServiceMetadata, ReferenceSystem
from resourceNew.xmlmapper.ogc.capabilities.wms.c.service import Wms130CapabilitiesConverter


class OgcServiceBuilder(ABC):
    """The Builder interface specifies methods for creating the different parts of
    ogc service objects.
    """

    @property
    @abstractmethod
    def transient_objects(self) -> None:
        pass

    @abstractmethod
    def produce_service(self) -> None:
        pass

    @abstractmethod
    def produce_service_metadata(self) -> None:
        pass

    @abstractmethod
    def produce_keywords(self) -> None:
        pass

    @abstractmethod
    def produce_reference_systems(self) -> None:
        pass


class WmsServiceBuilder(OgcServiceBuilder, ABC):
    """The Builder interface specifies methods for creating the different parts of
    wms service objects.
    """

    @abstractmethod
    def produce_layer_tree(self) -> None:
        pass

    @abstractmethod
    def produce_layer_metadata(self) -> None:
        pass


class Wms130Builder(WmsServiceBuilder):
    """The Concrete Builder classes follow the Builder interface and provide
    specific implementations of the building steps.
    """
    _keywords = None
    _reference_systems = None
    _service = None
    _service_metadata = None
    _layers = None
    _m2m_relations = None

    def __init__(self, base_service: Wms130CapabilitiesConverter) -> None:
        """A fresh builder instance should contain a blank service object, which is
        used in further assembly.
        """
        self._base_service = base_service
        self.reset()

    def reset(self) -> None:
        self._service = self._base_service.convert_to_model()
        self._service_metadata = None

    @property
    def transient_objects(self) -> OrderedDict:
        transient_objects = OrderedDict()
        transient_objects["keywords"] = self._keywords
        transient_objects["reference_systems"] = self._reference_systems
        transient_objects["service"] = self._service
        transient_objects["service_metadata"] = self._service_metadata
        transient_objects["layers"] = self._layers
        transient_objects["m2m_relations"] = self._m2m_relations
        return transient_objects

    def produce_service(self) -> None:
        """Convert the service object to model instance."""
        self._service = {"model": Service,
                         "objects": self._base_service.convert_to_model(),
                         "save_operation": "create"}

    def produce_service_metadata(self) -> None:
        """Convert the service_metadata object to model instance."""
        _service_metadata = self._base_service.service_metadata.convert_to_model()
        _service_metadata.described_object = self._service
        self._service_metadata = {"model": ServiceMetadata,
                                  "objects": self._service_metadata,
                                  "save_operation": "create"}

    def produce_keywords(self) -> None:
        """Covert all keywords of all possible objects"""
        _keywords = {}
        _service_metadata_keyword_pks = []
        for keyword in self._base_service.service_metadata.keywords:
            if not keyword.__str__() in self._keywords:
                _keywords.update({keyword.__str__(): keyword})
            _service_metadata_keyword_pks.append(keyword.__str__())

        self._m2m_relations.append({"object": self._service_metadata,
                                    "field_name": "keywords",
                                    "query_set": Keyword.objects.filter(pk__in=_service_metadata_keyword_pks)})

        self._keywords = {"model": Keyword,
                          "objects": _keywords.items(),
                          "save_operation": "get_or_create"}

    def produce_reference_systems(self) -> None:
        """Convert all reference systems of all possible objects"""
        _reference_systems = {}


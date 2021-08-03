from abc import ABC, abstractmethod

from resourceNew.models import Service, Keyword
from resourceNew.xmlmapper.ogc.capabilities.wms.c.service import Wms130CapabilitiesConverter


class OgcServiceBuilder(ABC):
    """The Builder interface specifies methods for creating the different parts of
    ogc service objects.
    """

    @property
    @abstractmethod
    def service(self) -> None:
        pass

    @abstractmethod
    def produce_service_metadata(self) -> None:
        pass

    @abstractmethod
    def produce_keywords(self) -> None:
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
    _service = None
    _service_metadata = None

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
    def service(self) -> Service:
        """
        Concrete Builders are supposed to provide their own methods for
        retrieving results. That's because various types of builders may create
        entirely different products that don't follow the same interface.
        Therefore, such methods cannot be declared in the base Builder interface
        (at least in a statically typed programming language).

        Usually, after returning the end result to the client, a builder
        instance is expected to be ready to start producing another product.
        That's why it's a usual practice to call the reset method at the end of
        the `getProduct` method body. However, this behavior is not mandatory,
        and you can make your builders wait for an explicit reset call from the
        client code before disposing of the previous result.
        """
        service = self._service
        self.reset()
        return service

    def produce_service_metadata(self) -> None:
        """Convert the service_metadata object to model instance and persist it to the database."""
        self._service_metadata = self._base_service.service_metadata.convert_to_model()
        self._service_metadata.described_object = self._service
        self._service_metadata.save()

    def produce_keywords(self) -> None:
        """Collect and covert all keywords and its pointing objects, persists all keywords in first step, link the
        persisted keywords in second step.

        complex_object = [(Keyword, [kw1, kw2, kw3]), (Service, [service1]), (ServiceMetadata, [service_md1.keywords.add(*[kw1, kw2])])]

        _keywords = {"kw1": kw1,
                     "kw2": kw2,
                     "kw3": kw3,
                     ...}
        _pointing_objects = [(obj1, ["kw1", "kw2"]), (obj2, ["kw2"]), (obj3, ["kw1", "kw3"])]

        """
        _keywords = {}
        _pointing_object_keywords = []
        _pointing_objects = []
        for keyword in self._base_service.service_metadata.keywords:
            if not keyword.__str__() in _keywords:
                _keywords.update({keyword.__str__(): keyword})
            _pointing_object_keywords.append(_keywords.get(keyword.__str__()))
        _pointing_objects.append((self._service_metadata, _pointing_object_keywords))

        for kw in _keywords.items():
            _kw = Keyword.objects.get_or_create(keyword=kw.keyword)
            # todo: change kw in _keywords

        for pointing_object, keywords in _pointing_objects:
            pointing_object.keywords.add(*[_keywords.get(kw)] for kw in keywords)

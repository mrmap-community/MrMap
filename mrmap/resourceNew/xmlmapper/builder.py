from abc import ABC, abstractmethod

from django.db.models import Q

from resourceNew.models import Service, Keyword, ServiceMetadata, Layer, LayerMetadata, ReferenceSystem, RemoteMetadata
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

    @abstractmethod
    def construct_keywords(self, db_obj, keywords) -> None:
        pass

    @abstractmethod
    def construct_reference_systems(self, db_obj, keywords) -> None:
        pass

    @abstractmethod
    def produce_remote_metadata(self) -> None:
        pass

    @abstractmethod
    def produce_m2m_relations(self) -> None:
        pass


class AbstractWmsBuilder(OgcServiceBuilder, ABC):
    """The Builder interface specifies methods for creating the different parts of
    wms service objects.
    """

    @abstractmethod
    def produce_layers(self) -> None:
        pass

    @abstractmethod
    def produce_layer_metadata(self) -> None:
        pass


class WmsBuilder(AbstractWmsBuilder):
    """The Concrete Builder classes follow the Builder interface and provide
    specific implementations of the building steps.
    """
    _proto_service = None
    _service = None
    _service_metadata = None
    _keywords = {}
    _reference_systems = {}
    _layers = []
    _layer_metadata = []
    _remote_metadata_list = []
    # todo:
    db_style_list = []
    db_legend_url_list = []
    db_dimension_list = []
    db_dimension_extent_list = []

    _m2m_relations = []  # tuple of (instance, "field_name", QuerySet/list)

    def __init__(self, proto_service) -> None:
        """A fresh builder instance should contain a blank service object, which is
        used in further assembly.
        """
        self._proto_service = proto_service
        self.reset()

    def reset(self) -> None:
        self._service = self._proto_service.convert_to_model()
        self._service_metadata = None
        self._keywords = {}
        self._reference_systems = {}
        self._layers = []
        self._layer_metadata = []
        self._m2m_relations = []

    @property
    def service(self) -> Service:
        service_pk = self._service.pk
        self.reset()
        return Service.objects.get_full_service(pk=service_pk)

    def produce_service(self) -> None:
        self._service.save()
        self.construct_remote_metadata(remote_metadata=self._proto_service.remote_metadata,
                                       service=self._service,
                                       content_type=Service,
                                       object_id=self._service.pk)

    def produce_service_metadata(self) -> None:
        """Convert the service_metadata object to model instance."""
        self._service_metadata = self._proto_service.service_metadata.convert_to_model()
        self._service_metadata.described_object = self._service
        self._service_metadata.save()
        self.construct_keywords(db_obj=self._service_metadata, keywords=self._proto_service.service_metadata.keywords)

    def construct_keywords(self, db_obj, keywords) -> None:
        """Covert all keywords of all possible objects"""
        if keywords:
            _keyword_pks = []
            for keyword in keywords:
                # todo: for loop in for loop!
                #  maybe this filtering is not efficient. Check if simply get_or_create with all is more efficient.
                if not keyword.__str__() in self._keywords:
                    self._keywords.update({keyword.__str__(): keyword.convert_to_model()})
                _keyword_pks.append(keyword.__str__())
            self._m2m_relations.append((db_obj, "keywords", Keyword.objects.filter(pk__in=_keyword_pks)))

    def construct_reference_systems(self, db_obj, reference_systems) -> None:
        """Convert all reference systems of all possible objects"""
        if reference_systems:
            _reference_system_query = Q()
            for reference_system in reference_systems:
                # todo: for loop in for loop!
                #  maybe this filtering is not efficient. Check if simply get_or_create with all is more efficient.
                if not f"{reference_system.prefix}:{reference_system.code}" in self._reference_systems:
                    self._reference_systems.update({f"{reference_system.prefix}:{reference_system.code}": reference_system.convert_to_model()})
                _reference_system_query |= Q(prefix=reference_system.prefix, code=reference_system.code)
            self._m2m_relations.append((db_obj, "keywords", Keyword.objects.filter(_reference_system_query)))

    def construct_remote_metadata(self, remote_metadata, service, content_type, object_id):
        if remote_metadata:
            _remote_metadata = remote_metadata.convert_to_model()
            _remote_metadata.service = service
            _remote_metadata.content_type = content_type
            _remote_metadata.object_id = object_id
            self._remote_metadata_list.append(_remote_metadata)

    def traverse_layer_tree(self, base_parent, db_parent):
        """Traverse all descendant layers, convert them to model and append them to the self._layers list."""
        for child_layer in base_parent.children:
            layer = child_layer.convert_to_model()
            layer.service = self._service
            layer.parent = db_parent
            self._layers.append(layer)

            layer_metadata = child_layer.metadata.convert_to_model()
            layer_metadata.described_object = layer
            self._layer_metadata.append(layer_metadata)

            self.construct_reference_systems(db_obj=layer,
                                             reference_systems=child_layer.reference_systems)

            self.construct_keywords(db_obj=self._layer_metadata,
                                    keywords=child_layer.metadata.keywords)

            self.construct_remote_metadata(remote_metadata=layer.remote_metadata,
                                           service=self._service,
                                           object_id=layer.pk,
                                           content_type=Layer)

            if child_layer.children:
                self.traverse_layer_tree(base_parent=base_parent, db_parent=db_parent)

    def construct_layer_tree(self) -> None:
        _root_layer = self._proto_service.root_layer.convert_to_model()
        _root_layer.service = self._service
        self._layers.append(_root_layer)
        self.traverse_layer_tree(base_parent=self._proto_service.root_layer,
                                 db_parent=_root_layer)

    def produce_layers(self) -> None:
        """"""
        Layer.objects.bulk_create(objs=self._layers)

    def produce_layer_metadata(self) -> None:
        """"""
        LayerMetadata.objects.bulk_create(objs=self._layer_metadata)

    def produce_keywords(self) -> None:
        """"""
        for keyword in self._keywords:
            ReferenceSystem.objects.get_or_create(keyword=keyword)

    def produce_reference_systems(self) -> None:
        """"""
        for reference_system in self._reference_systems:
            ReferenceSystem.objects.get_or_create(prefix=reference_system.prefix, code=reference_system.code)

    def produce_remote_metadata(self) -> None:
        """"""
        RemoteMetadata.objects.bulk_create(objs=self._remote_metadata_list)

    def produce_m2m_relations(self) -> None:
        """"""
        for instance, field_name, objects in self._m2m_relations:
            m2m_field = getattr(instance, field_name)
            m2m_field.add(*objects)



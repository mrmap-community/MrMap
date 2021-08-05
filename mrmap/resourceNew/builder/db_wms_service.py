from abc import ABC, abstractmethod

from django.db import transaction
from django.db.models import Q

from resourceNew.models import Service, Keyword, Layer, LayerMetadata, ReferenceSystem, RemoteMetadata, \
    MimeType, Style, LegendUrl, OperationUrl


class AbstractOgcDbServiceBuilder(ABC):
    """The Builder interface specifies methods for creating the different parts of
    ogc service objects.
    """
    _proto_service = None
    _service = None
    _service_metadata = None
    _operation_urls = []
    _keywords = {}
    _reference_systems = {}
    _mime_types = {}
    _remote_metadata_list = []
    _m2m_relations = []  # tuple of (instance, "field_name", QuerySet/list)
    _fk_relations = []  # tuple of (instance, "field_name", model instance) to store delayed fk relations

    def __init__(self, proto_service) -> None:
        """A fresh builder instance should contain a blank service object, which is
        used in further assembly.
        """
        self._proto_service = proto_service
        self.reset()

    def reset(self) -> None:
        self._service_metadata = None
        self._operation_urls = []
        self._keywords = {}
        self._reference_systems = {}
        self._mime_types = {}
        self._remote_metadata_list = []
        self._m2m_relations = []
        self._fk_relations = []

    @property
    @abstractmethod
    def service(self) -> None:
        """Return the fetched Service object from database and reset the builder."""
        raise NotImplementedError

    def construct_service(self) -> None:
        """Convert the proto_service to model instance and store it in private variable."""
        self._service = self._proto_service.convert_to_model()

    def construct_service_metadata(self) -> None:
        """Convert the proto_service_metadata to model instance and store it in private variable."""
        self._service_metadata = self._proto_service.service_metadata.convert_to_model()
        self._service_metadata.described_object = self._service

    def construct_service_metadata_keywords(self) -> None:
        """Convert the proto_service_metadata__keywords to model instance."""
        self.construct_keywords(db_obj=self._service_metadata, keywords=self._proto_service.service_metadata.keywords)

    def construct_remote_service_metadata(self) -> None:
        """Convert the proto_service_metadata__remote_metadata to model instance and store it in private variable."""
        self.construct_remote_metadata(remote_metadata=self._proto_service.remote_metadata,
                                       service=self._service,
                                       content_type=Service,
                                       object_id=self._service.pk)

    def construct_operation_urls(self) -> None:
        for operation_url in self._proto_service.operation_urls:
            db_operation_url = operation_url.convert_to_model()
            db_operation_url.service = self._service
            self._operation_urls.append(db_operation_url)
            self.construct_mime_types(db_obj=db_operation_url,
                                      mime_types=operation_url.mime_types)

    def construct_mime_types(self, db_obj, mime_types, m2m=True) -> None:
        if mime_types:
            _mime_type_pks = []
            for mime_type in mime_types:
                if not mime_type.__str__() in self._mime_types:
                    # todo: for loop in for loop!
                    #  maybe this filtering is not efficient. Check if simply get_or_create with all is more efficient.
                    self._mime_types.update({mime_type.__str__(): mime_type.convert_to_model()})
                _mime_type_pks.append(mime_type.__str__())
            if m2m:
                self._m2m_relations.append((db_obj, "mime_types", MimeType.objects.filter(pk__in=_mime_type_pks)))
            else:
                self._fk_relations.append((db_obj, "mime_types", MimeType.objects.get(pk=_mime_type_pks[0])))

    def construct_keywords(self, db_obj, keywords) -> None:
        """Generic method to construct keywords, store them in private list variable and store the m2m relation in
        private list variable."""
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
        """Generic method to construct reference system, store them in private list variable and store the m2m relation
        in private list variable."""
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
        """Generic method to convert proto_remote_metadata to model instance and store them in private list variable."""
        if remote_metadata:
            _remote_metadata = remote_metadata.convert_to_model()
            _remote_metadata.service = service
            _remote_metadata.content_type = content_type
            _remote_metadata.object_id = object_id
            self._remote_metadata_list.append(_remote_metadata)

    def persist_service(self) -> None:
        """Persist the constructed service instance."""
        self._service.save()

    def persist_operation_urls(self) -> None:
        """Persist all constructed operation url instances in bulk mode."""
        OperationUrl.objects.bulk_create(self._operation_urls)

    def persist_service_metadata(self) -> None:
        """Persist the constructed service metadata instance."""
        self._service_metadata.save()

    def persist_keywords(self) -> None:
        """Persist all constructed keywords in get_or_create mode."""
        for keyword in self._keywords.items():
            Keyword.objects.get_or_create(keyword=keyword)

    def persist_reference_systems(self) -> None:
        """Persist all constructed reference systems in get_or_create mode."""
        for reference_system in self._reference_systems.items():
            ReferenceSystem.objects.get_or_create(prefix=reference_system.prefix, code=reference_system.code)

    def persist_mime_types(self) -> None:
        """Persist all constructed mime types in get_or_create mode."""
        for mime_type in self._mime_types.items():
            MimeType.objects.get_or_create(mime_type=mime_type.mime_type)

    def persist_remote_metadata(self) -> None:
        """Persist all constructed remote metadata instances in bulk mode."""
        RemoteMetadata.objects.bulk_create(objs=self._remote_metadata_list)

    def persist_fk_relations(self) -> None:
        """Generic method to add fk relations to a specific model instance"""
        for instance, field_name, obj in self._fk_relations:
            setattr(instance, field_name, obj)
            instance.save()

    def persist_m2m_relations(self) -> None:
        """Generic method to add m2m relations in optimized add mode."""
        for instance, field_name, objects in self._m2m_relations:
            m2m_field = getattr(instance, field_name)
            m2m_field.add(*objects)


class WmsDbBuilder(AbstractOgcDbServiceBuilder):
    """The Concrete Builder classes follow the Builder interface and provide
    specific implementations of the building steps.
    """
    _proto_service = None

    def reset(self) -> None:
        """Reset all local variables the construct (non persisted) a new service instance."""
        super().reset()
        self._layers = []
        self._layer_metadata = []
        self._styles = []
        self._legend_urls = []

        # todo
        #  db_dimension_list = []
        #  db_dimension_extent_list = []

    @property
    def service(self) -> Service:
        """Return the fetched Service object from database and reset the builder."""
        service_pk = self._service.pk
        self.reset()
        return Service.objects.get_full_service(pk=service_pk)

    def traverse_layer_tree(self, base_parent, db_parent):
        """Recursive function to traverse all descendant layers."""
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
        """Construct the root layer and traverse all descendant layers to construct all descendant layers and related
        objects.

        .. note::
           To increase performance, this method will also construct all related objects of any layer. Otherwise we need
           to traverse the layer tree several times to construct the different types of related objects.
        """
        _root_layer = self._proto_service.root_layer.convert_to_model()
        _root_layer.service = self._service
        self._layers.append(_root_layer)

        layer_metadata = self._proto_service.root_layer.metadata.convert_to_model()
        layer_metadata.described_object = _root_layer
        self._layer_metadata.append(layer_metadata)

        self.construct_reference_systems(db_obj=_root_layer,
                                         reference_systems=self._proto_service.root_layer.reference_systems)

        self.construct_keywords(db_obj=self._layer_metadata,
                                keywords=self._proto_service.root_layer.metadata.keywords)

        self.construct_remote_metadata(remote_metadata=self._proto_service.root_layer.remote_metadata,
                                       service=self._service,
                                       object_id=_root_layer.pk,
                                       content_type=Layer)

        self.traverse_layer_tree(base_parent=self._proto_service.root_layer,
                                 db_parent=_root_layer)

    def construct_styles(self, db_layer, styles) -> None:
        """Construct styles for a specific layer"""
        if styles:
            for style in styles:
                db_style = style.convert_to_model()
                db_style.layer = db_layer
                self._styles.append(db_style)
                self.construct_legend_url(db_style=db_style, legend_url=style.legend_url)

    def construct_legend_url(self, db_style, legend_url) -> None:
        db_legend_url = legend_url.convert_to_model()
        db_legend_url.style = db_style
        self._legend_urls.append(db_legend_url)

    def persist_layers(self) -> None:
        """Persist all constructed layer instances in bulk mode."""
        Layer.objects.bulk_create(objs=self._layers)

    def persist_layer_metadata(self) -> None:
        """Persist all constructed layer metadata instances in bulk mode."""
        LayerMetadata.objects.bulk_create(objs=self._layer_metadata)

    def persist_styles(self) -> None:
        """Persist all constructed styles instances in bulk mode."""
        Style.objects.bulk_create(objs=self._styles)

    def persist_legend_urls(self) -> None:
        """Persist all constructed legend urls instances in bulk mode."""
        LegendUrl.objects.bulk_create(objs=self._legend_urls)


class WmsDirector:
    """
    The Director is only responsible for executing the building steps in a
    particular sequence. It is helpful when producing products according to a
    specific order or configuration. Strictly speaking, the Director class is
    optional, since the client can control builders directly.
    """

    def __init__(self) -> None:
        self._builder = None

    @property
    def builder(self) -> WmsDbBuilder:
        return self._builder

    @builder.setter
    def builder(self, builder: WmsDbBuilder) -> None:
        """
        The Director works with any builder instance that the client code passes
        to it. This way, the client code may alter the final type of the newly
        assembled product.
        """
        self._builder = builder

    """
    The Director can construct several product variations using the same
    building steps.
    """
    def build_service(self) -> None:
        # first construct all db instances which are not persisted.
        self.builder.construct_operation_urls()
        self.builder.construct_service_metadata()
        self.builder.construct_service_metadata_keywords()
        self.builder.construct_remote_service_metadata()
        self.builder.construct_layer_tree()

        with transaction.atomic():
            # build service tree.
            self.builder.persist_service()
            self.builder.persist_operation_urls()
            self.builder.persist_service_metadata()
            self.builder.persist_layers()
            self.builder.persist_layer_metadata()
            self.builder.persist_remote_metadata()
            self.builder.persist_styles()
            self.builder.persist_legend_urls()

            # build m2m pointed objects.
            self.builder.persist_keywords()
            self.builder.persist_reference_systems()

            # build delayed fk relations.
            self.builder.persist_fk_relations()

            # build m2m relations.
            self.builder.persist_m2m_relations()

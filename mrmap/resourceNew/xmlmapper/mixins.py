from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from eulxml import xmlmap
from lxml.etree import XPathEvalError
from django.conf import settings
from django.db import models
from django.utils import timezone
from main.models import get_current_owner
from crum import get_current_user


class DBModelConverter(xmlmap.XmlObject):
    """Abstract class which implements some generic functions to get the db model class and all relevant field content
    as dict.

    :attr model: the model where this instance shall be converted to.
    :type model: can be a str or a concrete type of :class:`models.Model`
    :attr common_info: some attributes to store common info, e.g. created_at, created_by_user ...
    :type common_info: dict
    :attr ignore_fields: a list of fields which shall ignored by the :meth:`~get_field_dict` function.
    :type ignore_fields: list
    """
    model = None
    common_info = {}
    ignore_fields = []

    def get_common_info(self):
        """Return common info attributes

        .. note::
           bulk_create will not call the default save() of CommonInfo model. So we need to set the attributes manual. We
           collect them once.

        :return common_info: the generated common info
        :rtype common_info: dict
        """
        if not self.common_info:
            now = timezone.now()
            current_user = get_current_user()
            self.common_info = {"created_at": now,
                                "last_modified_at": now,
                                "last_modified_by": current_user,
                                "created_by_user": current_user,
                                "owned_by_org": get_current_owner()}
        return self.common_info

    def get_model_class(self):
        """Return the configured model class. If model class is named as string like 'app_label.model_cls_name', the
        model will be resolved by the given string. If the model class is directly configured by do not lookup by
        string.

        :return self.model: the configured model class
        :rtype self.model: a subclass of :class:`models.Model`
        """
        if not self.model:
            raise ImproperlyConfigured(f"you need to configure the model attribute on class "
                                       f"'{self.__class__.__name__}'.")
        if isinstance(self.model, str):
            app_label, model_name = self.model.split('.', 1)
            self.model = apps.get_model(app_label=app_label, model_name=model_name)
        elif not issubclass(self.model, models.Model):
            raise ImproperlyConfigured(f"the configured model attribute on class '{self.__class__.__name__}' "
                                       f"isn't from type models.Model")
        return self.model

    def get_field_dict(self):
        """ Return a dict which contains the key, value pairs of the given field attribute name as key and the
            attribute value it self as value.

            Examples:
                If the following two classes are given:

                class Nested(DBModelConverterMixin, xmlmap.XmlObject):
                    ...

                class SomeXmlObject(DBModelConverterMixin, xmlmap.XmlObject):
                    name = xmlmap.StringField('name')
                    nested = xmlmap.NodeField('nested', Nested)
                    nested_list = xmlmap.NodeListField('nested', Nested)

                The SomeXmlObject().get_field_dict() function return {'name': 'Something'}

        Returns:
            field_dict (dict): the dict which contains all simple fields of the object it self.

        """
        field_dict = {}
        for key in self._fields.keys():
            if key in self.ignore_fields:
                continue
            try:
                if not (isinstance(self._fields.get(key), xmlmap.NodeField) or
                        isinstance(self._fields.get(key), xmlmap.NodeListField)):
                    if isinstance(self._fields.get(key), xmlmap.SimpleBooleanField) and getattr(self, key) is None or \
                       isinstance(self._fields.get(key), xmlmap.IntegerField) and getattr(self, key) is None:
                        # we don't append None values, cause if we construct a model with key=None and the db field
                        # don't allow Null values but has a default value for the field, the db will raise integrity
                        # errors.
                        continue
                    field_dict.update({key: getattr(self, key)})
            except XPathEvalError as e:
                settings.ROOT_LOGGER.error(msg=f"error during parsing field: {key} in class {self.__class__.__name__}")
                settings.ROOT_LOGGER.exception(e, stack_info=True, exc_info=True)
        return field_dict

    def convert_to_model(self, **kwargs):
        """Converter function to convert the current xml mapper instance to a db model instance."""
        return self.get_model_class()(**self.get_field_dict(), **self.get_common_info())

    @classmethod
    def convert_from_model(cls, db_model):
        """Converter function to convert a db model instance to the current xml mapper instance."""
        raise NotImplementedError

    def update_fields(self, obj: dict):
        """Update/Set all founded fields by the given obj dict.

        :class:`eulxml.xmlmap.fields.NodeField` and :class:`eulxml.xmlmap.fields.NodeListField` attributes shall be
        defined as sub dict.

        :Example:

        .. code-block:: python
           obj = {
                  "file_identifier": "id-123-123-123-123-123",
                  "md_data_identification":
                        {"equivalent_scale": 1.23}
                  }

           from resourceNew.xmlmapper.iso_metadata import iso_metadata

           iso_md = xmlmap.load_xmlobject_from_file(filename='something.xml',
                                                    xmlclass=WrappedIsoMetadata)
           iso_md.update_fields(obj=obj)

        :param obj: the object which shall be used to iterate fields
        :type obj: dict
        """
        field_keys = self._fields.keys()
        for key, value in obj.items():
            if key in field_keys:
                if isinstance(self._fields.get(key), xmlmap.NodeField) or \
                        isinstance(self._fields.get(key), xmlmap.NodeListField):
                    _field = self._fields.get(key)
                    _instance = _field.node_class.from_field_dict(value)
                    setattr(self, key, _instance)
                else:
                    setattr(self, key, value)

    @classmethod
    def from_field_dict(cls, initial: dict):
        """Initial the current class from the given dict.

        :class:`eulxml.xmlmap.fields.NodeField` and :class:`eulxml.xmlmap.fields.NodeListField` attributes shall be
        defined as sub dict.

        :Example:

        .. code-block:: python
           initial = {
                      "file_identifier": "id-123-123-123-123-123",
                      "md_data_identification":
                            {"equivalent_scale": 1.23}
                      }

           from resourceNew.xmlmapper.iso_metadata import iso_metadata

           # iso metadata from scratch
           iso_md = iso_metadata.IsoMetadata.from_field_dict(initial=initial)

        :param initial: the object which shall be used to iterate fields
        :type initial: dict
        """
        instance = cls()
        instance.update_fields(obj=initial)
        return instance

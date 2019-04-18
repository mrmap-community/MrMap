import datetime
from django.db import models
from django.contrib.gis.db import models
from structure.models import User, Group, UserGroupRoleRel, Organization


class Keyword(models.Model):
    keyword = models.CharField(max_length=100)

    def __str__(self):
        return self.keyword


class Metadata(models.Model):
    uuid = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    abstract = models.CharField(max_length=1000)
    online_resource = models.CharField(max_length=255)
    # Service md
    service = models.ForeignKey('Service', null=True, blank=True, on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=100, null=True)
    contact_person_position = models.CharField(max_length=100, null=True)
    contact_organization = models.CharField(max_length=100, null=True)
    address_type = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    state_or_province = models.CharField(max_length=100, null=True)
    post_code = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=100, null=True)
    contact_phone = models.CharField(max_length=100, null=True)
    contact_email = models.CharField(max_length=100, null=True)
    terms_of_use = models.ForeignKey('TermsOfUse', on_delete=models.DO_NOTHING, null=True)
    access_constraints = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(null=True)
    status = models.IntegerField(null=True)
    last_harvest_successful = models.BooleanField(null=True)
    last_harvest_exception = models.CharField(max_length=200, null=True)
    export_to_csw = models.BooleanField(default=False)
    spatial_res_type = models.CharField(max_length=100, null=True)
    spatial_res_value = models.CharField(max_length=100, null=True)
    is_active = models.BooleanField(default=False)
    is_inspire_conform = models.BooleanField(default=False)
    has_inspire_downloads = models.BooleanField(default=False)
    geom = models.GeometryField(null=True)
    bounding_geometry = models.GeometryField(null=True)
    # capabilities
    bbox = models.DecimalField(decimal_places=2, max_digits=4, null=True)
    dimension = models.CharField(max_length=100, null=True)
    authority_url = models.CharField(max_length=255, null=True)
    identifier = models.CharField(max_length=255, null=True)
    metadata_url = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.uuid


class KeywordToMetadata(models.Model):
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)

    def __str__(self):
        return self.keyword.keyword


class TermsOfUse(models.Model):
    service = models.ForeignKey('Service', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    symbol_url = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    is_open_data = models.BooleanField()
    fees = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
    title_DE = models.CharField(max_length=100, unique=True)
    title_EN = models.CharField(max_length=100, unique=True)
    description_DE = models.CharField(max_length=100, unique=True)
    description_EN = models.CharField(max_length=100, unique=True)
    is_inspire = models.BooleanField()
    symbol = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField()
    created = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.title_EN


class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    specification = models.URLField(blank=False, null=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    # metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Group, on_delete=models.DO_NOTHING)
    published_for = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    servicetype = models.ForeignKey(ServiceType, on_delete=models.DO_NOTHING, blank=True)
    categories = models.ManyToManyField(Category)
    availability = models.DecimalField(decimal_places=2, max_digits=4, default=0.0)
    is_available = models.BooleanField(default=False)
    # terms_of_use = models.ForeignKey(TermsOfUse, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.servicetype.name


class Layer(Service):
    identifier = models.CharField(max_length=500, null=True)
    hits = models.IntegerField(default=0)
    preview_image = models.CharField(max_length=100)
    preview_extend = models.CharField(max_length=100)
    preview_legend = models.CharField(max_length=100)
    service = models.ForeignKey(Service, on_delete=models.DO_NOTHING, related_name="+", null=True)
    parent_layer = models.ForeignKey("self", on_delete=models.DO_NOTHING, null=True, related_name="child_layer")
    position = models.IntegerField(default=0)
    is_queryable = models.BooleanField(default=False)
    is_opaque = models.BooleanField(default=False)
    is_cascaded = models.BooleanField(default=False)
    scale_min = models.FloatField(default=0)
    scale_max = models.FloatField(default=0)
    bbox_lat_lon = models.CharField(max_length=255, default='{"minx":-90.0, "miny":-180.0, "maxx": 90.0, "maxy":180.0}')

    def __str__(self):
        return self.identifier


class Module(Service):
    type = models.CharField(max_length=100)

    def __str__(self):
        return self.type


class ReferenceSystem(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ReferenceSystemToMetadata(models.Model):
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    reference_system = models.ForeignKey(ReferenceSystem, on_delete=models.CASCADE)

    def __str__(self):
        return self.reference_system.name


class Dataset(models.Model):
    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
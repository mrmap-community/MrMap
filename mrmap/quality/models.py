"""
Author: Jan Suleiman
Organization: terrestris GmbH & Co. KG
Contact: suleiman@terrestris.de
Created on: 27.10.20

"""
from django.db import models
from django.urls import reverse

from main.models import UuidPk
from quality.enums import RuleFieldNameEnum, RulePropertyEnum, \
    RuleOperatorEnum, \
    ConformityTypeEnum
from resourceNew.models.metadata import DatasetMetadata


class ConformityCheckConfigurationManager(models.Manager):
    """ Custom manager to extend ConformityCheckConfiguration methods """

    def get_for_metadata_type(self, metadata_type: str):
        """ Gets all configs that are allowed for the given metadata_type """
        return super().get_queryset().filter(
            metadata_types__contains=metadata_type)


class ConformityCheckConfiguration(UuidPk):
    """
    Base model for ConformityCheckConfiguration classes.
    """
    name = models.CharField(max_length=1000)
    metadata_types = models.JSONField()
    conformity_type = models.TextField(
        choices=ConformityTypeEnum.as_choices(drop_empty_choice=True))

    objects = ConformityCheckConfigurationManager()

    def __str__(self):
        return self.name

    def is_allowed_type(self, metadata: DatasetMetadata):
        """ Checks if type of metadata is allowed for this config.

            Args:
                metadata (Metadata): The metadata object to check
            Returns:
                True, if metadata type is allowed for this config,
                False otherwise.
        """

        return metadata.metadata_type in self.metadata_types


class ConformityCheckConfigurationExternal(ConformityCheckConfiguration):
    """
    Model holding the configs for an external conformity check.
    """
    external_url = models.URLField(max_length=1000, null=True)
    validation_target = models.TextField(max_length=1000, null=True)
    parameter_map = models.JSONField()
    polling_interval_seconds = models.IntegerField(default=5, blank=True,
                                                   null=False)
    polling_interval_seconds_max = models.IntegerField(default=5 * 60,
                                                       blank=True, null=False)


class Rule(UuidPk):
    """
    Model holding the definition of a single rule.
    """
    name = models.CharField(max_length=1000)
    field_name = models.TextField(
        choices=RuleFieldNameEnum.as_choices(drop_empty_choice=True))
    property = models.TextField(
        choices=RulePropertyEnum.as_choices(drop_empty_choice=True))
    operator = models.TextField(
        choices=RuleOperatorEnum.as_choices(drop_empty_choice=True))
    threshold = models.TextField(null=True)

    def __str__(self):
        return self.name

    def as_dict(self):
        """Returns the model's field values as simple dictionary.

        This method should only be used for read-operations. E.g. to display
        the model contents as text or json.
        """
        return {
            "name": self.name,
            "field_name": self.field_name,
            "property": self.property,
            "operator": self.operator,
            "threshold": self.threshold
        }


class RuleSet(UuidPk):
    """
    Model grouping rules and holding the result of a rule check run.
    """
    name = models.CharField(max_length=1000)
    rules = models.ManyToManyField(Rule, related_name="rule_set")

    def __str__(self):
        return self.name


class ConformityCheckConfigurationInternal(ConformityCheckConfiguration):
    """
    Model holding the configs for an internal conformity check.
    """
    mandatory_rule_sets = models.ManyToManyField(RuleSet,
                                                 related_name="mandatory_rule_sets")
    optional_rule_sets = models.ManyToManyField(RuleSet,
                                                related_name="optional_rule_sets",
                                                blank=True)


class ConformityCheckRunManager(models.Manager):
    """ Custom manager to extend ConformityCheckRun methods """

    def has_running_check(self, metadata: DatasetMetadata):
        """ Checks if the given metadata object has a non-finished
        ConformityCheckRun.

            Returns:
                True, if a non-finished ConformityCheckRun was found,
                false otherwise.
        """
        running_checks = super().get_queryset().filter(
            metadata=metadata, passed__isnull=True).count()
        return running_checks != 0

    def get_latest_check(self, metadata: DatasetMetadata):
        check = super().get_queryset().filter(metadata=metadata).latest(
            'time_start')
        return check


class ConformityCheckRun(UuidPk):
    """
    Model holding the relation of a metadata record to the results of a check.
    """
    # TODO handle other resources, Jonas: what is the best approach to model this?
    metadata = models.ForeignKey(DatasetMetadata, on_delete=models.CASCADE)
    conformity_check_configuration = models.ForeignKey(
        ConformityCheckConfiguration, on_delete=models.CASCADE)
    time_start = models.DateTimeField(auto_now_add=True)
    time_stop = models.DateTimeField(blank=True, null=True)
    passed = models.BooleanField(blank=True, null=True)
    result = models.TextField(blank=True, null=True)

    objects = ConformityCheckRunManager()

    def get_absolute_url(self):
        return reverse('check', kwargs={'pk': self.pk})

    def is_running(self):
        return self.time_start is not None and self.passed is None

    # TODO Discuss with Jonas: calling run_quality_check here results in cyclic imports,
    # so we moved this to the view

    # def save(self, *args, **kwargs):
    #     adding = False
    #     if self._state.adding:
    #         adding = True
    #     super().save(*args, **kwargs)
    #     if adding:
    #         # self.conformity_check_configuration = args.get('')
    #         from quality.tasks import run_quality_check, complete_validation, \
    #             complete_validation_error
    #         success_callback = complete_validation.s()
    #         error_callback = complete_validation_error.s(user_id=args[0].get('user_id'),
    #                                                      config_id=self.conformity_check_configuration.pk,
    #                                                      metadata_id=self.metadata.pk)
    #         # transaction.on_commit(lambda: run_quality_check.apply_async(
    #         #     args=(self.conformity_check_configuration.pk , self.metadata.pk),
    #         #     #kwargs={'created_by_user_pk': args[0].get('user_id')},
    #         #     countdown=settings.CELERY_DEFAULT_COUNTDOWN))
    #
    #         transaction.on_commit(
    #             lambda: run_quality_check.apply_async(args=(self.conformity_check_configuration.pk, self.metadata.pk),
    #                                                   link=success_callback,
    #                                                   link_error=error_callback))

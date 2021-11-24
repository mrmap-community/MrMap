# """
# Author: Jan Suleiman
# Organization: terrestris GmbH & Co. KG, Bonn, Germany
# Contact: suleiman@terrestris.de
# Created on: 26.02.2020

# """
# from celery import shared_task, current_task, states
# from celery.signals import beat_init
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
# from django.db import transaction
# from django.utils import timezone
# from django.utils.translation import gettext_lazy as _

# from extras.tasks import default_task_handler
# from registry.models import MonitoringSetting, MonitoringRun
# from registry.monitoring import Monitor


# @beat_init.connect
# def init_periodic_tasks(sender, **kwargs):
#     """ Load MonitoringSettings and create/update PeriodicTask records

#     Args:
#         sender:
#         kwargs:
#     Returns:

#     """
#     monitoring_settings = MonitoringSetting.objects.all()
#     for setting in monitoring_settings:
#         setting.update_periodic_tasks()


# @shared_task(name='run_service_monitoring')
# @transaction.atomic
# def run_monitoring(setting_id, *args, **kwargs):
#     try:
#         setting = MonitoringSetting.objects.get(pk=setting_id)
#     except (ObjectDoesNotExist, MultipleObjectsReturned):
#         print(f'Could not retrieve setting with id {setting_id}')
#         return
#     metadatas = setting.services.all()
#     monitoring_run = MonitoringRun.objects.create()
#     for metadata in metadatas:
#         if current_task:
#             current_task.update_state(
#                 state=states.STARTED,
#                 meta={
#                     'current': 0,
#                     'total': 100,
#                     'phase': f'start monitoring checks for {metadata}',
#                 }
#             )
#         try:
#             monitor = Monitor(metadata=metadata, monitoring_run=monitoring_run, )
#             monitor.run_checks()
#             settings.ROOT_LOGGER.debug(f'Health checks completed for {metadata}')
#         except Exception as e:
#             settings.ROOT_LOGGER.exception(e, exc_info=True, stack_info=True)

#     end_time = timezone.now()
#     duration = end_time - monitoring_run.start
#     monitoring_run.end = end_time
#     monitoring_run.duration = duration
#     monitoring_run.save()

#     return {'msg': 'Done. Service(s) successfully monitored.',
#             'id': str(monitoring_run.pk),
#             'absolute_url': monitoring_run.get_absolute_url(),
#             'absolute_url_html': f'<a href={monitoring_run.get_absolute_url()}>{monitoring_run.__str__()}</a>'}


# @shared_task(name='run_manual_service_monitoring')
# def run_manual_service_monitoring(owned_by_org: str, monitoring_run, *args, **kwargs):
#     default_task_handler(**kwargs)

#     monitoring_run = MonitoringRun.objects.get(pk=monitoring_run)
#     monitoring_run.start = timezone.now()
#     for resource in monitoring_run.resources_all:
#         if current_task:
#             current_task.update_state(
#                 state=states.STARTED,
#                 meta={
#                     'current': 0,
#                     'total': 100,
#                     'phase': f'start monitoring checks for {resource}',
#                 }
#             )
#         try:
#             monitor = Monitor(resource=resource, monitoring_run=monitoring_run, )
#             monitor.run_checks()
#             settings.ROOT_LOGGER.debug(f'Health checks completed for {resource}')
#         except Exception as e:
#             settings.ROOT_LOGGER.error(msg=_(f'Something went wrong while monitoring {resource}'))
#             settings.ROOT_LOGGER.exception(e, exc_info=True, stack_info=True, )

#     end_time = timezone.now()
#     duration = end_time - monitoring_run.start
#     monitoring_run.end = end_time
#     monitoring_run.duration = duration
#     monitoring_run.save()

#     return {'msg': 'Done. Service(s) successfully monitored.',
#             'id': str(monitoring_run.pk),
#             'absolute_url': monitoring_run.get_absolute_url(),
#             'absolute_url_html': f'<a href={monitoring_run.get_absolute_url()}>{monitoring_run.__str__()}</a>'}

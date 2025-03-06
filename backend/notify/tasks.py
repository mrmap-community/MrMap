from logging import Logger

from celery import Task, shared_task
from celery.signals import before_task_publish, task_prerun
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from django_celery_results.models import TaskResult
from notify.models import BackgroundProcess
from requests.exceptions import ConnectionError, Timeout

logger: Logger = settings.ROOT_LOGGER


def get_background_process_if_exists(background_process_pk):
    try:
        return BackgroundProcess.objects.get(
            pk=background_process_pk)
    except BackgroundProcess.ObjectDoesNotExist as e:
        logger.exception(e, stack_info=True, exc_info=True)


def append_task_to_background_process(task_pk, background_process_pk):
    if task_pk and background_process_pk:
        task_result, _ = TaskResult.objects.get_or_create(
            task_id=task_pk,
        )
        background_process = get_background_process_if_exists(
            background_process_pk)
        if background_process:
            background_process.threads.add(task_result)


@task_prerun.connect
def get_background_process(task, *args, **kwargs):
    """To automaticly get the BackgroundProcess object on task runtime."""
    background_process_pk = kwargs["kwargs"].get("background_process_pk", None)
    task.background_process = get_background_process_if_exists(
        background_process_pk)
    task.update_state(date_created=now(), date_done=now())


@before_task_publish.connect
def create_task_result(headers, body, *args, **kwargs):
    """create task results on publishing them. Without this signal connection, 
        the taskresult object is not created until update_state() inside the task is called.
    """
    task_id = headers.get("id")
    background_process_pk = body[1].get("background_process_pk", None)
    append_task_to_background_process(task_id, background_process_pk)


class BackgroundProcessBased(Task):
    thread_appended = False
    autoretry_for = (Timeout, ConnectionError)
    retry_backoff = 30
    retry_backoff_max = 5*60
    retry_jitter = False
    max_retries = 10

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.update_background_process(
            phase=f"An error occours: {einfo}",
            completed=True
        )

    def update_background_process(
        self,
        phase: str = "",
        service=None,
        total_steps=None,
        step_done=False,
        completed=False,
    ):
        # will be provided by get_background_process signal if the pk is provided by kwargs
        if hasattr(self, "background_process"):
            thread_appended = False
            try:
                with transaction.atomic():
                    if not self.thread_appended:
                        # add the TaskResult if this function is called the first time
                        task, _ = TaskResult.objects.get_or_create(
                            task_id=self.request.id)
                        self.background_process.threads.add(task)
                        thread_appended = True
                    if phase:
                        bg_p = BackgroundProcess.objects.select_for_update().filter(
                            pk=self.background_process.pk)[0]
                        bg_p.phase = phase
                        bg_p.save()  # Do not directly update with sql!
                        # Otherwise the post_save signal is not triggered and
                        # no notifications will be send via websocket!
                    if service:
                        service_ct = ContentType.objects.get_for_model(service)
                        BackgroundProcess.objects.select_for_update().filter(
                            pk=self.background_process.pk).update(
                                related_resource_type=service_ct,
                                related_id=service.pk
                        )
                    if total_steps:
                        bg_p = BackgroundProcess.objects.select_for_update().filter(
                            pk=self.background_process.pk).update(
                                total_steps=total_steps
                        )
                    if step_done:
                        bg_p = BackgroundProcess.objects.select_for_update().filter(
                            pk=self.background_process.pk)[0]
                        bg_p.done_steps += 1
                        bg_p.save()  # Do not directly update with sql!
                        # Otherwise the post_save signal is not triggered and
                        # no notifications will be send via websocket!
                    if completed:
                        bg_p = BackgroundProcess.objects.select_for_update().filter(
                            pk=self.background_process.pk).update(
                                total_steps=Coalesce(F("total_steps"), 1),
                                done_steps=Coalesce(F("total_steps"), 1),
                                done_at=now(),
                                phase="completed"
                        )
            except Exception as e:
                logger.exception(e, stack_info=True, exc_info=True)
            else:
                if thread_appended:
                    self.thread_appended = True

        else:
            logger.warning(
                f"No background process provided for BackgroundProcessBased task. {self.name}")


@shared_task(
    bind=True,
    queue="db-routines",
    base=BackgroundProcessBased
)
def finish_background_process(
    self,
    *args,
    **kwargs
):
    self.update_background_process(
        completed=True
    )

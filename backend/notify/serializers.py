import json

from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult
from extras.serializers import StringRepresentationSerializer
from notify.models import BackgroundProcess
from rest_framework.fields import (CharField, DateTimeField, IntegerField,
                                   SerializerMethodField)
from rest_framework_json_api.serializers import (HyperlinkedIdentityField,
                                                 ModelSerializer)


class TaskResultSerializer(ModelSerializer):

    task_meta = SerializerMethodField()
    result = SerializerMethodField()

    url = HyperlinkedIdentityField(
        view_name='notify:taskresult-detail',
    )

    class Meta:

        model = TaskResult
        # meta field clashes with json:api meta field. We use alternate naming. See task_meta above.
        exclude = ("meta", )

    def get_task_meta(self, obj):
        return json.loads(obj.meta if obj.meta else '{}')

    def get_result(self, obj):
        return json.loads(obj.result if obj.result else '{}')


class BackgroundProcessSerializer(
        StringRepresentationSerializer,
        ModelSerializer):

    url = HyperlinkedIdentityField(
        view_name='notify:backgroundprocess-detail',
    )
    pending_threads_count = IntegerField(
        read_only=True,
        label=_("pending threads"),
        help_text=_("count of currently pending threads"))
    running_threads_count = IntegerField(
        read_only=True,
        label=_("running threads"),
        help_text=_("count of currently running threads"))
    successed_threads_count = IntegerField(
        read_only=True,
        label=_("successed threads"),
        help_text=_("count of currently successed threads"))
    failed_threads_count = IntegerField(
        read_only=True,
        label=_("failed threads"),
        help_text=_("count of currently failed threads"))
    date_created = DateTimeField(
        read_only=True,
        label=_("date created"),
        help_text=_("the datetime when the first thread was created"))
    progress = SerializerMethodField(
        read_only=True,
        label=_("progress"),
        help_text=_("the current progress aggregated from all threads from 0 to 100"))
    status = CharField(
        read_only=True,
        label=_("status"),
        help_text=_("the current status, aggregated from all threads."))

    class Meta:
        model = BackgroundProcess
        fields = "__all__"

    def get_progress(self, instance) -> float:
        if instance.total_steps and instance.total_steps > 0:
            # there is an explecit step definitions stored on the model
            return round(instance.done_steps / instance.total_steps * 100, 2)

        if instance.all_threads_count == 0:
            return 0
        aggregated_running_task_progress = 0.0
        running_thread: TaskResult
        for running_thread in instance.running_threads_list:
            meta_info = json.loads(
                running_thread.meta) if running_thread.meta else {}
            try:
                aggregated_running_task_progress += \
                    int(meta_info['done']) / int(meta_info['total'])
            except (AttributeError, KeyError):
                pass
        return (aggregated_running_task_progress + instance.successed_threads_count + instance.failed_threads_count - instance.pending_threads_count) * 100 / instance.all_threads_count

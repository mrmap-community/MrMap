import json

from celery import states
from django_celery_results.models import TaskResult
from notify.models import BackgroundProcess
from notify.serializers import (BackgroundProcessSerializer,
                                TaskResultSerializer)
from rest_framework import status
from rest_framework.response import Response
from rest_framework_json_api.views import ReadOnlyModelViewSet


class TaskResultReadOnlyViewSet(ReadOnlyModelViewSet):
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    filterset_fields = {
        'id': ['exact', 'icontains', 'contains', 'in'],
        'task_id': ['exact', 'icontains', 'contains', 'in'],
        'periodic_task_name': ['exact', 'icontains', 'contains'],
        'task_name': ['exact', 'icontains', 'contains'],
        'task_args': ['exact', 'icontains', 'contains'],
        'task_kwargs': ['exact', 'icontains', 'contains'],
        'status': ['exact', 'icontains', 'contains'],
        'worker': ['exact', 'icontains', 'contains'],
        'content_type': ['exact', 'icontains', 'contains'],
        'content_encoding': ['exact', 'icontains', 'contains'],
        'result': ['exact', 'icontains', 'contains'],
        'traceback': ['exact', 'icontains', 'contains'],
        'meta': ['exact', 'icontains', 'contains'],
        "date_created": ["exact", "gt", "lt", "range"],
        'date_done': ["exact", "gt", "lt", "range"],
    }
    search_fields = [
        "id",
        'task_id',
        'periodic_task_name',
        'task_name',
        'task_args',
        'task_kwargs',
        'status',
        'worker',
        'content_type',
        'content_encoding',
        'result',
        'date_created',
        'date_done',
        'traceback',
        'meta',
    ]
    ordering_fields = [
        "id",
        'task_id',
        'periodic_task_name',
        'task_name',
        'task_args',
        'task_kwargs',
        'status',
        'worker',
        'content_type',
        'content_encoding',
        'result',
        'date_created',
        'date_done',
        'traceback',
        'meta',
    ]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status == states.SUCCESS and 'build_ogc_service' or 'fetch_remote_metadata_xml' in instance.task_name:
            # followed the jsonapi recommendation for async processing
            # https://jsonapi.org/recommendations/#asynchronous-processing
            result = json.loads(instance.result)
            return Response(
                status=status.HTTP_303_SEE_OTHER,
                headers={
                    "Location": str(
                        self.request.build_absolute_uri(
                            result["data"]["links"]["self"])
                    )
                },
            )
        else:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)


class BackgroundProcessViewSetMixin(

):
    queryset = BackgroundProcess.objects.process_info()
    serializer_class = BackgroundProcessSerializer
    filterset_fields = {
        'id': ['exact', 'icontains', 'contains', 'in'],
        "process_type": ["exact", "icontains", "contains"],
        "description": ["exact", "icontains", "contains"],
        "phase": ["exact", "icontains", "contains"],
    }
    ordering_fields = [
        "id",
    ]


class BackgroundProcessViewSet(
    BackgroundProcessViewSetMixin,
    ReadOnlyModelViewSet
):
    pass

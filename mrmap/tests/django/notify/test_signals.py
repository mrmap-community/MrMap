import asyncio
from typing import OrderedDict

from asgiref.sync import async_to_sync
from async_timeout import timeout
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import Client, TransactionTestCase, override_settings
from django_celery_results.models import TaskResult
from MrMap.asgi import application
from notify.models import BackgroundProcess, ProcessNameEnum
from notify.routing import websocket_urlpatterns
from rest_framework.test import APIRequestFactory
from simple_history.models import HistoricalRecords


# use in memory channel layer for testing to ignore redis behaviour
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class SignalsTestCase(TransactionTestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.client = Client()
        self.client.login(username='User1', password='User1')
        # workaround to login a user for WebsocketCommunicator since login is not implemented for this
        # ApplicationCommunicator (see: https://github.com/django/channels/issues/903#issuecomment-365448451)
        self.headers = [(b'origin', b'http://127.0.0.1:8000'), (b'cookie',
                                                                self.client.cookies.output(header='', sep='; ').encode())]

        dummy_request = APIRequestFactory().get(
            path="/api/notify/background-processes/")
        dummy_request.query_params = OrderedDict()

        HistoricalRecords.context.request = dummy_request

    def create_background_process(self):
        background_process = BackgroundProcess.objects.create(
            phase="started",
            process_type=ProcessNameEnum.REGISTERING.value,
            description="register a new service"
        )
        return BackgroundProcess.objects.process_info().get(
            pk=background_process.pk)

    def get_background_process(self, pk):
        return BackgroundProcess.objects.process_info().get(
            pk=pk)

    def create_thread(self, background_process):
        task_result = TaskResult.objects.create(task_id=123)
        task_result.processes.add(background_process)
        return task_result

    def update_thread(self):
        task_result = TaskResult.objects.get(task_id=123)
        task_result.status = "STARTED"
        task_result.meta = "{ \"done\": \"1\", \"total\": \"3\"}"
        task_result.save()
        return task_result

    def delete_pending_task(self):
        return TaskResult.objects.get(task_id=123).delete()

    # to wrap this test function as sync function,
    # so the test runner waits for this test before he runs into other tests
    # Otherwise the db connections could be corrupted by other tests which runs in other thread at the same time
    @async_to_sync
    async def test_signal_events_for_task_result(self):
        try:
            async with timeout(60):
                # test connection established for authenticated user
                communicator = WebsocketCommunicator(application=AuthMiddlewareStack(
                    URLRouter(
                        websocket_urlpatterns,
                    )
                ),
                    path="/ws/default/",
                    headers=self.headers)
                connected, exit_code = await communicator.connect()
                self.assertTrue(connected)

                # if a BackgroundProcess is created, we shall receive a create event
                background_process = await database_sync_to_async(self.create_background_process, thread_sensitive=False)()

                response = await communicator.receive_json_from()
                self.assertEqual(response['payload']
                                 ['type'], "BackgroundProcess")
                self.assertEqual(response['payload']
                                 ['id'], str(background_process.pk))
                self.assertEqual(response['type'],
                                 "backgroundProcesses/created")

                # if a thread is updated, we shall receive a update event
                await database_sync_to_async(self.create_thread, thread_sensitive=False)(background_process)
                await database_sync_to_async(self.update_thread, thread_sensitive=False)()
                await database_sync_to_async(self.get_background_process, thread_sensitive=False)(background_process.pk)

                response = await communicator.receive_json_from()
                self.assertEqual(response['payload']
                                 ['type'], "BackgroundProcess")
                self.assertEqual(response['payload']
                                 ['id'], str(background_process.pk))
                self.assertEqual(response['type'],
                                 "backgroundProcesses/updated")

                # Close
                await communicator.disconnect()
        except asyncio.TimeoutError:
            raise AssertionError(
                "test_signal_events_for_task_result timed out")

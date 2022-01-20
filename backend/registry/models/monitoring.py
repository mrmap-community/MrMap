import difflib
import hashlib
from io import BytesIO

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult
from PIL import Image, UnidentifiedImageError
from registry.models.service import Layer, WebMapService
from registry.settings import MONITORING_REQUEST_TIMEOUT
from requests.exceptions import ConnectTimeout, ReadTimeout, RequestException


class MonitoringResult(models.Model):
    task_result = models.OneToOneField(to=TaskResult,
                                       on_delete=models.CASCADE,
                                       related_name="%(class)s_monitoring_results",
                                       related_query_name="%(class)s_monitoring_result")
    status_code: int = models.IntegerField()
    error_msg: str = models.TextField(null=True, blank=True)
    monitored_uri: str = models.URLField(max_length=4096)
    request_duration = models.DurationField()

    response = None

    class Meta:
        abstract = True
        ordering = ['-task_result__date_done', ]
        get_latest_by = ('task_result__date_done')

    def check_url(self, service: WebMapService, url):
        try:
            self.monitored_uri = url
            self.response = service.send_get_request(
                url=url, timeout=MONITORING_REQUEST_TIMEOUT)
            self.status_code = self.response.status_code
            if self.status_code != 200:
                self.error_msg = self.response.text
        except ConnectTimeout:
            self.status_code = 0
            self.error_msg = "The request timed out in {MONITORING_REQUEST_TIMEOUT} seconds while trying to connect to the remote server."
        except ReadTimeout:
            self.status_code = 0
            self.error_msg = f"The server did not send any data in the allotted amount of time ({MONITORING_REQUEST_TIMEOUT} seconds)."
        except RequestException as exception:
            self.status_code = 0
            self.error_msg = str(exception)
        finally:
            self.request_duration = self.response.elapsed


class OgcServiceGetCapabilitiesResult(MonitoringResult):
    needs_update: bool = models.BooleanField(default=False)

    class Meta(MonitoringResult.Meta):
        abstract = True

    def get_document_diff(self, new_document: str, original_document: str):
        """Computes the diff between two documents.

        Compares the currently stored document and compares its hash to the one
        in the response of the latest check.

        Args:
            new_document (str): Document of last request.
            original_document (bytes): Original document.
        Returns:
            str: The diff of the two documents, if hashes have differences
            None: If the hashes have no differences
        """
        new_capabilities_hash = hashlib.sha256(
            new_document.encode("UTF-8")).hexdigest()
        original_document_hash = hashlib.sha256(
            original_document.encode("UTF-8")).hexdigest()
        if new_capabilities_hash == original_document_hash:
            return
        else:
            original_lines = original_document.splitlines(keepends=True)
            new_lines = new_document.splitlines(keepends=True)
            # info on the created diff on https://docs.python.org/3.6/library/difflib.html#difflib.unified_diff
            diff = difflib.unified_diff(original_lines, new_lines)
            return diff

    def run_checks(self):
        self.check_url(service=self.service,
                       url=self.service.get_capabilities_url)
        if self.status_code == 200:
            diff_obj = self.get_document_diff(
                self.response.text,
                self.service.xml_backup_string)
            if diff_obj:
                self.needs_update = True


class WebMapServiceMonitoringResult(OgcServiceGetCapabilitiesResult):
    service: WebMapService = models.ForeignKey(to=WebMapService,
                                               on_delete=models.CASCADE,
                                               related_name="monitoring_results",
                                               related_query_name="monitoring_result")

    class Meta(OgcServiceGetCapabilitiesResult.Meta):
        # Inheritate meta
        pass


class LayerGetMapMonitoringResult(MonitoringResult):
    layer: Layer = models.ForeignKey(to=Layer,
                                     on_delete=models.CASCADE,
                                     related_name="get_map_monitoring_results",
                                     related_query_name="get_map_monitoring_result")

    class Meta(OgcServiceGetCapabilitiesResult.Meta):
        # Inheritate meta
        pass

    def check_image(self):
        try:
            Image.open(BytesIO(self.response.content))
        except UnidentifiedImageError:
            self.error_msg = "Could not create image from response."

    def run_checks(self):
        self.check_url(service=self.layer.service,
                       url=self.layer.get_map_url())
        if self.status_code == 200:
            self.check_image()

import datetime
import logging

from celery import shared_task
from django.conf import settings

from common import enums

from .models import SecureUploadItem, StorageItem

logger = logging.getLogger("storage")


@shared_task
def purge_old_storage():
    if settings.FILE_PURGE_DAYS and settings.FILE_PURGE_DAYS >= 1:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        purge_before = now - datetime.timedelta(days=settings.FILE_PURGE_DAYS)
        for item in StorageItem.objects.filter(
            purged__isnull=True,
            created_at__lt=purge_before,
            app__in=[
                enums.FileType.REGISTRATION_FORM,
                enums.FileType.ABSENTEE_REQUEST_FORM,
            ],
        ):
            logger.info(f"Purging {item}")
            item.purged = now
            item.file.delete(save=True)

        for item in SecureUploadItem.objects.filter(
            purged__isnull=True,
            created_at__lt=purge_before,
            upload_type__in=[enums.SecureUploadType.SIGNATURE],
        ):
            logger.info(f"Purging {item}")
            item.purged = now
            item.file.delete(save=True)

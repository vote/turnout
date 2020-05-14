import datetime

import smalluuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django_smalluuid.models import SmallUUIDField, uuid_default

from absentee.models import BallotRequest
from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel
from multi_tenant.mixins_models import PartnerModel
from register.models import Registration

from .backends import HighValueDownloadStorage, HighValueStorage


def storage_expire_date_time():
    return now() + datetime.timedelta(hours=settings.FILE_EXPIRATION_HOURS)


class StorageItem(PartnerModel, UUIDModel, TimestampModel):
    token = SmallUUIDField(default=uuid_default())
    app = TurnoutEnumField(enums.FileType)
    file = models.FileField(storage=HighValueDownloadStorage())
    email = models.EmailField(blank=True, null=True)
    expires = models.DateTimeField(default=storage_expire_date_time)
    first_download = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def get_absolute_url(self):
        return self.file.url

    def refresh_token(self):
        self.token = smalluuid.SmallUUID()
        self.expires = storage_expire_date_time()
        self.save(update_fields=["token", "expires"])
        return self.token

    def validate_token(self, token):
        return token == str(self.token)

    @property
    def download_url(self):
        path = reverse("storage:download", kwargs={"pk": self.pk})
        return f"{settings.PRIMARY_ORIGIN}{path}?token={self.token}"

    @property
    def reset_url(self):
        return settings.FILE_TOKEN_RESET_URL.format(item_id=self.pk)

    def track_download(self):
        if self.app == enums.FileType.REGISTRATION_FORM:
            registration = Registration.objects.get(result_item=self)
            registration.action.track_event(enums.EventType.DOWNLOAD)
        if self.app == enums.FileType.ABSENTEE_REQUEST_FORM:
            ballot_request = BallotRequest.objects.get(result_item=self)
            ballot_request.action.track_event(enums.EventType.DOWNLOAD)
        if not self.first_download:
            self.first_download = now()
            self.save(update_fields=["first_download"])


class SecureUploadItem(UUIDModel, TimestampModel):
    file = models.FileField(storage=HighValueStorage())
    upload_type = TurnoutEnumField(enums.SecureUploadType)
    content_type = models.TextField()

    class Meta:
        ordering = ["-created_at"]

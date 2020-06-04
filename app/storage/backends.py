# Swiped from EveryVoter, which was swiped from Connect
import secrets
import string
from typing import Any, Optional

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.timezone import now
from pytz import timezone

AttachmentStorageEngine: Any = get_storage_class(
    import_path=settings.ATTACHMENT_STORAGE_ENGINE
)


def uniqify_filename(existing_filename: str) -> str:
    alphabet = string.ascii_letters + string.digits
    string_length = secrets.choice(range(5, 12))
    unique_code = "".join(secrets.choice(alphabet) for _ in range(string_length))
    return f"{unique_code}.{existing_filename}"


private_bucket_name: str = getattr(settings, "AWS_STORAGE_PRIVATE_BUCKET_NAME", "")
querystring_expire: int = getattr(settings, "AWS_STORAGE_PRIVATE_URL_EXPIRATION", 43200)


class AttachmentStorage(AttachmentStorageEngine):  # noqa
    def get_available_name(self, name: str, max_length: Optional[int] = None) -> str:
        # If the storage engine is S3, call _clean_name() to clean the name
        try:
            clean_name = self._clean_name(name)
        except AttributeError:
            clean_name = name

        # rsplit the filename on '/' so we have a 2 value list of the path and
        # filename
        splitname = clean_name.rsplit("/", 1)

        date = now().astimezone(timezone(settings.FILE_TIMEZONE)).strftime("%y%m%d")

        if len(splitname) == 2:
            final_name = f"{splitname[0]}/{date}.{uniqify_filename(splitname[1])}"
        else:
            final_name = f"{date}.{uniqify_filename(splitname[0])}"

        return final_name


class HighValueStorage(AttachmentStorage):
    default_acl = "private"
    secure_urls = True
    bucket_name = private_bucket_name

    # We have to override any `custom_domain` set in the settings file because our
    # storage engine will take that setting as a signal that all files have a
    # 'public' ACL
    custom_domain = None

    querystring_expire = querystring_expire
    querystring_auth = True


class HighValueDownloadStorage(HighValueStorage):
    def get_available_name(self, name: str, max_length: Optional[int] = None):
        self.original_name = name
        return super().get_available_name(name, max_length)

    def get_object_parameters(self, name: str):
        params = super().get_object_parameters(name)
        filename = self.original_name.split("/")[-1]
        params.update({"ContentDisposition": f'attachment; filename="{filename}"'})
        return params

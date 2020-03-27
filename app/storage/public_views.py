import logging

from django.utils.timezone import now
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin

from common.analytics import statsd
from common.utils.uuid_slug_mixin import UUIDSlugMixin

from .models import StorageItem

logger = logging.getLogger("storage")


class DownloadFileView(UUIDSlugMixin, SingleObjectMixin, RedirectView):
    model = StorageItem

    def get_redirect_url(self, *args, **kwargs):
        item = self.get_object()
        token = self.request.GET.get("token")
        if token and item.validate_token(token):
            logger.info(f"Valid token {item.pk}. Redirecting to file url.")
            if not item.first_download:
                item.first_download = now()
                item.save(update_fields=["first_download"])
            return item.file.url
        logger.info(f"Invalid token {item.pk}. Redirecting to reset URL.")
        statsd.increment("turnout.storage.download_token_invalid")
        return item.reset_url

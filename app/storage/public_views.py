import logging
import time

from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin
from smalluuid import SmallUUID

from common.analytics import statsd
from common.utils.uuid_slug_mixin import UUIDSlugMixin

from .models import StorageItem

logger = logging.getLogger("storage")


class DownloadFileView(UUIDSlugMixin, SingleObjectMixin, RedirectView):
    model = StorageItem

    def dispatch(self, request, *args, **kwargs):
        try:
            self.kwargs["pk"] = SmallUUID(kwargs["pk"]).hex_grouped
            kwargs["pk"] = SmallUUID(kwargs["pk"]).hex_grouped
            statsd.increment("turnout.storage.download_smalluuid_key_usage")
        except (TypeError, ValueError):
            pass
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        item = self.get_object()
        token = self.request.GET.get("token")
        statsd.distribution(
            "turnout.storage.token_validity_seconds",
            time.time() - item.expires.timestamp(),
        )
        if token and item.validate_token(token):
            logger.info(f"Valid token {item.pk}. Redirecting to file url.")

            try:
                item.track_download()
            except Exception:
                logger.exception(f"Unable to track download of {item.pk}")

            return item.file.url
        logger.info(f"Invalid token {item.pk}. Redirecting to reset URL.")
        statsd.increment("turnout.storage.download_token_invalid")
        return item.reset_url

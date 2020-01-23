import logging

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from .utils import audience_cachekey, fetch_catalist_token

logger = logging.getLogger("verifier")


@shared_task
def sync_catalist_token(return_token=False):
    audience = settings.CATALIST_AUDIENCE_VERIFY
    token = fetch_catalist_token(audience=audience)

    # OAuth tokens on the server expire after 24 hours, so we can expire our
    # local version at 23 hours and 59 minutes.
    cache.set(audience_cachekey(audience), token, 60 * 60 * 23 + 60 * 59)
    logger.info("Catalist Verification OAuth Token Set")

    if return_token:
        return token

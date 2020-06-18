import logging
from typing import Iterable

import CloudFlare
from django.conf import settings
from django.template.defaultfilters import slugify

from common.analytics import statsd
from common.apm import tracer

logger = logging.getLogger("cdn")


def generate_scoped_tag(raw_tag):
    """
    Cloudflare caches are scoped per domain (Cloudflare calles them "zones".)
    So that 2 apps on the same domain don't conflict, we need to scope their tags
    using something such as part of the app name (`to` in this case) and the
    environment (`settings.ENV` in this case.)
    """
    return slugify(f"to{settings.ENV}{str(raw_tag)}".lower())


@statsd.timed("turnout.cdn.purge_tags")
def purge_cdn_tags(tags: Iterable[str]) -> None:
    final_tags = [generate_scoped_tag(tag) for tag in tags]
    extra = {
        "tags": final_tags,
    }
    logger.info("Cache Tag Purge %(tags)s", extra, extra=extra)
    if not settings.CLOUDFLARE_ENABLED:
        logger.info("Cloudflare Disabled")
        return
    with tracer.trace("cf.purge_cache", service="cloudflareclient"):
        cf = CloudFlare.CloudFlare(token=settings.CLOUDFLARE_TOKEN)
        cf.zones.purge_cache.delete(
            identifier1=settings.CLOUDFLARE_ZONE, data={"tags": final_tags}
        )


def purge_cdn_tag(tag: str) -> None:
    purge_cdn_tags([tag])

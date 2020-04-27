from django.conf import settings

from .utils import generate_scoped_tag


class CDNMiddleware(object):
    """Middleware to generate cache tags"""

    def __init__(self, get_response):
        """Initialize the Middleware"""
        self.get_response = get_response

    def __call__(self, request):
        """Process a request"""
        response = self.get_response(request)

        if not hasattr(response, "cache_tags"):
            response.cache_tags: List[str] = []

        new_tags = []

        new_tags.append(f"detail_{settings.CLOUD_DETAIL}")
        new_tags.append(f"tag_{settings.TAG}")
        new_tags.append(f"build_{settings.BUILD}")
        new_tags.append(f"env_{settings.ENV}")

        response.cache_tags = new_tags + response.cache_tags

        keyed_tags = [generate_scoped_tag(tag) for tag in response.cache_tags]

        response._headers["cache-tag"] = ("Cache-Tag", ",".join(keyed_tags))

        return response

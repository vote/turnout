import base64
from typing import Optional, Tuple

from rest_framework import authentication, exceptions, permissions

from .crypto import check_key_secret
from .models import ApiKey


class ApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request) -> Optional[Tuple[None, ApiKey]]:
        if "HTTP_AUTHORIZATION" not in request.META:
            return None

        auth = request.META["HTTP_AUTHORIZATION"].split()
        if len(auth) != 2:
            return None

        if auth[0].lower() != "basic":
            return None

        key_id, hashed_secret = [
            s.strip() for s in base64.b64decode(auth[1]).decode().split(":")
        ]

        try:
            key = ApiKey.objects.select_related().get(
                pk=key_id, deactivated_by__isnull=True
            )
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("No such API key")

        if not check_key_secret(key.secret, hashed_secret):
            raise exceptions.AuthenticationFailed("Incorrect API key secret")

        return (None, key)

    def authenticate_header(self, request) -> str:
        return 'Basic realm="VoteAmerica API Key ID and Secret", charset="UTF-8"'


class ApiKeyRequired(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.auth and isinstance(request.auth, ApiKey)

import hmac
import hashlib
import pytest
from model_bakery import baker
from rest_framework.test import APIClient
from requests.auth import HTTPBasicAuth
from base64 import b64encode
import uuid

API_KEY_SECRET = "foo"
API_KEY_PEPPER = "pepp"
API_KEY_HASHED_SECRET = hmac.new(b"pepp", b"foo", hashlib.sha256).hexdigest()

API_KEY_CHECK_ENDPOINT = "/v1/apikey/check/"


def basicauth(username, password):
    return "Basic " + b64encode(":".join((username, password)).encode()).decode()


@pytest.fixture
def api_key():
    key = baker.make_recipe("apikey.apikey", secret=API_KEY_SECRET)
    key.subscriber.default_slug = baker.make_recipe(
        "multi_tenant.subscriberslug", subscriber=key.subscriber
    )
    key.subscriber.save()

    return key


@pytest.fixture
def mock_pepper(mocker):
    return mocker.patch("apikey.crypto.PEPPER", API_KEY_PEPPER.encode())


@pytest.mark.django_db
def test_auth_success(api_key, mock_pepper):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=basicauth(str(api_key.uuid), API_KEY_HASHED_SECRET)
    )
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 200
    assert response.json() == {"ok": True, "subscriber": api_key.subscriber.slug}


@pytest.mark.django_db
def test_missing_auth(api_key, mock_pepper):
    client = APIClient()
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication credentials were not provided."
    }
    assert (
        response.get("WWW-Authenticate")
        == 'Basic realm="VoteAmerica API Key ID and Secret", charset="UTF-8"'
    )


@pytest.mark.django_db
def test_wrong_key_id(api_key, mock_pepper):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=basicauth(str(uuid.uuid4()), API_KEY_HASHED_SECRET)
    )
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"detail": "No such API key"}


@pytest.mark.django_db
def test_wrong_secret(api_key, mock_pepper):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(api_key.uuid), "wrongsecret"))
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect API key secret"}


@pytest.mark.django_db
def test_unhashed_secret(api_key, mock_pepper):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(api_key.uuid), API_KEY_SECRET))
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect API key secret"}


@pytest.mark.django_db
def test_malformed_header(api_key, mock_pepper):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION="NotBasic "
        + b64encode(":".join((str(api_key.uuid), API_KEY_SECRET)).encode()).decode()
    )
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication credentials were not provided."
    }


@pytest.mark.django_db
def test_malformed_header_2(api_key, mock_pepper):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=basicauth(str(api_key.uuid), API_KEY_HASHED_SECRET)
        + " extra"
    )
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication credentials were not provided."
    }


@pytest.mark.django_db
def test_deleted_key(api_key, mock_pepper):
    api_key.deactivated_by = api_key.created_by
    api_key.save()

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=basicauth(str(api_key.uuid), API_KEY_HASHED_SECRET)
    )
    response = client.get(API_KEY_CHECK_ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"detail": "No such API key"}


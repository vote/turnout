import os

import environs
import sentry_sdk
from kombu import Queue
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

env = environs.Env()


SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default="localhost")
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
USE_I18N = True
USE_L10N = True
WSGI_APPLICATION = "turnout.wsgi.application"
ROOT_URLCONF = "turnout.urls"


##### DATABASE CONFIGURATION

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL", default="pgsql://postgres:turnout@postgres:5432/turnout"
    )
}

##### END DATABASE CONFIGURATION


##### CACHE CONFIGURATION

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://redis:6379"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": env.str("REDIS_KEY_PREFIX", default="turnout"),
    }
}

##### END CACHE CONFIGURATION


##### APPLICATION CONFIGURATION

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


THIRD_PARTY_APPS = [
    "sekizai",
    "crispy_forms",
    "reversion",
    "rest_framework",
    "django_alive",
    "ddtrace.contrib.django",
    "django_celery_results",
    "phonenumber_field",
]

FIRST_PARTY_APPS = [
    "accounts",
    "common",
    "manage",
    "multi_tenant",
    "election",
    "people",
    "verifier",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + FIRST_PARTY_APPS

##### END APPLICATION CONFIGURATION


##### MIDDLEWARE CONFIGURATION

MIDDLEWARE = [
    "django_alive.middleware.healthcheck_bypass_host_check",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#### END MIDDLEWARE CONFIGURATION


#### TEMPLATE CONFIGURATION

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "sekizai.context_processors.sekizai",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
CRISPY_TEMPLATE_PACK = "bootstrap4"

#### END TEMPLATE CONFIGURATION


#### STATIC ASSET CONFIGURATION

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
STATICFILES_DIRS = (os.path.join(BASE_PATH, "dist"),)

#### END ASSET CONFIGURATION


#### REST FRAMEWORK CONFIGURATION

DEFAULT_RENDERER_CLASSES = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_RENDERER_CLASSES": DEFAULT_RENDERER_CLASSES,
}

#### END REST FRAMEWORK CONFIGURATION


#### CELERY CONFIGURATION

CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://redis:6379")
CELERY_RESULT_BACKEND = "django-db"
CELERY_WORKER_CONCURRENCY = 6
CELERY_TASK_SERIALIZER = "json"

CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    Queue("default", routing_key="task.#"),
}
CELERY_BEAT_SCHEDULE = {}
CELERY_TIMEZONE = "UTC"

#### END CELERY CONFIGURATION


#### AUTH CONFIGURATION

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]
LOGIN_URL = "/manage/login/"

#### END AUTH CONFIGURATION


#### FILE CONFIGURATION

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_PATH, "static")

#### END FILE CONFIGURATION


#### DJANGO-ALIVE CONFIGURATION

ALIVE_CHECKS = {
    "django_alive.checks.check_migrations": {},
}

#### END ALIVE CONFIGURATION


#### DATADOG CONFIGURATION

DATADOG_TRACE = {
    "TRACER": "turnout.tracer.tracer",
    "TAGS": {"build": env.str("BUILD", default="")},
}

#### END DATADOG CONFIGURATION


#### SENTRY CONFIGURATION

RELEASE_TAG = env.str("TAG", default="")
SENTRY_DSN = env.str("SENTRY_DSN", default="")
if RELEASE_TAG and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), RedisIntegration(), CeleryIntegration()],
        send_default_pii=True,
        release=f"turnout@{RELEASE_TAG}",
        environment=env.str("CLOUD_STACK", default=None),
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("SERVER_GROUP", env.str("SERVER_GROUP", default=""))
        scope.set_tag("CLOUD_DETAIL", env.str("CLOUD_DETAIL", default=""))
        scope.set_tag("CLOUD_STACK", env.str("CLOUD_STACK", default=""))
        scope.set_tag("build", env.str("BUILD", default=""))
        scope.set_tag("tag", env.str("TAG", default=""))
        scope.set_extra("allowed_hosts", ALLOWED_HOSTS)

#### END SENTRY CONFIGURATION


#### LOGGING CONFIGURATION

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler",},},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "verifier": {
            "handlers": ["console"],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

#### END LOGGING CONFIGURATION

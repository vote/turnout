import os
from typing import Dict, Optional

import ddtrace
import environs
import sentry_sdk
from celery.schedules import crontab
from kombu import Queue
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

env = environs.Env()


SECRET_KEY = env.str("SECRET_KEY", default="SET_THIS_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default="localhost")
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
USE_I18N = True
USE_L10N = True
WSGI_APPLICATION = "turnout.wsgi.application"
ROOT_URLCONF = "turnout.urls"
PRIMARY_ORIGIN = env.str("PRIMARY_ORIGIN", default="http://localhost:9001")


# Useful analytics and tracking tags
CLOUD_DETAIL = env.str("CLOUD_DETAIL", default="")
SERVER_GROUP = env.str("SERVER_GROUP", default="")
CLOUD_STACK = env.str("CLOUD_STACK", default="local")
ENV = env.str("ENV", default=CLOUD_STACK)
TAG = env.str("TAG", default="")
BUILD = env.str("BUILD", default="0")

##### DATABASE CONFIGURATION

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL", default="postgis://postgres:turnout@postgres:5432/turnout"
    )
}
DATABASES["default"]["ENGINE"] = "common.db"
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["OPTIONS"] = {
    "MAX_CONNS": env.int("DATABASE_MAX_CONNECTIONS", default=4)
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
    "django.contrib.gis",
    "django.contrib.postgres",
    "django.contrib.humanize",
]


THIRD_PARTY_APPS = [
    "sekizai",
    "crispy_forms",
    "markdownify",
    "reversion",
    "rest_framework",
    "django_alive",
    "corsheaders",
    "django_celery_results",
    "phonenumber_field",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "s3_folder_storage",
    "nested_inline",
]

FIRST_PARTY_APPS = [
    "accounts",
    "common",
    "manage",
    "multi_tenant",
    "election",
    "people",
    "verifier",
    "register",
    "mailer",
    "storage",
    "event_tracking",
    "action",
    "absentee",
    "official",
    "smsbot",
    "reporting",
    "fax",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + FIRST_PARTY_APPS

##### END APPLICATION CONFIGURATION


##### MIDDLEWARE CONFIGURATION

MIDDLEWARE = [
    "cdn.middleware.CDNMiddleware",
    "django_alive.middleware.healthcheck_bypass_host_check",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    # Include for twilio gateway
    "two_factor.middleware.threadlocals.ThreadLocals",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#### END MIDDLEWARE CONFIGURATION


#### STATIC ASSET CONFIGURATION

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
STATICFILES_DIRS = (
    os.path.join(BASE_PATH, "dist"),
    os.path.join(BASE_PATH, "assets"),
)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_PATH, "static")

#### END ASSET CONFIGURATION


#### TEMPLATE CONFIGURATION

TEMPLATES_DIRS = [os.path.join(BASE_PATH, "templates")]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": TEMPLATES_DIRS,
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


#### REST FRAMEWORK CONFIGURATION

DEFAULT_RENDERER_CLASSES = ("rest_framework.renderers.JSONRenderer",)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_RENDERER_CLASSES": DEFAULT_RENDERER_CLASSES,
}

#### END REST FRAMEWORK CONFIGURATION


#### CELERY CONFIGURATION

# how often to recalculate subscriber stats
CALC_STATS_INTERVAL = 5

USVF_SYNC = env.bool("USVF_SYNC", False)
USVF_SYNC_HOUR = env.int("USVF_SYNC_HOUR", 6)
USVF_SYNC_MINUTE = env.int("USVF_SYNC_MINUTE", 30)

CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://redis:6379")
CELERY_RESULT_BACKEND = "django-db"
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=3)
CELERY_TASK_SERIALIZER = "json"

CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    Queue("default", routing_key="task.#"),
}
CELERY_BEAT_SCHEDULE = {
    "trigger-netlify-updated-information": {
        "task": "election.tasks.trigger_netlify_if_updates",
        "schedule": crontab(minute=0, hour="*"),
    },
    "trigger-calc-subscriber-stats": {
        "task": "reporting.tasks.calc_all_subscriber_stats",
        "schedule": crontab(minute=f"*/{CALC_STATS_INTERVAL}"),
    },
}
CELERY_TIMEZONE = "UTC"

if USVF_SYNC:
    CELERY_BEAT_SCHEDULE["trigger-usvf-sync"] = {
        "task": "official.tasks.sync_usvotefoundation",
        "schedule": crontab(minute=USVF_SYNC_MINUTE, hour=USVF_SYNC_HOUR),
    }

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
LOGIN_REDIRECT_URL = "/manage/"

INVITE_EXPIRATION_DAYS = env.int("INVITE_EXPIRATION_DAYS", default=7)

TWO_FACTOR_SMS_GATEWAY = "two_factor.gateways.twilio.gateway.Twilio"
PHONENUMBER_DEFAULT_REGION = "1"

# source number for 2FA SMS
TWILIO_CALLER_ID = env.str("TWO_FACTOR_SMS_NUMBER", default=None)

#### END AUTH CONFIGURATION


#### DJANGO-ALIVE CONFIGURATION

ALIVE_CHECKS: Dict[str, Dict[Optional[str], Optional[str]]] = {
    "django_alive.checks.check_migrations": {},
}

#### END ALIVE CONFIGURATION


#### AWS CONFIGURATION

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
AWS_DEFAULT_REGION = env.str("AWS_DEFAULT_REGION", default="us-west-2")

#### END AWS CONFIGURATION


#### STORAGE CONFIGURATION

DEFAULT_FILE_STORAGE = "storage.backends.AttachmentStorage"
FILE_EXPIRATION_HOURS = env.int("FILE_EXPIRATION_HOURS", default=168)
FILE_TIMEZONE = env.str("FILE_TIMEZONE", default="America/Los_Angeles")
FILE_TOKEN_RESET_URL = env.str(
    "FILE_TOKEN_RESET_URL", default="http://localhost:8000/download/?id={item_id}"
)

if env.bool("ATTACHMENT_USE_S3", False):
    ATTACHMENT_STORAGE_ENGINE = "s3_folder_storage.s3.DefaultStorage"

    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_STORAGE_PRIVATE_BUCKET_NAME = env.str("AWS_STORAGE_PRIVATE_BUCKET_NAME")

    AWS_STORAGE_PRIVATE_URL_EXPIRATION = env.int(
        "AWS_STORAGE_PRIVATE_URL_EXPIRATION", 7200
    )

    DEFAULT_S3_PATH = env.str("ATTACHMENT_DEFAULT_S3_PATH", ENV)
    AWS_DEFAULT_ACL = "public-read"
    AWS_QUERYSTRING_AUTH = False

    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default=AWS_DEFAULT_REGION)
    AWS_S3_CUSTOM_DOMAIN = env.str(
        "AWS_S3_CUSTOM_DOMAIN",
        default=f"{AWS_STORAGE_BUCKET_NAME}.s3-{AWS_DEFAULT_REGION}.amazonaws.com",
    )
    MEDIA_ROOT = f"/{DEFAULT_S3_PATH}/"
    MEDIA_URL = f"//{AWS_S3_CUSTOM_DOMAIN}/{DEFAULT_S3_PATH}/"
else:
    ATTACHMENT_STORAGE_ENGINE = "django.core.files.storage.FileSystemStorage"
    MEDIA_ROOT = os.path.join(BASE_PATH, "uploads")
    MEDIA_URL = "/uploads/"

#### END STORAGE CONFIGURATION


#### CORS CONFIGURATION

CORS_ORIGIN_REGEX_WHITELIST = [
    r"^https:\/\/voteamerica.com$",  # root
    r"^https:\/\/\w*.?voteamerica.com$",  # production and staging
    r"^https:\/\/[\w-]+--voteamerica.netlify.com$",  # branch builds
    r"^https:\/\/[\w-]+--voteamerica.netlify.app$",  # branch builds
    r"^http:\/\/localhost:8000$",  # local
    r"^http:\/\/localhost:6007$",  # local storybook
]

#### END CORS CONFIGURATION


#### CLOUDFLARE CONFIGURATION

CLOUDFLARE_ENABLED = env.bool("CLOUDFLARE_ENABLED", default=False)
CLOUDFLARE_TOKEN = env.str("CLOUDFLARE_TOKEN", default="")
CLOUDFLARE_ZONE = env.str("CLOUDFLARE_ZONE", default="")

#### END CLOUDFLARE CONFIGURATION


#### DATADOG CONFIGURATION

ddtrace.tracer.set_tags({"build": BUILD})

#### END DATADOG CONFIGURATION


#### STATSD CONFIGURATION

STATSD_TAGS = [
    f"env:{ENV}",
    f"spinnaker_detail:{CLOUD_DETAIL}",
    f"spinnaker_servergroup:{SERVER_GROUP}",
    f"spinnaker_stack:{CLOUD_STACK}",
    f"image_tag:{TAG}",
    f"build:{BUILD}",
]

#### END STATSD CONFIGURATION


#### SENDGRID CONFIGURATION

SENDGRID_API_KEY = env.str("SENDGRID_API_KEY", default="")
SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool(
    "SENDGRID_SANDBOX_MODE_IN_DEBUG", default=False
)
EMAIL_SEND_TIMEOUT = env.int("EMAIL_SEND_TIMEOUT", default=60 * 60 * 24)
EMAIL_BACKEND = "mailer.backend.TurnoutBackend"

#### END SENDGRID CONFIGURATION


#### SENTRY CONFIGURATION

SENTRY_DSN = env.str("SENTRY_DSN", default="")
if TAG and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), RedisIntegration(), CeleryIntegration()],
        send_default_pii=True,
        release=f"turnout@{TAG}",
        environment=ENV,
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("SERVER_GROUP", SERVER_GROUP)
        scope.set_tag("CLOUD_DETAIL", CLOUD_DETAIL)
        scope.set_tag("CLOUD_STACK", CLOUD_STACK)
        scope.set_tag("build", BUILD)
        scope.set_tag("tag", TAG)
        scope.set_extra("allowed_hosts", ALLOWED_HOSTS)

#### END SENTRY CONFIGURATION


#### LOGGING CONFIGURATION

handler = "console" if DEBUG else "json"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler",},
        "json": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "formatters": {"json": {"()": "pythonjsonlogger.jsonlogger.JsonFormatter"}},
    "loggers": {
        "django": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "ddtrace": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "verifier": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "election": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "register": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "mailer": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "multi_tenant": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "storage": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "official": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "absentee": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "pypdftk": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "cdn": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "reporting": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

#### END LOGGING CONFIGURATION


#### TARGETSMART CONFIGURATION

TARGETSMART_KEY = env.str("TARGETSMART_KEY", default=None)

#### END TARGETSMART CONFIGURATION


#### ALLOY CONFIGURATION

ALLOY_KEY = env.str("ALLOY_KEY", default=None)
ALLOY_SECRET = env.str("ALLOY_SECRET", default=None)

#### END ALLOY CONFIGURATION


#### ELECTION OFFICIALS CONFIGURATION

USVOTEFOUNDATION_KEY = env.str("USVOTEFOUNDATION_KEY", default=None)
PHONENUMBER_DEFAULT_REGION = "US"
PHONENUMBER_DEFAULT_FORMAT = "NATIONAL"

#### END ELECTION OFFICIALS CONFIGURATION


#### MANAGEMENT INTERFACE CONFIGURATION

MANAGEMENT_ACTION_PAGINATION_SIZE = env.int(
    "MANAGEMENT_ACTION_PAGINATION_SIZE", default=50
)
MANAGEMENT_NOTIFICATION_FROM = env.str(
    "MANAGEMENT_NOTIFICATION_FROM", default="noreply@voteamerica.com"
)

#### END MANAGEMENT INTERFACE CONFIGURATION

#### TWILIO CONFIGURATION

TWILIO_ACCOUNT_SID = env.str("TWILIO_ACCOUNT_SID", default=None)
TWILIO_AUTH_TOKEN = env.str("TWILIO_AUTH_TOKEN", default=None)
TWILIO_MESSAGING_SERVICE_SID = env.str("TWILIO_MESSAGING_SERVICE_SID", default=None)
TWILIO_ENDPOINT_IS_HTTPS = env.bool("TWILIO_ENDPOINT_IS_HTTPS", default=True)

SMS_OPTIN_REMINDER_DELAY = env.int("SMS_OPTIN_REMINDER_DELAY", default=60 * 60)
# If set, we will resend the welcome message if the last one is older than this
SMS_OPTIN_REMINDER_RESEND_SECONDS = env.int(
    "SMS_OPTIN_REMINDER_RESEND_SECONDS", default=None,
)
SMS_POST_SIGNUP_ALERT = env.bool("SMS_POST_SIGNUP_ALERT", default=False)

#### END TWILIO CONFIGURATION

#### GEOCODIO CONFIGURATION

GEOCODIO_KEY = env.str("GEOCODIO_KEY", default=None)

#### END GEOCODIO CONFIGURATION

#### PDF GENERATION CONFIGURATION

PDF_DEBUG = env.bool("PDF_DEBUG", default=DEBUG)

#### END PDF GENERATION CONFIGURATION


#### ABSENTEE CONFIGURATION

ABSENTEE_LEO_EMAIL_DISABLE = env.bool("ABSENTEE_LEO_EMAIL_DISABLE", default=True)
ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS = env.str(
    "ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS", default=None
)

ABSENTEE_LEO_EMAIL_FROM = env.str(
    "ABSENTEE_LEO_EMAIL_FROM", default="noreply@voteamerica.com"
)

ABSENTEE_LEO_FAX_EMAIL_REPLY_TO = env.str(
    "ABSENTEE_LEO_FAX_EMAIL_FROM", default=ABSENTEE_LEO_EMAIL_FROM
)

#### END ABSENTEE CONFIGURATION


#### SLACK DATA ERROR CONFIGURATION

SLACK_DATA_ERROR_ENABLED = env.bool("SLACK_DATA_ERROR_ENABLED", default=False)
SLACK_DATA_ERROR_WEBHOOK = env.str(
    "SLACK_DATA_ERROR_WEBHOOK", default="http://localhost"
)

#### END SLACK DATA ERROR CONFIGURATION


#### FAX CONFIGURATION

FAX_DISABLE = env.bool("FAX_DISABLE", default=True)

FAX_OVERRIDE_DEST = env.str("FAX_OVERRIDE_DEST", default=None)

FAX_GATEWAY_CALLBACK_URL = env.str(
    "FAX_GATEWAY_CALLBACK_URL", default=f"{PRIMARY_ORIGIN}/fax/gateway_callback/"
)

FAX_GATEWAY_SQS_QUEUE = env.str("FAX_GATEWAY_SQS_QUEUE", default=None)

#### END FAX CONFIGURATION

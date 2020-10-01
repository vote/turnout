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
WWW_ORIGIN = env.str("WWW_ORIGIN", default="http://localhost:8000")

DEFAULT_EMAIL_FROM = env.str("DEFAULT_EMAIL_FROM", "hello@voteamerica.com")

TEST_ADDRS = env.json("TEST_ADDRS", "[]")

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
    # "formtools",
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
    "integration",
    "subscription",
    "reminder",
    "apikey",
    "leouptime",
    "celery_admin",
    "voter",
    "polling_place",
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
NETLIFY_TRIGGER_INTERVAL = 10

# how often to check for delayed tasks (minutes)
DELAYED_TASKS_INTERVAL = 2

CELERY_REDBEAT_REDIS_URL = env.str("REDIS_URL", default="redis://redis:6379")
CELERY_BROKER_URL = env.str("AMQP_URL", default="amqp://guest:guest@amqp:5672/turnout")
CELERY_RESULT_BACKEND = "django-db"
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=8)
CELERY_TASK_SERIALIZER = "json"

CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    Queue("default", routing_key="task.#"),
    Queue("high-pri", routing_key="high-pri.#"),
    Queue("voter", routing_key="voter.#"),
    Queue("leouptime", routing_key="leouptime.#"),
    Queue("movers", routing_key="movers.#"),
    Queue("geocode", routing_key="geocode.#"),
    Queue("actionnetwork", routing_key="actionnetwork.#"),
    Queue("lob-status-updates", routing_key="lob.#"),
    Queue("bulk-tokens", max_length=10, durable=False),
}

# Celery rate limits are almost completely useless, in our case
# because we have tasks with different rate limits on the same worker,
# which means that all items effecively run at the rate of the slowest
# rate limit.
#
# Benefits:
#  - a global rate limit, regardless of worker scale
#  - rate limits can vary
# Caveats:
#  - very high rates are inefficient since we are generating tokens
#    regardless of whether there is work to do.

BULK_QUEUE_RATE_LIMITS = {
    "voter": 1 / 10,
    "actionnetwork": 1 / 4,
    "movers": 1 / 5,
    "geocode": 1 / 10,
    "lob-status-updates": 1 / 10,
}

CELERY_TASK_ROUTES = {
    "absentee.tasks.send_ballotrequest_notification": {"queue": "high-pri"},
    "absentee.tasks.send_ballotrequest_leo_email": {"queue": "high-pri"},
    "absentee.tasks.send_ballotrequest_leo_fax": {"queue": "high-pri"},
    "absentee.tasks.send_ballotrequest_leo_fax_sent_notification": {
        "queue": "high-pri"
    },
    "absentee.tasks.send_download_reminder": {"queue": "high-pri"},
    "absentee.tasks.send_print_and_forward_confirm_nag": {"queue": "high-pri"},
    "absentee.tasks.external_tool_upsell": {"queue": "high-pri"},
    "multi_tenant.tasks.send_invite_notification": {"queue": "high-pri"},
    "official.tasks.sunc_usvotefoundation": {"queue": "usvf"},
    "register.tasks.send_registration_notification": {"queue": "high-pri"},
    "register.tasks.send_registration_state_confirmation": {"queue": "high-pri"},
    "register.tasks.send_registration_reminder": {"queue": "high-pri"},
    "register.tasks.send_print_and_forward_nag": {"queue": "high-pri"},
    "register.tasks.external_tool_upsell": {"queue": "high-pri"},
    "register.tasks.send_print_and_forward_mailed": {"queue": "high-pri"},
    "register.tasks.send_print_and_forward_returned": {"queue": "high-pri"},
    "register.tasks.send_mail_chase": {"queue": "high-pri"},
    "subscription.tasks.send_organization_welcome_notification": {"queue": "high-pri"},
    "verifier.tasks.external_tool_upsell": {"queue": "high-pri"},
    "leouptime.tasks.*": {"queue": "leouptime"},
}

CELERY_BEAT_SCHEDULE = {
    "trigger-netlify-updated-information": {
        "task": "election.tasks.trigger_netlify_if_updates",
        "schedule": crontab(minute=f"*/{NETLIFY_TRIGGER_INTERVAL}"),
    },
    "trigger-calc-subscriber-stats": {
        "task": "reporting.tasks.calc_all_subscriber_stats",
        "schedule": crontab(minute=f"*/{CALC_STATS_INTERVAL}"),
    },
    "trigger-deliver-delayed-tasks": {
        "task": "common.tasks.deliver_delayed_tasks",
        "schedule": crontab(minute=f"*/{DELAYED_TASKS_INTERVAL}"),
    },
}

for name, rate in BULK_QUEUE_RATE_LIMITS.items():
    CELERY_BEAT_SCHEDULE[f"trigger-bulk-tokens-{name}"] = {
        "task": "common.tasks.process_token",
        "schedule": rate,
        "options": {"queue": f"bulk-tokens"},
        "args": (name,),
    }


CELERY_TIMEZONE = "UTC"

DJANGO_CELERY_RESULTS = {"ALLOW_EDITS": False}

BEAT_STATS_INTERVAL = env.int("BEAT_STATS_INTERVAL", default=15)
BEAT_STATS_METRIC_NAMESPACE = env.str("BEAT_STATS_METRIC_NAMESPACE", default=None)

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


#### SESSION AND COOKIE CONFIGURATION

SESSION_COOKIE_NAME = env.str("SESSION_COOKIE_NAME", default="turnout_sessionid")
SESSION_COOKIE_SECURE = DEBUG == False
SESSION_ENGINE = env.str(
    "SESSION_ENGINE", default="django.contrib.sessions.backends.cached_db"
)
CSRF_COOKIE_NAME = env.str("CSRF_COOKIE_NAME", default="turnout_csrftoken")

#### END SESSION AND COOKIE CONFIGURATION


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
FILE_EXPIRATION_HOURS = env.int("FILE_EXPIRATION_HOURS", default=60 * 24)
FILE_TIMEZONE = env.str("FILE_TIMEZONE", default="America/Los_Angeles")
FILE_TOKEN_RESET_URL = env.str(
    "FILE_TOKEN_RESET_URL", default="http://localhost:8000/download/?id={item_id}"
)

FILE_PURGE_DAYS = env.int("FILE_PURGE_DAYS", default=None)
FILE_TOKEN_PURGED_URL = env.str(
    "FILE_TOKEN_PURGED_URL",
    default="http://localhost:8000/download-purged/?id={item_id}&filetype={filetype}&purge_days={purge_days}",
)
if FILE_PURGE_DAYS and FILE_PURGE_DAYS >= 1:
    CELERY_BEAT_SCHEDULE["purge-old-storage"] = {
        "task": "storage.tasks.purge_old_storage",
        "schedule": crontab(minute=45, hour="*/12"),
    }

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
    r"^https:\/\/\w*.voteamerica.com$",  # production and staging
    r"^https:\/\/[\w-]+--voteamerica.netlify.com$",  # branch builds
    r"^https:\/\/[\w-]+--voteamerica.netlify.app$",  # branch builds
    r"^http:\/\/localhost:8000$",  # local
    r"^http:\/\/localhost:6007$",  # local storybook
    r"^https:\/\/\w*.creditkarma.com$",
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


#### EMAIL CONFIGURATION

SENDGRID_API_KEY = env.str("SENDGRID_API_KEY", default="")
SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool(
    "SENDGRID_SANDBOX_MODE_IN_DEBUG", default=False
)
EMAIL_SEND_TIMEOUT = env.int("EMAIL_SEND_TIMEOUT", default=60)
EMAIL_BACKEND = "mailer.backend.TurnoutBackend"

EMAIL_TASK_RETRIES = 3

# Set initial backoff to 5 minutes. Backoff doubles each time so we'll retry
# at 5 minutes, then 10 minutes, then 20 minutes.
#
# Backoffs are jittered, so the backoff is treated as a maximum and the
# actual value is randomly selected between 0 and the backoff.
EMAIL_TASK_RETRY_BACKOFF = 2
EMAIL_TASK_RETRY_BACKOFF_MAX = 20 * 60
EMAIL_TASK_RETRY_JITTER = True

#### END EMAIL CONFIGURATION


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
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(name) %(message)s %(levelname) %(module) %(filename) %(funcName) %(lineno)",
        }
    },
    "loggers": {
        "django": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "ddtrace": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "common": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
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
        "integration": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "leouptime": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "subscription": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "apikey": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "turnout": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "apm": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "smsbot": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "voter": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "i90": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "optimizely": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="DEBUG"),
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

# periodically check alloy about state data freshness
ALLOY_UPDATE_CHECK_HOURS = env.int("ALLOY_UPDATE_CHECK_HOURS", default=3)

if ALLOY_UPDATE_CHECK_HOURS:
    CELERY_BEAT_SCHEDULE["trigger-refresh_alloy-dates"] = {
        "task": "verifier.tasks.refresh_alloy_dates",
        "schedule": crontab(minute=1, hour=ALLOY_UPDATE_CHECK_HOURS),
    }

#### END ALLOY CONFIGURATION


#### ELECTION OFFICIALS CONFIGURATION

USVOTEFOUNDATION_KEY = env.str("USVOTEFOUNDATION_KEY", default=None)
USVF_GEOCODE = env.bool("USVF_GEOCODE", default=False)
USVF_SYNC = env.bool("USVF_SYNC", False)
USVF_SYNC_HOUR = env.int("USVF_SYNC_HOUR", 6)
USVF_SYNC_MINUTE = env.int("USVF_SYNC_MINUTE", 30)

if USVF_SYNC:
    CELERY_BEAT_SCHEDULE["trigger-usvf-sync"] = {
        "task": "official.tasks.sync_usvotefoundation",
        "schedule": crontab(minute=USVF_SYNC_MINUTE, hour=USVF_SYNC_HOUR),
    }

PHONENUMBER_DEFAULT_REGION = "US"
PHONENUMBER_DEFAULT_FORMAT = "NATIONAL"

STATE_TOOL_REDIRECT_BUCKET = env.str(
    "STATE_TOOL_REDIRECT_BUCKET", default=f"turnout{ENV}-public"
)
STATE_TOOL_REDIRECT_SYNC = env.bool("STATE_TOOL_REDIRECT_SYNC", default=False)
STATE_TOOL_REDIRECT_CRON_HOUR = env.str("STATE_TOOL_REDIRECT_CRON_HOUR", default="*/12")
STATE_TOOL_REDIRECT_CRON_MINUTE = env.str(
    "STATE_TOOL_REDIRECT_CRON_MINUTE", default="10"
)
if STATE_TOOL_REDIRECT_SYNC:
    CELERY_BEAT_SCHEDULE["publish-external-tool-redirects"] = {
        "task": "election.tasks.publish_external_tool_redirects",
        "schedule": crontab(
            minute=STATE_TOOL_REDIRECT_CRON_MINUTE, hour=STATE_TOOL_REDIRECT_CRON_HOUR
        ),
    }

#### END ELECTION OFFICIALS CONFIGURATION


#### MANAGEMENT INTERFACE CONFIGURATION

MANAGEMENT_ACTION_PAGINATION_SIZE = env.int(
    "MANAGEMENT_ACTION_PAGINATION_SIZE", default=50
)
MANAGEMENT_NOTIFICATION_FROM = env.str(
    "MANAGEMENT_NOTIFICATION_FROM", default="noreply@voteamerica.com"
)

#### END MANAGEMENT INTERFACE CONFIGURATION

#### ACTION CONFIGURATION

ACTION_CHECK_UNFINISHED_DELAY = env.int("ACTION_CHECK_UNFINISHED_DELAY", 900)

#### END ACTION CONFIGURATION

#### TWILIO CONFIGURATION

TWILIO_ACCOUNT_SID = env.str("TWILIO_ACCOUNT_SID", default=None)
TWILIO_AUTH_TOKEN = env.str("TWILIO_AUTH_TOKEN", default=None)
TWILIO_MESSAGING_SERVICE_SID = env.str("TWILIO_MESSAGING_SERVICE_SID", default=None)

SMS_OPTIN_REMINDER_DELAY = env.int("SMS_OPTIN_REMINDER_DELAY", default=600)
# If set, we will resend the welcome message if the last one is older than this
SMS_OPTIN_REMINDER_RESEND_SECONDS = env.int(
    "SMS_OPTIN_REMINDER_RESEND_SECONDS", default=None,
)
SMS_POST_SIGNUP_ALERT = env.bool("SMS_POST_SIGNUP_ALERT", default=False)

# max seconds of messages to fetch from twilio (if we haven't polled in a while)
SMS_OPTOUT_POLL_MAX_SECONDS = env.int("SMS_OPTOUT_POLL_MAX", 60 * 60 * 24)
SMS_OPTOUT_NUMBER = env.str("SMS_OPTOUT_NUMBER", None)
SMS_OPTOUT_POLL = env.bool("SMS_OPTOUT_POLL", False)
SMS_OPTOUT_POLL_SECONDS = env.int("SMS_OPTOUT_POLL_SECONDS", 5)

SMS_AUTOREPLY_THROTTLE_MINUTES = env.int("SMS_AUTOREPLY_THROTTLE_MINUTES", 60 * 12)

if SMS_OPTOUT_POLL:
    CELERY_BEAT_SCHEDULE["trigger-sms-poll-twilio"] = {
        "task": "smsbot.tasks.poll_twilio",
        "schedule": SMS_OPTOUT_POLL_SECONDS,
    }

#### END TWILIO CONFIGURATION

#### GEOCODIO CONFIGURATION

GEOCODIO_KEY = env.str("GEOCODIO_KEY", default=None)

#### END GEOCODIO CONFIGURATION

#### PDF GENERATION CONFIGURATION

PDF_GENERATION_LAMBDA_ENABLED = env.bool("PDF_GENERATION_LAMBDA_ENABLED", default=False)
PDF_GENERATION_LAMBDA_FUNCTION = env.str(
    "PDF_GENERATION_LAMBDA_FUNCTION", default="pdf-filler-local-fill"
)

#### END PDF GENERATION CONFIGURATION


#### REGISTER CONFIGURATION

REGISTER_CO_VRD_ENABLED = env.bool("REGISTER_CO_VRD_ENABLED", default=False)
REGISTER_CO_VRD_ID = env.str("REGISTER_CO_VRD_ID", default=None)

REGISTER_WA_VRD_ENABLED = env.bool("REGISTER_WA_VRD_ENABLED", default=False)
REGISTER_WA_VRD_ID = env.str("REGISTER_WA_VRD_ID", default=None)

REGISTER_RESUME_URL = env.str(
    "REGISTER_RESUME_URL", default="http://localhost:8000/register-to-vote/resume/"
)

REGISTER_JWT_EXPIRATION_MINUTES = env.int("REGISTER_JWT_EXPIRATION_MINUTES", default=60)

REGISTER_LOB_CONFIRM_NAG_SECONDS = env.int(
    "REGISTER_LOB_CONFIRM_NAG_SECONDS", default=300,
)
REGISTER_UPSELL_DELAY_SECONDS = env.int("REGISTER_UPSELL_DELAY_SECONDS", default=300)

#### END REGISTER CONFIGURATION


#### ABSENTEE CONFIGURATION

ABSENTEE_LEO_EMAIL_DISABLE = env.bool("ABSENTEE_LEO_EMAIL_DISABLE", default=True)
ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS = env.str(
    "ABSENTEE_LEO_EMAIL_OVERRIDE_ADDRESS", default=None
)

ABSENTEE_LEO_EMAIL_FROM = env.str(
    "ABSENTEE_LEO_EMAIL_FROM", default="transmission-staging@voteamerica.com"
)

ABSENTEE_LEO_FAX_EMAIL_REPLY_TO = env.str(
    "ABSENTEE_LEO_FAX_EMAIL_FROM", default=ABSENTEE_LEO_EMAIL_FROM
)

ABSENTEE_UPSELL_DELAY_SECONDS = env.int("ABSENTEE_UPSELL_DELAY_SECONDS", default=300)

# This daily sync refreshes region-level OVBM links
OVBM_SYNC = env.bool("OVBM_SYNC", False)
OVBM_SYNC_HOUR = env.int("OVBM_SYNC_HOUR", 4)
OVBM_SYNC_MINUTE = env.int("OVBM_SYNC_MINUTE", 30)

if OVBM_SYNC:
    CELERY_BEAT_SCHEDULE["trigger-ovbm-sync"] = {
        "task": "absentee.tasks.refresh_region_links",
        "schedule": crontab(minute=OVBM_SYNC_MINUTE, hour=OVBM_SYNC_HOUR),
    }

ABSENTEE_LOB_CONFIRM_NAG_SECONDS = env.int(
    "ABSENTEE_LOB_CONFIRM_NAG_SECONDS", default=300,
)

#### END ABSENTEE CONFIGURATION


#### SLACK DATA ERROR CONFIGURATION

SLACK_DATA_ERROR_ENABLED = env.bool("SLACK_DATA_ERROR_ENABLED", default=False)
SLACK_DATA_ERROR_WEBHOOK = env.str("SLACK_DATA_ERROR_WEBHOOK", default=None)
SLACK_SUBSCRIBER_INTEREST_ENABLED = env.bool(
    "SLACK_SUBSCRIBER_INTEREST_ENABLED", default=False
)
SLACK_SUBSCRIBER_INTEREST_WEBHOOK = env.str(
    "SLACK_SUBSCRIBER_INTEREST_WEBHOOK", default=None
)
SLACK_ALLOY_UPDATE_ENABLED = env.bool("SLACK_ALLOY_UPDATE_ENABLED", default=False)
SLACK_ALLOY_UPDATE_WEBHOOK = env.str("SLACK_ALLOY_UPDATE_WEBHOOK", default=None)

#### END SLACK DATA ERROR CONFIGURATION


#### FAX CONFIGURATION

FAX_DISABLE = env.bool("FAX_DISABLE", default=True)

FAX_OVERRIDE_DEST = env.str("FAX_OVERRIDE_DEST", default=None)

FAX_GATEWAY_CALLBACK_URL = env.str(
    "FAX_GATEWAY_CALLBACK_URL", default=f"{PRIMARY_ORIGIN}/fax/gateway_callback/"
)

FAX_GATEWAY_SQS_QUEUE = env.str("FAX_GATEWAY_SQS_QUEUE", default=None)

#### END FAX CONFIGURATION

#### ACTIONNETWORK CONFIGURATION

ACTIONNETWORK_KEY = env.str("ACTIONNETWORK_KEY", default=None)
ACTIONNETWORK_FORM_CACHE_TIMEOUT = env.int(
    "ACTIONNETWORK_FORM_CACHE_TIMEOUT", 24 * 60 * 60
)
ACTIONNETWORK_FORM_PREFIX = env.str("ACTIONNETWORK_FORM_PREFIX", "staging")

# This (daily?) sync is only to catch stragglers that don't sync in realtime.
ACTIONNETWORK_SYNC = env.bool("ACTIONNETWORK_SYNC", False)
ACTIONNETWORK_SYNC_DAILY = env.bool("ACTIONNETWORK_SYNC_DAILY", False)
ACTIONNETWORK_SYNC_HOUR = env.int("ACTIONNETWORK_SYNC_HOUR", 5)
ACTIONNETWORK_SYNC_MINUTE = env.int("ACTIONNETWORK_SYNC_MINUTE", 45)

# sleep between (batch) syncs
ACTIONNETWORK_SYNC_DELAY = env.float("ACTIONNETWORK_SYNC_DELAY", 0.5)

if ACTIONNETWORK_SYNC and ACTIONNETWORK_SYNC_DAILY:
    CELERY_BEAT_SCHEDULE["trigger-actionnetwork-sync"] = {
        "task": "integration.tasks.sync_actionnetwork",
        "schedule": crontab(
            minute=ACTIONNETWORK_SYNC_MINUTE, hour=ACTIONNETWORK_SYNC_HOUR
        ),
    }

#### END ACTIONNETWORK CONFIGURATION


#### MOVER CONFIGURATION

MOVER_LEADS_ENDPOINT = env.str("MOVER_LEADS_ENDPOINT", None)
MOVER_SOURCE = env.str("MOVER_SOURCE", None)
MOVER_ID = env.str("MOVER_ID", None)
MOVER_SECRET = env.str("MOVER_SECRET", None)
MOVER_PULL_INTERVAL_HOURS = env.int("MOVER_PULL_HOURS", 1)

if MOVER_ID and MOVER_PULL_INTERVAL_HOURS:
    CELERY_BEAT_SCHEDULE["trigger-sync-mover"] = {
        "task": "integration.tasks.sync_movers",
        "schedule": crontab(minute=5, hour=f"*/{MOVER_PULL_INTERVAL_HOURS}",),
    }
    CELERY_BEAT_SCHEDULE["trigger-send-movers-blank-register-forms"] = {
        "task": "integration.tasks.send_movers_blank_register_forms",
        "schedule": crontab(minute=35, hour=f"*/{MOVER_PULL_INTERVAL_HOURS}",),
    }

#### END MOVER CONFIGURATION


#### OPTIMIZELY CONFIGURATION

# Defaults to the "local development" environment
OPTIMIZELY_SDK_KEY = env.str("OPTIMIZELY_SDK_KEY", default="H9ZAgqK1oX4w3ZmzHLkVW6")
OPTIMIZELY_UPDATE_INTERVAL_SECONDS = env.int(
    "OPTIMIZELY_UPDATE_INTERVAL_SECONDS", default=30
)

#### END OPTIMIZELY CONFIGURATION


#### PA OVR CONFIGURATION

PA_OVR_KEY = env.str("PA_OVR_KEY", default=None)
PA_OVR_STAGING = env.bool("PA_OVR_STAGING", default=True)

#### END PA OVR CONFIGURATION


#### API CONFIGURATION

API_KEY_PEPPER = env.str("API_KEY_PEEPER", default="somepepper")

#### END API CONFIGURATION

#### UPTIME CONFIGURATION

UPTIME_ENABLED = env.bool("UPTIME_ENABLED", default=False)
UPTIME_CHECK_CRON_MINUTE = env.str("UPTIME_CHECK_CRON_MINUTE", default="*/15")
UPTIME_CHECK_DOWN_CRON_MINUTE = env.str("UPTIME_CHECK_DOWN_CRON_MINUTE", default="*/5")
UPTIME_TWITTER_CRON_MINUTE = env.str("UPTIME_TWITTER_CRON_MINUTE", default="*/5")

UPTIME_TWITTER_CONSUMER_KEY = env.str("UPTIME_TWITTER_CONSUMER_KEY", default=None)
UPTIME_TWITTER_CONSUMER_SECRET = env.str("UPTIME_TWITTER_CONSUMER_SECRET", default=None)
UPTIME_TWITTER_ACCESS_TOKEN = env.str("UPTIME_TWITTER_ACCESS_TOKEN", default=None)
UPTIME_TWITTER_ACCESS_TOKEN_SECRET = env.str(
    "UPTIME_TWITTER_ACCESS_TOKEN_SECRET", default=None
)

DIGITALOCEAN_KEY = env.str("DIGITALOCEAN_KEY", default=None)

PROXY_SSH_KEY = env.str("PROXY_SSH_KEY", default=None)
PROXY_SSH_PUB = env.str("PROXY_SSH_PUB", default=None)
PROXY_SSH_KEY_ID = env.int("PROXY_SSH_KEY_ID", default=None)
PROXY_COUNT = env.int("PROXY_COUNT", 5)
PROXY_TAG = env.str("PROXY_TAG", "env:dev")

SELENIUM_URL = env.str("SELENIUM_URL", None)

SLACK_UPTIME_WEBHOOK = env.str("SLACK_UPTIME_WEBHOOK", default=None)

if UPTIME_ENABLED:
    if UPTIME_CHECK_CRON_MINUTE:
        CELERY_BEAT_SCHEDULE["trigger-check-uptime"] = {
            "task": "leouptime.tasks.check_uptime",
            "schedule": crontab(minute=UPTIME_CHECK_CRON_MINUTE),
        }
        CELERY_BEAT_SCHEDULE["trigger-check-proxies"] = {
            "task": "leouptime.tasks.check_proxies",
            "schedule": crontab(minute=UPTIME_CHECK_CRON_MINUTE),
        }
    # if UPTIME_CHECK_DOWN_CRON_MINUTE:
    #    CELERY_BEAT_SCHEDULE["trigger-check-uptime-downsites"] = {
    #        "task": "leouptime.tasks.check_uptime_downsites",
    #        "schedule": crontab(minute=UPTIME_CHECK_CRON_MINUTE),
    #    }
    if UPTIME_TWITTER_CRON_MINUTE:
        CELERY_BEAT_SCHEDULE["trigger-tweet-uptime"] = {
            "task": "leouptime.tasks.tweet_uptime",
            "schedule": crontab(minute=UPTIME_TWITTER_CRON_MINUTE),
        }
elif DIGITALOCEAN_KEY:
    CELERY_BEAT_SCHEDULE["trigger-check-proxies"] = {
        "task": "leouptime.tasks.check_proxies",
        "schedule": crontab(minute=UPTIME_CHECK_CRON_MINUTE),
    }

#### END UPTIME CONFIGURATION

#### VOTER CONFIGURATION

# spread out lookups over time; max of N lookups every M minutes
VOTER_CHECK_INTERVAL_MINUTES = 7

# if a voter match fails, recheck it every few days
VOTER_RECHECK_INTERVAL_DAYS = 7

# give up eventually
VOTER_RECHECK_MAX_DAYS = 90

CELERY_BEAT_SCHEDULE["trigger-voter-check-new-actions"] = {
    "task": "voter.tasks.check_new_actions",
    "schedule": crontab(minute=f"*/{VOTER_CHECK_INTERVAL_MINUTES}"),
}
CELERY_BEAT_SCHEDULE["trigger-voter-recheck-old-actions"] = {
    "task": "voter.tasks.recheck_old_actions",
    "schedule": crontab(minute=f"*/{VOTER_CHECK_INTERVAL_MINUTES}"),
}

#### END VOTER CONFIGURATION

#### VERIFIER CONFIGURATION

VERIFIER_UPSELL_DELAY_SECONDS = env.int("VERIFIER_UPSELL_DELAY_SECONDS", default=60)

#### END VERIFIER CONFIGURATION

#### LOB CONFIGURATOIN

LOB_KEY = env.str("LOB_KEY", None)
LOB_LETTER_WEBHOOK_SECRET = env.str("LOB_LETTER_WEBHOOK_SECRET", None)
RETURN_ADDRESS = env.json(
    "RETURN_ADDRESS",
    '{"name": "VoteAmerica","address1": "PO BOX 123","city": "SAN FRANCISCO","state": "CA","zipcode": "12345"}',
)

#### END LOB CONFIGURATION

#### I90 CONFIGURATION

I90_KEY = env.str("I90_KEY", None)
I90_URL = env.str("I90_URL", "https://go.voteamerica.com")

#### END I90 CONFIGURATION

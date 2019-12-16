import environs

env = environs.Env()


SECRET_KEY = env.str("SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
USE_I18N = True
USE_L10N = True
WSGI_APPLICATION = "turnout.wsgi.application"
ROOT_URLCONF = "turnout.urls"


##### DATABASE CONFIGURATION

DATABASES = {"default": env.dj_db_url("DATABASE_URL")}

##### END DATABASE CONFIGURATION


##### CACHE CONFIGURATION

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://localhost:6379"),
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


THIRD_PARTY_APPS = []

FIRST_PARTY_APPS = []

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + FIRST_PARTY_APPS

##### END APPLICATION CONFIGURATION


##### MIDDLEWARE CONFIGURATION

MIDDLEWARE = [
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

#### END TEMPLATE CONFIGURATION


#### STATIC ASSET CONFIGURATION

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
STATICFILES_DIRS = (
    os.path.join(BASE_PATH, 'dist'),
)

#### END ASSET CONFIGURATION

#### AUTH CONFIGURATION

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

#### END AUTH CONFIGURATION


#### FILE CONFIGURATION

STATIC_URL = "/static/"

#### END FILE CONFIGURATION

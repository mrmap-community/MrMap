"""
Django settings for MrMap project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

import sys
from django.utils.translation import gettext_lazy as _
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from service.helper.enums import ConnectionEnum, OGCServiceVersionEnum, CategoryOriginEnum

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

GIT_REPO_URI = "https://git.osgeo.org/gitea/GDI-RP/MrMap/src/branch/pre_master"
GIT_GRAPH_URI = "https://git.osgeo.org/gitea/GDI-RP/MrMap/graph"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k7goig+64=-4ps7a(@-qqa(pdk^8+hq#1a9)^bn^m*j=ix-3j5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

HTTP_OR_SSL = "http://"
HOST_NAME = "127.0.0.1:8000"
HOST_IP = "127.0.0.1:8000"
# DEFINE ROOT URL FOR DYNAMIC AJAX REQUEST RESOLVING
ROOT_URL = HTTP_OR_SSL + HOST_NAME

EXEC_TIME_PRINT = "Exec time for %s: %1.5fs"

PAGE_SIZE_OPTIONS = [1, 3, 5, 10, 15, 20, 25, 30, 50, 75, 100, 200, 500]
PAGE_SIZE_DEFAULT = 5
PAGE_SIZE_MAX = 100
PAGE_DEFAULT = 1

CATEGORIES = {
    CategoryOriginEnum.INSPIRE.value: "https://www.eionet.europa.eu/gemet/getTopmostConcepts?thesaurus_uri=http://inspire.ec.europa.eu/theme/&language={}",
    CategoryOriginEnum.ISO.value: "http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/TopicCategory.{}.json",
}

CATEGORIES_LANG = {
    "locale_1": "de",
    "locale_2": "fr",
}

LICENCES = [
    {
        "name": "Creative Commons 3.0",
        "identifier": "cc-by-nc-nd-3.0",
        "symbol_url": "http://i.creativecommons.org/l/by-nc-nd/3.0/de/88x31.png",
        "description": "Creative Commons: Namensnennung - Keine kommerzielle Nutzung - Keine Bearbeitungen 3.0 Deutschland",
        "description_url": "http://creativecommons.org/licenses/by-nc-nd/3.0/de/",
        "is_open_data": False,
    },
    {
        "name": "Creative Commons 3.0",
        "identifier": "cc-nc-3.0",
        "symbol_url": "http://i.creativecommons.org/l/by-nc/3.0/de/88x31.png",
        "description": "Creative Commons: Namensnennung - Keine kommerzielle Nutzung 3.0 Deutschland",
        "description_url": "http://creativecommons.org/licenses/by-nc/3.0/de/",
        "is_open_data": False,
    },
    {
        "name": "Creative Commons 3.0",
        "identifier": "cc-by-3.0",
        "symbol_url": "http://i.creativecommons.org/l/by/3.0/de/88x31.png",
        "description": "Creative Commons: Namensnennung 3.0 Deutschland",
        "description_url": "http://creativecommons.org/licenses/by/3.0/de/",
        "is_open_data": True,
    },
    {
        "name": "Datenlizenz Deutschland 1.0",
        "identifier": "dl-de-by-nc-1.0",
        "symbol_url": None,
        "description": "Datenlizenz Deutschland – Namensnennung – nicht-kommerziell – Version 1.0",
        "description_url": "https://www.govdata.de/dl-de/by-nc-1-0",
        "is_open_data": False,
    },
    {
        "name": "Datenlizenz Deutschland 1.0",
        "identifier": "dl-de-by-1.0",
        "symbol_url": None,
        "description": "Datenlizenz Deutschland – Namensnennung – Version 1.0",
        "description_url": "https://www.govdata.de/dl-de/by-1-0",
        "is_open_data": True,
    },
    {
        "name": "Datenlizenz Deutschland 2.0",
        "identifier": "dl-de-zero-2.0",
        "symbol_url": None,
        "description": "Datenlizenz Deutschland – Zero – Version 2.0",
        "description_url": "https://www.govdata.de/dl-de/zero-2-0",
        "is_open_data": True,
    },
    {
        "name": "Datenlizenz Deutschland 2.0",
        "identifier": "dl-de-by-2.0",
        "symbol_url": None,
        "description": "Datenlizenz Deutschland Namensnennung 2.0",
        "description_url": "https://www.govdata.de/dl-de/by-2-0",
        "is_open_data": True,
    },
    {
        "name": "Open Data Commons Open Database License",
        "identifier": "odc-odbl-1.0",
        "symbol_url": None,
        "description": "Open Data Commons Open Database License (ODbL)",
        "description_url": "http://opendatacommons.org/licenses/odbl/1.0/",
        "is_open_data": True,
    },
]

XML_NAMESPACES = {
    "ogc": "http://www.opengis.net/ogc",
    "ows": "http://www.opengis.net/ows",
    "wfs": "http://www.opengis.net/wfs",
    "wms": "http://www.opengis.net/wms",
    "xlink": "http://www.w3.org/1999/xlink",
    "gml": "http://www.opengis.net/gml",
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "srv": "http://www.isotc211.org/2005/srv",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ave": "http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/1.0",
    "inspire_common": "http://inspire.ec.europa.eu/schemas/common/1.0",
    "inspire_com": "http://inspire.ec.europa.eu/schemas/common/1.0",
    "inspire_vs": "http://inspire.ec.europa.eu/schemas/inspire_vs/1.0",
    "inspire_ds": "http://inspire.ec.europa.eu/schemas/inspire_ds/1.0",
    "inspire_dls": "http://inspire.ec.europa.eu/schemas/inspire_dls/1.0",
    "epsg": "urn:x-ogp:spec:schema-xsd:EPSG:1.0:dataset",
    "ms": "http://mapserver.gis.umn.edu/mapserver",
    "se": "http://www.opengis.net/se",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "sld": "http://www.opengis.net/sld",
    "fes": "http://www.opengis.net/fes/2.0",
}
GENERIC_NAMESPACE_TEMPLATE = "*[local-name()='{}']"

# Home/Dashboard settings
LAST_ACTIVITY_DATE_RANGE = 7

# Threshold which indicates when to use multithreading instead of iterative approaches
MULTITHREADING_THRESHOLD = 2000

# configure your proxy like "http://10.0.0.1:8080"
# or with username and password: "http://username:password@10.0.0.1:8080"
HTTP_PROXY = ""

PROXIES = {
    "http": HTTP_PROXY,
    "https": HTTP_PROXY,
}

ALLOWED_HOSTS = [
    HOST_NAME,
    "127.0.0.1",
]

# Application definition
INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.gis',
    'formtools',
    'service',
    'users',
    'structure',
    'django_extensions',
    'editor',
    'captcha',
    'rest_framework',
    'rest_framework.authtoken',
    'api',
    'csw',
    'django_celery_beat',
    'monitoring',
    'bootstrap4',
    'fontawesome_5',
    'django_tables2',
    'django_filters',
    'query_parameters',
    'django_nose',
    'mathfilters',
]
if DEBUG:
    INSTALLED_APPS.append(
        'debug_toolbar',
    )
    # Disable all panels by default
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": {
            'debug_toolbar.panels.versions.VersionsPanel',
            'debug_toolbar.panels.timer.TimerPanel',
            'debug_toolbar.panels.settings.SettingsPanel',
            'debug_toolbar.panels.headers.HeadersPanel',
            'debug_toolbar.panels.request.RequestPanel',
            'debug_toolbar.panels.sql.SQLPanel',
            'debug_toolbar.panels.staticfiles.StaticFilesPanel',
            'debug_toolbar.panels.templates.TemplatesPanel',
            'debug_toolbar.panels.cache.CachePanel',
            'debug_toolbar.panels.signals.SignalsPanel',
            'debug_toolbar.panels.logging.LoggingPanel',
            'debug_toolbar.panels.redirects.RedirectsPanel',
            'debug_toolbar.panels.profiling.ProfilingPanel',
        }
    }

# Holds all apps which needs migrations. Will be used in command 'dev_makemigrations'
# If you added a new app with models, which need to be migrated, you have to put the app's name in this list
MIGRATABLE_APPS = [
    'csw',
    'structure',
    'service',
    'users',
    'monitoring',
]

TEMPLATE_LOADERS = (
    'django.template.loaders.structure.mr_map_filters.py',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dealer.contrib.django.Middleware',
]

# Password hashes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

ROOT_URLCONF = 'MrMap.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR + "/templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dealer.contrib.django.context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'MrMap.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'MrMap',
        'USER': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Cache
# Use local redis installation as cache
# The "regular" redis cache will be set to work in redis table 1 (see LOCATION)
# The default table (0) is preserved for celery task management
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        }
    }
}

# Session settings and password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

MIN_PASSWORD_LENGTH = 9
MIN_USERNAME_LENGTH = 5  # ToDo: For production use another, more appropriate length!

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            "min_length": MIN_PASSWORD_LENGTH,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
AUTH_USER_MODEL = 'structure.MrMapUser'
SESSION_COOKIE_AGE = 30 * 60  # Defines how many seconds can pass until the session expires, default is 30 * 60
SESSION_SAVE_EVERY_REQUEST = True  # Whether the session age will be refreshed on every request or only if data has been modified
LOGIN_URL = "/"  # Defines where to redirect a user, that has to be logged in for a certain route

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', _('English')),
    ('de', _('German')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

DEFAULT_DATE_TIME_FORMAT = 'YYYY-MM-DD hh:mm:ss'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# CELERY SETTINGS
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# API
from api.settings import REST_FRAMEWORK

RESPONSE_CACHE_TIME = 60 * 30  # 30 minutes

# Tests
if 'test' in sys.argv:
    CAPTCHA_TEST_MODE = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--with-xunit',
    '--xunit-file=tests/nosetests.xml',
    '--with-coverage',
    '--cover-erase',
    '--cover-xml',
    '--cover-xml-file=nosecover.xml',
]

# Progress bar
PROGRESS_STATUS_AFTER_PARSING = 90  # indicates at how much % status we are after the parsing

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + "/static/"
STATICFILES_DIRS = [
    BASE_DIR + '/MrMap/static',
]

# define the message tags for bootstrap4
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

MONITORING_TIME = "23:59:00"
MONITORING_REQUEST_TIMEOUT = 30  # seconds

# DJANGO DEBUG TOOLBAR
# Add the IP for which the toolbar should be shown
INTERNAL_IPS = [
    "127.0.0.1"
]

# DEALER Settings
DEALER_PATH = BASE_DIR

# django logging settings
import logging

root_logger = logging.getLogger('MrMap.root')

LOG_DIR = BASE_DIR + '/logs'
LOG_SUB_DIRS = {
    'root': {'dir': '/root', 'log_file': 'root.log'},
    'api': {'dir': '/api', 'log_file': 'api.log'},
    'csw': {'dir': '/csw', 'log_file': 'csw.log'},
    'editor': {'dir': '/editor', 'log_file': 'rooeditorog'},
    'monitoring': {'dir': '/monitoring', 'log_file': 'monitoring.log'},
    'service': {'dir': '/service', 'log_file': 'service.log'},
    'structure': {'dir': '/structure', 'log_file': 'structure.log'},
    'users': {'dir': '/users', 'log_file': 'users.log'},
}
LOG_FILE_MAX_SIZE = 1024 * 1024 * 20  # 20 MB
LOG_FILE_BACKUP_COUNT = 5

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'MrMap.root.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['root']['dir'] + '/' + LOG_SUB_DIRS['root']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.api.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['api']['dir'] + '/' + LOG_SUB_DIRS['api']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.csw.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['csw']['dir'] + '/' + LOG_SUB_DIRS['csw']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.editor.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['editor']['dir'] + '/' + LOG_SUB_DIRS['editor']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.monitoring.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['monitoring']['dir'] + '/' + LOG_SUB_DIRS['monitoring']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.service.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['service']['dir'] + '/' + LOG_SUB_DIRS['service']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.structure.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['structure']['dir'] + '/' + LOG_SUB_DIRS['structure']['log_file'],
            'formatter': 'verbose',
        },
        'MrMap.users.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': LOG_FILE_MAX_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'filename': LOG_DIR + LOG_SUB_DIRS['users']['dir'] + '/' + LOG_SUB_DIRS['users']['log_file'],
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'MrMap.root': {
            'handlers': ['MrMap.root.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.api': {
            'handlers': ['MrMap.api.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.csw': {
            'handlers': ['MrMap.csw.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.editor': {
            'handlers': ['MrMap.editor.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.monitoring': {
            'handlers': ['MrMap.monitoring.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.service': {
            'handlers': ['MrMap.service.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.structure': {
            'handlers': ['MrMap.structure.file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'MrMap.users': {
            'handlers': ['MrMap.users.file', ],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

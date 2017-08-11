# Django settings for prints project.

import os.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')

DEBUG = os.environ.has_key('DEBUG')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Hostmaster', 'hostmaster@test.com'),
)

MANAGERS = ADMINS

SITE_ID = 1


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_NAME', 'publications.sqlite'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TIME_ZONE = 'Europe/Ljubljana'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = os.environ.get('DJANGO_MEDIA_ROOT', os.path.join(ROOT_DIR, 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = os.environ.get('DJANGO_STATIC_ROOT', os.path.join(ROOT_DIR, "static"))
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATICFILES_DIRS = ()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = 'replace this with something secret'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

ROOT_URLCONF = 'publications.urls'

TEMPLATE_DIRS = (
    os.path.join(ROOT_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'taggit',
    'publications',
    'publications_bibtex',
    'django_extensions'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

if os.environ.has_key('LOG_FILE'):
  LOGGING['handlers']['log_file'] = {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.environ['LOG_FILE'],
        }
  LOGGING['loggers']['django.request']['handlers'].append('log_file')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

PUBLICATIONS_IMPORTERS = (
  'publications_bibtex.BibTeXImporter',
  )

PUBLICATIONS_EXPORTERS = (
  'publications_bibtex.BibTeXExporter',
  )

PUBLICATIONS_USE_XSENDFILE = True


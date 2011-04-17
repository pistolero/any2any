# Django settings for test_djangocast project.
import sys
import os

sys.path.append(os.path.abspath("../../.."))

ADMINS = ()

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'test.sqlite3',                 # Or path to database file if using sqlite3.
    }
}

ROOT_URLCONF = 'tests.urls'

INSTALLED_APPS = (
    'djangocast_tests.models',
    'django.contrib.contenttypes',
    'django_nose',
)

TEMPLATE_DIRS = (
    'templates',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

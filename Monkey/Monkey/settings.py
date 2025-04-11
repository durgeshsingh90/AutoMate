"""
Django settings for Monkey project.
Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# Add these settings at the end of the file
DATA_UPLOAD_MAX_NUMBER_FILES = 1000  # Set this to a value higher than the number of files you expect

# Create a directory for logs
LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the directory exists


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-w^xj)79i&kxnzmzif7q#des^2hfpz^$hcv+7&k831j$7(un=59'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'home',
    'slot_booking',
    'splunkparser',
    'binblock',
    'pdf_merger',
    'gen_reversals',
    'astrex_html_logs',
    'emvco_logs',
    # 'xml_logs',
    'oracle_query_executor',
    'validate_testcase',

    ]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'django.log'),  # Dynamic path for the log file
            # 'maxBytes': 10240,  # Set max file size to 10KB (~100 lines depending on log content)
            # 'backupCount': 5,  # Keep up to 5 backup log files
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {  # 'root' logger
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Monkey.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'html')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Monkey.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Define the path to the Oracle Instant Client libraries
ORACLE_CLIENT_PATH = r'C:\Oracle\Ora12c_64\BIN'

DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'dr_ist': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'A4PCDO8001.ESH.PAR_IST',
        'USER': 'F94GDOS',
        'PASSWORD': 'Ireland2025!',
        'HOST': '',
        'PORT': '',
        'client_path': ORACLE_CLIENT_PATH,
    },
    'prod_ist': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'A5PCDO8001.EQU.IST',
        'USER': 'F94GDOS',
        'PASSWORD': 'Ireland2025!',
        'HOST': '',
        'PORT': '',
        'client_path': ORACLE_CLIENT_PATH,
    },
    'uat_ist': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'ISTU2_EQU',
        'USER': 'oasis77',
        'PASSWORD': 'ist0py',
        'HOST': '',
        'PORT': '',
        'client_path': ORACLE_CLIENT_PATH,
    },
    'uat_novate': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'ISTU2',
        'USER': 'novate',
        'PASSWORD': 'nov1234',
        'HOST': '',
        'PORT': '',
        'client_path': ORACLE_CLIENT_PATH,
    },
    'uat_novate_conf': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'ISTU2',
        'USER': 'novate_conf',
        'PASSWORD': 'nov1234',
        'HOST': '',
        'PORT': '',
        'client_path': ORACLE_CLIENT_PATH,
    }
}

# Other settings...


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# Define the directory where collectstatic will collect all static files
STATIC_ROOT = BASE_DIR / "staticfiles"  # or os.path.join(BASE_DIR, 'staticfiles')

# Additional directories for static files from different apps
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "home/static",
    BASE_DIR / "splunkparser/static",
    BASE_DIR / "binblock/static",
    BASE_DIR / "slot_booking/static",
    BASE_DIR / "gen_reversals/static",
    BASE_DIR / "astrex_html_logs/static",
    # BASE_DIR / "emvco_logs/static",
    # BASE_DIR / "xml_logs/static",
    BASE_DIR / "oracle_query_executor/static",
    BASE_DIR / "validate_testcase/static",


    
    # Add other app static directories as needed
]

# Add a location for media uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

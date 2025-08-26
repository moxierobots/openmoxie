"""
Production settings for openmoxie project.

This file contains settings specific to the production environment.
"""

from .base import *
from decouple import config, Csv

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Allowed hosts must be explicitly defined in production
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Force HTTPS in production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = 'openmoxie_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# CSRF security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_NAME = 'openmoxie_csrftoken'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Database configuration for production
DATABASES['default'].update({
    'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
    'OPTIONS': {
        'connect_timeout': 10,
        'sslmode': config('DB_SSLMODE', default='disable'),
    }
})

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND',
            default='django.core.cache.backends.redis.RedisCache'
        ),
        'LOCATION': config('CACHE_LOCATION', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'openmoxie_prod',
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
    }
}

# Static files configuration for production
STATIC_ROOT = config('STATIC_ROOT', default='/var/www/openmoxie/static')
STATIC_URL = config('STATIC_URL', default='/static/')

# Media files configuration for production
MEDIA_ROOT = config('MEDIA_ROOT', default='/var/www/openmoxie/media')
MEDIA_URL = config('MEDIA_URL', default='/media/')

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@openmoxie.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@openmoxie.com')
ADMINS = [
    (admin.split(':')[0], admin.split(':')[1])
    for admin in config('ADMINS', default='', cast=Csv())
    if ':' in admin
]

# Sentry configuration for production
SENTRY_ENVIRONMENT = 'production'
SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float)
SENTRY_PROFILES_SAMPLE_RATE = config('SENTRY_PROFILES_SAMPLE_RATE', default=0.1, cast=float)
SENTRY_SEND_DEFAULT_PII = False

LOGGING['handlers']['sentry'] = {
    'level': 'ERROR',
    'class': 'sentry_sdk.integrations.logging.EventHandler',
}

LOGGING['root']['handlers'] = ['console', 'sentry']
LOGGING['loggers']['django']['handlers'] = ['console']
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['hive']['level'] = 'INFO'
LOGGING['loggers']['django.request']['handlers'] = ['sentry']
LOGGING['loggers']['django.security']['handlers'] = ['sentry']

# Limit file upload sizes in production
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = config('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=1000, cast=int)

# Rate limiting configuration
RATELIMIT_ENABLE = True

# Production-specific MQTT settings
MQTT_ENDPOINT.update({
    'cert_required': config('MQTT_CERT_REQUIRED', default=True, cast=bool),
    'ca_certs': config('MQTT_CA_CERTS', default='/etc/ssl/certs/ca-certificates.crt'),
    'certfile': config('MQTT_CERTFILE', default=''),
    'keyfile': config('MQTT_KEYFILE', default=''),
})

# Performance optimizations
CONN_MAX_AGE = 600
CONN_HEALTH_CHECKS = True

# Compress static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

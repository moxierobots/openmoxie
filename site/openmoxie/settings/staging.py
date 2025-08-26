"""
Staging settings for openmoxie project.

This file contains settings specific to the staging environment.
Staging is similar to production but with some relaxed constraints for testing.
"""

from .base import *
from decouple import config, Csv

# Debug mode off in staging, but can be overridden for testing
DEBUG = config('DEBUG', default=False, cast=bool)

# Secret key for staging
SECRET_KEY = config('SECRET_KEY')

# Allowed hosts for staging
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Force HTTPS in staging (can be disabled for testing)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security Headers (slightly relaxed for staging)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=3600, cast=int)  # 1 hour
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Session security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_NAME = 'openmoxie_staging_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF security
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_NAME = 'openmoxie_staging_csrftoken'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Database configuration for staging
DATABASES['default'].update({
    'HOST': config('DB_HOST', default='localhost'),
    'PORT': config('DB_PORT', default=5432, cast=int),
    'USER': config('DB_USER', default='openmoxie_staging'),
    'PASSWORD': config('DB_PASSWORD'),
    'NAME': config('DB_NAME', default='openmoxie_staging'),
    'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=300, cast=int),
    'OPTIONS': {
        'connect_timeout': 10,
        'sslmode': config('DB_SSLMODE', default='prefer'),
    }
})

# Cache configuration for staging
CACHES = {
    'default': {
        'BACKEND': config(
            'CACHE_BACKEND',
            default='django.core.cache.backends.redis.RedisCache'
        ),
        'LOCATION': config('CACHE_LOCATION', default='redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 25,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'openmoxie_staging',
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
    }
}

# Static files configuration for staging
STATIC_ROOT = config('STATIC_ROOT', default='/var/www/openmoxie-staging/static')
STATIC_URL = config('STATIC_URL', default='/static/')

# Media files configuration for staging
MEDIA_ROOT = config('MEDIA_ROOT', default='/var/www/openmoxie-staging/media')
MEDIA_URL = config('MEDIA_URL', default='/media/')

# Email configuration for staging
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@staging.openmoxie.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@staging.openmoxie.com')
ADMINS = [
    (admin.split(':')[0], admin.split(':')[1])
    for admin in config('ADMINS', default='', cast=Csv())
    if ':' in admin
]

# Sentry configuration for staging
SENTRY_ENVIRONMENT = 'staging'
SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.5, cast=float)
SENTRY_PROFILES_SAMPLE_RATE = config('SENTRY_PROFILES_SAMPLE_RATE', default=0.5, cast=float)
SENTRY_SEND_DEFAULT_PII = config('SENTRY_SEND_PII', default=False, cast=bool)

# Staging logging configuration
LOGGING['handlers']['file'] = {
    'level': 'WARNING',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': config('LOG_FILE', default='/var/log/openmoxie-staging/django.log'),
    'maxBytes': 1024 * 1024 * 50,  # 50 MB
    'backupCount': 5,
    'formatter': 'verbose',
}

LOGGING['handlers']['sentry'] = {
    'level': 'WARNING',
    'class': 'sentry_sdk.integrations.logging.EventHandler',
}

LOGGING['root']['handlers'] = ['console', 'file', 'sentry']
LOGGING['loggers']['django']['handlers'] = ['console', 'file']
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['hive']['level'] = config('HIVE_LOG_LEVEL', default='INFO')
LOGGING['loggers']['django.request']['handlers'] = ['file', 'sentry']
LOGGING['loggers']['django.security']['handlers'] = ['file', 'sentry']

# Allow debug toolbar in staging if explicitly enabled
if config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool):
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = config('INTERNAL_IPS', default='127.0.0.1', cast=Csv())

# File upload limits for staging
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = config('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=2000, cast=int)

# Rate limiting configuration (more lenient than production)
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)

# Staging-specific MQTT settings
MQTT_ENDPOINT.update({
    'cert_required': config('MQTT_CERT_REQUIRED', default=False, cast=bool),
    'ca_certs': config('MQTT_CA_CERTS', default=''),
    'certfile': config('MQTT_CERTFILE', default=''),
    'keyfile': config('MQTT_KEYFILE', default=''),
})

# Performance optimizations (less aggressive than production)
CONN_MAX_AGE = 300
CONN_HEALTH_CHECKS = True

# Template caching (optional in staging)
if config('ENABLE_TEMPLATE_CACHE', default=True, cast=bool):
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]

# Static files storage
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

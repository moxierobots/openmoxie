"""
Development settings for openmoxie project.

This file contains settings specific to the development environment.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
# In development, we can use a default key, but it should be overridden in production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-v&n3hpdmu^t0r^62+hj64&c$z8q3o2g9qby^x02jl8y8g@jmb@')

ALLOWED_HOSTS = ['*']

# Development-specific installed apps
INSTALLED_APPS += [
    'debug_toolbar',
]

# Development-specific middleware
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug Toolbar Configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
]

# Allow all origins in development (configure properly in production)
CORS_ALLOW_ALL_ORIGINS = True

# Database configuration for development - using SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files configuration for development
STATICFILES_DIRS = [
    BASE_DIR / 'static_dev',
] if (BASE_DIR / 'static_dev').exists() else []

# WhiteNoise configuration for development
WHITENOISE_AUTOREFRESH = True  # Auto-refresh static files in development
WHITENOISE_USE_FINDERS = True  # Use Django's static file finders
WHITENOISE_COMPRESS_OFFLINE = False  # Don't compress in development

# Media files configuration for development
MEDIA_ROOT = BASE_DIR / 'media_dev'

# Email backend for development (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable security features in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Cache configuration for development (dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Sentry configuration for development
# Usually disabled in development unless testing Sentry integration
SENTRY_ENVIRONMENT = 'development'
SENTRY_TRACES_SAMPLE_RATE = 0.0  # Disable performance monitoring in development
SENTRY_PROFILES_SAMPLE_RATE = 0.0  # Disable profiling in development

# Development logging configuration
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['hive']['level'] = 'DEBUG'

# Show SQL queries in console during development
if DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }

# Disable rate limiting in development
RATELIMIT_ENABLE = False

# Development-specific MQTT settings
MQTT_ENDPOINT.update({
    'cert_required': False,
})

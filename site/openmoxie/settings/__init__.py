"""
Django settings module that automatically selects the appropriate configuration
based on the DJANGO_ENV environment variable.
"""

import os
from pathlib import Path

# Determine which settings module to use based on environment
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import * #noqa
elif env == 'staging':
    from .staging import * #noqa
else:
    from .development import *

# Export commonly used paths
__all__ = ['BASE_DIR', 'DATA_STORE_DIR']

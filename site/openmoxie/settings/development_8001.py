"""
Development settings for openmoxie project on port 8001.

This file extends the base development settings to run on port 8001.
"""

from .development import *

# Override the default port for runserver command
import sys
if 'runserver' in sys.argv:
    # Set default port to 8001 if not specified
    if len(sys.argv) == 2 or (len(sys.argv) > 2 and not sys.argv[2].startswith('0.0.0.0:') and not sys.argv[2].startswith('127.0.0.1:') and not sys.argv[2].startswith('localhost:')):
        # Insert port 8001 as default
        if len(sys.argv) == 2:
            sys.argv.append('0.0.0.0:8001')
        elif not ':' in sys.argv[2]:
            # If just IP is specified, add port
            sys.argv[2] = sys.argv[2] + ':8001'

# Additional allowed hosts for port 8001
ALLOWED_HOSTS += [
    'localhost:8001',
    '127.0.0.1:8001',
    '0.0.0.0:8001',
]

# Update any URLs or configurations that might reference the port
# This ensures consistency across the application
SITE_URL = 'http://localhost:8001'

"""
Passenger WSGI entrypoint for IICE-CRM (DirectAdmin).
Sets DJANGO_SETTINGS_MODULE to production settings and exposes the WSGI `application`.
"""

import os
import sys
from pathlib import Path

# App Root is the project directory that contains manage.py and the IICE package
APP_ROOT = Path(__file__).resolve().parents[1]

# Ensure App Root is on sys.path so imports like `IICE.settings_production` work
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Optionally ensure the IICE package directory is also on sys.path
IICE_DIR = APP_ROOT / "IICE"
if str(IICE_DIR) not in sys.path:
    sys.path.insert(0, str(IICE_DIR))

# Use production settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IICE.settings_production")

# Create the WSGI application callable expected by Passenger/DirectAdmin
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
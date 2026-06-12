import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Add the IICE package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IICE'))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')

# Import Django and get the WSGI application
import django
from django.core.wsgi import get_wsgi_application

django.setup()
application = get_wsgi_application()
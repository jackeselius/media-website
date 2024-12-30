"""
WSGI config for MediaWebsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MediaWebsite.settings')

application = get_wsgi_application()

sys.path.append('/var/www/MediaWebsite/')
sys.path.append('/var/www/MediaWebsite/MediaWebsite')
sys.path.append('/var/www/MediaWebsite/mediasite_env/lib/python3.8/site-packages')

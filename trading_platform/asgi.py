"""
ASGI config for trading_platform project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_platform.settings')

application = get_asgi_application()

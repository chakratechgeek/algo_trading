"""
URL configuration for trading_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView
from core.views import home_view

# Force trading admin import
import trading.admin

# Force admin autodiscovery
admin.autodiscover()

def empty_favicon(request):
    """Return empty response for favicon requests to prevent 404s."""
    return HttpResponse(status=204)

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/angel/', include('angel_api.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/trading/', include('trading.urls')),
    path('api/core/', include('core.urls')),
    path('favicon.ico', empty_favicon),  # Prevent favicon 404s
]

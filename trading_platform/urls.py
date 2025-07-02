"""
URL configuration for trading_platform project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/angel/', include('angel_api.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/trading/', include('trading.urls')),
    path('api/core/', include('core.urls')),
]

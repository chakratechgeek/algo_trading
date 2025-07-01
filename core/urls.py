"""Core URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'logs', views.LogEntryViewSet)
router.register(r'config', views.ConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('market-status/', views.MarketStatusView.as_view(), name='market-status'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]

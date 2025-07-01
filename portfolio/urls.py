"""Portfolio URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'portfolios', views.PortfolioViewSet)
router.register(r'trades', views.TradeViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'sessions', views.TradingSessionViewSet)
router.register(r'watchlists', views.WatchListViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('summary/', views.PortfolioSummaryView.as_view(), name='portfolio-summary'),
    path('alerts/', views.AlertsView.as_view(), name='portfolio-alerts'),
]

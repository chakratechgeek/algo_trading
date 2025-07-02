"""Angel API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .url_manager import URLConfigManagerView

router = DefaultRouter()
router.register(r'symbols', views.NSESymbolViewSet)
router.register(r'market-data', views.MarketDataViewSet)
router.register(r'orders', views.OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('setup/', views.AngelOneSetupView.as_view(), name='angel-setup'),
    path('auth/', views.AuthenticationView.as_view(), name='angel-auth'),
    path('auth/callback/', views.AuthCallbackView.as_view(), name='angel_callback'),
    path('ngrok-setup/', views.NgrokSetupView.as_view(), name='ngrok-setup'),
    path('url-config/', URLConfigManagerView.as_view(), name='url-config'),
    path('ltp/<str:symbol>/', views.LTPView.as_view(), name='ltp'),
    path('portfolio/', views.PortfolioView.as_view(), name='angel-portfolio'),
    path('balance/', views.BalanceView.as_view(), name='angel-balance'),
    path('place-order/', views.PlaceOrderView.as_view(), name='place-order'),
]

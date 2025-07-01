"""Angel API URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'symbols', views.NSESymbolViewSet)
router.register(r'market-data', views.MarketDataViewSet)
router.register(r'orders', views.OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', views.AuthenticationView.as_view(), name='angel-auth'),
    path('ltp/<str:symbol>/', views.LTPView.as_view(), name='ltp'),
    path('portfolio/', views.PortfolioView.as_view(), name='angel-portfolio'),
    path('balance/', views.BalanceView.as_view(), name='angel-balance'),
    path('place-order/', views.PlaceOrderView.as_view(), name='place-order'),
]

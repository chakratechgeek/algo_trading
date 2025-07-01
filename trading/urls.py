"""Trading URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'strategies', views.TradingStrategyViewSet)
router.register(r'bots', views.TradingBotViewSet)
router.register(r'signals', views.TradingSignalViewSet)
router.register(r'executions', views.TradingExecutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('bot/<int:bot_id>/run/', views.RunBotView.as_view(), name='run-bot'),
    path('bot/<int:bot_id>/stop/', views.StopBotView.as_view(), name='stop-bot'),
    path('bot/<int:bot_id>/performance/', views.BotPerformanceView.as_view(), name='bot-performance'),
    path('create-bot/', views.CreateBotView.as_view(), name='create-bot'),
    path('generate-signals/', views.GenerateSignalsView.as_view(), name='generate-signals'),
]

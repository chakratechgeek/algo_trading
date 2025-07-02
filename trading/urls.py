"""Trading URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .monitoring_views import trading_monitor_dashboard, execution_details, live_monitoring_feed

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
    
    # Detailed monitoring dashboard
    path('monitor/', trading_monitor_dashboard, name='trading-monitor'),
    path('execution/<int:execution_id>/details/', execution_details, name='execution-details'),
    path('live-feed/', live_monitoring_feed, name='live-feed'),
]

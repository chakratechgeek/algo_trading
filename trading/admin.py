"""Trading app admin configurations - WORKING VERSION."""

from django.contrib import admin
from .models import (
    TradingStrategy, TradingBot, TradingSignal, 
    TradingExecution, MarketAnalysis, NewsAnalysis
)

@admin.register(TradingStrategy)
class TradingStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'strategy_type', 'is_active', 'total_trades', 'created_at']
    list_filter = ['strategy_type', 'is_active']
    search_fields = ['name']

@admin.register(TradingBot)
class TradingBotAdmin(admin.ModelAdmin):
    list_display = ['name', 'portfolio', 'strategy', 'is_active', 'last_run_at']
    list_filter = ['is_active', 'strategy']
    search_fields = ['name']

@admin.register(TradingSignal)
class TradingSignalAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'signal_type', 'strategy', 'confidence', 'is_executed', 'created_at']
    list_filter = ['signal_type', 'is_executed', 'strategy']
    search_fields = ['symbol__symbol']

@admin.register(TradingExecution)
class TradingExecutionAdmin(admin.ModelAdmin):
    """Main 10-minute execution monitoring view."""
    list_display = ['bot', 'signal', 'execution_type', 'status', 'quantity', 'created_at']
    list_filter = ['execution_type', 'status']
    search_fields = ['bot__name']
    date_hierarchy = 'created_at'

@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'analysis_date', 'current_price', 'recommendation']
    list_filter = ['recommendation', 'analysis_date']
    search_fields = ['symbol__symbol']

@admin.register(NewsAnalysis)
class NewsAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'sentiment', 'published_at']
    list_filter = ['sentiment']
    search_fields = ['symbol__symbol', 'headline']

print("✅ Trading admin loaded successfully!")

"""Trading admin configuration."""

from django.contrib import admin
from .models import (
    TradingStrategy, TradingBot, TradingSignal, TradingExecution,
    MarketAnalysis, NewsAnalysis
)


@admin.register(TradingStrategy)
class TradingStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'strategy_type', 'is_active', 'total_trades', 'total_pnl']
    list_filter = ['strategy_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TradingBot)
class TradingBotAdmin(admin.ModelAdmin):
    list_display = ['name', 'portfolio', 'strategy', 'is_active', 'last_run_at', 'total_runs']
    list_filter = ['is_active', 'is_paper_trading', 'created_at']
    search_fields = ['name', 'portfolio__user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_run_at', 'total_runs', 'error_count']


@admin.register(TradingSignal)
class TradingSignalAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'signal_type', 'confidence', 'entry_price', 'is_executed', 'created_at']
    list_filter = ['signal_type', 'signal_strength', 'is_executed', 'is_active', 'created_at']
    search_fields = ['symbol__symbol', 'strategy__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(TradingExecution)
class TradingExecutionAdmin(admin.ModelAdmin):
    list_display = ['bot', 'signal', 'execution_type', 'quantity', 'status', 'created_at']
    list_filter = ['execution_type', 'status', 'created_at']
    search_fields = ['bot__name', 'signal__symbol__symbol']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MarketAnalysis)
class MarketAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'analysis_date', 'current_price', 'recommendation', 'confidence_score']
    list_filter = ['recommendation', 'analysis_date']
    search_fields = ['symbol__symbol']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NewsAnalysis)
class NewsAnalysisAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'headline', 'sentiment', 'market_impact', 'published_at']
    list_filter = ['sentiment', 'market_impact', 'is_processed', 'published_at']
    search_fields = ['symbol__symbol', 'headline', 'source']
    readonly_fields = ['created_at', 'updated_at']

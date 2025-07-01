"""Portfolio admin configuration."""

from django.contrib import admin
from .models import Portfolio, Trade, Position, TradingSession, WatchList, WatchListItem


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'current_balance', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'symbol', 'action', 'quantity', 'price', 'profit', 'created_at']
    list_filter = ['action', 'status', 'created_at', 'portfolio']
    search_fields = ['symbol__symbol', 'portfolio__user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'symbol', 'total_quantity', 'average_price', 'unrealized_pnl', 'is_open']
    list_filter = ['is_open', 'created_at', 'portfolio']
    search_fields = ['symbol__symbol', 'portfolio__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TradingSession)
class TradingSessionAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'session_date', 'starting_balance', 'total_pnl', 'is_active']
    list_filter = ['is_active', 'session_date']
    search_fields = ['portfolio__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WatchList)
class WatchListAdmin(admin.ModelAdmin):
    list_display = ['name', 'portfolio', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'portfolio__user__username']


@admin.register(WatchListItem)
class WatchListItemAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'watchlist', 'target_price', 'priority', 'is_active']
    list_filter = ['priority', 'is_active', 'watchlist']
    search_fields = ['symbol__symbol', 'watchlist__name']

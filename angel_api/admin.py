"""Angel API admin configuration."""

from django.contrib import admin
from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order


@admin.register(AngelOneSession)
class AngelOneSessionAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'is_active', 'session_expiry', 'created_at')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NSESymbol)
class NSESymbolAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'exchange', 'instrument_type', 'lot_size')
    list_filter = ('exchange', 'instrument_type')
    search_fields = ('symbol', 'company_name')


@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'ltp', 'change_percent', 'volume', 'data_timestamp')
    list_filter = ('data_timestamp', 'symbol')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'method', 'status_code', 'response_time_ms', 'created_at')
    list_filter = ('method', 'status_code', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'symbol', 'transaction_type', 'quantity', 'price', 'status')
    list_filter = ('transaction_type', 'status', 'order_type')
    search_fields = ('order_id', 'symbol__symbol')

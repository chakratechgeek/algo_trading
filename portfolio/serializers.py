"""Portfolio serializers."""

from rest_framework import serializers
from .models import Portfolio, Trade, Position, TradingSession, WatchList, WatchListItem


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for portfolio."""
    username = serializers.CharField(source='user.username', read_only=True)
    total_pnl = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_invested = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    open_positions_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Portfolio
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user']


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for trades."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    portfolio_user = serializers.CharField(source='portfolio.user.username', read_only=True)
    
    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for positions."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    portfolio_user = serializers.CharField(source='portfolio.user.username', read_only=True)
    
    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TradingSessionSerializer(serializers.ModelSerializer):
    """Serializer for trading sessions."""
    portfolio_user = serializers.CharField(source='portfolio.user.username', read_only=True)
    
    class Meta:
        model = TradingSession
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WatchListSerializer(serializers.ModelSerializer):
    """Serializer for watchlists."""
    portfolio_user = serializers.CharField(source='portfolio.user.username', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = WatchList
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WatchListItemSerializer(serializers.ModelSerializer):
    """Serializer for watchlist items."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    watchlist_name = serializers.CharField(source='watchlist.name', read_only=True)
    
    class Meta:
        model = WatchListItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ExecuteTradeSerializer(serializers.Serializer):
    """Serializer for executing trades."""
    symbol = serializers.CharField(max_length=50)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=['BUY', 'SELL'])
    order_type = serializers.ChoiceField(choices=['MARKET', 'LIMIT'], default='MARKET')
    remarks = serializers.CharField(max_length=500, required=False, allow_blank=True)

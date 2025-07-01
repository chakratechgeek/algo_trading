"""Trading serializers."""

from rest_framework import serializers
from .models import (
    TradingStrategy, TradingBot, TradingSignal, TradingExecution,
    MarketAnalysis, NewsAnalysis
)


class TradingStrategySerializer(serializers.ModelSerializer):
    """Serializer for trading strategies."""
    win_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = TradingStrategy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_trades', 'winning_trades', 'total_pnl']


class TradingBotSerializer(serializers.ModelSerializer):
    """Serializer for trading bots."""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    portfolio_user = serializers.CharField(source='portfolio.user.username', read_only=True)
    
    class Meta:
        model = TradingBot
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_run_at', 'total_runs', 'error_count']


class TradingSignalSerializer(serializers.ModelSerializer):
    """Serializer for trading signals."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TradingSignal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'is_executed', 'executed_at', 'execution_price']


class TradingExecutionSerializer(serializers.ModelSerializer):
    """Serializer for trading executions."""
    bot_name = serializers.CharField(source='bot.name', read_only=True)
    symbol_name = serializers.CharField(source='signal.symbol.symbol', read_only=True)
    
    class Meta:
        model = TradingExecution
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MarketAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for market analysis."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = MarketAnalysis
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NewsAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for news analysis."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = NewsAnalysis
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CreateBotSerializer(serializers.Serializer):
    """Serializer for creating trading bots."""
    name = serializers.CharField(max_length=100)
    strategy_id = serializers.IntegerField()
    max_positions = serializers.IntegerField(default=5, min_value=1, max_value=20)
    position_size = serializers.DecimalField(max_digits=5, decimal_places=2, default=10.0, min_value=1.0, max_value=50.0)
    stop_loss_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=2.0, min_value=0.5, max_value=10.0)
    take_profit_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=5.0, min_value=1.0, max_value=20.0)
    is_paper_trading = serializers.BooleanField(default=True)
    check_interval_minutes = serializers.IntegerField(default=5, min_value=1, max_value=60)


class GenerateSignalsSerializer(serializers.Serializer):
    """Serializer for generating trading signals."""
    strategy_id = serializers.IntegerField()
    symbols = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )

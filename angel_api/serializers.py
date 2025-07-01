"""Angel API serializers."""

from rest_framework import serializers
from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order


class AngelOneSessionSerializer(serializers.ModelSerializer):
    """Serializer for Angel One sessions."""
    
    class Meta:
        model = AngelOneSession
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'auth_token': {'write_only': True},
            'refresh_token': {'write_only': True},
        }


class NSESymbolSerializer(serializers.ModelSerializer):
    """Serializer for NSE symbols."""
    
    class Meta:
        model = NSESymbol
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class MarketDataSerializer(serializers.ModelSerializer):
    """Serializer for market data."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = MarketData
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class APILogSerializer(serializers.ModelSerializer):
    """Serializer for API logs."""
    
    class Meta:
        model = APILog
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'angel_order_id']


class PlaceOrderSerializer(serializers.Serializer):
    """Serializer for placing orders."""
    symbol = serializers.CharField(max_length=50)
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    order_type = serializers.ChoiceField(choices=['MARKET', 'LIMIT', 'SL', 'SL-M'], default='MARKET')
    transaction_type = serializers.ChoiceField(choices=['BUY', 'SELL'])
    product = serializers.ChoiceField(choices=['CNC', 'MIS', 'NRML'], default='CNC')


class AuthenticationSerializer(serializers.Serializer):
    """Serializer for Angel One authentication."""
    client_id = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100, write_only=True)
    totp = serializers.CharField(max_length=10, write_only=True)

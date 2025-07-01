"""Angel API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import AngelOneSession, NSESymbol, MarketData, APILog, Order
from .services import AngelOneAPI
from .serializers import (
    AngelOneSessionSerializer, NSESymbolSerializer, MarketDataSerializer,
    APILogSerializer, OrderSerializer, PlaceOrderSerializer, AuthenticationSerializer
)


class NSESymbolViewSet(viewsets.ModelViewSet):
    """ViewSet for NSE symbols."""
    queryset = NSESymbol.objects.all()
    serializer_class = NSESymbolSerializer
    filterset_fields = ['exchange', 'instrument_type']
    search_fields = ['symbol', 'company_name']
    ordering = ['symbol']


class MarketDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for market data."""
    queryset = MarketData.objects.all()
    serializer_class = MarketDataSerializer
    filterset_fields = ['symbol', 'data_timestamp']
    ordering = ['-data_timestamp']


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for orders."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ['symbol', 'status', 'transaction_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter orders by user's portfolio if needed."""
        return self.queryset.all()


class AuthenticationView(APIView):
    """View for Angel One authentication."""
    permission_classes = []  # Allow unauthenticated access for login
    
    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            angel_api = AngelOneAPI()
            
            success, result = angel_api.authenticate(
                client_id=serializer.validated_data['client_id'],
                password=serializer.validated_data['password'],
                totp=serializer.validated_data['totp']
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Authentication successful',
                    'session_data': result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LTPView(APIView):
    """View to get Last Traded Price for a symbol."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, symbol):
        try:
            angel_api = AngelOneAPI()
            price = angel_api.get_ltp(symbol)
            
            return Response({
                'symbol': symbol,
                'ltp': price,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PortfolioView(APIView):
    """View to get portfolio holdings."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            angel_api = AngelOneAPI()
            portfolio = angel_api.get_portfolio()
            
            return Response({
                'portfolio': portfolio,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BalanceView(APIView):
    """View to get account balance."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            angel_api = AngelOneAPI()
            balance = angel_api.get_balance()
            
            return Response({
                'balance': balance,
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlaceOrderView(APIView):
    """View to place orders."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        if serializer.is_valid():
            try:
                angel_api = AngelOneAPI()
                
                success, result = angel_api.place_order(
                    symbol=serializer.validated_data['symbol'],
                    quantity=serializer.validated_data['quantity'],
                    price=serializer.validated_data.get('price'),
                    order_type=serializer.validated_data['order_type'],
                    transaction_type=serializer.validated_data['transaction_type']
                )
                
                if success:
                    return Response({
                        'success': True,
                        'order_id': result,
                        'message': 'Order placed successfully'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': result
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

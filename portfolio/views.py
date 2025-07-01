"""Portfolio views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Portfolio, Trade, Position, TradingSession, WatchList, WatchListItem
from .services import PortfolioService, TradingSessionService, WatchListService
from .serializers import (
    PortfolioSerializer, TradeSerializer, PositionSerializer,
    TradingSessionSerializer, WatchListSerializer, WatchListItemSerializer,
    ExecuteTradeSerializer
)


class PortfolioViewSet(viewsets.ModelViewSet):
    """ViewSet for portfolios."""
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter portfolios by user."""
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute_trade(self, request, pk=None):
        """Execute a trade for the portfolio."""
        portfolio = self.get_object()
        serializer = ExecuteTradeSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                portfolio_service = PortfolioService(portfolio)
                trade = portfolio_service.execute_trade(
                    symbol_name=serializer.validated_data['symbol'],
                    price=serializer.validated_data['price'],
                    quantity=serializer.validated_data['quantity'],
                    action=serializer.validated_data['action'],
                    order_type=serializer.validated_data.get('order_type', 'MARKET'),
                    remarks=serializer.validated_data.get('remarks', '')
                )
                
                return Response({
                    'success': True,
                    'trade_id': trade.id,
                    'message': f"Trade executed: {trade.action} {trade.quantity} {trade.symbol.symbol}"
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trades."""
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['action', 'status', 'symbol']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter trades by user's portfolios."""
        return self.queryset.filter(portfolio__user=self.request.user)


class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for positions."""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_open', 'symbol']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter positions by user's portfolios."""
        return self.queryset.filter(portfolio__user=self.request.user)


class TradingSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for trading sessions."""
    queryset = TradingSession.objects.all()
    serializer_class = TradingSessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'session_date']
    ordering = ['-session_date', '-start_time']
    
    def get_queryset(self):
        """Filter sessions by user's portfolios."""
        return self.queryset.filter(portfolio__user=self.request.user)


class WatchListViewSet(viewsets.ModelViewSet):
    """ViewSet for watchlists."""
    queryset = WatchList.objects.all()
    serializer_class = WatchListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    
    def get_queryset(self):
        """Filter watchlists by user's portfolios."""
        return self.queryset.filter(portfolio__user=self.request.user)


class PortfolioSummaryView(APIView):
    """View to get portfolio summary."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's portfolio
            portfolio = Portfolio.objects.filter(user=request.user, is_active=True).first()
            
            if not portfolio:
                return Response({
                    'error': 'No active portfolio found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio_service = PortfolioService(portfolio)
            summary = portfolio_service.get_portfolio_summary()
            
            return Response(summary)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertsView(APIView):
    """View to get portfolio alerts."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's portfolio
            portfolio = Portfolio.objects.filter(user=request.user, is_active=True).first()
            
            if not portfolio:
                return Response({
                    'error': 'No active portfolio found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio_service = PortfolioService(portfolio)
            watchlist_service = WatchListService(portfolio)
            
            # Get alerts
            position_alerts = portfolio_service.check_stop_loss_targets()
            watchlist_alerts = watchlist_service.check_watchlist_alerts()
            
            return Response({
                'position_alerts': position_alerts,
                'watchlist_alerts': watchlist_alerts,
                'total_alerts': len(position_alerts) + len(watchlist_alerts)
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

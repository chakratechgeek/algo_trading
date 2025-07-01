"""Trading views."""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import (
    TradingStrategy, TradingBot, TradingSignal, TradingExecution,
    MarketAnalysis, NewsAnalysis
)
from .services import TradingStrategyService, TradingBotService
from .serializers import (
    TradingStrategySerializer, TradingBotSerializer, TradingSignalSerializer,
    TradingExecutionSerializer, MarketAnalysisSerializer, NewsAnalysisSerializer,
    CreateBotSerializer, GenerateSignalsSerializer
)
from portfolio.models import Portfolio


class TradingStrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for trading strategies."""
    queryset = TradingStrategy.objects.all()
    serializer_class = TradingStrategySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['strategy_type', 'is_active']
    ordering = ['name']


class TradingBotViewSet(viewsets.ModelViewSet):
    """ViewSet for trading bots."""
    queryset = TradingBot.objects.all()
    serializer_class = TradingBotSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'is_paper_trading', 'strategy']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter bots by user's portfolios."""
        return self.queryset.filter(portfolio__user=self.request.user)
    
    def perform_create(self, serializer):
        """Set portfolio when creating bot."""
        # Get user's active portfolio
        portfolio = Portfolio.objects.filter(user=self.request.user, is_active=True).first()
        if not portfolio:
            raise serializers.ValidationError("No active portfolio found")
        serializer.save(portfolio=portfolio)


class TradingSignalViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trading signals."""
    queryset = TradingSignal.objects.all()
    serializer_class = TradingSignalSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['signal_type', 'signal_strength', 'is_executed', 'is_active']
    ordering = ['-created_at']


class TradingExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trading executions."""
    queryset = TradingExecution.objects.all()
    serializer_class = TradingExecutionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['execution_type', 'status', 'bot']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter executions by user's bots."""
        return self.queryset.filter(bot__portfolio__user=self.request.user)


class RunBotView(APIView):
    """View to run a specific trading bot."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, bot_id):
        try:
            bot = get_object_or_404(TradingBot, id=bot_id, portfolio__user=request.user)
            
            if not bot.is_active:
                return Response({
                    'error': 'Bot is not active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            bot_service = TradingBotService(bot_id)
            bot_service.run_bot_cycle()
            
            return Response({
                'success': True,
                'message': f'Bot {bot.name} cycle completed'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StopBotView(APIView):
    """View to stop a trading bot."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, bot_id):
        try:
            bot = get_object_or_404(TradingBot, id=bot_id, portfolio__user=request.user)
            
            bot_service = TradingBotService(bot_id)
            bot_service.stop_bot()
            
            return Response({
                'success': True,
                'message': f'Bot {bot.name} stopped'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BotPerformanceView(APIView):
    """View to get bot performance metrics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, bot_id):
        try:
            bot = get_object_or_404(TradingBot, id=bot_id, portfolio__user=request.user)
            
            bot_service = TradingBotService(bot_id)
            performance = bot_service.get_bot_performance()
            
            return Response(performance)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateSignalsView(APIView):
    """View to generate trading signals."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GenerateSignalsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                strategy_service = TradingStrategyService()
                
                signals = strategy_service.generate_trading_signals(
                    strategy_id=serializer.validated_data['strategy_id'],
                    symbols=serializer.validated_data.get('symbols')
                )
                
                return Response({
                    'success': True,
                    'signals_generated': len(signals),
                    'signals': [
                        {
                            'id': signal.id,
                            'symbol': signal.symbol.symbol,
                            'signal_type': signal.signal_type,
                            'confidence': float(signal.confidence),
                            'entry_price': float(signal.entry_price)
                        }
                        for signal in signals
                    ]
                })
                
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateBotView(APIView):
    """View to create a new trading bot."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateBotSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Get user's active portfolio
                portfolio = Portfolio.objects.filter(user=request.user, is_active=True).first()
                if not portfolio:
                    return Response({
                        'error': 'No active portfolio found'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get strategy
                try:
                    strategy = TradingStrategy.objects.get(id=serializer.validated_data['strategy_id'])
                except TradingStrategy.DoesNotExist:
                    return Response({
                        'error': 'Strategy not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Create bot
                bot_service = TradingBotService()
                bot = bot_service.create_bot(
                    name=serializer.validated_data['name'],
                    portfolio=portfolio,
                    strategy=strategy,
                    config={
                        'max_positions': serializer.validated_data['max_positions'],
                        'position_size': serializer.validated_data['position_size'],
                        'stop_loss_percent': serializer.validated_data['stop_loss_percent'],
                        'take_profit_percent': serializer.validated_data['take_profit_percent'],
                        'is_paper_trading': serializer.validated_data['is_paper_trading'],
                        'check_interval_minutes': serializer.validated_data['check_interval_minutes']
                    }
                )
                
                return Response({
                    'success': True,
                    'bot_id': bot.id,
                    'message': f'Bot {bot.name} created successfully'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

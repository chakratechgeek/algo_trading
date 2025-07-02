"""Custom monitoring views for detailed trading analysis."""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import datetime, timedelta
from .models import TradingExecution, TradingSignal, TradingBot, MarketAnalysis
from portfolio.models import Trade, Portfolio
import json


@staff_member_required
def trading_monitor_dashboard(request):
    """Comprehensive trading monitoring dashboard."""
    
    # Get recent trading activity (last 24 hours)
    yesterday = timezone.now() - timedelta(days=1)
    
    recent_executions = TradingExecution.objects.filter(
        created_at__gte=yesterday
    ).select_related('bot', 'signal__symbol', 'signal__strategy').order_by('-created_at')[:20]
    
    recent_signals = TradingSignal.objects.filter(
        created_at__gte=yesterday
    ).select_related('symbol', 'strategy').order_by('-created_at')[:15]
    
    active_bots = TradingBot.objects.filter(is_active=True).select_related('strategy', 'portfolio')
    
    # Performance stats
    today = timezone.now().date()
    today_executions = TradingExecution.objects.filter(created_at__date=today)
    today_signals = TradingSignal.objects.filter(created_at__date=today)
    
    context = {
        'recent_executions': recent_executions,
        'recent_signals': recent_signals,
        'active_bots': active_bots,
        'stats': {
            'today_executions': today_executions.count(),
            'today_signals': today_signals.count(),
            'successful_executions': today_executions.filter(status='EXECUTED').count(),
            'failed_executions': today_executions.filter(status='FAILED').count(),
            'pending_executions': today_executions.filter(status='PENDING').count(),
        }
    }
    
    return render(request, 'trading/monitor_dashboard.html', context)


@staff_member_required
def execution_details(request, execution_id):
    """Get detailed information about a specific execution."""
    try:
        execution = TradingExecution.objects.select_related(
            'bot', 'signal__symbol', 'signal__strategy'
        ).get(id=execution_id)
        
        # Get related market analysis
        market_analysis = MarketAnalysis.objects.filter(
            symbol=execution.signal.symbol,
            analysis_date=execution.created_at.date()
        ).first()
        
        # Get recent price movements for this symbol
        recent_trades = Trade.objects.filter(
            symbol=execution.signal.symbol,
            created_at__gte=execution.created_at - timedelta(hours=1)
        ).order_by('-created_at')[:5]
        
        data = {
            'execution': {
                'id': execution.id,
                'type': execution.execution_type,
                'status': execution.status,
                'quantity': execution.quantity,
                'requested_price': float(execution.requested_price),
                'executed_price': float(execution.executed_price) if execution.executed_price else None,
                'error_message': execution.error_message,
                'created_at': execution.created_at.isoformat(),
            },
            'signal': {
                'type': execution.signal.signal_type,
                'confidence': float(execution.signal.confidence),
                'strength': execution.signal.signal_strength,
                'entry_price': float(execution.signal.entry_price),
                'target_price': float(execution.signal.target_price) if execution.signal.target_price else None,
                'stop_loss': float(execution.signal.stop_loss_price) if execution.signal.stop_loss_price else None,
                'analysis_data': execution.signal.analysis_data,
            },
            'symbol': {
                'symbol': execution.signal.symbol.symbol,
                'company_name': execution.signal.symbol.company_name,
            },
            'bot': {
                'name': execution.bot.name,
                'strategy': execution.bot.strategy.name,
                'portfolio': execution.bot.portfolio.name,
            },
            'market_analysis': {
                'current_price': float(market_analysis.current_price) if market_analysis else None,
                'recommendation': market_analysis.recommendation if market_analysis else None,
                'rsi': float(market_analysis.rsi) if market_analysis and market_analysis.rsi else None,
                'price_change_1d': float(market_analysis.price_change_1d) if market_analysis and market_analysis.price_change_1d else None,
            } if market_analysis else None,
            'recent_trades': [
                {
                    'price': float(trade.price),
                    'quantity': trade.quantity,
                    'action': trade.action,
                    'time': trade.created_at.isoformat(),
                }
                for trade in recent_trades
            ]
        }
        
        return JsonResponse(data)
        
    except TradingExecution.DoesNotExist:
        return JsonResponse({'error': 'Execution not found'}, status=404)


@staff_member_required
def live_monitoring_feed(request):
    """Real-time feed of trading activities."""
    
    # Get last update timestamp from request
    since = request.GET.get('since')
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except:
            since_dt = timezone.now() - timedelta(minutes=5)
    else:
        since_dt = timezone.now() - timedelta(minutes=5)
    
    # Get new executions
    new_executions = TradingExecution.objects.filter(
        created_at__gt=since_dt
    ).select_related('bot', 'signal__symbol').order_by('-created_at')
    
    # Get new signals
    new_signals = TradingSignal.objects.filter(
        created_at__gt=since_dt
    ).select_related('symbol', 'strategy').order_by('-created_at')
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'new_executions': [
            {
                'id': exec.id,
                'symbol': exec.signal.symbol.symbol,
                'type': exec.execution_type,
                'status': exec.status,
                'bot': exec.bot.name,
                'price': float(exec.executed_price) if exec.executed_price else float(exec.requested_price),
                'time': exec.created_at.isoformat(),
            }
            for exec in new_executions
        ],
        'new_signals': [
            {
                'id': signal.id,
                'symbol': signal.symbol.symbol,
                'type': signal.signal_type,
                'confidence': float(signal.confidence),
                'strength': signal.signal_strength,
                'price': float(signal.entry_price),
                'time': signal.created_at.isoformat(),
            }
            for signal in new_signals
        ]
    }
    
    return JsonResponse(data)

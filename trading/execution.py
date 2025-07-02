"""
Trading Execution Engine
======================

This module handles the actual buy and sell order execution logic.
Integrates with Angel One API for real trading and includes paper trading simulation.
"""

import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import TradingExecution, TradingSignal, TradingBot
# from .transaction_models import TransactionRecord, PositionSummary, DailyTradingSummary
from angel_api.services import AngelOneAPI
from angel_api.models import Order, NSESymbol
from portfolio.services import PortfolioService




class TradingExecutor:
    """Main trading execution engine."""
    
    def __init__(self):
        self.logger = logging.getLogger('trading_execution')
        self.angel_api = AngelOneAPI()
        self.portfolio_service = PortfolioService()
        
    def execute_signal(self, signal: TradingSignal, bot: TradingBot, quantity=None):
        """
        Execute a trading signal (BUY/SELL).
        
        Args:
            signal: TradingSignal instance
            bot: TradingBot instance
            quantity: Override quantity (optional)
            
        Returns:
            TradingExecution instance
        """
        self.logger.info(f"Executing signal: {signal.signal_type} {signal.symbol.symbol}")
        
        try:
            with transaction.atomic():
                # Calculate position size if not provided
                if quantity is None:
                    quantity = self._calculate_position_size(signal, bot)
                
                # Create execution record
                execution = TradingExecution.objects.create(
                    bot=bot,
                    signal=signal,
                    execution_type='SIGNAL_ENTRY',
                    quantity=quantity,
                    requested_price=signal.entry_price,
                    status='PENDING'
                )
                
                # Execute the order
                success, result = self._place_order(signal, quantity, bot.is_paper_trading)
                
                if success:
                    execution.status = 'EXECUTED'
                    execution.executed_price = result.get('executed_price', signal.entry_price)
                    execution.order_id = result.get('order_id', '')
                    
                    # Mark signal as executed
                    signal.is_executed = True
                    signal.executed_at = timezone.now()
                    signal.execution_price = execution.executed_price
                    signal.save()
                    
                    # Update portfolio
                    self._update_portfolio(signal, quantity, execution.executed_price, bot)
                    
                    # Set up stop loss and take profit orders
                    self._setup_exit_orders(signal, execution, bot)
                    
                    self.logger.info(f"Successfully executed {signal.signal_type} order for {signal.symbol.symbol}")
                    
                else:
                    execution.status = 'FAILED'
                    execution.error_message = result.get('error', 'Unknown error')
                    self.logger.error(f"Failed to execute order: {execution.error_message}")
                
                execution.save()
                return execution
                
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            if 'execution' in locals():
                execution.status = 'FAILED'
                execution.error_message = str(e)
                execution.save()
            raise
    
    def _calculate_position_size(self, signal: TradingSignal, bot: TradingBot):
        """Calculate position size based on bot configuration or signal-specific quantity."""
        try:
            # Check if signal has a fixed quantity (for small-cap strategy)
            if hasattr(signal, 'analysis_data') and signal.analysis_data:
                fixed_quantity = signal.analysis_data.get('fixed_quantity')
                if fixed_quantity:
                    self.logger.info(f"Using fixed quantity from signal: {fixed_quantity} shares for {signal.symbol.symbol}")
                    return int(fixed_quantity)
            
            # Fallback to percentage-based calculation
            # Get portfolio value
            portfolio_value = self.portfolio_service.get_total_value(bot.portfolio)
            
            # Calculate position value based on percentage
            position_value = portfolio_value * (bot.position_size / 100)
            
            # Calculate quantity based on signal entry price
            quantity = int(position_value / signal.entry_price)
            
            # Ensure minimum quantity of 1
            quantity = max(1, quantity)
            
            self.logger.info(f"Calculated position size: {quantity} shares for {signal.symbol.symbol}")
            return quantity
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 1  # Default to 1 share
    
    def _place_order(self, signal: TradingSignal, quantity: int, is_paper_trading: bool):
        """Place buy/sell order via Angel One API or paper trading."""
        
        if is_paper_trading:
            return self._execute_paper_trade(signal, quantity)
        else:
            return self._execute_real_trade(signal, quantity)
    
    def _execute_paper_trade(self, signal: TradingSignal, quantity: int):
        """Execute paper trade (simulation)."""
        try:
            # Get current market price
            current_price = self.angel_api.get_ltp(signal.symbol.symbol)
            
            # Simulate order execution with slight slippage
            slippage = 0.001  # 0.1% slippage
            if signal.signal_type == 'BUY':
                executed_price = current_price * (1 + slippage)
            else:
                executed_price = current_price * (1 - slippage)
            
            # Round to 2 decimal places
            executed_price = Decimal(executed_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            self.logger.info(f"Paper trade executed: {signal.signal_type} {quantity} {signal.symbol.symbol} @ ₹{executed_price}")
            
            return True, {
                'order_id': f'PAPER_{int(time.time())}',
                'executed_price': executed_price,
                'quantity': quantity
            }
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def _execute_real_trade(self, signal: TradingSignal, quantity: int):
        """Execute real trade via Angel One API."""
        try:
            # Determine order type and transaction type
            transaction_type = signal.signal_type  # BUY or SELL
            order_type = 'MARKET'  # Use market orders for immediate execution
            
            # Place order via Angel One API
            success, order_id = self.angel_api.place_order(
                symbol=signal.symbol.symbol,
                quantity=quantity,
                price=None,  # Market order
                order_type=order_type,
                transaction_type=transaction_type
            )
            
            if success:
                # Get execution details
                executed_price = self.angel_api.get_ltp(signal.symbol.symbol)
                
                self.logger.info(f"Real trade executed: {transaction_type} {quantity} {signal.symbol.symbol} @ ₹{executed_price}")
                
                return True, {
                    'order_id': order_id,
                    'executed_price': executed_price,
                    'quantity': quantity
                }
            else:
                return False, {'error': order_id}  # order_id contains error message on failure
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def _update_portfolio(self, signal: TradingSignal, quantity: int, executed_price: Decimal, bot: TradingBot):
        """Update portfolio with the executed trade."""
        try:
            if signal.signal_type == 'BUY':
                self.portfolio_service.add_holding(
                    portfolio=bot.portfolio,
                    symbol=signal.symbol,
                    quantity=quantity,
                    average_price=executed_price
                )
            elif signal.signal_type == 'SELL':
                self.portfolio_service.reduce_holding(
                    portfolio=bot.portfolio,
                    symbol=signal.symbol,
                    quantity=quantity,
                    sale_price=executed_price
                )
                
            self.logger.info(f"Portfolio updated for {signal.signal_type} {quantity} {signal.symbol.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")
    
    def _setup_exit_orders(self, signal: TradingSignal, execution: TradingExecution, bot: TradingBot):
        """Set up stop loss and take profit orders."""
        try:
            if signal.signal_type == 'BUY':
                # Set up stop loss
                if signal.stop_loss_price or bot.stop_loss_percent:
                    stop_loss_price = signal.stop_loss_price or (
                        execution.executed_price * (1 - bot.stop_loss_percent / 100)
                    )
                    self._create_exit_signal(signal, stop_loss_price, 'STOP_LOSS', bot)
                
                # Set up take profit
                if signal.target_price or bot.take_profit_percent:
                    take_profit_price = signal.target_price or (
                        execution.executed_price * (1 + bot.take_profit_percent / 100)
                    )
                    self._create_exit_signal(signal, take_profit_price, 'TAKE_PROFIT', bot)
            
            # For SELL signals, the logic would be reversed
            
        except Exception as e:
            self.logger.error(f"Error setting up exit orders: {e}")
    
    def _create_exit_signal(self, original_signal: TradingSignal, exit_price: Decimal, exit_type: str, bot: TradingBot):
        """Create exit signal for stop loss or take profit."""
        try:
            # Create opposite signal (BUY -> SELL, SELL -> BUY)
            exit_signal_type = 'SELL' if original_signal.signal_type == 'BUY' else 'BUY'
            
            # This would typically be handled by a monitoring service
            # For now, we just log the intention
            self.logger.info(f"Exit order setup: {exit_type} at ₹{exit_price} for {original_signal.symbol.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error creating exit signal: {e}")


class OrderMonitor:
    """Monitor and manage active orders."""
    
    def __init__(self):
        self.logger = logging.getLogger('order_monitor')
        self.angel_api = AngelOneAPI()
        self.executor = TradingExecutor()
    
    def monitor_positions(self, bot: TradingBot):
        """Monitor active positions for stop loss and take profit triggers."""
        try:
            # Get bot's active executions
            active_executions = TradingExecution.objects.filter(
                bot=bot,
                status='EXECUTED'
            ).select_related('signal')
            
            for execution in active_executions:
                self._check_exit_conditions(execution)
                
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
    
    def _check_exit_conditions(self, execution: TradingExecution):
        """Check if position should be closed based on stop loss or take profit."""
        try:
            signal = execution.signal
            current_price = self.angel_api.get_ltp(signal.symbol.symbol)
            
            if signal.signal_type == 'BUY':
                # Check stop loss
                if signal.stop_loss_price and current_price <= signal.stop_loss_price:
                    self._trigger_exit(execution, 'STOP_LOSS', current_price)
                
                # Check take profit
                elif signal.target_price and current_price >= signal.target_price:
                    self._trigger_exit(execution, 'TAKE_PROFIT', current_price)
            
            # Similar logic for SELL positions would go here
            
        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {e}")
    
    def _trigger_exit(self, execution: TradingExecution, exit_type: str, current_price: Decimal):
        """Trigger exit order."""
        try:
            # Create exit signal
            exit_signal = TradingSignal.objects.create(
                strategy=execution.signal.strategy,
                symbol=execution.signal.symbol,
                signal_type='SELL' if execution.signal.signal_type == 'BUY' else 'BUY',
                confidence=90,  # High confidence for exit signals
                entry_price=current_price,
                signal_strength='STRONG'
            )
            
            # Execute exit order
            self.executor.execute_signal(exit_signal, execution.bot, execution.quantity)
            
            self.logger.info(f"Exit triggered: {exit_type} for {execution.signal.symbol.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error triggering exit: {e}")


class RiskManager:
    """Risk management for trading operations."""
    
    def __init__(self):
        self.logger = logging.getLogger('risk_manager')
    
    def validate_order(self, signal: TradingSignal, bot: TradingBot, quantity: int):
        """Validate order against risk parameters."""
        try:
            # Check portfolio allocation limits
            if not self._check_position_limits(signal, bot, quantity):
                return False, "Position limits exceeded"
            
            # Check daily loss limits
            if not self._check_daily_limits(bot):
                return False, "Daily loss limit reached"
            
            # Check market hours (if enabled)
            if bot.trading_hours_only and not self._is_market_open():
                return False, "Market is closed"
            
            return True, "Order validated"
            
        except Exception as e:
            self.logger.error(f"Error validating order: {e}")
            return False, str(e)
    
    def _check_position_limits(self, signal: TradingSignal, bot: TradingBot, quantity: int):
        """Check if order exceeds position limits."""
        # Check max positions per strategy
        active_positions = TradingExecution.objects.filter(
            bot=bot,
            status='EXECUTED'
        ).count()
        
        return active_positions < bot.max_positions
    
    def _check_daily_limits(self, bot: TradingBot):
        """Check daily loss limits."""
        if not bot.daily_loss_limit:
            return True
        
        # Calculate today's P&L
        today = timezone.now().date()
        # Implementation would calculate actual P&L
        
        return True  # Placeholder
    
    def _is_market_open(self):
        """Check if market is currently open."""
        now = timezone.now()
        
        # NSE trading hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
        if now.weekday() > 4:  # Saturday or Sunday
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close


# Main execution service instance
trading_executor = TradingExecutor()
order_monitor = OrderMonitor()
risk_manager = RiskManager()

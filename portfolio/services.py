"""Portfolio management services."""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Avg, Q
from .models import Portfolio, Trade, Position, TradingSession, WatchList, WatchListItem
from angel_api.models import NSESymbol
from angel_api.services import AngelOneAPI


class PortfolioService:
    """Service for portfolio management operations."""
    
    def __init__(self, portfolio=None):
        self.portfolio = portfolio
        self.logger = logging.getLogger('portfolio')
        self.angel_api = AngelOneAPI()
    
    def get_or_create_portfolio(self, user):
        """Get or create portfolio for user."""
        portfolio, created = Portfolio.objects.get_or_create(
            user=user,
            defaults={
                'name': f"{user.username}'s Portfolio",
                'initial_balance': 50000.00,
                'current_balance': 50000.00
            }
        )
        self.portfolio = portfolio
        return portfolio
    
    def update_balance(self, new_balance):
        """Update portfolio balance."""
        if self.portfolio:
            self.portfolio.current_balance = new_balance
            self.portfolio.save()
            self.logger.info(f"Portfolio balance updated to ₹{new_balance}")
    
    def get_balance(self):
        """Get current portfolio balance."""
        return float(self.portfolio.current_balance) if self.portfolio else 0.0
    
    def execute_trade(self, symbol_name, price, quantity, action, order_type='MARKET', remarks=''):
        """Execute a trade and update portfolio."""
        if not self.portfolio:
            raise ValueError("Portfolio not set")
        
        try:
            with transaction.atomic():
                # Get or create symbol
                symbol, created = NSESymbol.objects.get_or_create(
                    symbol=symbol_name,
                    exchange='NSE',
                    defaults={'token': symbol_name, 'lot_size': 1}
                )
                
                # Calculate trade amount
                trade_amount = price * quantity
                brokerage_fee = trade_amount * 0.0003  # 0.03% brokerage
                
                # Create trade record
                trade = Trade.objects.create(
                    portfolio=self.portfolio,
                    symbol=symbol,
                    price=price,
                    quantity=quantity,
                    action=action,
                    order_type=order_type,
                    brokerage_fee=brokerage_fee,
                    remarks=remarks
                )
                
                # Update portfolio balance and positions
                if action == 'BUY':
                    self._execute_buy_trade(trade, symbol, price, quantity, trade_amount, brokerage_fee)
                elif action == 'SELL':
                    self._execute_sell_trade(trade, symbol, price, quantity, trade_amount, brokerage_fee)
                
                self.logger.info(f"Trade executed: {action} {quantity} {symbol_name} @ ₹{price}")
                return trade
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            raise
    
    def _execute_buy_trade(self, trade, symbol, price, quantity, trade_amount, brokerage_fee):
        """Execute buy trade logic."""
        total_cost = trade_amount + brokerage_fee
        
        # Update portfolio balance
        self.portfolio.current_balance -= total_cost
        self.portfolio.save()
        
        # Update or create position
        position, created = Position.objects.get_or_create(
            portfolio=self.portfolio,
            symbol=symbol,
            defaults={
                'total_quantity': quantity,
                'average_price': price,
                'invested_amount': total_cost,
                'is_open': True
            }
        )
        
        if not created:
            # Update existing position
            total_invested = position.invested_amount + total_cost
            total_quantity = position.total_quantity + quantity
            position.average_price = total_invested / total_quantity
            position.total_quantity = total_quantity
            position.invested_amount = total_invested
            position.save()
    
    def _execute_sell_trade(self, trade, symbol, price, quantity, trade_amount, brokerage_fee):
        """Execute sell trade logic."""
        net_amount = trade_amount - brokerage_fee
        
        # Update portfolio balance
        self.portfolio.current_balance += net_amount
        self.portfolio.save()
        
        # Update position
        try:
            position = Position.objects.get(portfolio=self.portfolio, symbol=symbol, is_open=True)
            
            if position.total_quantity >= quantity:
                # Calculate profit/loss
                avg_buy_price = position.average_price
                profit = (price - avg_buy_price) * quantity - brokerage_fee
                profit_percent = (profit / (avg_buy_price * quantity)) * 100
                
                # Update trade with profit info
                trade.profit = profit
                trade.pnl_percent = profit_percent
                trade.save()
                
                # Update position
                position.total_quantity -= quantity
                if position.total_quantity == 0:
                    position.close_position()
                else:
                    position.invested_amount -= avg_buy_price * quantity
                    position.save()
                
                self.logger.info(f"Sell trade profit: ₹{profit:.2f} ({profit_percent:.2f}%)")
            else:
                raise ValueError(f"Insufficient quantity in position. Available: {position.total_quantity}, Requested: {quantity}")
                
        except Position.DoesNotExist:
            raise ValueError("No open position found for this symbol")
    
    def get_open_positions(self):
        """Get all open positions."""
        if not self.portfolio:
            return []
        
        return Position.objects.filter(portfolio=self.portfolio, is_open=True)
    
    def get_trades(self, limit=100):
        """Get recent trades."""
        if not self.portfolio:
            return []
        
        return Trade.objects.filter(portfolio=self.portfolio).order_by('-created_at')[:limit]
    
    def get_portfolio_summary(self):
        """Get portfolio summary with statistics."""
        if not self.portfolio:
            return {}
        
        trades = self.get_trades()
        open_positions = self.get_open_positions()
        
        # Calculate statistics
        total_trades = trades.count()
        buy_trades = trades.filter(action='BUY').count()
        sell_trades = trades.filter(action='SELL').count()
        
        total_invested = trades.filter(action='BUY').aggregate(
            total=Sum('buy_amount')
        )['total'] or 0
        
        total_profit = trades.filter(action='SELL').aggregate(
            total=Sum('profit')
        )['total'] or 0
        
        return {
            'current_balance': float(self.portfolio.current_balance),
            'initial_balance': float(self.portfolio.initial_balance),
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'open_positions': open_positions.count(),
            'total_invested': float(total_invested),
            'total_profit': float(total_profit),
            'profit_percentage': (total_profit / total_invested * 100) if total_invested > 0 else 0,
        }
    
    def update_positions_with_current_prices(self):
        """Update all open positions with current market prices."""
        open_positions = self.get_open_positions()
        
        for position in open_positions:
            try:
                current_price = self.angel_api.get_ltp(position.symbol.symbol)
                position.update_current_price(current_price)
                self.logger.info(f"Updated {position.symbol.symbol} price to ₹{current_price}")
            except Exception as e:
                self.logger.error(f"Error updating price for {position.symbol.symbol}: {e}")
    
    def check_stop_loss_targets(self):
        """Check stop loss and target prices for open positions."""
        open_positions = self.get_open_positions()
        alerts = []
        
        for position in open_positions:
            if not position.current_price:
                continue
            
            # Check stop loss
            if position.stop_loss and position.current_price <= position.stop_loss:
                alerts.append({
                    'type': 'STOP_LOSS',
                    'symbol': position.symbol.symbol,
                    'current_price': float(position.current_price),
                    'trigger_price': float(position.stop_loss),
                    'message': f"Stop loss triggered for {position.symbol.symbol}"
                })
            
            # Check target price
            if position.target_price and position.current_price >= position.target_price:
                alerts.append({
                    'type': 'TARGET',
                    'symbol': position.symbol.symbol,
                    'current_price': float(position.current_price),
                    'trigger_price': float(position.target_price),
                    'message': f"Target price reached for {position.symbol.symbol}"
                })
        
        return alerts


class TradingSessionService:
    """Service for managing trading sessions."""
    
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.logger = logging.getLogger('portfolio')
    
    def start_session(self):
        """Start a new trading session."""
        # End any active session first
        self.end_active_sessions()
        
        session = TradingSession.objects.create(
            portfolio=self.portfolio,
            starting_balance=self.portfolio.current_balance,
            is_active=True
        )
        
        self.logger.info(f"Trading session started with balance ₹{session.starting_balance}")
        return session
    
    def end_active_sessions(self):
        """End all active trading sessions."""
        active_sessions = TradingSession.objects.filter(
            portfolio=self.portfolio,
            is_active=True
        )
        
        for session in active_sessions:
            session.end_session()
            self.logger.info(f"Ended trading session from {session.session_date}")
    
    def get_active_session(self):
        """Get the active trading session."""
        return TradingSession.objects.filter(
            portfolio=self.portfolio,
            is_active=True
        ).first()
    
    def get_session_statistics(self, days=30):
        """Get trading session statistics for the last N days."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        sessions = TradingSession.objects.filter(
            portfolio=self.portfolio,
            session_date__gte=start_date,
            session_date__lte=end_date
        )
        
        if not sessions.exists():
            return {}
        
        total_sessions = sessions.count()
        profitable_sessions = sessions.filter(total_pnl__gt=0).count()
        
        total_pnl = sessions.aggregate(total=Sum('total_pnl'))['total'] or 0
        avg_pnl = sessions.aggregate(avg=Avg('total_pnl'))['avg'] or 0
        
        return {
            'total_sessions': total_sessions,
            'profitable_sessions': profitable_sessions,
            'loss_sessions': total_sessions - profitable_sessions,
            'win_rate': (profitable_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'total_pnl': float(total_pnl),
            'average_pnl': float(avg_pnl),
            'period_days': days
        }


class WatchListService:
    """Service for managing watchlists."""
    
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.logger = logging.getLogger('portfolio')
    
    def create_watchlist(self, name, description=''):
        """Create a new watchlist."""
        watchlist = WatchList.objects.create(
            portfolio=self.portfolio,
            name=name,
            description=description
        )
        
        self.logger.info(f"Created watchlist: {name}")
        return watchlist
    
    def add_symbol_to_watchlist(self, watchlist_id, symbol_name, target_price=None, notes='', priority=1):
        """Add a symbol to watchlist."""
        try:
            watchlist = WatchList.objects.get(id=watchlist_id, portfolio=self.portfolio)
            symbol, created = NSESymbol.objects.get_or_create(
                symbol=symbol_name,
                exchange='NSE',
                defaults={'token': symbol_name, 'lot_size': 1}
            )
            
            item, created = WatchListItem.objects.get_or_create(
                watchlist=watchlist,
                symbol=symbol,
                defaults={
                    'target_price': target_price,
                    'notes': notes,
                    'priority': priority
                }
            )
            
            if created:
                self.logger.info(f"Added {symbol_name} to watchlist {watchlist.name}")
            else:
                self.logger.info(f"{symbol_name} already in watchlist {watchlist.name}")
            
            return item
            
        except WatchList.DoesNotExist:
            raise ValueError("Watchlist not found")
    
    def get_watchlist_items(self, watchlist_id):
        """Get all items in a watchlist."""
        try:
            watchlist = WatchList.objects.get(id=watchlist_id, portfolio=self.portfolio)
            return WatchListItem.objects.filter(watchlist=watchlist, is_active=True)
        except WatchList.DoesNotExist:
            return WatchListItem.objects.none()
    
    def check_watchlist_alerts(self):
        """Check for price alerts in all watchlists."""
        alerts = []
        angel_api = AngelOneAPI()
        
        active_items = WatchListItem.objects.filter(
            watchlist__portfolio=self.portfolio,
            watchlist__is_active=True,
            is_active=True,
            target_price__isnull=False
        )
        
        for item in active_items:
            try:
                current_price = angel_api.get_ltp(item.symbol.symbol)
                if current_price <= item.target_price:
                    alerts.append({
                        'symbol': item.symbol.symbol,
                        'current_price': current_price,
                        'target_price': float(item.target_price),
                        'watchlist': item.watchlist.name,
                        'notes': item.notes,
                        'priority': item.priority
                    })
            except Exception as e:
                self.logger.error(f"Error checking price for {item.symbol.symbol}: {e}")
        
        return alerts

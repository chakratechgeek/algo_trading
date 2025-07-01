"""Portfolio management models."""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import TimeStampedModel
from angel_api.models import NSESymbol


class Portfolio(TimeStampedModel):
    """Model to represent a trading portfolio."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    name = models.CharField(max_length=100, default='Default Portfolio')
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=50000.00)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=50000.00)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.name} - ₹{self.current_balance}"
    
    @property
    def total_pnl(self):
        """Calculate total profit/loss."""
        return sum(trade.profit or 0 for trade in self.trades.all())
    
    @property
    def total_invested(self):
        """Calculate total amount invested."""
        return sum(trade.buy_amount or 0 for trade in self.trades.filter(action='BUY'))
    
    @property
    def open_positions_count(self):
        """Count open positions."""
        return self.positions.filter(is_open=True).count()


class Trade(TimeStampedModel):
    """Model to represent individual trades."""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='trades')
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE, related_name='trades')
    
    # Trade details
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField()
    action = models.CharField(max_length=10, choices=[
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ])
    
    # Financial details
    buy_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    brokerage_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    pnl_percent = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Order details
    order_type = models.CharField(max_length=20, choices=[
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('SL', 'Stop Loss'),
        ('SL-M', 'Stop Loss Market'),
    ], default='MARKET')
    exchange = models.CharField(max_length=10, default='NSE')
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ], default='EXECUTED')
    
    # Reference to related trades
    ref_trade = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                 help_text="Reference to the original buy trade for sell trades")
    
    # Additional information
    remarks = models.TextField(blank=True)
    holding_days = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['portfolio', 'symbol', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.quantity} {self.symbol.symbol} @ ₹{self.price} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Calculate derived fields before saving."""
        if self.action == 'BUY':
            self.buy_amount = self.price * self.quantity + self.brokerage_fee
        
        super().save(*args, **kwargs)


class Position(TimeStampedModel):
    """Model to represent current positions."""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE, related_name='positions')
    
    # Position details
    total_quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Financial details
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    unrealized_pnl_percent = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status
    is_open = models.BooleanField(default=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    exit_date = models.DateTimeField(null=True, blank=True)
    
    # Risk management
    stop_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['portfolio', 'symbol']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['portfolio', 'is_open']),
            models.Index(fields=['symbol', 'is_open']),
        ]
    
    def __str__(self):
        return f"{self.symbol.symbol} - {self.total_quantity} shares @ ₹{self.average_price}"
    
    def update_current_price(self, new_price):
        """Update current price and calculate unrealized P&L."""
        self.current_price = new_price
        self.current_value = new_price * self.total_quantity
        self.unrealized_pnl = self.current_value - self.invested_amount
        
        if self.invested_amount > 0:
            self.unrealized_pnl_percent = (self.unrealized_pnl / self.invested_amount) * 100
        
        self.save()
    
    def close_position(self):
        """Mark position as closed."""
        self.is_open = False
        self.exit_date = timezone.now()
        self.save()


class TradingSession(TimeStampedModel):
    """Model to track trading sessions."""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='trading_sessions')
    
    # Session details
    session_date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    starting_balance = models.DecimalField(max_digits=15, decimal_places=2)
    ending_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    profitable_trades = models.IntegerField(default=0)
    
    # Session statistics
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-session_date', '-start_time']
        indexes = [
            models.Index(fields=['portfolio', 'session_date']),
            models.Index(fields=['is_active', '-session_date']),
        ]
    
    def __str__(self):
        return f"Trading Session {self.session_date} - ₹{self.starting_balance}"
    
    def end_session(self):
        """End the trading session."""
        self.is_active = False
        self.end_time = timezone.now()
        self.ending_balance = self.portfolio.current_balance
        self.total_pnl = self.ending_balance - self.starting_balance
        self.save()


class WatchList(TimeStampedModel):
    """Model to store watchlist items."""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.portfolio.user.username}"


class WatchListItem(TimeStampedModel):
    """Model to store individual watchlist items."""
    watchlist = models.ForeignKey(WatchList, on_delete=models.CASCADE, related_name='items')
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE)
    
    # Entry criteria
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    priority = models.IntegerField(default=1, choices=[
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
    ])
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['watchlist', 'symbol']
        ordering = ['-priority', 'symbol__symbol']
    
    def __str__(self):
        return f"{self.symbol.symbol} in {self.watchlist.name}"

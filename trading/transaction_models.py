"""
Trading Transaction Records
==========================

Enhanced models for detailed transaction tracking with timestamps,
prices, percentages, and comprehensive trade history.
"""

from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel
from decimal import Decimal


class TransactionRecord(TimeStampedModel):
    """Detailed transaction record for all buy/sell activities."""
    
    # Basic transaction info
    portfolio = models.ForeignKey(
        'portfolio.Portfolio', 
        on_delete=models.CASCADE, 
        related_name='transaction_records'
    )
    symbol = models.ForeignKey(
        'angel_api.NSESymbol', 
        on_delete=models.CASCADE, 
        related_name='transaction_records'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=10, choices=[
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ])
    quantity = models.PositiveIntegerField()
    price_per_share = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Timing details
    transaction_date = models.DateTimeField(default=timezone.now)
    market_session = models.CharField(max_length=20, choices=[
        ('PRE_MARKET', 'Pre Market'),
        ('REGULAR', 'Regular Session'),
        ('POST_MARKET', 'Post Market'),
    ], default='REGULAR')
    
    # For SELL transactions - reference to original BUY
    related_buy_transaction = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='sell_transactions'
    )
    
    # P&L calculation (for SELL transactions)
    purchase_price_per_share = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Original purchase price for P&L calculation"
    )
    profit_loss_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    profit_loss_percentage = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True
    )
    
    # Holding period
    holding_period_days = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Days between buy and sell"
    )
    holding_period_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precise holding period in hours"
    )
    
    # Strategy and decision info
    strategy_name = models.CharField(max_length=100, blank=True)
    decision_reason = models.TextField(blank=True)
    ai_confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="AI confidence score 0-100"
    )
    
    # Market conditions at time of transaction
    market_trend = models.CharField(max_length=20, choices=[
        ('BULLISH', 'Bullish'),
        ('BEARISH', 'Bearish'),
        ('NEUTRAL', 'Neutral'),
        ('VOLATILE', 'Volatile'),
    ], blank=True)
    
    # Execution details
    execution_method = models.CharField(max_length=20, choices=[
        ('PAPER_TRADE', 'Paper Trading'),
        ('REAL_TRADE', 'Real Trading'),
        ('MANUAL', 'Manual Entry'),
    ], default='PAPER_TRADE')
    
    order_id = models.CharField(max_length=100, blank=True)
    slippage = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Price slippage from expected"
    )
    
    # Metadata
    additional_data = models.JSONField(
        default=dict,
        help_text="Additional metadata like LLM analysis, news sentiment, etc."
    )
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['portfolio', 'transaction_type', '-transaction_date']),
            models.Index(fields=['symbol', '-transaction_date']),
            models.Index(fields=['strategy_name', '-transaction_date']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.symbol.symbol} @ ₹{self.price_per_share}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate fields on save."""
        # Calculate total amount
        self.total_amount = self.quantity * self.price_per_share
        
        # For SELL transactions, calculate P&L if purchase price available
        if self.transaction_type == 'SELL' and self.purchase_price_per_share:
            self.profit_loss_amount = (self.price_per_share - self.purchase_price_per_share) * self.quantity
            if self.purchase_price_per_share > 0:
                self.profit_loss_percentage = (
                    (self.price_per_share - self.purchase_price_per_share) / self.purchase_price_per_share
                ) * 100
        
        super().save(*args, **kwargs)
    
    @property
    def is_profitable(self):
        """Check if this SELL transaction was profitable."""
        if self.transaction_type == 'SELL' and self.profit_loss_amount is not None:
            return self.profit_loss_amount > 0
        return None
    
    @property
    def return_on_investment(self):
        """Calculate ROI for SELL transactions."""
        if self.transaction_type == 'SELL' and self.profit_loss_percentage is not None:
            return f"{self.profit_loss_percentage:.2f}%"
        return None


class PositionSummary(TimeStampedModel):
    """Summary of completed positions (buy-sell cycles)."""
    
    portfolio = models.ForeignKey(
        'portfolio.Portfolio', 
        on_delete=models.CASCADE, 
        related_name='position_summaries'
    )
    symbol = models.ForeignKey(
        'angel_api.NSESymbol', 
        on_delete=models.CASCADE, 
        related_name='position_summaries'
    )
    
    # Position details
    entry_date = models.DateTimeField()
    exit_date = models.DateTimeField()
    entry_price = models.DecimalField(max_digits=12, decimal_places=2)
    exit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    
    # Performance metrics
    total_investment = models.DecimalField(max_digits=15, decimal_places=2)
    total_return = models.DecimalField(max_digits=15, decimal_places=2)
    net_profit_loss = models.DecimalField(max_digits=15, decimal_places=2)
    roi_percentage = models.DecimalField(max_digits=8, decimal_places=4)
    
    # Timing metrics
    holding_period_days = models.IntegerField()
    holding_period_hours = models.DecimalField(max_digits=10, decimal_places=2)
    annualized_return = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Annualized return percentage"
    )
    
    # Strategy information
    strategy_used = models.CharField(max_length=100)
    exit_reason = models.CharField(max_length=50, choices=[
        ('PROFIT_TARGET', 'Profit Target Hit'),
        ('STOP_LOSS', 'Stop Loss Triggered'),
        ('PRICE_RULE', '±2 INR Rule'),
        ('AI_RECOMMENDATION', 'AI Recommendation'),
        ('MANUAL', 'Manual Decision'),
        ('TIME_BASED', 'Time-based Exit'),
    ])
    
    # Risk metrics
    max_drawdown = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Maximum loss during holding period"
    )
    max_profit = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Maximum profit during holding period"
    )
    
    # References to transaction records
    buy_transaction = models.ForeignKey(
        TransactionRecord, 
        on_delete=models.CASCADE, 
        related_name='position_summaries_as_entry'
    )
    sell_transaction = models.ForeignKey(
        TransactionRecord, 
        on_delete=models.CASCADE, 
        related_name='position_summaries_as_exit'
    )
    
    class Meta:
        ordering = ['-exit_date']
        indexes = [
            models.Index(fields=['portfolio', '-exit_date']),
            models.Index(fields=['symbol', '-exit_date']),
            models.Index(fields=['roi_percentage']),
        ]
    
    def __str__(self):
        return f"{self.symbol.symbol}: {self.roi_percentage:.2f}% in {self.holding_period_days}d"
    
    @property
    def is_profitable(self):
        """Check if position was profitable."""
        return self.net_profit_loss > 0
    
    @property
    def trade_quality(self):
        """Assess trade quality based on ROI and holding period."""
        if self.roi_percentage >= 10:
            return "Excellent"
        elif self.roi_percentage >= 5:
            return "Good"
        elif self.roi_percentage >= 0:
            return "Fair"
        elif self.roi_percentage >= -5:
            return "Poor"
        else:
            return "Bad"


class DailyTradingSummary(TimeStampedModel):
    """Daily summary of trading activities."""
    
    portfolio = models.ForeignKey(
        'portfolio.Portfolio', 
        on_delete=models.CASCADE, 
        related_name='daily_summaries'
    )
    trading_date = models.DateField()
    
    # Transaction counts
    total_transactions = models.PositiveIntegerField(default=0)
    buy_transactions = models.PositiveIntegerField(default=0)
    sell_transactions = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_buy_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sell_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_trading_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # P&L metrics
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance metrics
    winning_trades = models.PositiveIntegerField(default=0)
    losing_trades = models.PositiveIntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Portfolio metrics
    portfolio_value_start = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    portfolio_value_end = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    daily_return = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    class Meta:
        unique_together = ['portfolio', 'trading_date']
        ordering = ['-trading_date']
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.trading_date} (P&L: ₹{self.total_pnl:.2f})"

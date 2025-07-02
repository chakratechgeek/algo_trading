"""Angel One API models."""

from django.db import models
from core.models import TimeStampedModel


class AngelOneSession(TimeStampedModel):
    """Model to store Angel One API session information."""
    client_id = models.CharField(max_length=100)
    auth_token = models.TextField(blank=True)
    feed_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    session_expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.client_id} - {'Active' if self.is_active else 'Inactive'}"


class NSESymbol(TimeStampedModel):
    """Model to store NSE symbol information."""
    symbol = models.CharField(max_length=50)
    token = models.CharField(max_length=50)
    lot_size = models.IntegerField(default=1)
    instrument_type = models.CharField(max_length=20, default='EQ')
    exchange = models.CharField(max_length=10, default='NSE')
    
    # Additional symbol information
    company_name = models.CharField(max_length=200, blank=True)
    isin = models.CharField(max_length=20, blank=True)
    
    class Meta:
        unique_together = ['symbol', 'exchange']
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} ({self.exchange})"


class MarketData(TimeStampedModel):
    """Model to store market data."""
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE, related_name='market_data')
    
    # Price information
    ltp = models.DecimalField(max_digits=12, decimal_places=2, help_text="Last Traded Price")
    open_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    close_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Volume and other data
    volume = models.BigIntegerField(null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Timestamp for the data
    data_timestamp = models.DateTimeField()
    
    class Meta:
        ordering = ['-data_timestamp']
        indexes = [
            models.Index(fields=['symbol', '-data_timestamp']),
            models.Index(fields=['-data_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol.symbol} - ₹{self.ltp} at {self.data_timestamp}"


class APILog(TimeStampedModel):
    """Model to log Angel One API calls."""
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ])
    
    # Request information
    request_data = models.JSONField(blank=True, null=True)
    
    # Response information
    status_code = models.IntegerField()
    response_data = models.JSONField(blank=True, null=True)
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # Error information
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['endpoint', '-created_at']),
            models.Index(fields=['status_code', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code} ({self.response_time_ms}ms)"


class Order(TimeStampedModel):
    """Model to store order information."""
    order_id = models.CharField(max_length=100, unique=True)
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    order_type = models.CharField(max_length=20, choices=[
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('SL', 'Stop Loss'),
        ('SL-M', 'Stop Loss Market'),
    ])
    transaction_type = models.CharField(max_length=10, choices=[
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ])
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    trigger_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Order status
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('OPEN', 'Open'),
        ('COMPLETE', 'Complete'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')
    
    # Execution details
    filled_quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Additional information
    product = models.CharField(max_length=20, default='CNC')
    exchange = models.CharField(max_length=10, default='NSE')
    duration = models.CharField(max_length=10, default='DAY')
    
    # Angel One specific fields
    angel_order_id = models.CharField(max_length=100, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['symbol', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.symbol.symbol} @ ₹{self.price or 'Market'} - {self.status}"


class FilteredSymbolList(TimeStampedModel):
    """Model to store filtered symbol lists by price range."""
    list_name = models.CharField(max_length=100, help_text="Name/description of the filtered list")
    price_range_min = models.DecimalField(max_digits=12, decimal_places=2, help_text="Minimum price filter")
    price_range_max = models.DecimalField(max_digits=12, decimal_places=2, help_text="Maximum price filter")
    total_count = models.IntegerField(help_text="Total number of symbols in this filtered list")
    
    # Optional additional filters
    market_cap_filter = models.CharField(max_length=50, blank=True, help_text="Market cap filter used")
    volume_filter = models.CharField(max_length=50, blank=True, help_text="Volume filter used")
    additional_criteria = models.TextField(blank=True, help_text="Any additional filtering criteria")
    
    # Metadata
    filter_date = models.DateTimeField(auto_now_add=True, help_text="When this filter was applied")
    is_active = models.BooleanField(default=True, help_text="Whether this list is currently active")
    
    class Meta:
        ordering = ['-filter_date']
        unique_together = ['list_name', 'price_range_min', 'price_range_max', 'filter_date']
    
    def __str__(self):
        return f"{self.list_name} (₹{self.price_range_min}-₹{self.price_range_max}) - {self.total_count} symbols"


class FilteredSymbolItem(TimeStampedModel):
    """Model to store individual symbols in a filtered list."""
    filtered_list = models.ForeignKey(FilteredSymbolList, on_delete=models.CASCADE, related_name='symbols')
    symbol = models.ForeignKey(NSESymbol, on_delete=models.CASCADE)
    
    # Price at the time of filtering
    price_at_filter = models.DecimalField(max_digits=12, decimal_places=2, help_text="Price when symbol was added to this list")
    
    # Additional data at time of filtering
    volume_at_filter = models.BigIntegerField(null=True, blank=True)
    market_cap_at_filter = models.BigIntegerField(null=True, blank=True, help_text="Market cap in millions")
    
    class Meta:
        unique_together = ['filtered_list', 'symbol']
        ordering = ['symbol__symbol']
    
    def __str__(self):
        return f"{self.symbol.symbol} in {self.filtered_list.list_name} @ ₹{self.price_at_filter}"

"""Core utility services for the trading platform."""

import logging
from datetime import datetime, time
import pytz
from django.conf import settings
from django.utils import timezone
from .models import LogEntry, Configuration


class MarketService:
    """Service for market-related operations."""
    
    def __init__(self):
        self.timezone = pytz.timezone(settings.MARKET_CONFIG['TIMEZONE'])
        self.market_start = time(*map(int, settings.MARKET_CONFIG['MARKET_START'].split(':')))
        self.market_end = time(*map(int, settings.MARKET_CONFIG['MARKET_END'].split(':')))
        self.trading_days = settings.MARKET_CONFIG['TRADING_DAYS']
    
    def is_market_open(self):
        """Check if NSE is currently open."""
        logger = logging.getLogger('trading_bot')
        current_time = datetime.now(self.timezone).time()
        
        # Check if it's a weekday (0 = Monday, 6 = Sunday)
        current_weekday = datetime.now(self.timezone).weekday()
        is_weekday = current_weekday in self.trading_days
        
        # Check if current time is within market hours
        is_within_hours = self.market_start <= current_time <= self.market_end
        
        if not is_weekday:
            logger.info(f"Market closed: Non-trading day (weekday: {current_weekday})")
            return False
        
        if not is_within_hours:
            logger.info(f"Market closed: Outside trading hours (Current IST: {current_time.strftime('%H:%M')})")
            return False
        
        logger.info(f"Market open: Trading hours active (Current IST: {current_time.strftime('%H:%M')})")
        return True
    
    def get_market_status(self):
        """Get detailed market status information."""
        now = datetime.now(self.timezone)
        current_time = now.time()
        current_weekday = now.weekday()
        
        return {
            'is_open': self.is_market_open(),
            'current_time': current_time.strftime('%H:%M:%S'),
            'current_date': now.date(),
            'current_weekday': current_weekday,
            'is_trading_day': current_weekday in self.trading_days,
            'market_start': self.market_start.strftime('%H:%M'),
            'market_end': self.market_end.strftime('%H:%M'),
            'timezone': str(self.timezone)
        }


class RiskManager:
    """Risk management service."""
    
    def __init__(self):
        self.config = settings.TRADING_CONFIG
        self.logger = logging.getLogger('trading_bot')
        self.logger.info(f"RiskManager initialized: Max positions: {self.config['MAX_POSITIONS']}, "
                        f"Fixed quantity: {self.config['FIXED_QTY']}")
    
    def determine_operation_mode(self, balance):
        """Determine whether to look for new positions or just monitor existing ones."""
        if balance > 0:
            self.logger.info(f"Operation mode: FULL (Balance: {balance}) - Looking for new positions and monitoring existing ones")
            return "FULL"
        else:
            self.logger.info(f"Operation mode: MONITOR_ONLY (Balance: {balance}) - Monitoring existing positions only")
            return "MONITOR_ONLY"
    
    def check_position_size(self, cost, total_portfolio):
        """Check if position size is within limits."""
        position_percentage = (cost / total_portfolio) * 100 if total_portfolio > 0 else 0
        max_position_percent = self.config['MAX_POSITION_SIZE'] * 100
        
        if cost / total_portfolio > self.config['MAX_POSITION_SIZE']:
            self.logger.warning(f"Position size check failed: Cost {cost} is {position_percentage:.2f}% of portfolio {total_portfolio} (max: {max_position_percent}%)")
            return False
        
        self.logger.info(f"Position size check passed: Cost {cost} is {position_percentage:.2f}% of portfolio {total_portfolio}")
        return True
    
    def check_max_positions(self, trades):
        """Check if we can take new positions by counting actual open positions."""
        trades_by_symbol = {}
        for trade in trades:
            symbol = trade.symbol
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(trade)
        
        # Count truly open positions (more buys than sells)
        open_positions = 0
        open_symbols = []
        for symbol, symbol_trades in trades_by_symbol.items():
            buys = len([t for t in symbol_trades if t.action == 'BUY'])
            sells = len([t for t in symbol_trades if t.action == 'SELL'])
            if buys > sells:
                open_positions += 1
                open_symbols.append(symbol)
        
        self.logger.info(f"Current open positions: {open_positions}/{self.config['MAX_POSITIONS']}")
        if open_symbols:
            self.logger.info(f"Open position symbols: {', '.join(open_symbols)}")
        
        return {
            'can_open_more': open_positions < self.config['MAX_POSITIONS'],
            'open_positions': open_positions,
            'open_symbols': open_symbols
        }
    
    def calculate_position_size(self, price, total_portfolio):
        """Calculate the number of shares to buy based on risk management rules."""
        self.logger.info(f"Calculating position size - Price: {price}, Available balance: {total_portfolio}")
        
        # Calculate how many shares we can afford with current balance
        affordable_shares = int(total_portfolio / price) if price > 0 else 0
        fixed_qty = self.config['FIXED_QTY']
        
        if affordable_shares >= fixed_qty:
            self.logger.info(f"Full position possible: Will buy {fixed_qty} shares")
            return fixed_qty
        elif affordable_shares > 0:
            self.logger.info(f"Partial position: Can only afford {affordable_shares}/{fixed_qty} shares")
            return affordable_shares
        else:
            self.logger.warning(f"Cannot open position: Insufficient balance ({total_portfolio}) for even 1 share at {price}")
            return 0


class LoggingService:
    """Service for managing application logging."""
    
    @staticmethod
    def setup_logger(name='trading_bot'):
        """Setup and return a configured logger."""
        logger = logging.getLogger(name)
        
        # Prevent adding multiple handlers if logger already exists
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # File handler for all logs
        fh = logging.FileHandler(settings.BASE_DIR.parent / 'trading_bot.log', encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Console handler for important messages
        import sys
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Create formatters and add to handlers
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
        console_formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S')
        
        fh.setFormatter(file_formatter)
        ch.setFormatter(console_formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger


class ConfigurationService:
    """Service for managing dynamic configuration."""
    
    @classmethod
    def get_config(cls, key, default=None):
        """Get a configuration value."""
        try:
            config = Configuration.objects.get(key=key, is_active=True)
            return config.value
        except Configuration.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, key, value, description=''):
        """Set a configuration value."""
        config, created = Configuration.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        return config
    
    @classmethod
    def get_trading_config(cls):
        """Get all trading-related configuration."""
        return {
            'CHECK_INTERVAL': int(cls.get_config('CHECK_INTERVAL', settings.TRADING_CONFIG['CHECK_INTERVAL'])),
            'MAX_POSITIONS': int(cls.get_config('MAX_POSITIONS', settings.TRADING_CONFIG['MAX_POSITIONS'])),
            'FIXED_QTY': int(cls.get_config('FIXED_QTY', settings.TRADING_CONFIG['FIXED_QTY'])),
            'MAX_POSITION_SIZE': float(cls.get_config('MAX_POSITION_SIZE', settings.TRADING_CONFIG['MAX_POSITION_SIZE'])),
            'MAX_LOSS_PERCENT': float(cls.get_config('MAX_LOSS_PERCENT', settings.TRADING_CONFIG['MAX_LOSS_PERCENT'])),
            'PRICE_THRESHOLD': float(cls.get_config('PRICE_THRESHOLD', settings.TRADING_CONFIG['PRICE_THRESHOLD'])),
        }

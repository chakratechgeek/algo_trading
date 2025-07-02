"""
Trading Signal Generator
======================

This module creates sample trading signals for testing the execution engine.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from trading.models import TradingStrategy, TradingSignal, TradingBot
from angel_api.models import NSESymbol
from portfolio.models import Portfolio
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Generate sample trading signals for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='RELIANCE',
            help='Stock symbol to generate signal for (default: RELIANCE)',
        )
        parser.add_argument(
            '--signal-type',
            type=str,
            choices=['BUY', 'SELL'],
            default='BUY',
            help='Type of signal to generate (default: BUY)',
        )
        parser.add_argument(
            '--price',
            type=float,
            default=2500.0,
            help='Entry price for the signal (default: 2500.0)',
        )
        parser.add_argument(
            '--confidence',
            type=int,
            default=75,
            help='Signal confidence (0-100, default: 75)',
        )
    
    def handle(self, *args, **options):
        """Generate trading signals."""
        symbol_name = options['symbol']
        signal_type = options['signal_type']
        price = Decimal(str(options['price']))
        confidence = options['confidence']
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('[SIGNAL GENERATOR] Creating Trading Signals'))
        self.stdout.write("=" * 60)
        
        try:
            # Get or create test data
            strategy = self._get_or_create_strategy()
            symbol = self._get_or_create_symbol(symbol_name)
            bot = self._get_or_create_bot(strategy)
            
            # Create trading signal
            signal = self._create_signal(strategy, symbol, signal_type, price, confidence)
            
            self.stdout.write(f'[CREATED] {signal_type} signal for {symbol_name}')
            self.stdout.write(f'[PRICE] Entry: ₹{price}')
            self.stdout.write(f'[CONFIDENCE] {confidence}%')
            self.stdout.write(f'[SIGNAL ID] {signal.id}')
            
            self.stdout.write("=" * 60)
            self.stdout.write(self.style.SUCCESS('[SUCCESS] Signal generated successfully!'))
            self.stdout.write("Run the trading bot to execute this signal:")
            self.stdout.write(f"  python manage.py run_trading_bot --bot-id {bot.id} --once --paper-only")
            self.stdout.write("=" * 60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] {e}'))
    
    def _get_or_create_strategy(self):
        """Get or create a test trading strategy."""
        strategy, created = TradingStrategy.objects.get_or_create(
            name='Test Strategy',
            defaults={
                'description': 'Test strategy for signal generation',
                'strategy_type': 'CUSTOM',
                'config_parameters': {
                    'test_mode': True,
                    'max_positions': 5,
                    'stop_loss_percent': 2.0,
                    'take_profit_percent': 5.0
                },
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('[CREATED] Test strategy')
        else:
            self.stdout.write('[FOUND] Existing test strategy')
            
        return strategy
    
    def _get_or_create_symbol(self, symbol_name):
        """Get or create a test symbol."""
        symbol, created = NSESymbol.objects.get_or_create(
            symbol=symbol_name,
            defaults={
                'name': f'{symbol_name} Limited',
                'exchange': 'NSE',
                'instrument_type': 'EQ',
                'lot_size': 1,
                'tick_size': Decimal('0.05'),
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'[CREATED] Symbol {symbol_name}')
        else:
            self.stdout.write(f'[FOUND] Existing symbol {symbol_name}')
            
        return symbol
    
    def _get_or_create_bot(self, strategy):
        """Get or create a test trading bot."""
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_trader',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'Trader'
            }
        )
        
        # Get or create test portfolio
        portfolio, created = Portfolio.objects.get_or_create(
            user=user,
            name='Test Portfolio',
            defaults={
                'description': 'Test portfolio for signal execution',
                'initial_balance': Decimal('100000.00'),  # 1 lakh
                'current_balance': Decimal('100000.00')
            }
        )
        
        if created:
            self.stdout.write('[CREATED] Test portfolio')
        else:
            self.stdout.write('[FOUND] Existing test portfolio')
        
        # Get or create test bot
        bot, created = TradingBot.objects.get_or_create(
            portfolio=portfolio,
            name='Test Bot',
            defaults={
                'strategy': strategy,
                'is_active': True,
                'is_paper_trading': True,  # Default to paper trading
                'max_positions': 5,
                'position_size': Decimal('10.0'),  # 10% per position
                'stop_loss_percent': Decimal('2.0'),
                'take_profit_percent': Decimal('5.0'),
                'check_interval_minutes': 5
            }
        )
        
        if created:
            self.stdout.write('[CREATED] Test trading bot')
        else:
            self.stdout.write('[FOUND] Existing test bot')
            
        return bot
    
    def _create_signal(self, strategy, symbol, signal_type, price, confidence):
        """Create a trading signal."""
        # Calculate target and stop loss prices
        if signal_type == 'BUY':
            target_price = price * Decimal('1.05')  # 5% profit target
            stop_loss_price = price * Decimal('0.98')  # 2% stop loss
        else:  # SELL
            target_price = price * Decimal('0.95')  # 5% profit target
            stop_loss_price = price * Decimal('1.02')  # 2% stop loss
        
        signal = TradingSignal.objects.create(
            strategy=strategy,
            symbol=symbol,
            signal_type=signal_type,
            confidence=Decimal(str(confidence)),
            entry_price=price,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
            signal_strength='STRONG' if confidence >= 80 else 'MODERATE',
            analysis_data={
                'generated_by': 'signal_generator',
                'timestamp': timezone.now().isoformat(),
                'test_signal': True
            },
            is_active=True,
            expires_at=timezone.now() + timezone.timedelta(hours=1)  # Expire in 1 hour
        )
        
        return signal

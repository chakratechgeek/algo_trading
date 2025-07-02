"""Django management command to run the trading bot with execution engine."""

import time
import signal
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from trading.models import TradingBot, TradingSignal, TradingExecution
from trading.execution import trading_executor, order_monitor, risk_manager


class Command(BaseCommand):
    help = 'Run trading bots with order execution'
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--bot-id',
            type=int,
            help='Specific bot ID to run (optional)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit (no continuous loop)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Check interval in seconds (default: 300)',
        )
        parser.add_argument(
            '--paper-only',
            action='store_true',
            help='Force paper trading mode only',
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        bot_id = options.get('bot_id')
        run_once = options.get('once')
        interval = options.get('interval')
        paper_only = options.get('paper_only')
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('[TRADING BOT] Starting Trading Bot Engine'))
        self.stdout.write("=" * 60)
        
        if paper_only:
            self.stdout.write(self.style.WARNING('[MODE] Paper Trading ONLY - No real orders'))
        
        try:
            if bot_id:
                bots = TradingBot.objects.filter(id=bot_id, is_active=True)
                if not bots.exists():
                    self.stdout.write(self.style.ERROR(f'[ERROR] Bot with ID {bot_id} not found or inactive'))
                    return
            else:
                bots = TradingBot.objects.filter(is_active=True)
            
            if not bots.exists():
                self.stdout.write(self.style.WARNING('[WARNING] No active trading bots found'))
                return
            
            self.stdout.write(f'[INFO] Found {bots.count()} active bot(s)')
            
            # Main execution loop
            iteration = 0
            while self.running:
                iteration += 1
                self.stdout.write(f'\n[CYCLE {iteration}] Running trading cycle at {timezone.now().strftime("%H:%M:%S")}')
                
                for bot in bots:
                    if not self.running:
                        break
                    self._run_bot_cycle(bot, paper_only)
                
                if run_once:
                    break
                
                # Wait for next interval
                self.stdout.write(f'[WAIT] Sleeping for {interval} seconds...')
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n[SHUTDOWN] Received interrupt signal'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] {e}'))
        finally:
            self.stdout.write(self.style.SUCCESS('[SHUTDOWN] Trading bot stopped'))
    
    def _run_bot_cycle(self, bot: TradingBot, paper_only: bool = False):
        """Run a single cycle for a trading bot."""
        try:
            self.stdout.write(f'[BOT] Processing {bot.name} (Strategy: {bot.strategy.name})')
            
            # Force paper trading if requested
            original_paper_mode = bot.is_paper_trading
            if paper_only:
                bot.is_paper_trading = True
            
            # 1. Monitor existing positions
            order_monitor.monitor_positions(bot)
            
            # 2. Check for new signals
            new_signals = self._get_pending_signals(bot)
            
            if new_signals.exists():
                self.stdout.write(f'[SIGNALS] Found {new_signals.count()} pending signal(s)')
                
                for signal in new_signals:
                    if not self.running:
                        break
                    self._process_signal(signal, bot)
            else:
                self.stdout.write('[SIGNALS] No new signals to process')
            
            # 3. Update bot statistics
            self._update_bot_stats(bot)
            
            # Restore original paper trading mode
            if paper_only:
                bot.is_paper_trading = original_paper_mode
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[BOT ERROR] {bot.name}: {e}'))
            bot.error_count += 1
            bot.last_error = str(e)
            bot.save()
    
    def _get_pending_signals(self, bot: TradingBot):
        """Get pending signals for the bot's strategy."""
        return TradingSignal.objects.filter(
            strategy=bot.strategy,
            is_active=True,
            is_executed=False
        ).exclude(
            signal_type='HOLD'
        ).order_by('-confidence', '-created_at')
    
    def _process_signal(self, signal: TradingSignal, bot: TradingBot):
        """Process a trading signal."""
        try:
            self.stdout.write(f'[SIGNAL] Processing {signal.signal_type} {signal.symbol.symbol} @ ₹{signal.entry_price}')
            
            # Calculate quantity
            quantity = self._calculate_quantity(signal, bot)
            
            # Validate order with risk manager
            is_valid, validation_message = risk_manager.validate_order(signal, bot, quantity)
            
            if not is_valid:
                self.stdout.write(self.style.WARNING(f'[RISK] Order rejected: {validation_message}'))
                return
            
            # Execute the signal
            execution = trading_executor.execute_signal(signal, bot, quantity)
            
            if execution.status == 'EXECUTED':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[EXECUTED] {signal.signal_type} {quantity} {signal.symbol.symbol} @ ₹{execution.executed_price}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'[FAILED] {execution.error_message}')
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[SIGNAL ERROR] {e}'))
    
    def _calculate_quantity(self, signal: TradingSignal, bot: TradingBot):
        """Calculate appropriate quantity for the signal."""
        # Simple calculation based on confidence and base quantity
        base_quantity = 10  # Base quantity
        
        # Adjust based on confidence
        confidence_multiplier = signal.confidence / 100
        quantity = int(base_quantity * confidence_multiplier)
        
        return max(1, quantity)  # Minimum 1 share
    
    def _update_bot_stats(self, bot: TradingBot):
        """Update bot statistics."""
        try:
            bot.last_run_at = timezone.now()
            bot.total_runs += 1
            bot.save()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[STATS ERROR] {e}'))
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING(f'\n[SIGNAL] Received signal {signum}, shutting down...'))
        self.running = False

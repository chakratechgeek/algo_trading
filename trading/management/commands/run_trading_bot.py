"""Django management command to run the trading bot."""

import time
import signal
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading.models import TradingBot
from trading.services import TradingBotService
from core.services import LoggingService


class Command(BaseCommand):
    help = 'Run trading bots'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.logger = LoggingService.setup_logger('trading_bot')
    
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
    
    def handle(self, *args, **options):
        """Main command handler."""
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        bot_id = options.get('bot_id')
        run_once = options.get('once')
        interval = options.get('interval')
        
        self.stdout.write(
            self.style.SUCCESS('Starting trading bot runner...')
        )
        
        if bot_id:
            self.logger.info(f"Running specific bot: {bot_id}")
            bots = TradingBot.objects.filter(id=bot_id, is_active=True)
        else:
            self.logger.info("Running all active bots")
            bots = TradingBot.objects.filter(is_active=True)
        
        if not bots.exists():
            self.stdout.write(
                self.style.WARNING('No active bots found')
            )
            return
        
        self.logger.info(f"Found {bots.count()} active bot(s)")
        
        # Run trading loop
        try:
            if run_once:
                self._run_bots_once(bots)
            else:
                self._run_bots_continuously(bots, interval)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, stopping...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
        finally:
            self.logger.info("Trading bot runner stopped")
    
    def _run_bots_once(self, bots):
        """Run all bots once."""
        self.logger.info("Running bots once...")
        
        for bot in bots:
            try:
                bot_service = TradingBotService(bot.id)
                bot_service.run_bot_cycle()
                self.stdout.write(f"✓ Bot {bot.name} completed cycle")
            except Exception as e:
                self.logger.error(f"Error running bot {bot.name}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"✗ Bot {bot.name} failed: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS("All bots completed")
        )
    
    def _run_bots_continuously(self, bots, interval):
        """Run bots continuously with specified interval."""
        self.logger.info(f"Running bots continuously with {interval}s interval...")
        
        while self.running:
            start_time = time.time()
            
            # Refresh bot list (in case of configuration changes)
            active_bots = TradingBot.objects.filter(is_active=True)
            
            if not active_bots.exists():
                self.logger.info("No active bots found, waiting...")
                time.sleep(interval)
                continue
            
            self.stdout.write(f"Running cycle at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            for bot in active_bots:
                if not self.running:
                    break
                
                try:
                    bot_service = TradingBotService(bot.id)
                    bot_service.run_bot_cycle()
                    self.stdout.write(f"  ✓ {bot.name}")
                except Exception as e:
                    self.logger.error(f"Error running bot {bot.name}: {e}")
                    self.stdout.write(f"  ✗ {bot.name}: {e}")
            
            # Calculate sleep time
            cycle_time = time.time() - start_time
            sleep_time = max(0, interval - cycle_time)
            
            if self.running and sleep_time > 0:
                self.stdout.write(f"Cycle completed in {cycle_time:.1f}s, sleeping for {sleep_time:.1f}s...")
                time.sleep(sleep_time)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

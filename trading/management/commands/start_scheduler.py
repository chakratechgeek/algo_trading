"""
Trading Strategy Scheduler Management Command
===========================================

Django management command to run the automated trading scheduler.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from trading.scheduler import TradingScheduler


class Command(BaseCommand):
    help = 'Start the automated trading strategy scheduler'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Interval in minutes between strategy runs (default: 10)'
        )
        parser.add_argument(
            '--market-hours-only',
            action='store_true',
            help='Only run during market hours (9:15 AM - 3:30 PM IST)'
        )
        parser.add_argument(
            '--weekdays-only',
            action='store_true',
            help='Only run on weekdays (Monday-Friday)'
        )
    
    def handle(self, *args, **options):
        """Start the automated scheduler."""
        interval = options['interval']
        market_hours_only = options['market_hours_only']
        weekdays_only = options['weekdays_only']
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS('[SCHEDULER] Starting Automated Trading Scheduler'))
        self.stdout.write("=" * 70)
        self.stdout.write(f'[CONFIG] Strategy interval: Every {interval} minutes')
        self.stdout.write(f'[CONFIG] Market hours only: {market_hours_only}')
        self.stdout.write(f'[CONFIG] Weekdays only: {weekdays_only}')
        self.stdout.write("-" * 70)
        
        try:
            # Initialize scheduler with configuration
            scheduler = TradingScheduler()
            scheduler.interval_minutes = interval
            scheduler.market_hours_only = market_hours_only
            scheduler.weekdays_only = weekdays_only
            
            self.stdout.write('[SCHEDULER] Scheduler initialized successfully')
            self.stdout.write('[SCHEDULER] Press Ctrl+C to stop the scheduler')
            self.stdout.write("-" * 70)
            
            # Start the scheduler (this will block)
            scheduler.start_scheduler()
            
        except KeyboardInterrupt:
            self.stdout.write('\n[SCHEDULER] Scheduler stopped by user')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Scheduler failed: {e}'))
            raise
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS('[SCHEDULER] Automated Trading Scheduler Stopped'))
        self.stdout.write("=" * 70)

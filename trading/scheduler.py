"""
Trading Strategy Scheduler
=========================

Automated scheduler for running trading strategies at regular intervals.
"""

import time
import logging
from datetime import datetime, timedelta
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from portfolio.models import Portfolio


class TradingScheduler:
    """Scheduler for automated trading strategy execution."""
    
    def __init__(self):
        self.logger = logging.getLogger('trading_scheduler')
        self.is_running = False
        self.interval_minutes = 10
        self.market_hours_only = True
        self.weekdays_only = True
        
    def start_scheduler(self):
        """Start the automated scheduler."""
        self.logger.info("[SCHEDULER] Starting automated trading scheduler...")
        self.logger.info(f"[CONFIG] Interval: {self.interval_minutes} minutes")
        self.logger.info(f"[CONFIG] Market hours only: {self.market_hours_only}")
        self.logger.info(f"[CONFIG] Weekdays only: {self.weekdays_only}")
        
        self.is_running = True
        
        # Main scheduler loop
        try:
            while self.is_running:
                self._check_and_run_strategy()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("[SCHEDULER] Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"[SCHEDULER] Error: {e}")
        finally:
            self.is_running = False
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.is_running = False
        self.logger.info("[SCHEDULER] Scheduler stopped")
    
    def _check_and_run_strategy(self):
        """Check if it's time to run the strategy and execute it."""
        current_time = timezone.now()
        
        # Check market hours if enabled
        if self.market_hours_only:
            market_start = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
            market_end = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
            
            if not (market_start <= current_time <= market_end):
                return
        
        # Check weekdays if enabled
        if self.weekdays_only and current_time.weekday() >= 5:  # Saturday or Sunday
            return
        
        # Check if it's time to run (every N minutes)
        if current_time.minute % self.interval_minutes == 0 and current_time.second < 30:
            self._run_smallcap_strategy()
    
    def _run_smallcap_strategy(self):
        """Run small-cap strategy for all active portfolios."""
        try:
            self.logger.info("[SCHEDULER] Running small-cap strategy...")
            
            # Get all active portfolios
            active_portfolios = Portfolio.objects.filter(is_active=True)
            
            if not active_portfolios.exists():
                self.logger.warning("[SCHEDULER] No active portfolios found")
                return
            
            for portfolio in active_portfolios:
                try:
                    self.logger.info(f"[SCHEDULER] Running strategy for portfolio {portfolio.id}: {portfolio.name}")
                    
                    # Run the strategy
                    call_command('run_smallcap_strategy', portfolio_id=portfolio.id)
                    
                    self.logger.info(f"[SCHEDULER] Completed strategy for portfolio {portfolio.id}")
                    
                except Exception as e:
                    self.logger.error(f"[SCHEDULER] Error running strategy for portfolio {portfolio.id}: {e}")
            
        except Exception as e:
            self.logger.error(f"[SCHEDULER] Error in small-cap strategy execution: {e}")


def start_automated_trading():
    """Function to start automated trading scheduler."""
    scheduler = TradingScheduler()
    scheduler.start_scheduler()
